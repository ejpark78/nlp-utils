#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from glob import glob
from os.path import isdir, isfile
from time import sleep
from uuid import uuid4

import dataframe_image as dfi
import pandas as pd
import requests
import seaborn as sns
import urllib3
import json
import webvtt
from bs4 import BeautifulSoup
from tqdm import tqdm
from crawler.utils.es import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class YoutubeVttCrawler(object):
    """ 유튜브 자막 유틸입니다."""

    def __init__(self):

        self.sleep = 5

        self.url_list = [
            {
                'url': 'https://www.youtube.com/channel/UCS8OYB0PsSjMNJLf9DpPGdQ/playlists',
                'filename': '100home studio-cmd.json'
            },
            {
                'url': 'https://www.youtube.com/user/googlecloudplatform/playlists?view=1&flow=grid',
                'filename': 'Google Cloud Platform-cmd.json'
            },
            {
                'url': 'https://www.youtube.com/user/TEDtalksDirector/playlists',
                'filename': 'TED-cmd.json'
            },
            {
                'url': 'https://www.youtube.com/user/knowhow0901/playlists',
                'filename': '사람사는세상노무현재단-cmd.json'
            },
            {
                'url': 'https://www.youtube.com/channel/UC22go5LdQEw-iDuxFb4C0hw/playlists?view=1&sort=dd&shelf_id=0',
                'filename': '애니멀봐-cmd.json'
            },
            {
                'url': 'https://www.youtube.com/channel/UCQen5AwxSV3fIDOSM0uqJcA/playlists?view=1&sort=dd&shelf_id=0',
                'filename': '조선총잡이-cmd.json'
            },
            {
                'url': 'https://www.youtube.com/user/thestoryplus/playlists',
                'filename': 'Thestory 더스토리-cmd.json'
            },
            {
                'url': 'https://www.youtube.com/user/MBCworld/playlists',
                'filename': 'MBC global-cmd.json'
            },
            {
                'url': 'https://www.youtube.com/user/jtbcstar/playlists',
                'filename': 'JTBC Voyage-cmd.json'
            },
            {
                'url': 'https://www.youtube.com/channel/UC2mh3isUlxcxh4KshnuRxHw/playlists',
                'filename': '정치초단-cmd.json'
            },
            {
                'url': 'https://www.youtube.com/channel/UCYn09ySlShmzBtYwl1OgOsA/playlists',
                'filename': 'Cheeze Film-cmd.json'
            },
            {
                'url': 'https://www.youtube.com/channel/UC5W3wHMAkp6b_8HrhReP5aQ/playlists',
                'filename': '슈스스TV-cmd.json'
            },
            {
                'url': 'https://www.youtube.com/channel/UCybPxZoFDPR1qbN04daAc2g/playlists',
                'filename': '콬TV-cmd.json'
            },
            {
                'url': 'https://www.youtube.com/user/KBSKpop/playlists',
                'filename': 'KBSKpop-cmd.json'
            },
        ]

    @staticmethod
    def get_play_list(url):
        """ """
        from nested_lookup import nested_lookup

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) ' +
                          'AppleWebKit/537.36 (KHTML, like Gecko) ' +
                          'Chrome/77.0.3865.90 Safari/537.36',
        }

        resp = requests.get(url, headers=headers)

        soup = BeautifulSoup(resp.text)

        init_data = [l for l in resp.text.split('\n') if l.find('ytInitialData') > 0][0]
        init_data = init_data.split('=', maxsplit=1)[-1].rsplit(';', maxsplit=1)[0]

        init_json = json.loads(init_data)

        return nested_lookup('gridPlaylistRenderer', init_json)

    @staticmethod
    def make_cmd(item, proxy):
        """ """
        info = {
            'title': item['title']['runs'][0]['text'],
            'playlistId': item['playlistId'],
            'cmd': 'youtube-dl --skip-download --ignore-errors --no-overwrites --sleep-interval 5 --max-sleep-interval 10',
            'cmd_sub': '--write-sub --all-subs --write-description --write-info-json --write-annotations',
            'cmd_auto_sub': '--write-auto-sub --sub-lang ko,en',
        }

        info['cmd'] += ' ' + proxy

        info['url'] = 'https://www.youtube.com/playlist?list={playlistId}'.format(**info)
        info['all_sub'] = '{cmd} {cmd_sub} "{url}"'.format(**info)
        info['auto_sub'] = '{cmd} {cmd_auto_sub} "{url}"'.format(**info)

        return info

    def batch(self):
        """ """
        play_list = self.get_play_list(url=self.url_list[-1]['url'])

        proxy = ''
        # proxy = '--proxy socks5://127.0.0.1:9150/'

        filename = self.url_list[-1]['filename']
        with open(filename, 'w') as fp:
            print(filename)
            for data in play_list:
                info = self.make_cmd(data, proxy=proxy)
                line = json.dumps(info, ensure_ascii=False) + '\n'

                fp.write(line)

        # cat ../cmd.json| jq -r .subtitle_ko | sh -
        # cat ../cmd.json| jq -r .subtitle | sh -

        # cat ../cmd2.json| jq -r .subtitle | sh -

        # # play_list = []
        # for f_list in tqdm(glob(path + '/list*.json')):
        #     item = json.load(open(f_list, 'r'))
        #     item = nested_lookup('gridPlaylistRenderer', item)
        #
        #     play_list += item

        # # proxy = '--proxy socks5://127.0.0.1:9150/'
        # proxy = ''
        #
        # with open(filename, 'w') as fp:
        #     print(filename)
        #     for data in play_list:
        #         info = make_cmd(data, proxy=proxy)
        #         line = json.dumps(info, ensure_ascii=False) + '\n'
        #
        #         fp.write(line)

        return


