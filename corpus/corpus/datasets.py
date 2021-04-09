#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
import sys
from glob import glob
from os import getenv
from os.path import basename, isfile

import urllib3
import yaml
from tqdm import tqdm

from corpus.utils.elasticsearch_utils import ElasticSearchUtils
from corpus.utils.minio_utils import MinioUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class DataSetsUtils(object):

    def __init__(self):
        self.params = {}

        self.data_path = {
            'local': getenv('DATASETS_LOCAL_HOME', 'data/datasets'),
            'remote': getenv('DATASETS_REMOTE_HOME', 'datasets')
        }

        self.meta_path = {
            'local': f'{self.data_path["local"]}/meta',
            'remote': f'{self.data_path["remote"]}/meta',
        }

        self.elastic: ElasticSearchUtils = ElasticSearchUtils()

    def read_datasets_meta(self) -> dict:
        result = {}
        for filename in glob(f"{self.meta_path['local']}/*.yaml"):
            with open(filename, 'r') as fp:
                contents = yaml.load(stream=fp, Loader=yaml.FullLoader)
                result[contents['name']] = contents

        return result

    @staticmethod
    def read_corpus(filename: str, limit: int = -1) -> (list, dict):
        count, result, settings = 0, [], None
        with bz2.open(filename, 'rb') as fp:
            for line in tqdm(fp, desc=f'Read: {filename}'):
                doc = json.loads(line.decode('utf-8'))
                if settings is None and 'settings' in doc:
                    settings = doc
                    continue

                result.append(doc)

                count += 1
                if limit > 0 and count < limit:
                    break

        return result, settings

    def _update_file_info(self, info: dict, file_info: dict, corpus_count: dict) -> None:
        name = file_info['name']

        filename = f"{self.data_path['local']}/{info['path']['local']}/{name}"
        data, settings = self.read_corpus(limit=10, filename=filename)

        file_info['count'] = corpus_count[name] if name in corpus_count else -1

        if settings:
            file_info['columns'] = self.elastic.get_index_columns(mappings={'index': settings})['index']
            return

        file_info['columns'] = {col: 'text' if isinstance(v, str) else 'object' for col, v in data[-1].items()}
        return

    def _read_corpus_count(self, info: dict) -> dict:
        filename = f"{self.data_path['local']}/{info['path']['local']}/corpus.count"
        if isfile(filename) is False:
            return {}

        result = {}
        with open(filename, 'r') as fp:
            for x in fp.readlines():
                token = x.strip().split('\t')
                result[token[0]] = int(token[1])

        return result

    def filter_columns(self) -> None:
        exclude = self.params['exclude'].split(',')

        for line in sys.stdin:
            doc = json.loads(line)

            for col in exclude:
                if col not in doc:
                    continue

                del doc[col]

            print(json.dumps(doc, ensure_ascii=False))

        return None

    def update_datasets_meta(self, include: set = None) -> None:
        # add meta.files: count, columns
        meta = self.read_datasets_meta()

        bar = tqdm(meta.items())
        for name, info in bar:
            if include and name not in include:
                continue

            # read corpus count
            corpus_count = self._read_corpus_count(info=info)

            # read local files
            files = [basename(x) for x in glob(f"{self.data_path['local']}/{info['path']['local']}/*.json.bz2")]
            if 'files' not in info or len(info['files']) == 0:
                info['files'] = [{'name': x} for x in files]

            # update files
            for file_info in info['files']:
                bar.set_description(desc=f"{name}/{file_info['name']}")
                self._update_file_info(info=info, file_info=file_info, corpus_count=corpus_count)

            # save updated file
            with open(f"{self.meta_path['local']}/{name}.yaml", 'w') as fp:
                yaml.dump(
                    data=info,
                    stream=fp,
                    default_flow_style=False,
                    allow_unicode=True,
                    explicit_start=True,
                    sort_keys=False,
                )

        return None


