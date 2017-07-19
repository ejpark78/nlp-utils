#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import json
import time

from datetime import datetime

from sqlalchemy import *
from slackclient import SlackClient


class NCSlackBot:
    """
    슬랙 봇
    """

    def __init__(self):
        self.team_alias = {
            'HH': '한화',
            'SS': '삼성',
            'OB': '두산',
            'SK': 'SK',
            'LT': '롯데',
            'LG': 'LG',
            'KT': 'KT',
            'NC': 'NC',
            'WO': '넥센',
            'HD': '현대',
            'SB': '쌍방울',
            'HT': 'KIA'
        }

        self.bot_token = {
            'kmat': 'xoxb-174737823697-ykwsRKY2oIjGvKbBJASQB2mB',
            'search': 'xoxb-174664305860-7YMJQTG5imvKA41YGr0Hx8V8',
            'summarization': 'xoxb-174771318582-iENlD1DYrsfGjcfEBxQhwlZr'
        }


    def get_channel_list(self, bot_name):
        """
        채널 목록 표시
        """
        slack_client = SlackClient(self.bot_token[bot_name])

        api_call = slack_client.api_call("channels.list")

        result = {}
        if api_call.get('ok'):
            channels = api_call.get('channels')

            for channel in channels:
                result[channel['name']] = channel['id']

        print(json.dumps(result, indent=4, ensure_ascii=False), flush=True)
        return result

    def get_bot_id(self, bot_name):
        """
        token 과 봇 이름으로 아이디 반환
        """
        slack_client = SlackClient(self.bot_token[bot_name])

        api_call = slack_client.api_call("users.list")

        if api_call.get('ok'):
            users = api_call.get('members')

            for user in users:
                if 'name' in user and user.get('name') == bot_name:
                    return user.get('id')
        else:
            print("could not find bot user with the name " + bot_name)

        return None

    @staticmethod
    def monitoring_channel(token):
        """
        대화 모니터핑
        """
        slack_client = SlackClient(token)

        if slack_client.rtm_connect() is True:
            while True:
                ret = slack_client.rtm_read()
                if len(ret) > 0:
                    print(ret)

                time.sleep(1)

        return

    def parse_team_info(self, team_code):
        """
        팀명 반환
        """
        teams_token = team_code.split(r',')

        if teams_token[0] in self.team_alias:
            teams_token[0] = self.team_alias[teams_token[0]]

        if len(teams_token) > 1 and teams_token[1] in self.team_alias:
            teams_token[1] = self.team_alias[teams_token[1]]

        return teams_token

    @staticmethod
    def get_summary_text(str_summary):
        """
        요약 결과 반환
        """
        summary = json.loads(str_summary)

        output = {}
        for item in summary['output']:
            output[item['SEQ']] = item['SENT_TEXT']

        buf = []
        for key in sorted(output.keys()):
            buf.append(output[key])

        return '\n'.join(buf)

    @staticmethod
    def get_summary(db_info):
        """
        가장 최근 요약문 반환
        """
        url = 'mysql+pymysql://{user}:{passwd}@{host}:{port}/{db_name}?charset=utf8mb4'.format(**db_info)
        print('url: ', url)

        engine = create_engine(url)

        with engine.connect() as connection:
            # 가장 최근 한 경기 선택
            query = "SELECT * FROM `ap_event_slack` WHERE pushed=0 ORDER BY token DESC LIMIT 1"
            query_result = connection.execute(text(query))

            if query_result is None:
                return None

            row = query_result.fetchone()
            if row is None:
                return None

            query = "UPDATE `ap_event_slack` SET pushed=1 WHERE token='{}'".format(row['token'])
            connection.execute(text(query))

        return row

    @staticmethod
    def parse_slack_message(slack_rtm_message):
        """
        봇에서 호출 받았을 때, 메세지 분리
        """
        if slack_rtm_message and len(slack_rtm_message) > 0:
            for output in slack_rtm_message:
                if 'text' in output:
                    return output['channel'], output['text'].strip()

        return None, None

    @staticmethod
    def search_elastic(keyword_list):
        """
        입력된 키워드로 검색 결과 반환
        """
        from elasticsearch import Elasticsearch

        # 검색
        elastic = Elasticsearch(['elastic'], port=9200)

        must = []
        for keyword in keyword_list:
            must.append({
                'match_phrase': {
                    'keywords.words': keyword.strip()
                }
            })

        search_result = elastic.search(
            size=10,
            index='nate_baseball',
            body={
                '_source': ['title', 'date'],
                'sort': [{
                    'date': {'order': 'desc'}
                }],
                'query': {
                    'bool': {
                        'must': must
                    }
                }
            }
        )

        # 검색 결과 가공
        total = 0
        hits = None
        if 'hits' in search_result and 'hits' in search_result['hits']:
            total = search_result['hits']['total']
            hits = search_result['hits']['hits']

        return total, hits

    def get_search_response(self, message):
        """
        사용자 메세지로 검색
        """
        # 키워드 분리
        keyword_list = []
        for keyword in message.split(','):
            keyword_list.append(keyword)

        # 검색
        total, hits = self.search_elastic(keyword_list)

        result = []
        for item in hits[:5]:
            source = item['_source']
            result.append('{} ({})'.format(source['title'], source['date'].split('T')[0]))

        if total == 0 or result is None:
            response = [{
                'pretext': '"{}"에 대한 검색 결과가 없습니다.'.format(','.join(keyword_list))
            }]
        else:
            response = [{
                'pretext': '"{}"에 대한 검색 결과, {:,} 개가 검색 되었습니다.'.format(','.join(keyword_list), total),
                'text': '\n'.join(result)
            }]

        return response

    def run_kmat_bot(self):
        """
        형태소 분석 봇 실행
        """

        while True:
            time.sleep(10000)


    # slack_client = SlackClient(self.bot_token['kmat'])
        #
        # sleep_time = 1  # 초 단위
        # if slack_client.rtm_connect() is False:
        #     print('ERROR', '슬랙 연결 오류', file=sys.stderr, flush=True)
        #     return
        #
        # from NCNlpUtil import NCNlpUtil
        #
        # util = NCNlpUtil()
        # util.open_pos_tagger(dictionary_path='dictionary/rsc')
        #
        # print('형태소 분석 봇 시작: ', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), file=sys.stderr, flush=True)
        # while True:
        #     channel, message = self.parse_slack_message(slack_client.rtm_read())
        #     if channel is None or message == '':
        #         time.sleep(sleep_time)
        #         continue
        #
        #     print('입력 채널 정보: ', channel, message, file=sys.stderr, flush=True)
        #
        #     # 분석
        #     pos_tagged, _ = util.run_pos_tagger_sentence(message)
        #     response = [{
        #         'pretext': message,
        #         'text': pos_tagged
        #     }]
        #
        #     # 결과 전송
        #     try:
        #         slack_client.api_call("chat.postMessage", channel=channel, attachments=response, as_user=True)
        #     except Exception:
        #         print('ERROR', 'send message', file=sys.stderr, flush=True)
        #
        #     time.sleep(sleep_time)

    def run_search_bot(self):
        """
        검색 봇 실행
        """
        slack_client = SlackClient(self.bot_token['search'])

        sleep_time = 1  # 초 단위
        if slack_client.rtm_connect() is False:
            print('ERROR', '슬랙 연결 오류', file=sys.stderr, flush=True)
            return

        print('검색 봇 시작: ', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), file=sys.stderr, flush=True)
        while True:
            channel, message = self.parse_slack_message(slack_client.rtm_read())
            if channel is None or message == '':
                time.sleep(sleep_time)
                continue

            print('입력 채널 정보: ', channel, message, file=sys.stderr, flush=True)

            # 검색
            response = self.get_search_response(message)

            # 결과 전송
            try:
                slack_client.api_call("chat.postMessage", channel=channel, attachments=response, as_user=True)
            except Exception:
                print('ERROR', 'send message', file=sys.stderr, flush=True)

            time.sleep(sleep_time)

    def run_summarization_bot(self):
        """
         야구 기사 요약 푸시 봇 실행
        """
        from dateutil.relativedelta import relativedelta

        db_info = {
            'host': '172.20.92.10',  # yoma10
            'port': 83,
            'user': 'root',
            'passwd': 'ncldc',
            'db_name': 'ncapp'
        }

        slack_client = SlackClient(self.bot_token['summarization'])
        channel_list = self.get_channel_list('summarization')

        if slack_client.rtm_connect() is False:
            print('ERROR', '슬랙 연결 오류', file=sys.stderr, flush=True)
            return

        print('야구 기사 요약 봇 시작: ', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), file=sys.stderr, flush=True)
        next_date = datetime.now() + relativedelta(minutes=-6)

        while True:
            if next_date < datetime.now():
                next_date = datetime.now() + relativedelta(minutes=5)

                print('요약 디비 조회: {}, 다음 디비 조회: {}'.format(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    next_date.strftime("%Y-%m-%d %H:%M:%S")),
                    file=sys.stderr, flush=True)

                self.send_new_summary(slack_client, channel_list, db_info)

            time.sleep(2)

    def send_new_summary(self, slack_client, channel_list, db_info):
        """
        """
        row = self.get_summary(db_info)
        if row is None or 'token' not in row:
            print('INFO: ', datetime.now(), ' 요약 결과가 없습니다.', file=sys.stderr, flush=True)
            return

        str_date = row['token'].replace('T', ' ')
        str_date = str_date.replace('Z', ' ').strip()

        teams = self.parse_team_info(row['teams'])
        summary = self.get_summary_text(row['summary'])

        response = [{
            "pretext": '{} (summarized in {} docs.)'.format(' vs. '.join(teams), row['doc_count']),
            "title": '{}'.format(row['rep_doc_title']),
            "image_url": row['image_url'],
            "text": summary,
            "footer": '{} {}'.format(' vs. '.join(teams), str_date)
        }]

        print(
            '[{}] '.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ' vs. '.join(teams),
            row['rep_doc_title'],
            '({})'.format(row['token'].replace('T', ' ').replace('Z', ''))
            , file=sys.stderr
            , flush=True)

        try:
            slack_client.api_call(
                "chat.postMessage",
                channel=channel_list['요약'],
                attachments=response,
                as_user=True
            )
        except Exception:
            print('ERROR', 'send message', file=sys.stderr, flush=True)

        for team_name in teams:
            try:
                team_name = team_name.lower()
                if team_name not in channel_list:
                    continue

                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel_list[team_name],
                    attachments=response,
                    as_user=True
                )
            except Exception:
                print('ERROR', 'send message', file=sys.stderr, flush=True)

        return

    @staticmethod
    def parse_argument():
        """"
        옵션 설정
        """
        import argparse

        arg_parser = argparse.ArgumentParser(description='slack bot option')

        arg_parser.add_argument('-kmat', help='', action='store_true', default=False)
        arg_parser.add_argument('-search', help='', action='store_true', default=False)
        arg_parser.add_argument('-summarization', help='', action='store_true', default=False)

        arg_parser.add_argument('-get_channel_list', help='', action='store_true', default=False)

        return arg_parser.parse_args()


# end of NCSlackBot


if __name__ == '__main__':
    bot = NCSlackBot()
    args = bot.parse_argument()

    if args.summarization is True:
        bot.run_summarization_bot()
    elif args.search is True:
        bot.run_search_bot()
    elif args.kmat is True:
        bot.run_kmat_bot()
    elif args.get_channel_list is True:
        bot.get_channel_list('summarization')

# end of __main__
