#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import os
from datetime import datetime
from os.path import isfile
from time import sleep

import pytz
import requests
import urllib3
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY

from module.utils.elasticsearch_utils import ElasticSearchUtils
from module.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class NaverKBOGameCenterUtils(object):
    """ 응원 댓글 수집 유틸 """

    def __init__(self):
        """ """
        self.host = os.getenv('ELASTIC_SEARCH_HOST', 'https://corpus.ncsoft.com:9200')
        self.auth = os.getenv('ELASTIC_SEARCH_AUTH', 'crawler:crawler2019')
        self.index = {
            'comments': os.getenv('ELASTIC_SEARCH_INDEX_COMMENTS', 'crawler-naver-kbo_game_center_comments'),
            'game_info': os.getenv('ELASTIC_SEARCH_INDEX_GAME_INFO', 'crawler-naver-kbo_game_center_game_info'),
            'relay_text': os.getenv('ELASTIC_SEARCH_INDEX_RELAY_TEXT', 'crawler-naver-kbo_game_center_relay_text'),
        }

        self.timeout = 30
        self.sleep_time = 2

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/81.0.4044.113 '
                          'Safari/537.36'
        }

        self.es = {}
        self.open_elasticsearch()

        self.logger = Logger()

        return

    def open_elasticsearch(self):
        """ 엘라스틱서치에 연결한다."""
        self.es = {
            'comments': ElasticSearchUtils(
                host=self.host,
                http_auth=self.auth,
                index=self.index['comments'],
                split_index=True,
                tag='2019'
            ),
            'game_info': ElasticSearchUtils(
                host=self.host,
                http_auth=self.auth,
                index=self.index['game_info'],
                split_index=False
            ),
            'relay_text': ElasticSearchUtils(
                host=self.host,
                http_auth=self.auth,
                index=self.index['relay_text'],
                split_index=False
            ),
        }

        return

    def get_game_info_by_date(self, game_date, game_id='20190923HHLG02019'):
        """해당 날짜의 경기 정보를 조회한다."""
        url = 'https://sports.news.naver.com/ajax/game/relayGameList.nhn?categoryId=kbo&gameDate=' + game_date

        headers = {
            'referer': 'https://sports.news.naver.com/gameCenter/textRelay.nhn?category=kbo&gameId=' + game_id
        }
        headers.update(self.headers)

        resp = requests.get(url, headers=headers, timeout=self.timeout, verify=False)
        if resp.content == b'':
            return None

        result = resp.json()

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

        resp = ''
        try:
            resp = requests.get(url, headers=headers, timeout=self.timeout, verify=False)
            return resp.json()
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '문자 중계 조회 에러',
                'text': resp.text,
                'exception': str(e),
            })

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

        resp = requests.get(url, headers=headers, timeout=self.timeout, verify=False)

        content = resp.content

        try:
            if isinstance(content, bytes):
                content = content.decode('utf-8')

            content = content.replace(r"\'", r"\\'")
            content = content.replace(r"\>", r'>')
            content = content.replace(u'\\x3C', ' ')

            return json.loads(content)
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '댓글 파싱 에러',
                'content': content,
                'exception': str(e),
            })

            info = {
                'url': url,
                'headers': headers
            }

            self.save_debug_info(info=info, content=content)

        return None

    def save_debug_info(self, info, content):
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
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '디버깅 정보 저장 에러',
                'info': info,
                'exception': str(e),
            })

        return

    def save_state(self, game_id, filename='relay_text.state'):
        """ 현재 상태 정보를 저장한다."""
        try:
            with open(filename, 'a') as fp:
                fp.write(game_id + '\n')
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '현재 상태 저장 에러',
                'filename': filename,
                'exception': str(e),
            })

        return

    def read_state(self, filename='relay_text.state'):
        """ 현재 상태 정보를 저장한다."""
        result = {}

        if isfile(filename) is False:
            return result

        try:
            with open(filename, 'r') as fp:
                for game_id in fp.readlines():
                    result[game_id.strip()] = True
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '현재 상태 정보 읽기 에러',
                'filename': filename,
                'exception': str(e),
            })

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
        max_page = -1
        max_count = 8

        game_info = {
            'game_date': str(g_date),
            'away_team': a_code,
            'home_team': h_code,
        }
        team_names = [a_code, h_code]

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

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '응원 댓글 조회',
                'page': page,
                'game_id': game_id,
                'game_date': game_info['game_date'],
                'max_page': max_page,
            })

            page += 1
            self.set_state(game_id=game_id, state=page)

            sleep(self.sleep_time)

        return

    def trace_game_info(self, game_date):
        """ 경기 정보 목록을 조회한다. """

        game_id = ''
        while game_date != '':
            print(game_date)

            game_info = self.get_game_info_by_date(game_date=game_date, game_id=game_id)
            if game_info is None:
                continue

            game_date = game_info['dates']['prevGameDate']

            game_id = game_info['games'][0]['gameId']

            sleep(self.sleep_time)

        return

    def get_game_list(self, gdate):
        """ 게임 목록을 조회한다."""
        query_cond = {
            '_source': ['gameId', 'suspendedInfo', 'state', 'cancelFlag', 'aCode', 'hCode', 'gdate'],
            'query': {
                'bool': {
                    'must': [
                        {
                            'match': {
                                'gdate': gdate
                            }
                        }
                    ],
                    'must_not': [
                        {
                            'match': {
                                'cancelFlag': 'Y'
                            }
                        }
                    ]
                }
            }
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

    def trace_comments(self, date_range):
        """ 응원글 전체를 조회한다. """
        date_list = self.get_date_list(date_range=date_range)

        for dt in date_list:
            game_list = self.get_game_list(gdate=dt.strftime('%Y%m%d'))

            for game_id in sorted(game_list.keys(), reverse=True):
                game_info = game_list[game_id]

                page = 1
                if 'state' in game_info and isinstance(game_info['state'], str) and game_info['state'].isdecimal():
                    page = int(game_info['state'])

                self.trace_comment_list(
                    page=page,
                    game_id=game_info['gameId'],
                    a_code=game_info['aCode'],
                    h_code=game_info['hCode'],
                    g_date=str(game_info['gdate']),
                )

                self.set_state(game_id=game_info['gameId'], state='done')

        return

    def trace_relay_texts(self, game_list):
        """ 문자 중계 전체를 조회한다. """
        if len(game_list.keys()) == 0:
            return

        i = 0
        for game_id in sorted(game_list.keys(), reverse=True):
            game_info = game_list[game_id]

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '문자 중계 조회',
                'i': i,
                'size': len(game_list),
                'game_id': game_id,
                'gdate': game_info['gdate'],
                'hFullName': game_info['hFullName'],
                'aFullName': game_info['aFullName'],
            })

            i += 1

            if 'cancelFlag' in game_info and game_info['cancelFlag'] == 'Y':
                continue

            relay_text = self.get_relay_text(game_id=game_id)
            if relay_text is not None:
                self.save_relay_text(game_id=game_id, relay_text=relay_text)

            sleep(self.sleep_time)

        return

    @staticmethod
    def get_date_list(date_range):
        """ """
        timezone = pytz.timezone('Asia/Seoul')
        yesterday = datetime.now(timezone) + relativedelta(days=-1)

        date_list = [yesterday]
        if date_range is not None:
            token = date_range.split('~', maxsplit=1)

            dt_start = parse_date(token[0])
            dt_end = yesterday.strftime('%Y-%m-%d')

            if len(token) > 1:
                dt_end = parse_date(token[1])

            date_list = list(rrule(DAILY, dtstart=dt_start, until=dt_end))

        return date_list

    def get_game_info(self, date_range=None):
        """ 어제 경기 정보와 문자 중계를 조회한다. """
        date_list = self.get_date_list(date_range=date_range)

        game_list = {}
        for dt in date_list:
            game_date = dt.strftime('%Y%m%d')

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '경기 정보 조회',
                'game_date': game_date,
            })

            info = self.get_game_info_by_date(game_date=game_date)
            if info is None:
                continue

            for g in info['games']:
                game_list[g['gameId']] = g

            sleep(self.sleep_time)

        self.trace_relay_texts(game_list=game_list)

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--game_info', action='store_true', default=False, help='날짜 범위안의 게임 정보')
        parser.add_argument('--trace_comments', action='store_true', default=False, help='응원글 조회')
        parser.add_argument('--set_state', action='store_true', default=False, help='게임 상태 변경')

        parser.add_argument('--date_range', default=None, help='게임 날짜 범위, 미지정시 어제 날짜')

        parser.add_argument('--state', default=None, help='상태 정보')
        parser.add_argument('--game_id', default=None, help='게임 아이디')

        parser.add_argument('--sleep', default=2, type=int, help='슬립 시간')

        return parser.parse_args()


def main():
    """ """
    utils = NaverKBOGameCenterUtils()

    args = utils.init_arguments()

    utils.sleep_time = args.sleep

    if args.game_info:
        utils.get_game_info(date_range=args.date_range)

    if args.trace_comments:
        utils.trace_comments(date_range=args.date_range)

    if args.set_state:
        utils.set_state(game_id=args.game_id, state=args.state)
        return

    return


if __name__ == '__main__':
    main()