class VikiCrawler(object):
    """ Viki 자막 유틸입니다."""

    def __init__(self):
        """생성자"""

        self.sleep = 5

    def batch_collection(self):
        """ """
        # category = 'viki'
        # url_list = self.trace_collection_list(category=category, start=start, end=end)
        # self.get_collection_info(category=category, url_list=url_list)

        category = 'fan'
        url_list = self.trace_collection_list(category=category, start=1, end=84)
        self.get_collection_info(category=category, url_list=url_list)
        return

    def get_collection_info(self, category, url_list):
        """ 컬랙션 전체 정보를 조회한다."""
        for collection in tqdm(url_list):
            base = collection.split('-')[0]

            filename = 'collection_info/{category}/{collection}.json'.format(
                category=category,
                collection=base.rsplit('/')[-1]
            )
            if isfile(filename) is True:
                print('skip', filename)
                continue

            buf = []
            for page in range(1, 200):
                u = '{base}/items.json?per_page=10&page={page}'.format(base=base, page=page)
                print(collection, u, len(buf))

                resp = requests.get(u, verify=False).json()
                if resp is None or resp['value'] is None:
                    continue

                buf += resp['value']

                sleep(self.sleep)
                if resp['more'] is False:
                    break

            with open(filename, 'w') as fp:
                fp.write(json.dumps(buf, indent=4, ensure_ascii=False) + '\n')

        return

    def trace_collection_list(self, category, start, end):
        """ 컬랙션 목록을 조회한다."""
        list_frame = 'https://www.viki.com/collections/{category}?page={page}'

        css = 'div > div.card-content.emphasis > h3 > a'

        result = []
        for page in range(start, end + 1):
            u = list_frame.format(category=category, page=page)
            print(u, len(result))

            resp = requests.get(u, verify=False)
            soup = BeautifulSoup(resp.content, 'lxml')

            a_list = soup.select(css)
            url_list = ['https://www.viki.com' + x['href'] for x in a_list if x.has_attr('href') if x['href'][0] == '/']

            result += url_list

            filename = 'collection_info/{category}/page.{page}.json'.format(category=category, page=page)
            with open(filename, 'w') as fp:
                fp.write(json.dumps(url_list, indent=4, ensure_ascii=False) + '\n')

            sleep(self.sleep)

        return list(set(result))

    def trace_language_list(self, lang, start, end):
        """드라마 목록을 조회한다."""
        list_frame = 'https://www.viki.com/explore?language={lang}&page={page}'

        css = 'div.row div.card.explore-results div.fade.explore-content ' \
              'div.thumbnail-description.dropdown-menu-wrapper a'

        result = []
        for page in range(start, end + 1):
            u = list_frame.format(lang=lang, page=page)
            print(u)

            resp = requests.get(u, verify=False)
            soup = BeautifulSoup(resp.content, 'lxml')

            a_list = soup.select(css)

            url_list = ['https://www.viki.com' + x['href'] for x in a_list if x.has_attr('href') if x['href'][0] == '/']
            result += url_list

            filename = 'data/{lang}.{page}.list'.format(lang=lang, page=page)
            with open(filename, 'w') as fp:
                fp.write('\n'.join(url_list) + '\n')

            sleep(self.sleep)

        return list(set(result))

    @staticmethod
    def make_cmd(url_list, proxy=''):
        """youtube-dl 쉘 명령어를 생성한다."""
        # '--proxy socks5://127.0.0.1:9050/'

        home = '/home/ejpark/workspace/mt/data/viki/data/'

        args = ' '.join([
            '--verbose',
            '--skip-download',
            '--ignore-errors',
            '--no-overwrites',
            '--sleep-interval 5',
            '--max-sleep-interval 10',
            '--write-sub',
            '--all-subs',
            '--write-description',
            '--write-info-json',
            '--write-annotations',
            '--limit-rate 1k',
            proxy
        ])

        cmd = 'echo "{d_name}" && mkdir -p "{d_name}" && cd "{d_name}" && pwd && ' \
              'youtube-dl {args} "{url}" ; sleep 3 ; cd {home} && echo'

        result = []
        for url in url_list:
            d_name = url.split('/')[-1]
            result.append(cmd.format(d_name=d_name, url=url, args=args, home=home))

        return result

    def batch_trace_language(self):
        """ """
        # %load_ext autoreload
        # %autoreload 2

        # lang = 'ko'
        # url_list = self.trace_language_list(lang=lang, start=1, end=2)

        lang = 'en'
        url_list = self.trace_language_list(lang=lang, start=1, end=8)

        # '--proxy socks5://127.0.0.1:9150/'
        cmd_list = self.make_cmd(url_list=url_list, proxy='')

        with open('{}.sh'.format(lang), 'w') as fp:
            fp.write('\n'.join(cmd_list) + '\n')

        return


