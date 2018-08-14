#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from utils import Utils

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)


class NaverKinUtils(Utils):
    """ 네이버 크롤링 결과 저장 유틸 """

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.data_home = 'data/naver/kin'

        self.elastic_info = {
            'host': 'http://gollum:9200',
            'index': 'naver-kin',
            'type': 'naver-kin',
            'insert': True
        }

        self.detail_parsing_info = [
            {
                'key': 'category',
                'type': 'text',
                'tag': [{
                    'name': 'div',
                    'attribute': {'class': 'depth depth2'}
                }]
            }, {
                'key': 'question',
                'type': 'text',
                'tag': [{
                    'name': 'div',
                    'attribute': {'class': 'title_wrapper'}
                }]
            }, {
                'key': 'info',
                'type': 'text',
                'tag': [{
                    'name': 'div',
                    'attribute': {'class': '_questionArea'}
                }, {
                    'name': 'div',
                    'attribute': {'class': 'info_zone'}
                }]
            }, {
                'key': 'reply_count',
                'type': 'text',
                'tag': [{
                    'name': 'a',
                    'attribute': {'class': 'reply_count'}
                }, {
                    'name': 'em',
                    'attribute': {'class': 'count_number'}
                }]
            }, {
                'key': 'detail_question',
                'type': 'text',
                'tag': [{
                    'name': 'div',
                    'attribute': {'class': '_questionArea'}
                }, {
                    'name': 'div',
                    'attribute': {'class': 'user_content'}
                }]
            }, {
                'key': 'answer',
                'type': 'text',
                'tag': [{
                    'name': 'div',
                    'attribute': {'class': '_answer'}
                }, {
                    'name': 'div',
                    'attribute': {'class': 'user_content'}
                }]
            }, {
                'key': 'answer_user',
                'type': 'text',
                'tag': [{
                    'name': 'div',
                    'attribute': {'class': '_answer'}
                }, {
                    'name': 'h3',
                    'attribute': {'class': 'heading'}
                }]
            }, {
                'key': 'user_uid',
                'type': 'data-u',
                'tag': [{
                    'name': 'a',
                    'attribute': {'class': 'button_friend'}
                }]
            }
        ]

        self.category_list = {
            '금융': '401',
            '예금, 적금': '40101',
            '주식, 증권': '40102',
            '보험': '40103',
            '신용카드': '40104',
            '대출': '40105',
            '개인 신용, 회복': '40106',
            '뱅킹, 금융업무': '40107',
            '가상화폐': '40108',
            '부동산': '402',
            '매매': '40201',
            '임대차': '40202',
            '분양, 청약': '40203',
            '경매': '40204',
            '세금, 세무': '403',
            '소득세': '40301',
            '법인세': '40302',
            '상속세, 증여세': '40303',
            '부가가치세': '40304',
            '종합부동산세': '40305',
            '취득세, 등록세': '40306',
            '재산세': '40307',
            '자동차세': '40308',
            '세금 정책, 제도': '40309',
            '관세': '40310',
            '연말정산': '40311',
            '경영': '404',
            '마케팅, 영업': '40401',
            '회계, 감사, 재무 관리': '40402',
            '인사, 조직 관리': '40403',
            '연구개발, 생산, 물류': '40404',
            '경영정보시스템': '40405',
            '무역': '405',
            '수출': '40501',
            '수입': '40502',
            '직업, 취업': '406',
            '공무원': '40601',
            '교육, 연구, 학문': '40602',
            '의료, 법률, 금융': '40603',
            '복지, 종교': '40604',
            '문화, 예술': '40605',
            '관광, 요식업, 스포츠': '40606',
            '유통, 판매, 영업': '40607',
            '컴퓨터, 프로그래밍': '40608',
            '생산, 기술': '40609',
            '사무지원': '40610',
            '아르바이트': '40611',
            '취업 정책, 제도': '40612',
            '구인구직사이트': '40613',
            '창업': '407',
            '판매, 유통업': '40701',
            '관광, 요식업': '40702',
            '서비스업': '40703',
            '창업성장': '40704',
            '경제 정책, 제도': '408',
            '경제 동향, 이론': '409',
            '경제 기관, 단체': '410',
        }

    @staticmethod
    def save_to_excel(file_name, data, column_names):
        """ 크롤링 결과를 엑셀로 저장한다.

        :param file_name: 파일명
        :param data: 저장할 데이터
        :param column_names: 컬럼 이름
        :return:
        """
        from openpyxl import Workbook

        status = []

        wb = Workbook()

        for path in data:
            count = '{:,}'.format(len(data[path]))
            status.append([path, count])

            ws = wb.create_sheet(path)

            if len(column_names) == 0:
                column_names = list(data[path][0].keys())

            ws.append(column_names)
            for doc in data[path]:
                lines = []
                for c in column_names:
                    v = doc[c]
                    if v is None:
                        v = ''

                    lines.append('{}'.format(v))

                ws.append(lines)

        # 통계 정보 저장
        ws = wb['Sheet']
        for row in status:
            ws.append(row)

        ws.title = 'status'

        wb.save(file_name)

        return

    @staticmethod
    def get_columns(cursor):
        """"""
        return [d[0] for d in cursor.description]

    def merge_question(self, data_path='detail.json.bz2', result_filename='detail.xlsx'):
        """ 네이버 지식인 질문 목록 결과를 취합한다.

        :param data_path: 질문 목록 경로
        :param result_filename: 결과 파일명
        :return:
        """
        import bz2
        import sys
        import json

        from os import listdir
        from os.path import isdir, join

        # 파일 목록 추출
        file_list = []
        if isdir(data_path):
            for file in listdir(data_path):
                filename = join(data_path, file)
                if isdir(filename):
                    continue

                file_list.append(filename)

            file_list = sorted(file_list)
        else:
            file_list = [data_path]

        doc_index = {}

        # columns = []
        columns = 'fullDirNamePath,docId,title,previewContents,tagList'.split(',')

        count = 0
        for file in file_list:
            doc_list = []
            if file.find('.bz2') > 0:
                with bz2.open(file, 'rb') as fp:
                    buf = []
                    for line in fp.readlines():
                        line = str(line, encoding='utf-8').strip()

                        buf.append(line)

                        if len(buf) > 0 and line == '}':
                            body = ''.join(buf)
                            doc_list.append(json.loads(body))

                            buf = []
            else:
                with open(file, 'r') as fp:
                    doc_list = json.loads(''.join(fp.readlines()))

            for doc in doc_list:
                path = 'etc'
                if 'fullDirNamePath' in doc:
                    path = doc['fullDirNamePath'].replace('Q&A > ', '')

                if 'category' in doc:
                    path = doc['category']

                if isinstance(path, list):
                    path = 'etc'

                if path not in doc_index:
                    doc_index[path] = []

                doc_index[path].append(doc)

                line = json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=4)
                print(line, end='\n\n', flush=True)

                count += 1
                print('{} {:,}'.format(file, count), end='\r', flush=True, file=sys.stderr)

        # excel 저장
        self.save_to_excel(file_name=result_filename, data=doc_index, column_names=columns)

        return

    def parse_content(self, html, soup=None):
        """ 상세 정보 HTML 을 파싱한다.

        :param html: html
        :param soup: soup
        :return: 파싱된 결과
        """
        import re
        from bs4 import BeautifulSoup

        if html is not None:
            soup = BeautifulSoup(html, 'html5lib')

        if soup is None:
            return None, None

        # 테그 정리
        self.replace_tag(soup, ['script', 'javascript', 'style'])

        self.remove_comment(soup)
        self.remove_banner(soup=soup)
        self.remove_attribute(soup, ['onclick', 'role', 'style', 'data-log'])

        result = {}
        for item in self.detail_parsing_info:
            tag_list = []
            self.trace_tag(soup=soup, tag_list=item['tag'], index=0, result=tag_list)

            value_list = []
            for tag in tag_list:
                if item['type'] == 'text':
                    value = tag.get_text().strip().replace('\n', '')
                    value = re.sub('\s+', ' ', value)
                elif item['type'] == 'html':
                    value = str(tag.prettify())
                else:
                    if tag.has_attr(item['type']):
                        value = tag[item['type']]
                    else:
                        value = str(tag.prettify())

                value_list.append(value)

            if len(value_list) == 1:
                value_list = value_list[0]

            result[item['key']] = value_list

        return result, soup

    def trace_tag(self, soup, tag_list, index, result):
        """ 전체 HTML 문서에서 원하는 값을 가진 태그를 찾는다.

        :param soup: bs4 개체
        :param tag_list: 테그 위치 목록
        :param index: 테그 인덱스
        :param result: 결과
        :return:
        """
        from bs4 import element

        if soup is None:
            return

        if len(tag_list) == index and soup is not None:
            result.append(soup)
            return

        soup = soup.findAll(tag_list[index]['name'], attrs=tag_list[index]['attribute'])

        if isinstance(soup, element.ResultSet):
            for tag in soup:
                self.trace_tag(soup=tag, tag_list=tag_list, index=index + 1, result=result)

        return

    @staticmethod
    def remove_comment(soup):
        """ html 태그 중에서 주석 태그를 제거한다.

        :param soup: 웹페이지 본문
        :return: True/False
        """
        from bs4 import Comment

        for element in soup(text=lambda text: isinstance(text, Comment)):
            element.extract()

        return True

    @staticmethod
    def remove_banner(soup):
        """ 자살 방지 베너 삭제를 삭제한다.

        :param soup:
        :return:
        """
        tag_list = soup.findAll('div', {'id': 'suicidalPreventionBanner'})
        for tag in tag_list:
            tag.extract()

        return soup

    @staticmethod
    def remove_attribute(soup, attribute_list):
        """ 속성을 삭제한다.

        :param soup: html 객체
        :param attribute_list: [onclick, style, ...]
        :return:
        """

        for tag in soup.findAll(True):
            if len(tag.attrs) == 0:
                continue

            new_attribute = {}
            for name in tag.attrs:
                if name in attribute_list:
                    continue

                if 'javascript' in tag.attrs[name] or 'void' in tag.attrs[name] or '#' in tag.attrs[name]:
                    continue

                new_attribute[name] = tag.attrs[name]

            tag.attrs = new_attribute

        return soup

    def get_document_list(self, index, query, only_source=True, limit=-1):
        """elastic-search 에서 문서를 검색해 반환한다.

        :param index: 인덱스명
        :param query: 검색 조건
        :param only_source: _source 필드 반환
        :param limit: 최대 반환 크기 설정
        :return: 문서 목록
        """
        # 한번에 가져올 문서수
        size = 1000

        count = 1
        sum_count = 0
        scroll_id = ''
        total = -1

        # 서버 접속
        elastic = self.open_elastic_search(host=self.elastic_info['host'], index=index)
        if elastic is None:
            return None, None

        result = []

        while count > 0:
            # 스크롤 아이디가 있다면 scroll 함수 호출
            if scroll_id == '':
                search_result = elastic.search(index=index, doc_type=index, body=query, scroll='2m', size=size)
            else:
                search_result = elastic.scroll(scroll_id=scroll_id, scroll='2m')

            # 검색 결과 추출
            scroll_id = search_result['_scroll_id']

            hits = search_result['hits']

            if total != hits['total']:
                total = hits['total']

            count = len(hits['hits'])

            sum_count += count
            logging.info(msg='{} {:,} {:,} {:,}'.format(index, count, sum_count, total))

            for item in hits['hits']:
                if only_source is True:
                    result.append(item['_source'])
                else:
                    result.append(item)

            # 종료 조건
            if count < size:
                break

            if 0 < limit < sum_count:
                break

        return result, elastic

    def dump_elastic_search(self, host='http://localhost:9200', index='detail'):
        """elastic-search 의 데이터를 덤프 받는다.

        :param host: 접속 주소
        :param index: 인덱스명
        :return: 없음
        """
        import json

        # 한번에 가져올 문서수
        size = 1000

        count = 1
        sum_count = 0
        scroll_id = ''
        total = -1

        # 서버 접속
        elastic = self.open_elastic_search(host=[host], index=index)
        if elastic is None:
            return

        while count > 0:
            # 스크롤 아이디가 있다면 scroll 함수 호출
            if scroll_id == '':
                search_result = elastic.search(index=index, doc_type=index, body={}, scroll='2m', size=size)
            else:
                search_result = elastic.scroll(scroll_id=scroll_id, scroll='2m')

            # 검색 결과 추출
            scroll_id = search_result['_scroll_id']

            hits = search_result['hits']

            if total != hits['total']:
                total = hits['total']

            count = len(hits['hits'])

            sum_count += count
            logging.info(msg='{} {:,} {:,} {:,}'.format(index, count, sum_count, total))

            for item in hits['hits']:
                line = json.dumps(item, ensure_ascii=False, sort_keys=True)
                print(line, flush=True)

            # 종료 조건
            if count < size:
                break

        return

    def export_detail(self):
        """"""
        host = 'http://localhost:9200'
        index = 'detail'

        # 한번에 가져올 문서수
        size = 1000

        count = 1
        sum_count = 0
        scroll_id = ''
        total = -1

        # 서버 접속
        elastic = self.open_elastic_search(host=[host], index=index)
        if elastic is None:
            return

        query = {
            '_source': 'category,question,detail_question,answer,answer_user'.split(','),
            'size': '1000'
        }

        while count > 0:
            # 스크롤 아이디가 있다면 scroll 함수 호출
            if scroll_id == '':
                search_result = elastic.search(index=index, doc_type=index, body=query, scroll='2m', size=size)
            else:
                search_result = elastic.scroll(scroll_id=scroll_id, scroll='2m')

            # 검색 결과 추출
            scroll_id = search_result['_scroll_id']

            hits = search_result['hits']

            if total != hits['total']:
                total = hits['total']

            count = len(hits['hits'])

            sum_count += count
            logging.info(msg='{} {:,} {:,} {:,}'.format(index, count, sum_count, total))

            for item in hits['hits']:
                doc = item['_source']

                common = [
                    item['_id'],
                    doc['category'],
                    doc['question'],
                    doc['detail_question']
                ]

                for i in range(len(doc['answer'])):
                    try:
                        answer = [doc['answer_user'][i], doc['answer'][i]]
                        print('\t'.join(common + answer), flush=True)
                    except Exception as e:
                        pass

            # 종료 조건
            if count < size:
                break

        return


