#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
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
        self.data_path = {
            'local': getenv('NLPLAB_DATASET_LOCAL_HOME', 'data/datasets'),
            'remote': getenv('NLPLAB_DATASET_REMOTE_HOME', 'datasets')
        }

        self.meta_path = {
            'local': f'{self.data_path["local"]}/meta',
            'remote': f'{self.data_path["remote"]}/meta',
        }

    def read_datasets_meta(self) -> dict:
        result = {}
        for filename in glob(f"{self.meta_path['local']}/*.yaml"):
            with open(filename, 'r') as fp:
                contents = yaml.load(stream=fp, Loader=yaml.FullLoader)
                result[contents['name']] = contents

        return result

    @staticmethod
    def read_corpus(filename: str) -> list:
        result = []
        with bz2.open(filename, 'rb') as fp:
            for line in tqdm(fp, desc=f'read: {filename}'):
                result.append(json.loads(line.decode('utf-8')))

        return result

    def batch(self) -> None:
        # add meta.files: count, columns

        meta = self.read_datasets_meta()

        bar = tqdm(meta.items())
        for name, info in bar:
            for f in info['files']:
                bar.set_description(desc=f"{name}/{f['name']}")

                data = self.read_corpus(
                    filename=f"{self.data_path['local']}/{info['path']['local']}/{f['name']}"
                )

                f['count'] = len(data)
                f['columns'] = {col: 'text' if isinstance(v, str) else 'object' for col, v in data[0].items()}

            filename = f"{self.meta_path['local']}/{name}.yaml"
            with open(filename, 'w') as fp:
                yaml.dump(
                    data=info,
                    stream=fp,
                    default_flow_style=False,
                    allow_unicode=True,
                    explicit_start=True,
                    sort_keys=False,
                )

        return


class DataSets(DataSetsUtils):

    def __init__(self, use_cache: bool = True):
        super().__init__()

        self.minio: MinioUtils = MinioUtils()
        self.elastic: ElasticSearchUtils = ElasticSearchUtils()

        self.use_cache: bool = use_cache

    def push_all_datasets(self) -> None:
        for filename in glob(f"{self.meta_path['local']}/*.yaml"):
            self.push_datasets_meta(filename=basename(filename))

        return None

    def pull_all_datasets(self, meta: dict = None) -> None:
        if meta is None:
            meta = self.pull_datasets_meta()

        bar = tqdm(meta.items())
        for name, info in bar:
            for f in info['files']:
                bar.set_description(desc=f"{name}/{f['name']}")

                local_file = f"{self.data_path['local']}/{info['path']['local']}/{f['name']}"
                if isfile(local_file) and self.use_cache:
                    continue

                self.pull_minio_file(filename=f['name'], info=info)

        return None

    def push_datasets_meta(self, filename: str) -> None:
        self.minio.push(
            local=f"{self.meta_path['local']}/{filename}",
            remote=f"{self.meta_path['remote']}/{filename}",
        )
        return

    def update_meta(self) -> dict:
        return {
            **self.pull_datasets_meta(),
            **self.pull_elasticsearch_meta()
        }

    def pull_datasets_meta(self) -> dict:
        meta_list: list = self.minio.ls(path=self.meta_path['remote'])

        # download meta
        for remote_file in meta_list:
            self.minio.pull(
                local=f"{self.meta_path['local']}/{basename(remote_file)}",
                remote=remote_file
            )

        return self.read_datasets_meta()

    def pull_elasticsearch_meta(self) -> dict:
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

    def load(self, name: str, meta: dict, filename: str = None, use_cache: bool = True,
             source: list = None) -> None or list:
        if meta and name in meta:
            info = meta[name]
        else:
            return None

        self.use_cache = use_cache

        if 'location' not in info:
            if filename:
                return self.load_minio_data(info=info, filename=filename)

            result = []
            for x in info['files']:
                result += self.load_minio_data(info=info, filename=x['name'])

            return result

        if info['location'] == 'elasticsearch':
            return self.load_elasticsearch_data(info=info, name=name, source=source)

        return None

    def load_elasticsearch_data(self, info: dict, name: str, source: list = None) -> list:
        filename = f"{self.data_path['local']}/{info['path']['local']}/{name}.bz2"

        if isfile(filename) is False or self.use_cache is False:
            self.elastic.export(filename=filename, index=name, source=source)

        return self.read_corpus(filename=filename)

    def load_minio_data(self, info: dict, filename: str) -> list:
        local_file = f"{self.data_path['local']}/{info['path']['local']}/{filename}"

        if isfile(local_file) is False or self.use_cache is False:
            self.pull_minio_file(filename=filename, info=info)

        return self.read_corpus(filename=filename)

    def pull_minio_file(self, filename: str, info: dict) -> None:
        self.minio.pull(
            local=f"{self.data_path['local']}/{info['path']['local']}/{filename}",
            remote=f"{self.data_path['remote']}/{info['path']['remote']}/{filename}"
        )
        return

    def push_minio_file(self, info: dict, filename: str) -> None:
        self.minio.push(
            local=f"{self.data_path['local']}/{info['path']['local']}/{filename}",
            remote=f"{self.data_path['remote']}/{info['path']['remote']}/{filename}"
        )

        return None

    def upload(self, info: dict, filename: str = None) -> None:
        return self.push_minio_file(filename=filename, info=info)

    def test(self) -> None:
        # self.push_all_datasets()

        self.pull_all_datasets()

        # self.batch()

        # self.update_meta()
        # print(meta)

        # meta = self.pull_datasets_meta()
        # print(meta)

        # data = self.load(name='daum_movie_reviews', meta=meta)
        # print(data)

        # es_meta = self.pull_elasticsearch_meta()
        # print(es_meta)

        # data = self.load(name='crawler-naver-economy-2021', source='title,content'.split(','), meta=es_meta)
        # print(data)

        return


if __name__ == '__main__':
    DataSets().test()
