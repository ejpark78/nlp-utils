#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import sys
import json

from NCNlpUtil import NCNlpUtil


class NCCorpus:
    """
    코퍼스 변환 및 처리
    """

    def __init__(self):
        pass

    @staticmethod
    def get_korean_baseball():
        """
        한국 야구 뉴스만 추출
        """
        util = NCNlpUtil()

        negative = ['치어']
        positive = ['두산', '삼성', 'KIA', '넥센', '한화', 'SK', '롯데', 'LG', 'NC', 'KT']

        count = 0
        for line in sys.stdin:
            document = json.loads(line)

            content = ''
            for paragraph in document['paragraph']:
                content += ' '.join(paragraph) + ' '

            skip = False
            for word in negative:
                if content.find(word) > 0:
                    skip = True
                    break

            if skip is True:
                continue

            skip = True
            for word in positive:
                if content.find(word) > 0:
                    skip = False
                    break

            if skip is True:
                continue

            print(line.strip(), flush=True)

            count += 1
            util.print_runtime(count=count, interval=10000)

        return

    def get_json_value(self, document, key):
        """
        문서에서 키에 해당하는 값을 반환
        하위 트리를 찾아서 반환
        """
        if document is None:
            return None

        if isinstance(key, str) and key in document:
            return document[key]

        if isinstance(key, list) and key[0] in document:
            if len(key) == 1:
                return self.get_json_value(document, key[0])
            else:
                return self.get_json_value(document[key[0]], key[1:])

        return None

    def read_json_value(self, key):
        """
        문서에서 값을 찾아 반환
        """
        util = NCNlpUtil()

        key_list = key.split(',')

        count = 0
        for line in sys.stdin:
            document = json.loads(line)

            if document is None:
                continue

            result = {}
            for key in key_list:
                key_token = key.split('.')
                value = self.get_json_value(document, key_token)

                if len(key_list) > 1:
                    result[key_token[0]] = value
                else:
                    result = value

            if result is None:
                continue

            if isinstance(result, str):
                str_result = result
            else:
                str_result = json.dumps(result, ensure_ascii=False, default=util.json_serial)

            if str_result.strip() == '':
                continue

            print(str_result, flush=True)

            count += 1
            util.print_runtime(count=count, interval=10000)

        return

    def set_json_value(self, document, key, value):
        """
        문서에서 키에 해당하는 값을 반환
        하위 트리를 찾아서 반환
        """
        if document is None:
            return

        if isinstance(key, str):
            if key not in document:
                document[key] = value
            elif isinstance(document[key], list):
                document[key].append(value)

            return

        if isinstance(key, list):
            if len(key) == 1:
                self.set_json_value(document, key[0], value)
            else:
                if key[0] not in document:
                    document[key[0]] = {}

                self.set_json_value(document[key[0]], key[1:], value)

        return

    def to_json(self, key):
        """
        탭 구분자의 병렬 코퍼스를 json 형태로 변환
        """
        util = NCNlpUtil()

        token_key = key.split(',')

        count = 0
        for line in sys.stdin:
            line = line.strip()
            if line == '':
                continue

            token = line.split('\t')

            stop_flag = False
            for i in range(0, len(token)):
                token[i] = re.sub(r'&nbsp;', ' ', token[i].strip())
                token[i] = re.sub(r'nbsp;', ' ', token[i].strip())
                token[i] = re.sub(r'\s+', ' ', token[i])

                token[i] = re.sub(r'^(\s*[!-=#,./?*~>]+\s*)+', '', token[i].strip())

                token[i] = token[i].strip()

                if token[i] == '' or token[i].lower() == 'null':
                    stop_flag = True
                    break

            if stop_flag is True:
                continue

            if len(token_key) != len(token):
                continue

            document = {}
            for i, k in enumerate(token_key):
                self.set_json_value(document, k.split('.'), token[i])

            result = json.dumps(document, ensure_ascii=False, default=util.json_serial)
            print(result, flush=True)

            count += 1
            util.print_runtime(count=count, interval=10000)

        return

    @staticmethod
    def get_clean_document():
        """
        분석에 빠진 문장 추출
        """
        column_list = ['pos_tagged', 'dictionary_base_named_entity']

        for line in sys.stdin:
            line = line.strip()
            if line == '':
                continue

            document = json.loads(line)

            count = []
            for paragraph in document['paragraph']:
                count.append(len(paragraph))

            stop = False
            for column in column_list:
                if column not in document:
                    stop = True
                    break

                for i, paragraph in enumerate(document[column]):
                    if count[i] != len(paragraph):
                        stop = True
                        break

                    for sentence in paragraph:
                        if sentence.strip() == '':
                            stop = True
                            break

            if stop is True:
                print(line, file=sys.stderr, flush=True)
            else:
                print(line, flush=True)

        return

    @staticmethod
    def convert_mlbpark():
        """
        mlbpark 데이터 변환
        """
        import re
        import dateutil.parser

        from bs4 import BeautifulSoup

        util = NCNlpUtil()

        count = 0

        for line in sys.stdin:
            document = json.loads(line)

            # 헤더가 없는 경우 추출
            if 'title_header' not in document:
                document['title_header'] = ''

            if document['title_header'] == '' and document['title_header'].find('[') > 0:
                document['title_header'] = re.sub(r'^\[(.+?)\].+$', '\g<1>', document['title']).strip()

            document['title'] = re.sub(r'^\[(.+?)\]', '', document['title']).strip()

            simple_id = document['_id']
            for t in simple_id.split('.'):
                if t.isdigit():
                    simple_id = int(t)
                    break

            dt = dateutil.parser.parse(document['date']['$date'])

            result = {
                '_id': simple_id,
                'title_header': document['title_header'],
                'title': document['title'],
                'nick': document['nick'],
                'date': dt.strftime("%Y-%m-%dT%H:%M:%S"),
                'contents': '',
                'reply_list': []
            }

            if 'view_count' in document:
                view_count = document['view_count'].replace(',', '')
                result['view_count'] = int(view_count)

            # body
            soup = BeautifulSoup(document['html_content'], 'lxml')
            result['contents'] = soup.get_text()

            # replay
            soup = BeautifulSoup(document['reply_list'], 'lxml')
            for tag in soup.find_all('div', attrs={'class': 'txt_box'}):
                nick = tag.find('span', attrs={'class': 'name'}).get_text().strip()
                date = tag.find('span', attrs={'class': 'date'}).get_text().strip()

                reply_to = ''
                re_txt = []
                for txt in tag.find_all('span', attrs={'class': 're_txt'}):
                    str_txt = txt.get_text()
                    str_txt = re.sub(r'[/]+', '//', str_txt)

                    token = str_txt.split('//', maxsplit=1)

                    if len(token) == 1:
                        str_txt = token[0].strip()
                    else:
                        reply_to = token[0].strip()
                        str_txt = token[1].strip()

                    re_txt.append(str_txt.strip())

                # simple
                dt = dateutil.parser.parse(date)
                result['reply_list'].append({
                    'nick': nick,
                    'date': dt.strftime("%Y-%m-%dT%H:%M:%S"),
                    'reply_to': reply_to,
                    're_txt': ' '.join(re_txt)
                })

                # full version
                # result['reply_list'].append({
                #     'nick': nick,
                #     'date': dateutil.parser.parse(date),
                #     'reply_to': reply_to,
                #     're_txt': ' '.join(re_txt)
                # })

            # msg = json.dumps(result, ensure_ascii=False, indent=4, default=NCNlpUtil().json_serial)
            msg = json.dumps(result, ensure_ascii=False, default=NCNlpUtil().json_serial)
            print(msg, flush=True)

            count += 1
            util.print_runtime(count=count, interval=1000)

        return

    @staticmethod
    def convert_game_info():
        """
        다음 실시간 중계 데이터 변환
        """
        from bs4 import BeautifulSoup

        for line in sys.stdin:
            document = json.loads(line)

            if 'castertext' in document:
                result = []
                for castertext in document['castertext']:
                    live_text = castertext['livetext']

                    soup = BeautifulSoup(live_text, 'lxml')
                    result.append(soup.get_text())

                if len(result) > 0:
                    print(json.dumps({'_id': document['id'], 'castertext': result}, ensure_ascii=False))

        return

    @staticmethod
    def cpcode2naver_gid(cp_game_id):
        if cp_game_id is not None:
            gid = cp_game_id.replace('|', '').strip()
            if gid.endswith('2016'):
                return gid

            return gid[:-4]

        return None

    def convert_3mins(self):
        """
        다음 3분 야구에서 정보를 변환
        """
        game_info = {}

        for line in sys.stdin:
            document = json.loads(line)

            game_id = str(document['gameId'])
            if game_id not in game_info:
                game_info[game_id] = {}

            if 'related_contents' in document:
                game_info[game_id]['related_contents'] = document['related_contents']

            if 'lineup_bat' in document:
                game_info[game_id]['game_summary'] = document['lineup_bat']

        for game_id in game_info:
            game_summary = game_info[game_id]['game_summary']
            related_contents = game_info[game_id]['related_contents']

            document = {
                '_id': game_id,
                'tbSingularPoint': []
            }

            bb3min = {}

            div_conid = ''
            high_conid = ''
            for contents in related_contents:
                if contents['PURPOSE'] == 'lineup':
                    lineup_bat = None
                    if 'DATA' in contents and 'lineup_bat' in contents['DATA']:
                        if len(contents['DATA']['lineup_bat']) > 0:
                            lineup_bat = contents['DATA']['lineup_bat'][0]

                    if lineup_bat and 'CP_GAME_ID' in lineup_bat:
                        bb3min['gid'] = lineup_bat['CP_GAME_ID'].split('|')[0]
                        if bb3min['gid'][0:4] == '2016':
                            bb3min['gid'] = ''.join([bb3min['gid'], '2016'])
                    else:
                        bb3min['gid'] = None
                        for item in game_summary:
                            if 'CP_GAME_ID' in item:
                                bb3min['gid'] = self.cpcode2naver_gid(item['CP_GAME_ID'])
                                break

                    bb3min['tbgameid'] = contents['GAME_ID']
                elif contents['PURPOSE'] == 'divider':
                    if 'DATA' in contents:
                        for key in ['prefix', 'pitcher', 'batter', 'outline', 'title', 'situation']:
                            bb3min[key] = None
                            if key in contents['DATA']:
                                contents['DATA'][key] = contents['DATA'][key].replace('<br>', ' ')
                                contents['DATA'][key] = contents['DATA'][key].replace('<BR>', ' ')

                                bb3min[key] = contents['DATA'][key]

                    div_conid = str(contents['CONTENTS_ID'])
                elif contents['PURPOSE'] == 'highlight':
                    high_conid = str(contents['CONTENTS_ID'])
                    for media in contents['DATA']['mediaList']:
                        if len(media.keys()) == 0:
                            continue

                        bb3min['mediaTitle'] = None
                        if 'title' in media:
                            bb3min['mediaTitle'] = media['title']

                        bb3min['description'] = None
                        if 'description' in media:
                            media['description'] = media['description'].replace('<br>', ' ')
                            media['description'] = media['description'].replace('<BR>', ' ')

                            bb3min['description'] = media['description']
                elif contents['PURPOSE'] == 'sports_summary':
                    bb3min['gameName'] = contents['DATA']['name']

                    contents['DATA']['title'] = contents['DATA']['title'].replace('<br>', ' ')
                    contents['DATA']['title'] = contents['DATA']['title'].replace('<BR>', ' ')

                    bb3min['gameTitle'] = contents['DATA']['title']
                elif contents['PURPOSE'] == 'viewpoint':
                    criticism_list = contents['DATA']['criticismList']
                    for critic in criticism_list:
                        if 'division' in critic:
                            key = 'batterCritic'
                            if critic['division'] == 'pitcher':
                                key = 'pitcherCritic'

                            critic['comment'] = critic['comment'].replace('<br>', ' ')
                            critic['comment'] = critic['comment'].replace('<BR>', ' ')

                            bb3min[key] = critic['comment']
                elif contents['PURPOSE'] in ['keyplayer_home', 'keyplayer_away']:
                    data = contents['DATA']

                    bb3min[contents['PURPOSE']] = '/'.join(
                        [str(int(data['personId'])), str(int(data['cpPersonId'])), data['personName']])

                if div_conid != '' and high_conid != '':
                    item = dict(bb3min)
                    for key in ['batterCritic', 'pitcherCritic']:
                        if key in item:
                            del item[key]

                    document['tbSingularPoint'].append(dict(item))

                    for key in ['contentid', 'title', 'prefix', 'pitcher', 'batter', 'outline', 'situation',
                                'mediaTitle', 'description']:
                        if key in bb3min:
                            del bb3min[key]

                    div_conid = ''
                    high_conid = ''

            document['tbPrevSum'] = bb3min
            print('{}'.format(json.dumps(document, ensure_ascii=False)))

        return

    @staticmethod
    def extract_sentence_3mins():
        """
        3분 야구 뉴스에서 문장 추출
        """
        util = NCNlpUtil()

        for line in sys.stdin:
            document = json.loads(line)

            if 'tbPrevSum' in document:
                item = document['tbPrevSum']
                for key in ['pitcherCritic', 'batterCritic', 'gameTitle']:
                    if key in item and item[key] is not None:
                        result = json.dumps({'sentence': item[key]}, ensure_ascii=False, default=util.json_serial)
                        print(result, flush=True)

            if 'tbSingularPoint' in document:
                for item in document['tbSingularPoint']:
                    for sentence in util.split_sentence(item['description']):
                        result = json.dumps({'sentence': sentence}, ensure_ascii=False, default=util.json_serial)
                        print(result, flush=True)

                    for key in ['situation', 'mediaTitle', 'title']:
                        if key in item and item[key] is not None:
                            result = json.dumps({'sentence': item[key]}, ensure_ascii=False, default=util.json_serial)
                            print(result, flush=True)

        return

    def merge_result_3mins(self, index_file_name):
        """
        문서를 입력 받아 문서 내에 있는 문장을 기분석 사전에서 찾아서 분석 결과 병합
        """
        import sqlite3

        util = NCNlpUtil()

        conn = sqlite3.connect(index_file_name)

        cursor = conn.cursor()
        self.set_pragam(cursor)

        column_list = []

        for line in sys.stdin:
            document = json.loads(line)

            if 'tbPrevSum' in document:
                item = document['tbPrevSum']
                for key in ['pitcherCritic', 'batterCritic', 'gameTitle']:
                    if key in item and item[key] is not None:
                        value = self.get_value(cursor, item[key], column_list)
                        self.merge_value(item, value, key)

            if 'tbSingularPoint' in document:
                for item in document['tbSingularPoint']:
                    for sentence in util.split_sentence(item['description']):
                        if 'description_sentence' not in item:
                            item['description_sentence'] = []
                        item['description_sentence'].append(sentence)

                        value = self.get_value(cursor, sentence, column_list)
                        self.merge_value(item, value, 'description')

                    for key in ['situation', 'mediaTitle', 'title']:
                        if key in item and item[key] is not None:
                            value = self.get_value(cursor, item[key], column_list)
                            self.merge_value(item, value, key)

            result = json.dumps(document, ensure_ascii=False, default=util.json_serial)
            print(result, flush=True)

        return

    @staticmethod
    def parse_argument():
        """
        파라메터 옵션 정의
        """
        import argparse

        arg_parser = argparse.ArgumentParser(description='')

        # 병렬 자막 코퍼스 변환
        arg_parser.add_argument('-to_json', help='', action='store_true', default=False)

        arg_parser.add_argument('-get_json_value', help='', action='store_true', default=False)
        arg_parser.add_argument('-key', help='json 키', default=None)

        # 이호엽 대리 요청 처리
        arg_parser.add_argument('-get_korean_baseball', help='', action='store_true', default=False)

        # 분석에 빠진 문장 추출
        arg_parser.add_argument('-get_clean_document', help='', action='store_true', default=False)

        # mlbpark 데이터 변환
        arg_parser.add_argument('-convert_mlbpark', help='', action='store_true', default=False)

        # 다음 실시간 중계 데이터 변환
        arg_parser.add_argument('-convert_game_info', help='', action='store_true', default=False)

        # 3분 야구 변환 관련 함수
        arg_parser.add_argument('-convert_3mins', help='3분 야구 데이터에서 필요한 정보 추출', action='store_true', default=False)
        arg_parser.add_argument('-extract_sentence_3mins', help='3분 야구 뉴스에서 문장 추출', action='store_true', default=False)
        arg_parser.add_argument('-merge_result_3mins', help='3분 야구 뉴스 문장 분석 결과 병합', action='store_true', default=False)

        return arg_parser.parse_args()


if __name__ == "__main__":
    manager = NCCorpus()

    args = manager.parse_argument()

    if args.to_json is True:
        manager.to_json(args.key)
    elif args.get_json_value is True:
        manager.read_json_value(args.key)
    elif args.get_korean_baseball is True:
        manager.get_korean_baseball()
    elif args.get_clean_document is True:
        manager.get_clean_document()

    # mlbpark 데이터 변환 관련
    if args.convert_mlbpark is True:
        manager.convert_mlbpark()

    # 다음 야구 실시간 분석 관련
    if args.convert_game_info is True:
        manager.convert_game_info()

    # 3분 뉴스 변환 및 분석
    if args.convert_3mins is True:
        manager.convert_3mins()
    elif args.extract_sentence_3mins is True:
        manager.extract_sentence_3mins()
    elif args.merge_result_3mins is True:
        manager.merge_result_3mins(args.index_file_name)