class Crawler(NaverKinUtils):
    """ 네이버 지식인 크롤러 """

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

    def batch_question_list(self):
        """ 질문 목록 전부를 가져온다.

        :return: 없음
        """
        url = 'https://m.kin.naver.com/mobile/qna/kinupList.nhn?' \
              'sortType=writeTime&resultMode=json&dirId={dir_id}&countPerPage={size}&page={page}'

        dir_id_list = [4, 11, 1, 2, 3, 8, 7, 6, 9, 10, 5, 13, 12, 20]
        for dir_id in dir_id_list:
            self.get_question_list(url=url, dir_id=dir_id, end=500)

        return

    def get_question_list(self, url, dir_id=4, start=1, end=90000, size=20):
        """ 네이버 지식인 경제 분야 질문 목록을 크롤링한다.

        :param url:
            쿼리 조회 URL 패턴::

                https://m.kin.naver.com/mobile/qna/kinupList.nhn?
                    sortType=writeTime
                    &resultMode=json
                    &dirId={dir_id}
                    &countPerPage={size}
                    &page={page}

        :param dir_id: 도메인 (4: 경제)
        :param start: 시작 페이지
        :param end: 종료 페이지
        :param size: 페이지 크기
        :return: 없음
        """
        import requests
        from time import sleep

        delay = 5
        bulk_size = 100

        table_name = 'naver-kin-question_list'

        self.elastic_info['index'] = table_name
        self.elastic_info['type'] = 'doc'

        for page in range(start, end):
            query_url = url.format(dir_id=dir_id, size=size, page=page)

            request_result = requests.get(url=query_url, headers=self.headers,
                                          allow_redirects=True, timeout=60)

            result = request_result.json()

            result_list = []
            if 'answerList' in result:
                result_list = result['answerList']

            if 'lists' in result:
                result_list = result['lists']

            if len(result_list) == 0:
                break

            logging.info(msg='{} {:,} ~ {:,} {:,}'.format(dir_id, page, end, len(result_list)))

            # 결과 저장
            for doc in result_list:
                doc['_id'] = '{}-{}-{}'.format(doc['d1Id'], doc['dirId'], doc['docId'])

                self.save_elastic_search_document(host=self.elastic_info['host'], index=table_name,
                                                  doc_type=self.elastic_info['type'], document=doc,
                                                  bulk_size=bulk_size, insert=True)

            self.save_elastic_search_document(host=self.elastic_info['host'], index=table_name,
                                              doc_type=self.elastic_info['type'], document=None,
                                              bulk_size=0, insert=True)

            sleep(delay)

        return

    def move_document(self, source_index, target_index, document_id, host, source_id=None):
        """ 문서를 이동한다.

        :param source_index: 원본 인덱스명
        :param target_index: 이동할 인덱스명
        :param source_id: 원본 문서 아이디
        :param document_id: 문서 아이디
        :param host: 접속 주소
        :return: 없음
        """
        # import elasticsearch

        if source_id is None:
            source_id = document_id

        source = self.open_elastic_search(host=host, index=source_index)

        # 문서 읽기
        try:
            document = source.get(index=source_index, doc_type=source_index, id=source_id)

            if source_id != document_id:
                document['_source']['_id'] = document_id
        except Exception as e:
            logging.error(msg='error as move_document', exc_info=e)
            return

        # 문서 저장
        self.save_elastic_search_document(document=document['_source'], index=target_index, host=host,
                                          bulk_size=0, insert=True, doc_type='doc')

        # 기존 문서 삭제
        source.delete(index=source_index, doc_type=source_index, id=source_id)

        return

    def sync_id(self, index='detail'):
        """document_id 와 _id 가 형식에 맞지 않는 것을 바꾼다. """
        query = {
            '_source': 'd1Id,dirId,docId,document_id'.split(','),
            'size': '1000',
            'query': {
                'match_all': {}
            }
        }

        data_list, elastic = self.get_document_list(index=index, query=query, only_source=False, limit=-1)

        for item in data_list:
            doc = item['_source']

            if index == 'detail' and 'document_id' in doc:
                d_id = doc['document_id']
            else:
                if 'd1Id' not in doc:
                    doc['d1Id'] = str(doc['dirId'])[0]

                d_id = '{}-{}-{}'.format(doc['d1Id'], doc['dirId'], doc['docId'])

            if item['_id'].find('201807') == 0 or d_id != item['_id']:
                print(item)
                self.move_document(host=self.elastic_info['host'], source_index=index, target_index=index,
                                   document_id=d_id, source_id=item['_id'])

        return

    def get_detail(self, index='question_list', match_phrase='{"fullDirNamePath": "주식"}'):
        """질문/답변 상세 페이지를 크롤링한다.

        :param index: 인덱스명 question_list, answer_list
        :param match_phrase: "fullDirNamePath": "주식"
        :return:
            https://m.kin.naver.com/mobile/qna/detail.nhn?d1id=4&dirId=40308&docId=303328933
            https://m.kin.naver.com/mobile/qna/detail.nhn?d1Id=6&dirId=60222&docId=301601614
        """
        import json
        import requests
        from time import sleep

        from bs4 import BeautifulSoup

        delay = 5
        url_frame = 'https://m.kin.naver.com/mobile/qna/detail.nhn?dirId={dirId}&docId={docId}'

        query = {
            '_source': 'd1Id,dirId,docId'.split(','),
            'size': '1000',
            'query': {
                'bool': {
                    'must': {
                        'match_phrase': {}
                    }
                }
            }
        }

        if match_phrase is not None:
            if isinstance(match_phrase, str):
                match_phrase = json.loads(match_phrase)

            query['query']['bool']['must']['match_phrase'] = match_phrase

        question_list, elastic = self.get_document_list(index=index, query=query)

        detail_index = 'naver-kin-detail'

        # 저장 인덱스명 설정
        self.elastic_info['index'] = detail_index
        self.elastic_info['type'] = 'doc'

        i = -1
        size = len(question_list)

        for question in question_list:
            if 'd1Id' not in question:
                question['d1Id'] = str(question['dirId'])[0]

            i += 1
            doc_id = '{}-{}-{}'.format(question['d1Id'], question['dirId'], question['docId'])

            exists = elastic.exists(index=detail_index, doc_type=detail_index, id=doc_id)
            if exists is True:
                logging.info(msg='skip {} {}'.format(doc_id, detail_index))
                self.move_document(source_index=index, target_index='{}.done'.format(index),
                                   document_id=doc_id, host=self.elastic_info['host'])
                continue

            request_url = url_frame.format(**question)

            # 질문 상세 페이지 크롤링
            logging.info(msg='상세 질문: {:,}/{:,} {} {}'.format(i, size, doc_id, request_url))
            request_result = requests.get(url=request_url, headers=self.headers,
                                          allow_redirects=True, timeout=60)

            # 저장
            soup = BeautifulSoup(request_result.content, 'html5lib')

            content = soup.find('div', {'class': 'sec_col1'})
            if content is None:
                continue

            detail_doc, content = self.parse_content(html=None, soup=content)

            detail_doc['_id'] = doc_id
            detail_doc['html'] = str(content.prettify())

            self.save_elastic_search_document(host=self.elastic_info['host'], index=detail_index,
                                              doc_type=self.elastic_info['type'], document=detail_doc,
                                              bulk_size=0, insert=True)

            self.move_document(source_index=index, target_index='{}.done'.format(index),
                               document_id=doc_id, host=self.elastic_info['host'])

            sleep(delay)

        return

    @staticmethod
    def batch_answer_list(index, match_phrase):
        """사용자별 답변 목록를 가져온다.

        :return:
        """
        answer_list = {}
        # with open(user_filename, 'r') as fp:
        #     for line in fp.readlines():
        #         line = line.strip()
        #
        #         if line == '' or line[0] == '#':
        #             continue
        #
        #         user_id, user_name = line.split('\t', maxsplit=1)
        #
        #         answer_list[user_name] = user_id

        # https://m.kin.naver.com/mobile/user/answerList.nhn?
        #   page=3&countPerPage=20&dirId=0&u=LOLmw2nTPw02cmSW5fzHYaVycqNwxX3QNy3VuztCb6c%3D

        url = 'https://m.kin.naver.com/mobile/user/answerList.nhn' \
              '?page={{page}}&countPerPage={{size}}&dirId={{dir_id}}&u={user_id}'

        for user_name in answer_list:
            user_id = answer_list[user_name]

            query_url = url.format(user_id=user_id)

            print(user_name, user_id, query_url)

        return

    def get_partner_list(self):
        """지식 파트너 목록을 크롤링한다.

        저장 구조::

            {
              "countPerPage": 10,
              "page": 1,
              "totalCount": 349,
              "isSuccess": true,
              "queryTime": "2018-07-13 16:28:46",
              "lists": [
                {
                  "partnerName": "여성가족부.한국청소년상담복지개발원",
                  "bestAnswerRate": 70.5,
                  "bestAnswerCnt": 10083,
                  "u": "6oCfeacJKVQGwsBB7OHEIS4miiPixwQ%2FoueervNeYrg%3D",
                  "userActiveDirs": [
                    {
                      "divisionIds": [],
                      "masterId": 0,
                      "dirType": "NONLEAF",
                      "localId": 0,
                      "sexFlag": "N",
                      "parentId": 20,
                      "dbName": "db_worry",
                      "open100Flag": "N",
                      "topShow": "N",
                      "relatedIds": "0",
                      "restFlag": "N",
                      "namePath": "고민Q&A>아동, 미성년 상담",
                      "hiddenFlag": "N",
                      "adultFlag": "N",
                      "linkedId": "0",
                      "displayFlag": 0,
                      "dirName": "아동, 미성년 상담",
                      "templateIds": [],
                      "depth": 2,
                      "dirId": 2001,
                      "linkId": 0,
                      "didPath": "20>2001",
                      "childCnt": 7,
                      "edirId": 0,
                      "expertListType": "",
                      "popular": "N",
                      "showOrder": 0
                    }
                  ],
                  "memberViewType": false,
                  "viewType": "ANSWER",
                  "photoUrl": "https://kin-phinf.pstatic.net/20120727_216/1343367618928V5OzE_JPEG/%B3%D7%C0%CC%B9%F6%BF%EB%B7%CE%B0%ED%28300.3000%29.jpg"
                },
                (...)
              ]
            }
        :return:
        """
        import requests
        from time import sleep

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

        url_frame = 'https://m.kin.naver.com/mobile/people/partnerList.nhn' \
                    '?resultMode=json&m=partnerList&page={page}&dirId=0'

        table_name = 'naver-kin-partner_list'

        # 인덱스명 설정
        self.elastic_info['index'] = table_name
        self.elastic_info['type'] = 'doc'

        for page in range(1, 1000):
            request_url = url_frame.format(page=page)

            request_result = requests.get(url=request_url, headers=headers,
                                          allow_redirects=True, timeout=30, verify=False)

            result = request_result.json()

            if 'lists' in result:
                size = len(result['lists'])
                if size == 0:
                    break

                logging.info(msg='{}, {}'.format(size, request_url))

                for doc in result['lists']:
                    doc['_id'] = doc['u']

                    self.save_elastic_search_document(host=self.elastic_info['host'], index=table_name,
                                                      doc_type=self.elastic_info['type'], document=doc,
                                                      bulk_size=100, insert=True)

            self.save_elastic_search_document(host=self.elastic_info['host'], index=table_name,
                                              doc_type=self.elastic_info['type'], document=None,
                                              bulk_size=0, insert=True)

            sleep(5)

        return

    def get_expert_list(self):
        """분야별 전문가 목록을 크롤링한다.

            반환 구조::

                {
                  "result": [
                    {
                      "locationUrl": "http://map.naver.com/local/siteview.nhn?code=71373752",
                      "occupation": "전문의",
                      "companyOpen": "Y",
                      "organizationName": "하이닥",
                      "expertRole": 1,
                      "encodedU": "%2F3soE1QYD7D3mkrmubU2VOr7v7y2zOUWTkk2cj31yRU%3D",
                      "organizationId": 2,
                      "companyName": "고운마취통증의학과의원",
                      "photo": "https://kin-phinf.pstatic.net/exphoto/expert/65/fourlong_1452051150989.jpg",
                      "homepage": "http://gwpainfree.com",
                      "country": "",
                      "area": "경남",
                      "locationOpen": "Y",
                      "answerCount": 5587,
                      "writeTime": "2016-01-06 12:15:59.0",
                      "edirId": 3,
                      "divisionId": 1,
                      "companyPosition": "원장",
                      "workingArea": "domestic",
                      "name": "노민현",
                      "homepageOpen": "Y",
                      "edirName": "마취통증의학과"
                    },
                    (...)
                  ],
                  "totalCount": 10,
                  "errorMsg": "",
                  "isSuccess": true
                }
        """
        import requests
        from time import sleep
        from urllib.parse import unquote

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

        expert_type_list = ['doctor', 'lawyer', 'labor', 'animaldoctor', 'pharmacist', 'taxacc', 'dietitian']

        url_frame = 'https://m.kin.naver.com/mobile/ajax/getExpertListAjax.nhn' \
                    '?resultMode=json&m=getExpertListAjax&expertType={expert_type}&page={page}&all=0'

        table_name = 'naver-kin-expert_user_list'

        # 인덱스명 설정
        self.elastic_info['index'] = table_name
        self.elastic_info['type'] = 'doc'

        for expert_type in expert_type_list:
            for page in range(1, 1000):
                request_url = url_frame.format(expert_type=expert_type, page=page)

                request_result = requests.get(url=request_url, headers=headers,
                                              allow_redirects=True, timeout=30, verify=False)

                result = request_result.json()

                if 'result' in result:
                    size = len(result['result'])
                    if size == 0:
                        break

                    logging.info(msg='{}, {}'.format(size, request_url))

                    for doc in result['result']:
                        doc['expert_type'] = expert_type

                        doc['u'] = unquote(doc['encodedU'])
                        doc['_id'] = doc['u']

                        self.save_elastic_search_document(host=self.elastic_info['host'], index=table_name,
                                                          doc_type=self.elastic_info['type'], document=doc,
                                                          bulk_size=100, insert=True)

                self.save_elastic_search_document(host=self.elastic_info['host'], index=table_name,
                                                  doc_type=self.elastic_info['type'], document=None,
                                                  bulk_size=0, insert=True)
                sleep(5)

        return

    def get_elite_user_list(self):
        """ 명예의 전당 채택과 년도별 사용자 목록을 가져온다.

        :return:
        """
        import requests
        from time import sleep

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

        month = 0
        for year in range(2012, 2019):
            table_name = 'naver-kin-expert_user_list_{}'.format(year)

            # 인덱스명 설정
            self.elastic_info['index'] = table_name
            self.elastic_info['type'] = 'doc'

            url = 'https://kin.naver.com/hall/eliteUser.nhn?year={}'.format(year)

            result = requests.get(url=url, headers=headers,
                                  allow_redirects=True, timeout=30, verify=False)

            cookies = requests.utils.dict_from_cookiejar(result.cookies)
            logging.info(msg='eliteUser cookie: {} {}'.format(result, cookies))

            headers['referer'] = url

            for page in range(1, 6):
                list_url = 'https://kin.naver.com/ajax/eliteUserAjax.nhn' \
                           '?year={}&month={}&page={}'.format(year, month, page)

                request_result = requests.get(url=list_url, headers=headers, cookies=cookies,
                                              allow_redirects=True, timeout=60)

                result = request_result.json()

                if 'eliteUserList' in result:
                    logging.info(msg='{}, {}'.format(len(result['eliteUserList']), list_url))

                    for doc in result['eliteUserList']:
                        doc['_id'] = doc['u']

                        self.save_elastic_search_document(host=self.elastic_info['host'], index=table_name,
                                                          doc_type=self.elastic_info['type'], document=doc,
                                                          bulk_size=100, insert=True)

                    self.save_elastic_search_document(host=self.elastic_info['host'], index=table_name,
                                                      doc_type=self.elastic_info['type'], document=None,
                                                      bulk_size=0, insert=True)
                sleep(5)

        return

    def get_rank_user_list(self):
        """ 분야별 전문가 목록을 추출한다.

        :return:
        """
        import requests
        from time import sleep

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

        url_frame = 'https://kin.naver.com/qna/directoryExpertList.nhn?dirId={dir_id}'

        list_url_frame = [
            'https://kin.naver.com/ajax/qnaWeekRankAjax.nhn?requestId=weekRank&dirId={dir_id}&page={page}',
            'https://kin.naver.com/ajax/qnaTotalRankAjax.nhn?requestId=totalRank&dirId={dir_id}&page={page}'
        ]

        table_name = 'naver-kin-rank_user_list'

        # 인덱스명 설정
        self.elastic_info['index'] = table_name
        self.elastic_info['type'] = 'doc'

        for dir_name in self.category_list:
            dir_id = self.category_list[dir_name]
            url = url_frame.format(dir_id=dir_id)

            result = requests.get(url=url, headers=headers,
                                  allow_redirects=True, timeout=30, verify=False)

            cookies = requests.utils.dict_from_cookiejar(result.cookies)
            logging.info(msg='cookie: {} {}'.format(result, cookies))

            headers['referer'] = url

            for u_frame in list_url_frame:
                for page in range(1, 10):
                    list_url = u_frame.format(dir_id=dir_id, page=page)

                    request_result = requests.get(url=list_url, headers=headers, cookies=cookies,
                                                  allow_redirects=True, timeout=60)

                    result = request_result.json()

                    if 'result' in result:
                        logging.info(msg='{}, {}'.format(len(result['result']), list_url))

                        for doc in result['result']:
                            doc['_id'] = doc['u']
                            doc['rank_type'] = dir_name

                            self.save_elastic_search_document(host=self.elastic_info['host'], index=table_name,
                                                              doc_type=self.elastic_info['type'], document=doc,
                                                              bulk_size=100, insert=True)

                        self.save_elastic_search_document(host=self.elastic_info['host'], index=table_name,
                                                          doc_type=self.elastic_info['type'], document=None,
                                                          bulk_size=0, insert=True)

                        if len(result['result']) != 20:
                            break

                    sleep(5)

        return


