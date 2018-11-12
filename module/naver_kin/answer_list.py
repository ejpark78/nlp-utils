#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from time import sleep

import requests

from html_parser import HtmlParser

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class AnswerList(HtmlParser):
    """답변 목록을 중심으로 크롤링"""

    def __init__(self):
        """ 생성자 """

        super().__init__()

    @staticmethod
    def batch_answer_list(index, match_phrase):
        """사용자별 답변 목록를 가져온다. """
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
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

        url_frame = 'https://m.kin.naver.com/mobile/people/partnerList.nhn' \
                    '?resultMode=json&m=partnerList&page={page}&dirId=0'

        table_name = 'crawler-naver-kin-partner_list'

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
                                                      doc_type='doc', document=doc,
                                                      bulk_size=100, insert=True)

            self.save_elastic_search_document(host=self.elastic_info['host'], index=table_name,
                                              doc_type='doc', document=None,
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
        from urllib.parse import unquote

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

        expert_type_list = ['doctor', 'lawyer', 'labor', 'animaldoctor', 'pharmacist', 'taxacc', 'dietitian']

        url_frame = 'https://m.kin.naver.com/mobile/ajax/getExpertListAjax.nhn' \
                    '?resultMode=json&m=getExpertListAjax&expertType={expert_type}&page={page}&all=0'

        table_name = 'crawler-naver-kin-expert_user_list'

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
                                                          doc_type='doc', document=doc,
                                                          bulk_size=100, insert=True)

                self.save_elastic_search_document(host=self.elastic_info['host'], index=table_name,
                                                  doc_type='doc', document=None,
                                                  bulk_size=0, insert=True)
                sleep(5)

        return

    def get_elite_user_list(self):
        """ 명예의 전당 채택과 년도별 사용자 목록을 가져온다. """
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

        month = 0
        for year in range(2012, 2019):
            table_name = 'crawler-naver-kin-expert_user_list_{}'.format(year)

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
                                                          doc_type='doc', document=doc,
                                                          bulk_size=100, insert=True)

                    self.save_elastic_search_document(host=self.elastic_info['host'], index=table_name,
                                                      doc_type='doc', document=None,
                                                      bulk_size=0, insert=True)
                sleep(5)

        return

    def get_rank_user_list(self):
        """ 분야별 전문가 목록을 추출한다. """
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

        table_name = 'crawler-naver-kin-rank_user_list'

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
                                                              doc_type='doc', document=doc,
                                                              bulk_size=100, insert=True)

                        self.save_elastic_search_document(host=self.elastic_info['host'], index=table_name,
                                                          doc_type='doc', document=None,
                                                          bulk_size=0, insert=True)

                        if len(result['result']) != 20:
                            break

                    sleep(5)

        return
