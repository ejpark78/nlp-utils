#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
from datetime import datetime
from os.path import isfile
from time import sleep

import pytz
import requests
import urllib3
from tqdm.autonotebook import tqdm

from module.elasticsearch_utils import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MESSAGE = 25

logger = logging.getLogger()


class NaverKBOGameCenterUtils(object):
    """ 응원 댓글 수집 유틸 """

    def __init__(self):
        """ """
        host = 'https://corpus.ncsoft.com:9200'
        index = {
            'comments': 'crawler-naver-kbo_game_center_comments',
            'game_info': 'crawler-naver-kbo_game_center_game_info',
            'relay_text': 'crawler-naver-kbo_game_center_relay_text',
        }

        self.es = {
            'comments': ElasticSearchUtils(host=host, index=index['comments'], split_index=True, tag='2019'),
            'game_info': ElasticSearchUtils(host=host, index=index['game_info'], split_index=False),
            'relay_text': ElasticSearchUtils(host=host, index=index['relay_text'], split_index=False),
        }

        self.sleep_time = 2

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/77.0.3865.90 Safari/537.36'
        }

        return

    def get_game_info(self, game_date, game_id='20190923HHLG02019'):
        """해당 날짜의 경기 정보를 조회한다."""
        url = 'https://sports.news.naver.com/ajax/game/relayGameList.nhn?categoryId=kbo&gameDate=' + game_date

        headers = {
            'referer': 'https://sports.news.naver.com/gameCenter/textRelay.nhn?category=kbo&gameId=' + game_id
        }
        headers.update(self.headers)

        result = requests.get(url, headers=headers).json()

        # 저장
        self.save_game_info(game_list=result['games'])

        return result

    def get_relay_text(self, game_id):
        """ 문자 중계를 조회한다. """
        url = 'https://sports.news.naver.com/ajax/game/relayData.nhn?gameId=' + game_id

        headers = {
            'referer': 'https://sports.news.naver.com/gameCenter/textRelay.nhn?category=kbo&gameId=' + game_id
        }
        headers.update(self.headers)

        try:
            return requests.get(url, headers=headers).json()
        except Exception as e:
            print(e)

        return None

    def get_comments(self, game_id, page):
        """ 댓글 정보를 조회한다."""
        url = 'https://sports.news.naver.com/comments/list_category_comment.nhn?'
        url += 'ticket=sports1'
        url += '&object_id=' + game_id
        url += '&page_no=' + str(page)
        url += '&page_size=8'
        url += '&view_category_ids=0%2C1'
        url += '&page_size_list=8%2C8'

        headers = {
            'referer': 'https://sports.news.naver.com/gameCenter/textRelay.nhn?category=kbo&gameId=' + game_id
        }
        headers.update(self.headers)

        resp = requests.get(url, headers=headers)

        content = resp.content

        try:
            if isinstance(content, bytes):
                content = content.decode('utf-8')

            content = content.replace(r"\'", r"\\'")
            content = content.replace(u'\\x3C', ' ')

            return json.loads(content)
        except Exception as e:
            print(e)

            info = {
                'url': url,
                'headers': headers
            }

            self.save_debug_info(info=info, content=content)

        return None

    @staticmethod
    def save_debug_info(info, content):
        """ 디버깅 정보를 기록한다."""
        try:
            mode = 'w'
            str_info = json.dumps(info)

            if isinstance(content, bytes):
                mode = 'wb'
                str_info = str_info.encode('utf-8')

            dt = datetime.now(pytz.timezone('Asia/Seoul'))
            filename = dt.strftime('error.%Y-%m-%d_%H.%M.%S.log')
            with open(filename, mode) as fp:
                fp.write(str_info + '\n\n')
                fp.write(content)
        except Exception as e:
            print(e)

        return

    @staticmethod
    def save_state(game_id, filename='relay_text.state'):
        """ 현재 상태 정보를 저장한다."""
        try:
            with open(filename, 'a') as fp:
                fp.write(game_id + '\n')
        except Exception as e:
            print(e)

        return

    @staticmethod
    def read_state(filename='relay_text.state'):
        """ 현재 상태 정보를 저장한다."""
        result = {}

        if isfile(filename) is False:
            return result

        try:
            with open(filename, 'r') as fp:
                for game_id in fp.readlines():
                    result[game_id.strip()] = True
        except Exception as e:
            print(e)

        return result

    def save_game_info(self, game_list):
        """ 응원글을 저장한다. """
        for doc in game_list:
            doc['_id'] = '{gameId}'.format(**doc)

            self.es['game_info'].save_document(document=doc, delete=False)

        self.es['game_info'].flush()

        return

    def save_relay_text(self, relay_text, game_id):
        """ 문자 중계 데이터를 저장한다. """
        relay_text['_id'] = game_id

        self.es['relay_text'].save_document(document=relay_text, delete=False)
        self.es['relay_text'].flush()

        return

    def save_comments(self, game_info, team_name, comment_list):
        """ 응원글을 저장한다. """
        self.es['comments'].index = self.es['comments'].get_target_index(
            tag=game_info['game_date'][:4],
            index=self.es['comments'].index,
            split_index=True,
        )

        for doc in comment_list:
            doc['_id'] = '{object_id}-{comment_no}'.format(**doc)
            doc['date'] = doc['registered_ymdt']
            doc['team_name'] = team_name

            doc.update(game_info)

            self.es['comments'].save_document(document=doc, delete=False)

        self.es['comments'].flush()

        return

    def trace_comment_list(self, page, game_id, a_code, h_code, g_date):
        """ 댓글 목록을 조회한다. """
        from time import sleep
        from tqdm.autonotebook import tqdm

        max_page = -1
        max_count = 8

        game_info = {
            'game_date': str(g_date),
            'away_team': a_code,
            'home_team': h_code,
        }
        team_names = [a_code, h_code]

        p_bar = None
        while max_page < 0 or page < max_page:
            comments = self.get_comments(game_id=game_id, page=page)
            if comments is None:
                page += 1
                continue

            category_list = comments['category_list']

            count = []
            for i, team in enumerate(category_list):
                self.save_comments(
                    game_info=game_info,
                    team_name=team_names[i],
                    comment_list=team['comment_list'],
                )

                count.append(len(team['comment_list']))

                if max_page < 0:
                    total_count = team['total_count']

                    team_max_page = int(total_count / max_count) + 2
                    if team_max_page > max_page:
                        max_page = team_max_page

            if max(count) < max_count:
                break

            if p_bar is None:
                p_bar = tqdm(
                    desc='{}: {:,}'.format(game_id, max_page),
                    total=max_page,
                    dynamic_ncols=True
                )

                if page > 2:
                    p_bar.update(page)

            p_bar.update(1)

            page += 1
            self.set_state(game_id=game_id, state=page)

            sleep(self.sleep_time)

        return

    def trace_game_info(self, game_date):
        """ 경기 정보 목록을 조회한다. """
        game_id = '20190923HHLG02019'

        while game_date != '':
            print(game_date)

            game_info = self.get_game_info(game_date=game_date, game_id=game_id)
            game_date = game_info['dates']['prevGameDate']

            game_id = game_info['games'][0]['gameId']

            sleep(self.sleep_time)

        return

    def get_game_list(self):
        """ 게임 목록을 조회한다."""
        query_cond = {
            '_source': ['gameId', 'suspendedInfo', 'state', 'cancelFlag', 'aCode', 'hCode', 'gdate']
        }

        return self.es['game_info'].get_id_list(
            index=self.es['game_info'].index,
            query_cond=query_cond,
        )

    def set_state(self, game_id, state):
        """ done 으로 상태를 변경한다. """
        doc = {
            '_id': game_id,
            'state': state,
        }

        self.es['game_info'].save_document(document=doc, delete=False)
        self.es['game_info'].flush()
        return

    def trace_comments(self):
        """ 응원글 전체를 조회한다. """
        game_list = self.get_game_list()

        for game_id in tqdm(
                sorted(game_list.keys(), reverse=True),
                desc='{:,}'.format(len(game_list))
        ):
            if game_id[:2] != '20':
                continue

            page = 1

            game_info = game_list[game_id]
            if 'state' in game_info:
                if game_info['state'] == 'done':
                    continue

                page = int(game_info['state'])

            if 'cancelFlag' in game_info and game_info['cancelFlag'] != 'N':
                continue

            if 'suspendedInfo' in game_info and game_info['suspendedInfo'] != '':
                continue

            self.trace_comment_list(
                page=page,
                game_id=game_id,
                a_code=game_info['aCode'],
                h_code=game_info['hCode'],
                g_date=str(game_info['gdate']),
            )

            self.set_state(game_id=game_id, state='done')

        return

    def trace_relay_texts(self):
        """ 문자 중계 전체를 조회한다. """
        game_list = self.get_game_list()

        filename = 'relay_text.state'
        state = self.read_state(filename=filename)

        for game_id in tqdm(sorted(game_list.keys(), reverse=True)):
            if game_id in state:
                continue

            game_info = game_list[game_id]

            if 'cancelFlag' in game_info and game_info['cancelFlag'] != 'N':
                continue

            relay_text = self.get_relay_text(game_id=game_id)
            if relay_text is not None:
                self.save_relay_text(game_id=game_id, relay_text=relay_text)

            self.save_state(game_id, filename=filename)
            sleep(self.sleep_time)

        return

    def exports(self):
        """ 코퍼스를 덤프한다. """
        import pandas as pd

        # 게임 정보
        game_info = self.es['game_info'].dump()

        game_info_df = pd.DataFrame(game_info)

        game_info_df['aScore'] = game_info_df['score'].apply(lambda x: x['aScore'])
        game_info_df['hScore'] = game_info_df['score'].apply(lambda x: x['hScore'])

        game_info_df.drop(columns='score', inplace=True)

        game_info_df.to_excel('naver-game-center-game_info-kbo.xlsx', index=False)

        # 댓글
        comments = self.es['comments'].dump()

        comments_df = pd.DataFrame(comments)

        comments_df.to_excel('naver-game-center-comments.xlsx', index=False)

        # 문자 중계
        relay_text = self.es['relay_text'].dump()

        data_list = [k for x in relay_text for v in x['relayTexts'].values() for k in v if isinstance(k, dict)]
        relay_text_df = pd.DataFrame(data_list)

        relay_text_df.fillna('', inplace=True)

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('-trace_comments', action='store_true', default=False, help='응원글 조회')
        parser.add_argument('-trace_relay_texts', action='store_true', default=False, help='문자 중계')
        parser.add_argument('-get_game_info', action='store_true', default=False, help='게임 정보')
        parser.add_argument('-exports', action='store_true', default=False, help='코퍼스 덤프')
        parser.add_argument('-set_state', action='store_true', default=False, help='게임 상태 변경')

        parser.add_argument('-date', default=None, help='게임 날짜')
        parser.add_argument('-game_id', default=None, help='게임 아이디')
        parser.add_argument('-state', default=None, help='상태 정보')

        parser.add_argument('-sleep', default=2, type=int, help='슬립 시간')

        return parser.parse_args()


def main():
    """ """
    utils = NaverKBOGameCenterUtils()

    args = utils.init_arguments()

    utils.sleep_time = args.sleep

    if args.trace_comments:
        utils.trace_comments()
        return

    if args.trace_relay_texts:
        utils.trace_relay_texts()
        return

    if args.get_game_info:
        utils.get_game_info(game_date=args.date)
        return

    if args.exports:
        utils.exports()
        return

    if args.set_state:
        utils.set_state(game_id=args.game_id, state=args.state)
        return

    return


if __name__ == '__main__':
    main()