class VttUtils(object):
    """ 자막 취합 유틸입니다."""

    def __init__(self):
        """생성자"""
        self.lang_pair = [
            'ko-en',
            'ko-ja', 'ko-zh', 'ko-tw', 'ko-vi', 'ko-th', 'ko-id',
            'en-ja', 'en-zh', 'en-tw', 'en-vi', 'en-th', 'en-id',
        ]

        host_info = {
            'host': 'https://corpus.ncsoft.com:9200',
            'http_auth': 'elastic:nlplab',
        }

        self.elastic = ElasticSearchUtils(**host_info)

    @staticmethod
    def get_lang_list(df_list):
        """ 전체 언어 목록을 반환한다."""
        result = set()
        for name in tqdm(df_list):
            df = df_list[name]

            result.update(df.columns)

        return list(result)

    def import_vtt(self, index):
        """ vtt 를 elasticsearch 에 입력한다."""
        # !curl -X DELETE -u elastic:nlplab https://corpus.ncsoft.com:9200/crawler-viki

        df_list = self.read_vtt(home='.')

        for name in df_list:
            df = df_list[name]

            for i, row in tqdm(df.iterrows(), total=len(df), desc=name):
                doc = dict(row)

                doc['_id'] = str(uuid4())

                self.elastic.save_document(index=index, document=doc)

            self.elastic.flush()

        return

    @staticmethod
    def merge_vtt(path):
        """ 다국어 자막을 합해서 반환한다."""
        file_list = sorted(glob('{}/*.vtt'.format(path)))

        prev = ''
        data = {}
        for f_vtt in tqdm(file_list, desc=path):
            title, lang = f_vtt.split('/')[-1].replace('.vtt', '').rsplit('.', maxsplit=1)

            try:
                vtt = webvtt.read(f_vtt)
            except Exception as e:
                print('error:', f_vtt, str(e))
                continue

            for caption in vtt:
                text = caption.text.strip()
                start = caption.start.strip()
                end = caption.end.strip()

                token = text.split('\n')
                if token[0] == prev:
                    text = '\n'.join(token[1:])

                if text != '':
                    if title not in data:
                        data[title] = {}

                    if start not in data[title]:
                        data[title][start] = {}

                    data[title][start]['start'] = start
                    data[title][start]['end'] = end
                    data[title][start]['title'] = title
                    data[title][start][lang] = text

                    prev = text

        df_data = []
        for title in data:
            for start in sorted(data[title]):
                df_data.append(data[title][start])

        return pd.DataFrame(df_data).fillna('').reset_index().drop(columns=['index'])

    def count_lang(self, df_list):
        """ 언어쌍별 수량을 집계한다."""
        result = []
        for name in df_list:
            df = df_list[name]

            item = {}
            for lp in self.lang_pair:
                l1, l2 = lp.split('-', maxsplit=1)

                item[lp] = 0
                if l1 not in df or l2 not in df:
                    continue

                lang_df = df[(df[l1] != '') & (df[l2] != '')]
                item[lp] = len(lang_df)

            item.update({
                'name': name,
                'total': len(df),
            })

            result.append(item)

        return result

    def read_vtt(self, home):
        """전체 자막을 로딩한다."""
        result = {}
        for path in tqdm(glob('{home}/data/*'.format(home=home))):
            if isdir(path) is False:
                continue

            result[path.split('/')[-1]] = self.merge_vtt(path=path)

        return result

    def get_count_table(self, df_list):
        """수량 테이블을 반환한다."""
        count_data = self.count_lang(df_list=df_list)

        df = pd.DataFrame(count_data).set_index('name')

        df.loc['total'] = df.sum()

        styler = df.style.format('{:,.0f}').set_properties(**{'text-align': 'right'})

        u = styler.index.get_level_values(0)

        return styler.background_gradient(
            cmap=sns.light_palette("seagreen", as_cmap=True),
            subset=pd.IndexSlice[u[:-1], styler.columns[:-1]]
        )

    def batch(self):
        """ """
        # %load_ext autoreload
        # %autoreload 2
        df_list = self.read_vtt(home='.')

        styled_table = self.get_count_table(df_list=df_list)
        dfi.export(styled_table, 'viki.png', max_rows=-1)

        return styled_table


if __name__ == '__main__':
    VttUtils().batch()
