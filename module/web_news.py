#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin

import urllib3
from dateutil.parser import parse as date_parse
from dateutil.rrule import rrule, DAILY
from time import sleep

from module.crawler_base import CrawlerBase
from module.elasticsearch_utils import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=MESSAGE)


class WebNewsCrawler(CrawlerBase):
    """웹 뉴스 크롤러 베이스"""

    def __init__(self, job_category='', job_id='', column=''):
        """ 생성자 """
        super().__init__()

        self.job_category = job_category
        self.job_id = job_id
        self.column = column

        self.trace_depth = 0

    def daemon(self):
        """데몬으로 실행"""
        while True:
            # batch 시작전 설정 변경 사항을 업데이트 한다.
            self.update_config()
            daemon_info = self.cfg.job_info['daemon']

            # 시작
            self.batch()

            log_msg = {
                'task': '웹 문서 수집',
                'message': '데몬 슬립',
                'sleep_time': daemon_info['sleep']
            }

            logging.log(level=MESSAGE, msg=log_msg)
            sleep(daemon_info['sleep'])

    def batch(self):
        """카테고리 하위 목록을 크롤링한다."""
        # 카테고리 하위 목록을 크롤링한다.
        for job in self.job_info:
            self.sleep_time = job['sleep']

            self.trace_url_list(job=job)

        return

    def trace_url_list(self, job):
        """url_frame 목록을 반복한다."""
        # url 목록 반복
        for url in job['list']:
            if url['url_frame'].find('date') < 0:
                # page 단위로 크롤링한다.
                self.trace_page_list(url=url, job=job, dt='')
                continue

            # 날짜 지정시
            start_date = date_parse(self.status['start_date'])
            until = date_parse(self.status['end_date'])

            date_list = list(rrule(DAILY, dtstart=start_date, until=until))
            for dt in date_list:
                if dt > datetime.now() + timedelta(1):
                    break

                # page 단위로 크롤링한다.
                self.trace_page_list(url=url, job=job, dt=dt.strftime(url['date_format']))

                # 현재 크롤링 위치 저장
                now = dt - timedelta(1)
                if now > start_date:
                    self.status['start_date'] = now.strftime('%Y-%m-%d')
                    self.cfg.save_status()

        return

    def trace_page_list(self, url, job, dt):
        """뉴스 목록을 크롤링한다."""

        self.trace_depth = 0

        # start 부터 end 까지 반복한다.
        for page in range(self.status['start'], self.status['end'] + 1, self.status['step']):
            # 쿼리 url 생성
            q = {
                'page': page,
                'date': dt
            }
            url['url'] = url['url_frame'].format(**q)

            log_msg = {
                'task': '웹 문서 수집',
                'message': '뉴스 목록 크롤링',
                'url': url,
                'query': q
            }

            logging.info(msg=log_msg)

            if 'category' in url:
                job['category'] = url['category']

            # 기사 목록 조회
            resp = self.get_html_page(url_info=url)
            if resp is None:
                continue

            # 문서 저장
            early_stop = self.trace_news(html=resp, url_info=url, job=job)
            if early_stop is True:
                break

            # 현재 크롤링 위치 저장
            self.status['start'] = page
            self.cfg.save_status()

            # 현재 상태 로그 표시
            log_msg = {
                'task': '웹 문서 수집',
                'message': '기사 목록 조회',
                'category': job['category'],
                'url': url['url']
            }

            logging.log(level=MESSAGE, msg=log_msg)
            sleep(self.sleep_time)

        # 위치 초기화
        self.status['start'] = 1
        if 'category' in self.status:
            del self.status['category']

        self.cfg.save_status()

        return

    def trace_news(self, html, url_info, job):
        """개별 뉴스를 따라간다."""
        # 기사 목록을 추출한다.
        trace_list = self.get_trace_list(html=html, url_info=url_info)
        if trace_list is None:
            return True

        # url 저장 이력 조회
        doc_history = self.get_history(name='doc_history', default={})

        # 베이스 url 추출
        base_url = self.parser.parse_url(url_info['url'])[1]

        # 디비에 연결한다.
        elastic_utils = ElasticSearchUtils(host=job['host'], index=job['index'], bulk_size=20)

        # 개별 뉴스를 따라간다.
        for trace in trace_list:
            item = self.parse_tag(resp=trace, url_info=url_info, parsing_info=self.parsing_info['list'])
            if item is None:
                continue

            item['url'] = urljoin(base_url, item['url'])
            item['category'] = job['category']

            # 기존 크롤링된 문서를 확인한다.
            doc_id = self.get_doc_id(url=item['url'], job=job, item=item)
            if doc_id is None:
                continue

            if 'check_doc_id' in url_info and url_info['check_doc_id'] is True:
                is_skip = self.check_doc_id(doc_id=doc_id, elastic_utils=elastic_utils,
                                            url=item['url'], index=job['index'], doc_history=doc_history)
                if is_skip is True:
                    continue

            # 기사 본문 조회
            article = self.get_article(doc_id, item, job, elastic_utils)
            doc_history[doc_id] = 1

            # 후처리 작업 실행
            if 'post_process' not in job:
                job['post_process'] = None

            self.post_process_utils.insert_job(document=article, post_process_list=job['post_process'])

            log_msg = {
                'task': '웹 문서 수집',
                'message': '뉴스 본문 크롤링: 슬립',
                'sleep_time': self.sleep_time
            }
            logging.info(msg=log_msg)
            sleep(self.sleep_time)

        # 캐쉬 저장
        self.set_history(value=doc_history, name='doc_history')

        # 다음 페이지 정보가 있는 경우
        self.trace_next_page(html=html, url_info=url_info, job=job)

        return False

    def get_article(self, doc_id, item, job, elastic_utils):
        """"""
        article_url = None
        if 'article' in job:
            article_url = job['article']
            article_url['url'] = item['url']

        resp = self.get_html_page(url_info=article_url)
        if resp is None:
            return None

        # 문서 저장
        article = self.parse_tag(resp=resp, url_info=article_url, parsing_info=self.parsing_info['article'])

        article['_id'] = doc_id

        doc = self.save_article(html=resp, article=article, doc=item, elastic_utils=elastic_utils)
        return doc

    def trace_next_page(self, html, url_info, job):
        """다음 페이지를 따라간다."""
        if 'trace_next_page' not in self.parsing_info:
            return

        # html 이 json 인 경우
        if isinstance(html, dict) or isinstance(html, list):
            return

        # 한번에 따라갈 깊이
        trace_tag = self.parsing_info['trace_next_page']
        if trace_tag['max_trace'] > 0:
            if trace_tag['max_trace'] < self.trace_depth:
                self.trace_depth = 0
                return

        self.trace_depth += 1

        # 다음 페이지 url 추출
        trace_list = []
        soup = self.parser.parse_html(html=html, parser_type=self.parsing_info['parser'])
        self.parser.trace_tag(soup=soup, tag_list=trace_tag['tag'], index=0, result=trace_list)

        for tag in trace_list:
            if tag.has_attr('href') is False:
                continue

            url = urljoin(url_info['url'], tag['href'])
            if 'replace' in trace_tag:
                for pattern in trace_tag['replace']:
                    url = re.sub(pattern['from'], pattern['to'], url, flags=re.DOTALL)

            next_url = self.parsing_info
            next_url['url'] = url

            resp = self.get_html_page(url_info=self.parsing_info)
            if resp is None:
                continue

            log_msg = {
                'task': '웹 문서 수집',
                'message': '다음페이지 크롤링: 슬립',
                'sleep_time': self.sleep_time
            }
            logging.info(msg=log_msg)
            sleep(self.sleep_time)

            self.trace_news(html=resp, url_info=url_info, job=job)

        return

    def save_article(self, html, doc, article, elastic_utils):
        """크롤링한 문서를 저장한다."""
        # 후처리
        doc = self.parser.merge_values(item=doc)
        article = self.parser.merge_values(item=article)

        # 파싱 에러 처리
        if 'html_content' in article and len(article['html_content']) != 0:
            doc.update(article)
        else:
            doc['parsing_error'] = True
            doc['raw_html'] = str(html)

            log_msg = {
                'task': '웹 문서 수집',
                'message': 'html_content 필드가 없음',
                'url': doc['url']
            }
            logging.error(msg=log_msg)

        # 문서 아이디 추출
        doc['curl_date'] = datetime.now()

        # 문서 저장
        elastic_utils.save_document(document=doc)
        elastic_utils.flush()

        # 로그 표시
        log_msg = {
            'task': '웹 문서 수집',
            'message': '기사 저장',
            'doc_url': '{}/{}/doc/{}?pretty'.format(elastic_utils.host, elastic_utils.index, doc['document_id'])
        }

        for k in ['document_id', 'date', 'title']:
            if k in doc:
                log_msg[k] = doc[k]

        logging.log(level=MESSAGE, msg=log_msg)

        return doc

    def get_doc_id(self, url, job, item):
        """문서 아이디를 반환한다."""
        id_frame = job['article']['document_id']

        q, _, url_info = self.parser.parse_url(url)

        result = '{}.{}'.format(url_info.path, '.'.join(q.values()))

        if id_frame['type'] == 'path':
            result = url_info.path

            for pattern in id_frame['replace']:
                result = re.sub(pattern['from'], pattern['to'], result, flags=re.DOTALL)
        elif id_frame['type'] == 'query':
            if len(q) == 0:
                log_msg = {
                    'task': '웹 문서 수집',
                    'message': '중복 문서, 건너뜀',
                    'url': url
                }

                logging.info(msg=log_msg)
                return None

            result = id_frame['frame'].format(**q)
        elif id_frame['type'] == 'value':
            result = id_frame['frame'].format(**item)

        result = result.strip()

        return result

    def get_trace_list(self, html, url_info):
        """trace tag 목록을 추출해서 반환한다."""
        trace_list = []
        if 'parser' in url_info and url_info['parser'] == 'json':
            column = url_info['trace']
            if column in html:
                trace_list = html[column]

            str_trace_list = json.dumps(trace_list, ensure_ascii=False, sort_keys=True)
        else:
            soup = self.parser.parse_html(html=html, parser_type=self.parsing_info['parser'])

            self.parser.trace_tag(soup=soup, tag_list=self.parsing_info['trace'],
                                  index=0, result=trace_list)

            str_trace_list = ''
            for item in trace_list:
                str_trace_list += str(item)

        # trace_list 이력 조회
        trace_list_history = self.get_history(name='trace_list', default='')
        if isinstance(trace_list_history, str) is True:
            if str_trace_list == trace_list_history:
                log_msg = {
                    'task': '웹 문서 수집: 개별 기사 조회',
                    'message': '이전 목록과 일치함, 조기 종료',
                    'trace_size': len(trace_list),
                    'sleep_time': self.sleep_time
                }

                logging.log(level=MESSAGE, msg=log_msg)

                sleep(self.sleep_time)
                return None

        self.set_history(value=str_trace_list, name='trace_list')

        return trace_list

    def parse_tag(self, resp, url_info, parsing_info):
        """trace tag 하나를 파싱해서 반환한다."""
        # json 인 경우 맵핑값 매칭
        if 'parser' in url_info and url_info['parser'] == 'json':
            item = resp

            mapping_info = {}
            if 'mapping' in url_info:
                mapping_info = url_info['mapping']

            for k in mapping_info:
                if k[0] == '_':
                    continue

                v = mapping_info[k]
                if v == '' and k in item:
                    del item[k]
                    continue

                if v == '/' and k in item:
                    item.update(item[k])
                    del item[k]
                    continue

            for k in mapping_info:
                if k[0] == '_':
                    continue

                v = mapping_info[k]
                if v.find('{') < 0:
                    continue

                item[k] = v.format(**resp)

        else:
            if isinstance(resp, str) or isinstance(resp, bytes):
                resp = self.parser.parse_html(html=resp, parser_type=self.parsing_info['parser'])

            # 목록에서 기사 본문 링크 추출
            item = self.parser.parse(html=None, soup=resp, parsing_info=parsing_info)

        # url 추출
        if 'url' in item and isinstance(item['url'], list):
            if len(item['url']) > 0:
                item['url'] = item['url'][0]
            else:
                return None

        return item
