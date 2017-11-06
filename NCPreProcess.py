#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import json


from NCCrawlerUtil import NCCrawlerUtil
from NCHtmlParser import NCHtmlParser
from NCNewsKeywords import NCNewsKeywords

from language_lab_utils.language_lab_utils import LanguageLabUtils


class NCPreProcess:
    """
    웹 신문 기사에 형태소분석, 개체명 인식 정보를 부착
    """

    def __init__(self):
        self.util = None
        self.parser = None

        self.keywords_extractor = None

    @staticmethod
    def open_db(db_name, host='gollum', port=27017):
        """
        몽고 디비 핸들 오픈
        """
        from pymongo import MongoClient

        connect = MongoClient('mongodb://{}:{}'.format(host, port))
        db = connect[db_name]

        return connect, db

    def update_state(self, state, count, total, job_info, scheduler_db_info):
        """
        현재 작업 상태 변경
            # state: 상태, running, ready, stoped
            # status: 경과 시간
        """
        job_info['state']['state'] = state
        if state == 'running':
            job_info['state']['total'] = '{:,}'.format(total)
            job_info['state']['running'] = '{:,}'.format(count)
            job_info['state']['progress'] = '{:0.1f}'.format(count / total * 100)
        elif state == 'done':
            job_info['state']['progress'] = '100.0'

        connect, db = self.open_db(
            scheduler_db_info['scheduler_db_name'],
            scheduler_db_info['scheduler_db_host'],
            scheduler_db_info['scheduler_db_port'])

        collection_name = scheduler_db_info['scheduler_db_collection']
        db[collection_name].replace_one({'_id': job_info['_id']}, job_info)

        connect.close()
        return

    def get_text(self, document):
        """
        html 문서에서 텍스트를 추출하고 문장 분리 및 이미지 추출 결과 반환
        """
        if self.util is None:
            self.util = LanguageLabUtils()

        if self.parser is None:
            self.parser = NCHtmlParser()

        if 'html_content' in document:
            content, document['image_list'] = self.parser.get_article_body(document['html_content'])

            document['content'], document['header'], document['tail'] = self.parser.parse_content(content)
            document['paragraph'], _ = self.util.split_document(document['content'])

        if '_id' not in document:
            document['_id'] = NCCrawlerUtil().get_document_id(document['url'])

        return document

    @staticmethod
    def split_by_month(file_header):
        """
        년도별 문서 뭉치를 월별로 분리
        """
        import bz2
        import dateutil.parser

        file_list = {}
        util = LanguageLabUtils()

        count = 0
        for line in sys.stdin:
            document = json.loads(line)

            # source = 'etc'
            # if document['url'].find('daum') > 0:
            #     source = 'daum'
            # elif document['url'].find('nate') > 0:
            #     source = 'nate'
            # elif document['url'].find('naver') > 0:
            #     source = 'naver'
            
            if 'date' not in document:
                continue

            date = dateutil.parser.parse(document['date']['$date'])

            filename = '{}{}.bz2'.format(file_header, date.strftime('%Y.%m'))
            if filename not in file_list:
                file_list[filename] = bz2.open(filename, 'at')

            file_list[filename].write('{}\n'.format(line))

            count += 1
            util.print_runtime(count=count, interval=5000)

        return

    def extract_text_stdin(self):
        """
        HTML 기사를 읽어서 문장 분리
        """
        if self.util is None:
            self.util = LanguageLabUtils()

        if self.parser is None:
            self.parser = NCHtmlParser()

        for line in sys.stdin:
            line = line.strip()
            if line == '':
                print(line, flush=True)
                continue

            try:
                document = json.loads(line)

                document = self.restore_date(document)

                result = self.get_text(document)

                if result is not None:
                    str_json = json.dumps(result, ensure_ascii=False, default=NCNlpUtil().json_serial)
                    print(str_json, flush=True)
                else:
                    print('ERROR:', line, flush=True)
            except Exception as err:
                print(line, flush=True)
                continue

        return

    @staticmethod
    def extract_sentence(document, format='json'):
        """
        입력된 json 파일에서 문장만 추출
        """
        result = []
        if 'title' in document and document['title'] != '':
            sentence = document['title']
            if format == 'json':
                sentence = json.dumps({'sentence': sentence},
                                      ensure_ascii=False, default=LanguageLabUtils().json_serial)

            result.append(sentence)

        if 'image_list' in document:
            for item in document['image_list']:
                if 'caption' in item and item['caption'] != '':
                    sentence = item['caption']
                    if format == 'json':
                        sentence = json.dumps({'sentence': sentence},
                                              ensure_ascii=False, default=LanguageLabUtils().json_serial)

                    result.append(sentence)

        if 'paragraph' in document:
            for paragraph in document['paragraph']:
                for sentence in paragraph:
                    if sentence == '':
                        continue

                    if format == 'json':
                        sentence = json.dumps({'sentence': sentence},
                                              ensure_ascii=False, default=LanguageLabUtils().json_serial)

                    result.append(sentence)

        return result

    def extract_sentence_stdin(self, format='json'):
        """
        입력된 json 파일에서 문장만 추출
        """
        import json

        for line in sys.stdin:
            line = line.strip()
            if line == '':
                print(line, flush=True)
                continue

            try:
                document = json.loads(line)
            except Exception as err:
                print(line, flush=True)
                continue

            if format != 'json':
                print('# {}'.format(document['_id']), flush=True)

            result = self.extract_sentence(document, format)
            if result is None:
                continue

            for line in result:
                print(line, flush=True)

            if format != 'json':
                print('', flush=True)

        return

    @staticmethod
    def preprocess(domain='baseball', max_sentence=2048):
        """
        """
        util = LanguageLabUtils()

        util.open_pos_tagger()
        #util.open_ner()
        util.open_sp_project_ner(domain=domain)

        for line in sys.stdin:
            document = json.loads(line)

            if 'sentence' not in document:
                continue

            sentence = document['sentence'].strip()
            if sentence == '':
                continue

            pos_tagged = ''
            named_entity = ''

            # 1. 형태소 분석, 2. 개체명 인식
            if len(sentence) < max_sentence:
                pos_tagged, _ = util.run_pos_tagger_sentence(sentence)
                named_entity = util.run_sp_project_named_entity_sentence(sentence, pos_tagged)

            result = json.dumps({
                'sentence': sentence,
                'pos_tagged': pos_tagged,
                'named_entity': named_entity
            }, ensure_ascii=False, default=LanguageLabUtils().json_serial)

            print(result, flush=True)

        return

    def make_sentence_index(self, file_name):
        """
        분석 결과를 문장으로 찾을 수 있는 사전 형태로 가공
        """
        import sqlite3

        util = NCNlpUtil()

        conn = sqlite3.connect(file_name)

        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS [sentence_index] '
                       '([key] TEXT PRIMARY KEY NOT NULL, [value] TEXT NOT NULL)')

        self.set_pragam(cursor, readonly=False)

        count = 0
        for line in sys.stdin:
            document = json.loads(line)

            sql = 'INSERT INTO [sentence_index] (key, value) VALUES (?, ?)'
            try:
                cursor.execute(sql, (document['sentence'], line))
            except Exception:
                print('error: ', document['sentence'], file=sys.stderr)

            count += 1
            util.print_runtime(count=count, interval=100000)

        conn.commit()
        cursor.close()
        conn.close()

        return

    @staticmethod
    def sentence_exists(cursor, sentence):
        """
        디비에서 문장을 가져온다.
        """
        cursor.execute('SELECT 1 FROM [sentence_index] WHERE [key]=?', (sentence,))
        row = cursor.fetchone()

        if row is None or len(row) == 0:
            return False

        return True

    @staticmethod
    def set_pragam(cursor, readonly=True):
        """
        sqlite의 속도 개선을 위한 설정
        """
        # cursor.execute('PRAGMA threads       = 8;')

        # 700,000 = 1.05G, 2,100,000 = 3G
        cursor.execute('PRAGMA cache_size    = 2100000;')
        cursor.execute('PRAGMA count_changes = OFF;')
        cursor.execute('PRAGMA foreign_keys  = OFF;')
        cursor.execute('PRAGMA journal_mode  = OFF;')
        cursor.execute('PRAGMA legacy_file_format = 1;')
        cursor.execute('PRAGMA locking_mode  = EXCLUSIVE;')
        cursor.execute('PRAGMA page_size     = 4096;')
        cursor.execute('PRAGMA synchronous   = OFF;')
        cursor.execute('PRAGMA temp_store    = MEMORY;')

        if readonly is True:
            cursor.execute('PRAGMA query_only    = 1;')

        return

    @staticmethod
    def get_value(cursor, sentence, key_list, value_list=None):
        """
        디비에서 문장을 가져온다.
        """
        if sentence is None or sentence == '':
            return None

        cursor.execute('SELECT [value] FROM [sentence_index] WHERE [key]=?', (sentence,))
        row = cursor.fetchone()

        value = {}
        if row is not None and len(row) > 0:
            value = json.loads(row[0])

        # 분석이 안된 문장 처리
        if len(key_list) > 0:
            for key in key_list:
                if key not in value:
                    value[key] = ''

        if value_list is not None:
            for key in value:
                if key == 'sentence':
                    continue

                if key not in key_list:
                    key_list.append(key)

                if key not in value_list:
                    value_list[key] = []

                value_list[key].append(value[key])

        return value

    @staticmethod
    def merge_value(document, value_list, key_header):
        """
        문장 인덱스 디비에서 분석된 문장을 추출
        """
        if value_list is None:
            return

        for key in value_list:
            if key == 'sentence':
                continue

            new_key = key
            if key_header != '':
                new_key = '{}_{}'.format(key_header, key)

            if new_key not in document:
                document[new_key] = value_list[key]
                continue

            # 리스트로 변환
            if isinstance(document[new_key], str):
                document[new_key] = [document[new_key]]

            document[new_key].append(value_list[key])

        return

    @staticmethod
    def merge_paragraph_value(document, value_list):
        """
        """
        for key in value_list:
            if key not in document:
                document[key] = []

            document[key].append(value_list[key])

        return

    def merge_result(self, index_file_name):
        """
        문서를 입력 받아 문서 내에 있는 문장을 기분석 사전에서 찾아서 분석 결과 병합
        """
        import sqlite3

        util = LanguageLabUtils()

        conn = sqlite3.connect(index_file_name)

        cursor = conn.cursor()
        self.set_pragam(cursor)

        column_list = []

        count = 0
        for line in sys.stdin:
            document = json.loads(line)

            if 'title' in document and document['title'] != '':
                value = self.get_value(cursor, document['title'], column_list)
                self.merge_value(document, value, 'title')

            if 'image_list' in document:
                for item in document['image_list']:
                    if 'caption' in item and item['caption'] != '':
                        value = self.get_value(cursor, item['caption'], column_list)
                        self.merge_value(item, value, 'caption')

            if 'paragraph' in document:
                for paragraph in document['paragraph']:
                    value_list = {}
                    for sentence in paragraph:
                        self.get_value(cursor, sentence, column_list, value_list)

                    self.merge_paragraph_value(document, value_list)

            result = json.dumps(document, ensure_ascii=False, default=NCNlpUtil().json_serial)
            print(result, flush=True)

            count += 1
            util.print_runtime(count=count, interval=1000)

        cursor.close()
        conn.close()

        return

    def get_missing_sentence(self, index_file_name):
        """
        입력 문장에서 기분석 사전에 없는 문장을 출력
        """
        import os
        import sqlite3

        util = LanguageLabUtils()

        connect = None
        cursor = None

        count = 0
        if os.path.exists(index_file_name) is True:
            connect = sqlite3.connect(index_file_name)

            cursor = connect.cursor()
            self.set_pragam(cursor)

        for line in sys.stdin:
            document = json.loads(line)

            if connect is not None:
                if not self.sentence_exists(cursor, document['sentence']):
                    print(line.strip(), flush=True)
            else:
                print(line.strip(), flush=True)

            count += 1
            util.print_runtime(count=count, interval=100000)

        if connect is not None:
            cursor.close()
            connect.close()

        return

    @staticmethod
    def get_missing_column(column='pos_tagged'):
        """
        컬럼 정보가 없는 문장을 출력한다.
        """
        for line in sys.stdin:
            document = json.loads(line)

            if column not in document or document[column] == '':
                print(document['sentence'])

        return

    @staticmethod
    def remove_duplication_document():
        """
        네이트 tv 와 연예기사가 잘못 크롤링되었음.
        tv 기사와 연예 기사의 문서아이디가 같은 경우 연예 기사를 삭제
        """
        collection = '2016'

        from pymongo import MongoClient

        connect = MongoClient('mongodb://{}:{}'.format('gollum01', 27017))

        # 네이트 TV 문서 아이디를 가져옴
        db = connect['nate_tv']

        document_list = {}

        cursor = db[collection].find({}, {'_id': 1}, no_cursor_timeout=True)
        for doc in cursor:
            document_list[doc['_id']] = 1

        cursor.close()

        # 네이트 TV 문서 아이디를 가져옴
        db = connect['nate_entertainment']

        cursor = db[collection].find({}, {'_id': 1}, no_cursor_timeout=True)
        for doc in cursor:
            if doc['_id'] in document_list:
                print('.', end='')
                db[collection].remove({'_id': doc['_id']})

        cursor.close()

        connect.close()

        return

    @staticmethod
    def pos_tagging():
        """
        형태소 분석
        """
        util = LanguageLabUtils()

        util.open_pos_tagger()

        for line in sys.stdin:
            line = line.strip()

            pos_tagged, _ = util.run_pos_tagger_sentence(line)
            print('{}\t{}'.format(line, pos_tagged), flush=True)

        return

    @staticmethod
    def english_pos_tagging():
        """
        영어 형태소 분석
        """
        import re

        util = NCNlpUtil()

        for line in sys.stdin:
            line = re.sub(u'[ ]+', ' ', line.strip())

            if line == '':
                continue

            pos_tagged, _ = util.run_engllish_pos_tagger_sentence(line)
            print('{}\t{}'.format(line, pos_tagged), flush=True)

        return

    def spark_batch(self, document, max_sentence=2048):
        """
        스파크에서 전처리 모듈
        """
        try:
            document = self.get_text(document)
        except Exception as err:
            msg = 'get text: {}, {}'.format(document['url'], document['_id'])
            print(msg, file=sys.stderr, flush=True)
            return {'ERROR': msg}

        pos_tagged_buffer = []

        if 'title' in document and document['title'] != '':
            sentence = document['title']

            pos_tagged, _ = self.util.run_pos_tagger_sentence(sentence, max_sentence)
            named_entity = {}

            if pos_tagged != '':
                named_entity = self.util.run_multi_domain_ner_sentence(sentence, pos_tagged)
                pos_tagged_buffer.append([pos_tagged])

            document['title'] = {
                'sentence': sentence,
                'pos_tagged': pos_tagged,
                'named_entity': named_entity
            }

        if 'image_list' in document:
            buf = []
            for item in document['image_list']:
                if 'caption' in item and item['caption'] != '':
                    sentence = item['caption']

                    pos_tagged, _ = self.util.run_pos_tagger_sentence(sentence, max_sentence)
                    named_entity = {}

                    if pos_tagged != '':
                        named_entity = self.util.run_multi_domain_ner_sentence(sentence, pos_tagged)
                        buf.append(pos_tagged)

                    document['caption'] = {
                        'sentence': sentence,
                        'pos_tagged': pos_tagged,
                        'named_entity': named_entity
                    }

            if len(buf) > 0:
                pos_tagged_buffer.append(buf)

        if 'paragraph' in document:
            document['pos_tagged'] = []
            document['named_entity'] = {}

            """
            named_entity {
                economy [
                    [
                    ],
                ],
                baseball [
                
                ],
                baseball terms [
                
                ]
            }
            """

            for paragraph in document['paragraph']:
                pos_tagged_buf = []

                named_entity_buf = {}

                for sentence in paragraph:
                    if sentence == '':
                        continue

                    named_entity = {}
                    pos_tagged, _ = self.util.run_pos_tagger_sentence(sentence, max_sentence)

                    if pos_tagged != '':
                        named_entity = self.util.run_multi_domain_ner_sentence(sentence, pos_tagged)

                    pos_tagged_buf.append(pos_tagged)

                    for domain in named_entity:
                        if domain not in named_entity_buf:
                            named_entity_buf[domain] = []

                        named_entity_buf[domain].append(named_entity[domain])

                document['pos_tagged'].append(pos_tagged_buf)

                for domain in named_entity_buf:
                    if domain not in document['named_entity']:
                        document['named_entity'][domain] = []

                    document['named_entity'][domain].append(named_entity_buf[domain])

                pos_tagged_buffer.append(pos_tagged_buf)

        if self.keywords_extractor is not None and len(pos_tagged_buffer) > 0:
            words, _, _ = self.keywords_extractor.extract_keywords(pos_tagged_buffer, 'by_sentence')
            document['keywords'] = {'words': words}

        return document

    @staticmethod
    def restore_date(document):
        """
        날짜 변환, mongodb 의 경우 날짜가 $date 안에 들어가 있음.
        """
        for k in document:
            try:
                if '$date' in document[k]:
                    document[k] = document[k]['$date']
            except Exception as err:
                # print(document['document_id'], flush=True)
                pass

        return document

    def spark_batch_stdin(self, domain='baseball'):
        """
        스파크에서 전처리 모듈 테스트
        하둡 스트리밍에서 사용
        """
        self.util = LanguageLabUtils()
        self.util.open_pos_tagger(dictionary_path='dictionary/rsc')
        self.util.open_sp_project_ner(config='src/sp_config.ini', domain=domain)
        self.util.open_multi_domain_ner(config='src/sp_config.ini')

        self.keywords_extractor = NCNewsKeywords(entity_file_name='dictionary/keywords/nc_entity.txt')

        for line in sys.stdin:
            try:
                document = json.loads(line)
            except Exception as err:
                msg = 'ERROR at json parsing: {}'.format(line)
                print(msg, file=sys.stderr, flush=True)
                continue

            document = self.restore_date(document)

            # 전처리 시작
            result = self.spark_batch(document)

            if 'date' in result and 'insert_date' not in result:
                result['insert_date'] = result['date']

            try:
                str_result = json.dumps(result, ensure_ascii=False, default=NCNlpUtil().json_serial)
            except Exception as err:
                msg = 'ERROR at json dumps: {}, {}'.format(document['url'], document['_id'])
                print(msg, file=sys.stderr, flush=True)
                continue

            print(str_result, flush=True)

        return

    def eval_ner(self):
        """
        """
        import re

        self.util = LanguageLabUtils()
        self.util.open_ner()

        data_path = 'data/ner_eval'
        for fname in ['baseball_kangwon_test.sent', 'baseball_ncsoft_test.sent', 'general_test.sent']:
            with open('{}/{}'.format(data_path, fname), 'r') as fp:
                for sentence in fp.readlines():
                    sentence = sentence.strip()

                    # train
                    named_entity = self.util.run_named_entity_sentence(sentence)
                    print(named_entity)

        return

    @staticmethod
    def parse_argument():
        """
        파라메터 옵션 정의
        """
        import argparse

        arg_parser = argparse.ArgumentParser(description='')

        # 원문 디비
        arg_parser.add_argument('-source_db_host', help='source host name', default='gollum01')
        arg_parser.add_argument('-source_db_port', help='source port', default=27017)
        arg_parser.add_argument('-source_db_name', help='source db name', default='nate_baseball')
        arg_parser.add_argument('-source_db_collection', help='source collection name', default='2014')

        # 검색 조건
        arg_parser.add_argument('-where', help='where condition', default=None)
        arg_parser.add_argument('-limit', help='limit', type=int, default=-1)

        arg_parser.add_argument('-start_date', help='start date', default='2014-07-04')
        arg_parser.add_argument('-end_date', help='end date', default='2014-07-05')

        # 결과 저장 디비
        arg_parser.add_argument('-target_db_host', help='target host name', default='gollum')
        arg_parser.add_argument('-target_db_port', help='target host port', default=27017)
        arg_parser.add_argument('-target_db_name', help='target db name', default='summarization')
        arg_parser.add_argument(
            '-target_db_collection', help='target collection name', default='regular_season_2014_new_format')

        # 실행 옵션
        arg_parser.add_argument('-debug', help='debug', action='store_true', default=False)

        # 0. 월별 분리
        arg_parser.add_argument('-split_by_month', help='월별 분리', action='store_true', default=False)
        arg_parser.add_argument('-header', help='파일 헤더', default='data/')

        # 1. html에서 텍스트 추출 및 문장 분리 (결과 json)
        arg_parser.add_argument('-extract_text', help='extract text from html', action='store_true', default=False)
        # 2. 문장만 추출 (결과 텍스트)
        arg_parser.add_argument('-extract_sentence', help='문장 추출', action='store_true', default=False)
        # 3. 문장을 입력 받아 형태소 분석, 개체명 인식 수행 (결과 json)
        arg_parser.add_argument('-preprocess', help='형태소 분석 및 개체명 인식 실행', action='store_true', default=False)
        arg_parser.add_argument('-domain', help='개체명 인식기 도메인', default='baseball')
        # 4. 분석 결과 병합
        arg_parser.add_argument('-make_sentence_index', help='문장 인덱스 디비 생성', action='store_true',
                                default=False)
        arg_parser.add_argument('-merge_result', help='분석 결과 병합', action='store_true', default=False)
        arg_parser.add_argument('-index_file_name', help='인덱스 파일 이름', default='baseball.sqlite3')

        arg_parser.add_argument('-get_missing_sentence', help='빠진 문장 추출', action='store_true', default=False)
        # 5. 분석 결과가 없는 문장 추출
        arg_parser.add_argument('-get_missing_column', help='분석 결과가 없는 문장 추출', action='store_true', default=False)
        arg_parser.add_argument('-column', help='컬럼 이름', default='pos_tagged')

        arg_parser.add_argument('-remove_duplication_document', help='중복 문서 제거', action='store_true', default=False)

        # 형태소 분석
        arg_parser.add_argument('-pos_tagging', help='한국어 형태소 분석', action='store_true', default=False)
        arg_parser.add_argument('-english_pos_tagging', help='영어 형태소 분석', action='store_true', default=False)

        arg_parser.add_argument('-spark_batch', help='스파크 테스트', action='store_true', default=False)

        arg_parser.add_argument('-eval_ner', help='개체명 인식기 실행', action='store_true', default=False)

        arg_parser.add_argument('-format', help='출력 형식', default='json')

        return arg_parser.parse_args()


if __name__ == "__main__":
    manager = NCPreProcess()

    args = manager.parse_argument()

    if args.remove_duplication_document is True:
        manager.remove_duplication_document()

    # 형태소 분석
    if args.pos_tagging is True:
        manager.pos_tagging()
    elif args.english_pos_tagging is True:
        manager.english_pos_tagging()

    # 분산 처리 관련
    if args.split_by_month is True:
        manager.split_by_month(args.header)
    elif args.extract_text is True:
        manager.extract_text_stdin()
    elif args.extract_sentence is True:
        manager.extract_sentence_stdin(args.format)
    elif args.preprocess is True:
        manager.preprocess(args.domain)
    elif args.make_sentence_index is True:
        manager.make_sentence_index(args.index_file_name)
    elif args.get_missing_sentence is True:
        manager.get_missing_sentence(args.index_file_name)
    elif args.merge_result is True:
        manager.merge_result(args.index_file_name)
    elif args.get_missing_column is True:
        manager.get_missing_column(args.column)

    # 하둡 관련
    if args.spark_batch is True:
        manager.spark_batch_stdin(args.domain)

    if args.eval_ner is True:
        manager.eval_ner()