def init_arguments():
    """ 옵션 설정

    :return:
    """
    import textwrap
    import argparse

    description = textwrap.dedent('''\
# 질문 목록 크롤링
python3 naver_kin_crawler.py -question_list 

# 답변 목록 크롤링 
python3 naver_kin_crawler.py -answer_list \\
    -index partner_list \\
    -match_phrase '{"dirName": "가전제품"}'

# 질문 상세 페이지 크롤링 
python3 naver_kin_crawler.py -detail -index answer_list -match_phrase '{"fullDirNamePath": "주식"}'

python3 naver_kin_crawler.py -detail -index question_list -match_phrase '{"fullDirNamePath": "주식"}'
python3 naver_kin_crawler.py -detail -index question_list -match_phrase '{"fullDirNamePath": "경제 정책"}'
python3 naver_kin_crawler.py -detail -index question_list -match_phrase '{"fullDirNamePath": "경제 동향"}'
python3 naver_kin_crawler.py -detail -index question_list -match_phrase '{"fullDirNamePath": "경제 기관"}'


# 답변 목록을 DB에 저장
python3 naver_kin_crawler.py -insert_answer_list -data_path "data/naver/kin/by_user.economy/(사)한국무역협회"

IFS=$'\\n'
data_path="data/naver/kin/by_user.economy.done"
for d in $(ls -1 ${data_path}) ; do
    echo ${d}

    python3 naver_kin_crawler.py -insert_answer_list \\
        -data_path "${data_path}/${d}"
done

# 데이터 덤프 
python3 naver_kin_crawler.py -dump_elastic_search \\
    -host http://localhost:9200 -index detail \\
    | bzip2 - > detail.detail.json.bz2 

    ''')

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=description)

    # 크롤링
    parser.add_argument('-question_list', action='store_true', default=False,
                        help='질문 목록 크롤링')
    parser.add_argument('-detail', action='store_true', default=False,
                        help='답변 상세 페이지 크롤링')
    parser.add_argument('-answer_list', action='store_true', default=False,
                        help='답변 목록 크롤링 (전문가 답변, 지식 파트너 답변 등)')

    parser.add_argument('-elite_user_list', action='store_true', default=False,
                        help='전문가 목록 크롤링')
    parser.add_argument('-rank_user_list', action='store_true', default=False,
                        help='랭킹 사용자 목록 크롤링')
    parser.add_argument('-partner_list', action='store_true', default=False,
                        help='지식 파트너 목록 크롤링')
    parser.add_argument('-get_expert_list', action='store_true', default=False,
                        help='전문가 목록 크롤링')

    # 결과 덤프
    parser.add_argument('-export_detail', action='store_true', default=False,
                        help='export_detail')
    parser.add_argument('-dump_elastic_search', action='store_true', default=False,
                        help='데이터 덤프')

    parser.add_argument('-sync_id', action='store_true', default=False,
                        help='')

    # 파라메터
    parser.add_argument('-host', default='http://localhost:9200', help='elastic-search 주소')
    parser.add_argument('-index', default='question_list', help='인덱스명')
    parser.add_argument('-match_phrase', default='{"fullDirNamePath": "주식"}', help='검색 조건')

    return parser.parse_args()


def main():
    """메인"""
    args = init_arguments()

    crawler = Crawler()

    if args.question_list:
        crawler.batch_question_list()

    if args.answer_list:
        crawler.batch_answer_list(index=args.index, match_phrase=args.match_phrase)

    if args.detail:
        crawler.get_detail(index=args.index, match_phrase=args.match_phrase)

    # 사용자 목록 크롤링
    if args.elite_user_list:
        crawler.get_elite_user_list()

    if args.rank_user_list:
        crawler.get_rank_user_list()

    if args.partner_list:
        crawler.get_partner_list()

    if args.get_expert_list:
        crawler.get_expert_list()

    # 데이터 추출
    if args.dump_elastic_search:
        crawler.dump_elastic_search(host=args.host, index=args.index)

    if args.export_detail:
        crawler.export_detail()

    if args.sync_id:
        crawler.sync_id(index=args.index)

    return


if __name__ == '__main__':
    main()
