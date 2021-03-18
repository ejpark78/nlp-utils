#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import os
import re
from copy import deepcopy
from datetime import datetime, timedelta
from time import sleep
from urllib.parse import parse_qs, urljoin

import requests
import urllib3
from bs4 import BeautifulSoup
from dateutil.rrule import rrule, DAILY
from dotty_dict import dotty
from jsonfinder import jsonfinder

from crawler.utils.elasticsearch_utils import ElasticSearchUtils
from crawler.web_news.base import WebNewsBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class WebNewsCrawler(WebNewsBase):
    """웹 뉴스 크롤러"""

    def __init__(self):
        super().__init__()

        self.trace_depth: int = 0

        self.update_date: bool = False

        self.job_names: set or None = None
        self.job_sub_category: set or None = None

    def post_request(self, job: dict, article: dict, item: dict) -> None:
        """댓글을 요청한다."""
        if 'post_request' not in job:
            return

        req_params = {
            **deepcopy(item),
            **deepcopy(article)
        }

        for url_info in job['post_request']:
            if url_info['response_type'] != 'json':
                return

            headers = self.headers['desktop']
            if 'headers' in url_info:
                headers.update(url_info['headers'])

            url = url_info['url_frame'].format(**req_params)

            try:
                if url_info['method'] != "POST":
                    resp = requests.get(
                        url=url,
                        verify=False,
                        timeout=60,
                        headers=headers,
                        allow_redirects=True,
                    )
                else:
                    body = url_info['data'].format(**req_params)
                    body = parse_qs(body)

                    resp = requests.post(
                        url=url,
                        data=body,
                        verify=False,
                        timeout=60,
                        headers=headers,
                        allow_redirects=True,
                    )
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'post request 조회 에러',
                    'url': url,
                    'exception': str(e),
                })
                return

            # 결과 파싱
            try:
                req_result = resp.json()
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'post request 파싱 에러',
                    'url': url,
                    'exception': str(e),
                })
                return

            result = []
            self.get_dict_value(
                data=req_result,
                result=result,
                key_list=url_info['field'].split('.'),
            )

            if len(result) > 0:
                article[url_info['key']] = result

        return

    def get_trace_list(self, html: str, parsing_info: dict = None) -> list or None:
        """trace tag 목록을 추출해서 반환한다."""
        trace_list = []
        if len(parsing_info) > 0 and 'parser' in parsing_info[0]:
            parsing = parsing_info[0]

            soup = html
            if parsing['parser'] == 'json':
                if isinstance(html, str):
                    soup = json.loads(html)

                column = parsing['column']
                if column == '*':
                    soup = {
                        '*': soup
                    }

                dot = dotty(soup)

                trace_list = list(dot[column]) if column in dot else []
                trace_list = self.flatten(trace_list=trace_list)
            elif parsing['parser'] == 'javascript':
                if isinstance(html, str):
                    soup = BeautifulSoup(html)

                js = [''.join(x.contents) for x in soup.find_all('script') if 'list:' in ''.join(x.contents)][0]

                trace_list = [x for _, _, x in jsonfinder(js) if x is not None][0]
        else:
            soup = self.parser.parse_html(
                html=html,
                parser_type=self.job_config['parsing']['parser'],
            )

            self.parser.trace_tag(
                soup=soup,
                index=0,
                result=trace_list,
                tag_list=self.job_config['parsing']['trace'],
            )

        if len(trace_list) == 0:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'trace_list 가 없음',
                'trace_size': len(trace_list),
                'sleep_time': self.params['sleep'],
            })

            sleep(self.params['sleep'])
            return None

        return trace_list

    def trace_next_page(self, html: str, url_info: dict, job: dict, date: datetime, es: ElasticSearchUtils,
                        query: dict) -> None:
        """다음 페이지를 따라간다."""
        if 'trace_next_page' not in self.job_config['parsing']:
            return

        # html 이 json 인 경우
        if isinstance(html, dict) or isinstance(html, list):
            return

        trace_tag = self.job_config['parsing']['trace_next_page']

        if len(trace_tag) == 0:
            return

        # 한번에 따라갈 깊이
        if trace_tag['max_trace'] > 0:
            if trace_tag['max_trace'] < self.trace_depth:
                self.trace_depth = 0
                return

        self.trace_depth += 1

        # 다음 페이지 url 추출
        soup = self.parser.parse_html(
            html=html,
            parser_type=self.job_config['parsing']['parser'],
        )

        trace_list = []
        self.parser.trace_tag(
            soup=soup,
            index=0,
            result=trace_list,
            tag_list=trace_tag['value'],
        )

        for tag in trace_list:
            if tag.has_attr('href') is False:
                continue

            url = urljoin(url_info['url'], tag['href'])
            if 'replace' in trace_tag:
                for pattern in trace_tag['replace']:
                    url = re.sub(pattern['from'], pattern['to'], url, flags=re.DOTALL)

            next_url = self.job_config['parsing']
            next_url['url'] = url

            resp = self.get_html_page(url_info=self.job_config['parsing'])
            if resp is None:
                continue

            sleep(self.params['sleep'])

            early_stop = self.trace_news(html=resp, url_info=url_info, job=job, date=date, es=es, query=query)
            if early_stop is True:
                break

        return

    def save_article_list(self, item: dict, job: dict, es: ElasticSearchUtils) -> None:
        # 임시 변수 삭제
        for k in ['encoding', 'raw']:
            if k not in item:
                continue
            del item[k]

        item['status'] = 'raw_list'

        self.save_article(es=es, job=job, doc=item, flush=False)

        return

    def trace_article(self, item: dict, job: dict, doc_id: str, es: ElasticSearchUtils) -> bool:
        # 기사 본문 조회
        article_html = self.get_article_body(item=item, offline=False)

        # 문서 저장
        article = self.parse_tag(
            resp=article_html,
            url_info=item,
            base_url=item['url'],
            parsing_info=self.job_config['parsing']['article'],
        )

        self.summary['article'] += 1
        if self.params['verbose'] == 0:
            self.logger.log(msg={'CONFIG_DEBUG': 'article', 'article': self.simplify(article)})

        # 임시 변수 삭제
        if 'encoding' in item:
            del item['encoding']

        if article is None or len(article) == 0:
            return True

        article['_id'] = doc_id

        # 댓글 post process 처리
        self.post_request(article=article, job=job, item=item)

        item['status'] = 'article'

        # 기사 저장
        self.save_article(
            es=es,
            job=job,
            doc=item,
            html=article_html,
            article=article,
        )
        return False

    def trace_news(self, html: str, url_info: dict, job: dict, date: datetime, es: ElasticSearchUtils,
                   query: dict) -> bool:
        """개별 뉴스를 따라간다."""
        # 기사 목록을 추출한다.
        trace_list = self.get_trace_list(html=html, parsing_info=self.job_config['parsing']['trace'])
        if self.params['verbose'] == 0:
            self.logger.log(msg={'CONFIG_DEBUG': 'trace_list', 'trace_list': self.simplify(trace_list)})

        if trace_list is None:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': 'trace_list 가 없음: 조기 종료',
                **url_info
            })
            return True

        # 베이스 url 추출
        base_url = self.parser.parse_url(url_info['url'])[1]

        is_date_range_stop = False

        # 개별 뉴스를 따라간다.
        for trace in trace_list:
            item = self.parse_tag(
                resp=trace,
                url_info=url_info,
                base_url=base_url,
                default_date=date,
                parsing_info=self.job_config['parsing']['list'],
            )

            self.summary['list'] += 1
            if self.params['verbose'] == 0:
                self.logger.log(msg={
                    'CONFIG_DEBUG': 'list info',
                    'trace': self.simplify(trace),
                    'item': self.simplify(item)
                })

            if item is None or 'url' not in item:
                continue

            item['url'] = urljoin(base_url, item['url'])
            item['category'] = job['category']
            item['encoding'] = url_info['encoding'] if 'encoding' in url_info else None

            if date is None and 'date' in item:
                date = item['date']

            if self.is_within_date_range(doc=item, query=query) is False:
                is_date_range_stop = True
                break

            # 기존 크롤링된 문서를 확인한다.
            doc_id = self.get_doc_id(url=item['url'], job=job, item=item)
            self.cache.set(key=doc_id, value=True)

            if self.params['verbose'] == 0:
                self.logger.log(msg={'CONFIG_DEBUG': 'document id', 'doc_id': doc_id})

            if doc_id is None:
                continue

            item['_id'] = doc_id

            is_skip, _ = self.is_skip(date=date, job=job, url=item['url'], doc_id=doc_id, es=es)
            if is_skip is True:
                self.summary['exists'] += 1
                continue

            # 기사 목록 저장
            self.save_article_list(item=item, job=job, es=es)

            if self.params['list']:
                continue

            # 기사 본문을 수집한다.
            if self.trace_article(doc_id=doc_id, item=item, job=job, es=es):
                continue

            sleep(self.params['sleep'])

        if self.params['list']:
            es.flush()

        # 다음 페이지 정보가 있는 경우
        self.trace_next_page(html=html, url_info=url_info, job=job, date=date, es=es, query=query)

        # 날짜 범위 점검
        if is_date_range_stop is True:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '날짜 범위 넘어감: 조기 종료',
            })
            return True

        return False

    def trace_page(self, url_info: dict, job: dict, dt: datetime = None) -> None:
        """뉴스 목록을 크롤링한다."""
        self.trace_depth = 0

        self.cache.clear()
        self.skip_count = 0

        # 디비에 연결한다.
        es = self.open_elasticsearch(date=dt, job=job, mapping=self.params['mapping'])

        # start 부터 end 까지 반복한다.
        for page in range(self.page_range['start'], self.page_range['end'] + 1, self.page_range['step']):
            # 쿼리 url 생성
            q = dict(page=page)
            if dt is not None and 'date_format' in url_info:
                q['date'] = dt.strftime(url_info['date_format'])

            url_info['url'] = url_info['url_frame'].format(**q)

            if 'category' in url_info:
                job['category'] = url_info['category']

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '뉴스 목록 크롤링',
                'job_name': job['name'] if 'name' in job else '',
                'url': url_info['url'] if 'url' in url_info else '',
                'query': q,
                'date': dt.strftime('%Y-%m-%d') if dt is not None else '',
                'skip_count': self.skip_count,
            })

            # 기사 목록 조회
            resp = self.get_html_page(url_info=url_info, log_msg={'trace': '뉴스 목록 조회'})
            self.summary['page'] += 1

            if self.params['verbose'] == 0:
                self.logger.log(msg={'CONFIG_DEBUG': 'list page', 'url': url_info['url']})

            if resp is None:
                continue

            prev_skip_count = self.skip_count

            # 문서 저장
            early_stop = self.trace_news(html=resp, url_info=url_info, job=job, date=dt, es=es, query=q)
            if early_stop is True:
                break

            self.summary['skip'] += self.skip_count

            # 중복 문서 개수 점검
            if 0 < prev_skip_count < self.skip_count - self.params['notice_count']:
                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '마지막 페이지: 종료',
                    'skip_count': f'{self.skip_count} > {prev_skip_count}',
                    **url_info
                })
                return

            sleep(self.params['sleep'])

        return

    def trace_category(self, job: dict) -> None:
        """url_frame 목록을 반복한다."""
        # url 목록 반복
        for url_info in job['list']:
            if self.job_sub_category is not None and 'category' in url_info and \
                    url_info['category'] not in self.job_sub_category:
                continue

            if url_info['url_frame'].find('date') < 0:
                # page 단위로 크롤링한다.
                self.trace_page(url_info=url_info, job=job, dt=None)
                continue

            # 날짜 지정시
            date_list = list(rrule(DAILY, dtstart=self.date_range['start'], until=self.date_range['end']))

            if self.date_range['step'] < 0:
                date_list = sorted(date_list, reverse=True)

            for dt in date_list:
                date_now = datetime.now(self.timezone)
                if dt > date_now + timedelta(1):
                    break

                # page 단위로 크롤링한다.
                self.trace_page(url_info=url_info, job=job, dt=dt)

            self.running_state(tag='category')

        return

    def trace_job(self, job: dict) -> None:
        if 'name' in job and self.job_names is not None:
            if job['name'] not in self.job_names:
                return

        self.params, job = self.merge_params(
            job=job,
            params=self.params,
            default_params=self.default_params
        )

        self.date_range = self.update_date_range(
            step=self.params['date_step'],
            date_range=self.params['date_range'],
        )

        self.page_range = self.update_page_range(
            step=self.params['page_step'],
            page_range=self.params['page_range'],
        )

        if 'host' not in job or 'index' not in job:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '[CONFIG_ERROR] elasticsearch 저장 정보 없음',
            })
            return

        self.trace_category(job=job)

        self.running_state(tag='job')

        return

    def batch(self) -> None:
        """ config -> job -> category -> date -> page 순서 """
        self.params, self.default_params = self.init_arguments()

        params_org = deepcopy(self.params)

        self.job_names = set(self.params['job_name'].split(',')) if self.params['job_name'] != '' else None

        self.job_sub_category = set(self.params['sub_category'].split(',')) \
            if self.params['sub_category'] != '' else None

        # 카테고리 하위 목록을 크롤링한다.
        config_list = self.open_config(filename=self.params['config'])

        for self.job_config in config_list:
            for job in self.job_config['jobs']:
                self.trace_job(job=job)

                # restore original params
                self.params = deepcopy(params_org)

        self.running_state(tag='completed')

        return

    @staticmethod
    def init_arguments() -> (dict, dict):
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--job-name', default='', type=str, help='잡 이름, 없는 경우 전체')

        parser.add_argument('--overwrite', action='store_true', default=False, help='덮어쓰기')

        parser.add_argument('--list', action='store_true', default=False, help='기사 목록 크롤링')
        parser.add_argument('--contents', action='store_true', default=False, help='TODO: 기사 본문 크롤링')
        parser.add_argument('--pipeline', default='', type=str, help='TODO: pipeline')

        parser.add_argument('--verbose', default=-1, type=int, help='verbose 모드: 0=config, 1=INFO')

        parser.add_argument('--sub-category', default='', type=str, help='하위 카테고리')

        parser.add_argument('--date-range', default=None, type=str, help='date 날짜 범위: 2000-01-01~2019-04-10')
        parser.add_argument('--date-step', default=-1, type=int, help='date step')

        parser.add_argument('--page-range', default=None, type=str, help='page 범위: 1~100')
        parser.add_argument('--page-step', default=1, type=int, help='page step')

        parser.add_argument('--sleep', default=10, type=float, help='sleep time')

        parser.add_argument('--config', default=None, type=str, help='설정 파일 정보')
        parser.add_argument('--mapping', default=None, type=str, help='인덱스 맵핑 파일 정보')

        parser.add_argument('--notice-count', default=0, type=int, help='공지 사항 개수')

        return vars(parser.parse_args()), vars(parser.parse_args([]))


if __name__ == '__main__':
    WebNewsCrawler().batch()