class DataSets(DataSetsUtils):

    def __init__(self, use_cache: bool = True):
        super().__init__()

        self.minio: MinioUtils = MinioUtils()

        self.use_cache: bool = use_cache

    def _upload(self, info: dict, filename: str) -> None:
        self.minio.push(
            local=f"{self.data_path['local']}/{info['path']['local']}/{filename}",
            remote=f"{self.data_path['remote']}/{info['path']['remote']}/{filename}"
        )

        return None

    def _download(self, filename: str, info: dict) -> None:
        self.minio.pull(
            local=f"{self.data_path['local']}/{info['path']['local']}/{filename}",
            remote=f"{self.data_path['remote']}/{info['path']['remote']}/{filename}"
        )
        return

    def _upload_datasets_meta(self, filename: str) -> None:
        self.minio.push(
            local=f"{self.meta_path['local']}/{filename}",
            remote=f"{self.meta_path['remote']}/{filename}",
        )
        return

    def _download_datasets_meta(self) -> dict:
        meta_list: list = self.minio.ls(path=self.meta_path['remote'])

        # download meta
        for remote_file in meta_list:
            self.minio.pull(
                local=f"{self.meta_path['local']}/{basename(remote_file)}",
                remote=remote_file
            )

        return self.read_datasets_meta()

    def _download_elasticsearch_meta(self) -> dict:
        mappings: dict = self.elastic.get_index_columns()

        result = {}
        for item in self.elastic.get_index_size():
            index: str = item['index']

            if index not in mappings:
                continue

            result[index] = {
                'name': index,
                'count': item['count'],
                'columns': mappings[index],
                'location': 'elasticsearch',
                'path': {
                    'local': 'elasticsearch'
                },
            }

        return result

    def _load_datasets(self, info: dict, filename: str) -> list:
        local_file = f"{self.data_path['local']}/{info['path']['local']}/{filename}"

        if isfile(local_file) is False or self.use_cache is False:
            self._download(filename=filename, info=info)

        return self.read_corpus(filename=local_file)[0]

    def _load_elasticsearch_corpus(self, info: dict, name: str, source: list = None) -> list:
        local_file = f"{self.data_path['local']}/{info['path']['local']}/{name}.bz2"

        if isfile(local_file) is False or self.use_cache is False:
            self.elastic.export(filename=local_file, index=name, source=source)

        return self.read_corpus(filename=local_file)[0]

    def load(self, name: str, meta: dict, filename: str = None, use_cache: bool = True,
             source: list = None) -> None or list:
        if meta and name in meta:
            info = meta[name]
        else:
            return None

        self.use_cache = use_cache

        if 'location' in info and info['location'] == 'elasticsearch':
            return self._load_elasticsearch_corpus(info=info, name=name, source=source)

        # single file
        if filename:
            return self._load_datasets(info=info, filename=filename)

        # multiple files
        result = []
        for x in info['files']:
            result += self._load_datasets(info=info, filename=x['name'])

        return result

    def upload_datasets(self, include: set = None, meta_only: bool = False) -> None:
        meta = self.read_datasets_meta()

        # upload meta & corpus
        bar = tqdm(meta.items())
        for name, info in bar:
            bar.set_description(desc=name)

            if include and name not in include:
                continue

            self._upload_datasets_meta(filename=f'{name}.yaml')

            if meta_only is True:
                continue

            for file_info in info['files']:
                bar.set_description(desc=f"{name}/{file_info['name']}")

                self._upload(info=info, filename=file_info['name'])

        return None

    def download_datasets(self, meta: dict = None) -> None:
        if meta is None:
            meta = self._download_datasets_meta()

        bar = tqdm(meta.items())
        for name, info in bar:
            for file_info in info['files']:
                bar.set_description(desc=f"{name}/{file_info['name']}")

                local_file = f"{self.data_path['local']}/{info['path']['local']}/{file_info['name']}"
                if isfile(local_file) and self.use_cache:
                    continue

                self._download(filename=file_info['name'], info=info)

        return None

    def get_meta(self, name: str = 'all') -> dict:
        if name == 'all':
            return {
                **self._download_datasets_meta(),
                **self._download_elasticsearch_meta()
            }

        if name == 'datasets':
            return self._download_datasets_meta()

        if name == 'elasticsearch':
            return self._download_elasticsearch_meta()

        return {}

    def test(self) -> None:
        """
        self.download_datasets()
        self.upload_datasets(include={'wiki'})

        self.update_datasets_meta()

        self.update_meta()
        print(meta)

        meta = self.get_meta('datasets')
        print(meta)

        data = self.load(name='daum_movie_reviews', meta=meta)
        print(data)

        es_meta = self.get_meta('elasticsearch')
        print(es_meta)

        data = self.load(name='crawler-naver-economy-2021', source='title,content'.split(','), meta=es_meta)
        print(data)
        """

        self.params = self.init_arguments()

        if self.params['filter_columns']:
            self.filter_columns()
        else:
            name = 'naver-terms'

            self.update_datasets_meta(include={name})

            self.upload_datasets(include={name}, meta_only=False)

            # meta = self.get_meta('datasets')

        return

    @staticmethod
    def init_arguments() -> dict:
        import argparse

        parser = argparse.ArgumentParser(description='')

        parser.add_argument('--filter-columns', action='store_true', default=False, help='컬럼 필터')

        parser.add_argument('--exclude', default='_index,json', type=str, help='제외할 컬럼 목록')

        return vars(parser.parse_args())


if __name__ == '__main__':
    DataSets().test()
