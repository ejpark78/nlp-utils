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

            logging.info('데몬 슬립: {} 초'.format(daemon_info['sleep']))
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
        url_list = job['url_frame']

        # url 목록 반복
        for url in url_list:
            if url['url'].find('date') < 0:
                # page 단위로 크롤링한다.
                self.trace_page_list(url=url, job=job, dt='')
            else:
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
            query_url = url['url'].format(**q)
            logging.info('page url: {}'.format(query_url))

            if 'category' in url:
                job['category'] = url['category']

            parser_type = None
            if 'parser' in url:
                parser_type = url['parser']

            # 기사 목록 조회
            resp = self.get_html_page(url=query_url, parser_type=parser_type)
            if resp is None:
                continue

            # 문서 저장
            early_stop = self.trace_news(html=resp, base_url=query_url, job=job)
            if early_stop is True:
                break

            # 현재 크롤링 위치 저장
            self.status['start'] = page
            self.cfg.save_status()

            # 현재 상태 로그 표시
            msg = '기사 목록: {}, {}'.format(job['category'], query_url)
            logging.log(level=MESSAGE, msg=msg)
            sleep(self.sleep_time)

        # 위치 초기화
        self.status['start'] = 1
        if 'category' in self.status:
            del self.status['category']

        self.cfg.save_status()

        return

    def trace_news(self, html, base_url, job):
        """개별 뉴스를 따라간다."""
        # 기사 목록을 추출한다.
        trace_list = self.get_trace_list(html=html)
        if trace_list is None:
            return True

        # url 저장 이력 조회
        doc_history = self.get_history(name='doc_history', default={})

        # 베이스 url 추출
        base_url = self.parser.parse_url(base_url)[1]

        # 디비에 연결한다.
        elastic_utils = ElasticSearchUtils(host=job['host'], index=job['index'], bulk_size=20)

        # 개별 뉴스를 따라간다.
        for trace in trace_list:
            item = self.get_trace_item(trace=trace)
            if item is None:
                continue

            item['url'] = urljoin(base_url, item['url'])
            item['category'] = job['category']

            # 기존 크롤링된 문서를 확인한다.
            doc_id = self.get_doc_id(url=item['url'], job=job)
            if doc_id is None:
                continue

            is_skip = self.check_doc_id(doc_id=doc_id, elastic_utils=elastic_utils,
                                        url=item['url'], index=job['index'], doc_history=doc_history)
            if is_skip is True:
                continue

            # 기사 본문 조회
            resp = self.get_html_page(item['url'])
            if resp is None:
                continue

            # 문서 저장
            item['_id'] = doc_id
            doc = self.save_doc(resp, item, elastic_utils=elastic_utils)

            doc_history[doc_id] = 1

            # 후처리 작업 실행
            if 'post_process' not in job:
                job['post_process'] = None

            self.post_process_utils.insert_job(document=doc, post_process_list=job['post_process'])

            logging.info('슬립: {} 초'.format(self.sleep_time))
            sleep(self.sleep_time)

        # 캐쉬 저장
        self.set_history(value=doc_history, name='doc_history')

        # 다음 페이지 정보가 있는 경우
        self.trace_next_page(html=html, base_url=base_url, job=job)

        return False

    def trace_next_page(self, html, base_url, job):
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

            url = urljoin(base_url, tag['href'])
            if 'replace' in trace_tag:
                for pattern in trace_tag['replace']:
                    url = re.sub(pattern['from'], pattern['to'], url, flags=re.DOTALL)

            resp = self.get_html_page(url=url, parser_type=self.parsing_info['parser'])
            if resp is None:
                continue

            logging.info('슬립: {} 초'.format(self.sleep_time))
            sleep(self.sleep_time)

            self.trace_news(html=resp, base_url=url, job=job)

        return

    def save_doc(self, html, doc, elastic_utils):
        """크롤링한 문서를 저장한다."""
        soup = self.parser.parse_html(html=html, parser_type=self.parsing_info['parser'])

        # html 본문에서 값 추출
        item = self.parser.parse(soup=soup, parsing_info=self.parsing_info['article'])

        doc.update(item)

        # 문서 아이디 추출
        doc['curl_date'] = datetime.now()

        # 문서 저장
        elastic_utils.save_document(document=doc)
        elastic_utils.flush()

        # 로그 표시
        doc_url = '{}/{}/doc/{}?pretty'.format(elastic_utils.host, elastic_utils.index, doc['document_id'])
        msg = '문서 저장: {} {} {}, {}'.format(doc['document_id'], doc['date'], doc['title'], doc_url)
        logging.log(level=MESSAGE, msg=msg)

        return doc

    def get_doc_id(self, url, job):
        """문서 아이디를 반환한다."""
        id_frame = job['id_frame']

        q, _, url_info = self.parser.parse_url(url)

        result = '{}.{}'.format(url_info.path, '.'.join(q.values()))

        if id_frame['type'] == 'path':
            result = url_info.path

            for pattern in id_frame['replace']:
                result = re.sub(pattern['from'], pattern['to'], result, flags=re.DOTALL)
        elif id_frame['type'] == 'query':
            if len(q) == 0:
                logging.info('skip {}'.format(url))
                return None

            result = id_frame['frame'].format(**q)

        result = result.strip()

        return result

    def get_trace_list(self, html):
        """trace tag 목록을 추출해서 반환한다."""
        trace_list = []
        if isinstance(html, dict) or isinstance(html, list):
            column = self.parsing_info['trace']
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
                msg = '이전 목록과 일치함, 조기 종료: size {}, 슬립: {} 초'.format(len(trace_list), self.sleep_time)
                logging.log(level=MESSAGE, msg=msg)

                sleep(self.sleep_time)
                return None

        self.set_history(value=str_trace_list, name='trace_list')

        return trace_list

    def get_trace_item(self, trace):
        """trace tag 하나를 파싱해서 반환한다."""
        if isinstance(trace, dict):
            item = trace

            for k in self.parsing_info['list']:
                v = self.parsing_info['list'][k]
                item[k] = v.format(**trace)
        else:
            # 목록에서 기사 본문 링크 추출
            item = self.parser.parse(html=None, soup=trace,
                                     parsing_info=self.parsing_info['list'])

        if isinstance(item['url'], list):
            if len(item['url']) > 0:
                item['url'] = item['url'][0]
            else:
                return None

        return item
