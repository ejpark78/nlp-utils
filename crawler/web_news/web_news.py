#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
from copy import deepcopy
from datetime import datetime, timedelta
from time import sleep
from urllib.parse import parse_qs, urljoin

import requests
import urllib3
from dateutil.rrule import rrule, DAILY, YEARLY

from crawler.utils.elasticsearch_utils import ElasticSearchUtils
from crawler.web_news.base import WebNewsBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'


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
                        timeout=self.params['request_timeout'],
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
                        timeout=self.params['request_timeout'],
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

            early_stop, _ = self.trace_article_list(
                html=resp, url_info=url_info, job=job, date=date, es=es, query=query
            )

            if early_stop is True:
                break

        return

    def trace_article_body(self, item: dict, job: dict, doc_id: str, es: ElasticSearchUtils) -> bool:
        # 기사 본문 조회
        article_html = self.get_article_body(item=item, offline=False)

        # 문서 파싱
        article = self.parse_tag(
            resp=article_html,
            url_info=item,
            base_url=item['url'],
            parsing_info=self.job_config['parsing']['article'],
        )

        if article is None or len(article) == 0:
            self.summary['article_parsing_error'] += 1

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '[EMPTY_DATE] article 내용이 없는 문서, 건너뜀',
                'doc_id': doc_id,
                **item,
            })
            return True

        # check column missing
        columns = set([x['key'] for x in self.job_config['parsing']['article']])
        doc_columns = set(article.keys())

        missing_columns = list(columns.difference(doc_columns))

        if self.params['contents'] and len(missing_columns) > 0:
            self.summary['column_missing_error'] += 1
            # flag = self.is_deleted(resp=article_html)

            item['status'] = 'column_missing_error'
            article['_id'] = doc_id

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': f'[COLUMN_MISSING] {",".join(missing_columns)} 가 없는 문서',
                'doc_id': doc_id,
                'missing_columns': ','.join(missing_columns),
                'url': item['url'] if 'url' in item else '',
            })

            # 기사 저장
            self.save_article(
                es=es,
                job=job,
                doc=item,
                html=article_html,
                article=article,
            )
            return True

        self.summary['article'] += 1

        # 임시 변수 삭제
        if 'encoding' in item:
            del item['encoding']

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

    def trace_article_list(self, html: str, url_info: dict, job: dict, date: datetime, es: ElasticSearchUtils,
                           query: dict) -> (bool, set):
        """개별 뉴스를 따라간다."""
        # 기사 목록을 추출한다.
        trace_list = self.get_trace_list(html=html, parsing_info=self.job_config['parsing']['trace'])

        if len(trace_list) == 0:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '[조기 종료] trace 목록이 없음',
                **url_info
            })
            return True, set()

        # 베이스 url 추출
        base_url = self.parser.parse_url(url_info['url'])[1]

        cache, is_date_range_stop = set(), False

        # 개별 뉴스를 추적한다.
        for trace in trace_list:
            item = self.parse_tag(
                resp=trace,
                url_info=url_info,
                base_url=base_url,
                default_date=date,
                parsing_info=self.job_config['parsing']['list'],
            )

            self.summary['list'] += 1

            if item is None or 'url' not in item:
                continue

            item['url'] = urljoin(base_url, item['url'])
            item['category'] = job['category']
            item['encoding'] = url_info['encoding'] if 'encoding' in url_info else None

            if date is None and 'date' in item:
                date = item['date']

            # 날자 범위 점검: today
            if self.is_within_date_range(doc=item, query=query) is False:
                is_date_range_stop = True
                break

            # 기존 크롤링된 문서를 확인한다.
            doc_id = self.get_doc_id(url=item['url'], job=job, item=item)

            if doc_id is None:
                continue

            item['_id'] = doc_id

            # 캐쉬에 저장된 문서가 있는지 조회
            if item['url'] in cache:
                self.summary['skip'] += 1

                if self.params['verbose'] == 1:
                    self.logger.log(msg={
                        'level': 'INFO',
                        'message': '[CACHE_EXISTS] cache 중복 문서, 건너뜀',
                    })
                continue

            cache.add(item['url'])

            is_skip, _ = self.is_skip(date=date, job=job, url=item['url'], doc_id=doc_id, es=es)
            if is_skip is True:
                self.summary['exists'] += 1
                continue

            # 기사 목록 저장
            self.save_article_list(item=item, job=job, es=es)

            if self.params['list']:
                continue

            # 기사 본문을 수집한다.
            if self.trace_article_body(doc_id=doc_id, item=item, job=job, es=es):
                continue

            sleep(self.params['sleep'])

        if self.params['list']:
            es.flush()

        # 날짜 범위 점검
        if is_date_range_stop is True:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '[조기 종료] 날짜 범위 넘어감',
            })
            return True, cache

        return False, cache

    def trace_page_list(self, url_info: dict, job: dict, dt: datetime = None) -> None:
        """뉴스 목록을 크롤링한다."""
        self.trace_depth = 0

        history = set()

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
                'category': '[' + ']['.join([job[x] for x in ['name', 'category'] if x in job]) + ']',
                'url': url_info['url'] if 'url' in url_info else '',
                'date': dt.strftime('%Y-%m-%d') if dt is not None else '',
            })

            # 기사 목록 조회
            resp = self.get_html_page(url_info=url_info, log_msg={'trace': '뉴스 목록 조회'})
            self.summary['page'] += 1

            if resp is None:
                continue

            # 문서 저장
            early_stop, cache = self.trace_article_list(
                html=resp, url_info=url_info, job=job, date=dt, es=es, query=q
            )
            if early_stop is True:
                break

            # 중복 문서 개수 점검
            if 0 == len(cache) or history.intersection(cache) == cache:
                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '[조기 종료] 마지막 페이지',
                    **url_info
                })
                return

            if len(history) > 200:
                history.clear()

            history.update(cache)

            sleep(self.params['sleep'])

        return

    def trace_category(self, job: dict) -> None:
        """url_frame 목록을 반복한다."""
        self.summary['job'] = {**job}

        # url 목록 반복
        for url_info in job['list']:
            if self.job_sub_category is not None and 'category' in url_info and \
                    url_info['category'] not in self.job_sub_category:
                continue

            if url_info['url_frame'].find('date') < 0:
                # page 단위로 크롤링한다.
                self.trace_page_list(url_info=url_info, job=job, dt=None)
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
                self.trace_page_list(url_info=url_info, job=job, dt=dt)

            self.show_summary(tag='category', es=ElasticSearchUtils(host=job['host'], http_auth=job['http_auth']))

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

        # contents
        if self.params['contents'] is True:
            self.trace_contents(job=job)
        else:
            self.trace_category(job=job)

        self.show_summary(tag='job', es=ElasticSearchUtils(host=job['host'], http_auth=job['http_auth']))

        return

    def trace_contents(self, job: dict) -> None:
        self.params, job = self.merge_params(
            job=job,
            params=self.params,
            default_params=self.default_params
        )

        es = ElasticSearchUtils(host=job['host'], http_auth=job['http_auth'])

        dt_query = es.get_date_range_query(date_range=self.params['date_range'])

        query = {
            'track_total_hits': True,
            '_source': ['url', 'status'],
            'query': {
                'bool': {
                    'must_not': [{
                        'exists': {
                            'field': 'contents'
                        }
                    }, {
                        'term': {
                            'status': {
                                'value': 'column_missing_error'
                            }
                        }
                    }],
                    **dt_query['query']['bool']
                }
            }
        }

        date_list = list(rrule(YEARLY, dtstart=self.date_range['start'], until=self.date_range['end']))

        for dt in date_list:
            prev_index, es.index = es.index, job['index'].format(year=dt.year)

            doc_list = []
            es.dump_index(index=es.index, query=query, result=doc_list)

            doc_list = [x for x in doc_list if 'status' in x and x['status'].find('error') < 0]

            for doc in doc_list:
                # 기사 본문을 수집한다.
                self.trace_article_body(doc_id=doc['_id'], item={'url': doc['url']}, job=job, es=es)

                sleep(self.params['sleep'])

            es.index = prev_index

        return

    def batch(self) -> None:
        """  순서
        batch(config)
            -> trace_job
            -> trace_category
            -> trace_page_list(date)
            -> trace_article_list(page)
            -> trace_article_body
        """
        self.params, self.default_params = self.init_arguments()

        params_org = deepcopy(self.params)

        self.job_names = set(self.params['job_name'].split(',')) if self.params['job_name'] != '' else None

        self.job_sub_category = set(self.params['sub_category'].split(',')) \
            if self.params['sub_category'] != '' else None

        # 카테고리 하위 목록을 크롤링한다.
        config_list = self.open_config(filename=self.params['config'])

        last_job = None
        for self.job_config in config_list:
            for job in self.job_config['jobs']:
                self.trace_job(job=job)

                last_job = job

                # restore original params
                self.params = deepcopy(params_org)

        if 'job' in self.summary:
            del self.summary['job']

        if last_job:
            self.show_summary(
                tag='completed',
                es=ElasticSearchUtils(
                    host=last_job['host'],
                    http_auth=last_job['http_auth']) if 'host' in last_job else None
            )

        return

    @staticmethod
    def init_arguments() -> (dict, dict):
        import argparse

        parser = argparse.ArgumentParser()

        # flow-control
        parser.add_argument('--list', action='store_true', default=False, help='기사 목록 크롤링')
        parser.add_argument('--contents', action='store_true', default=False, help='기사 본문 크롤링')

        # essential
        parser.add_argument('--config', default=None, type=str, help='설정 파일 정보')

        # config overwrite
        parser.add_argument('--job-name', default='', type=str, help='잡 이름, 없는 경우 전체')
        parser.add_argument('--sub-category', default='', type=str, help='하위 카테고리')

        parser.add_argument('--date-range', default=None, type=str, help='date 날짜 범위: 2000-01-01~2019-04-10')
        parser.add_argument('--date-step', default=-1, type=int, help='date step')

        parser.add_argument('--page-range', default=None, type=str, help='page 범위: 1~100')
        parser.add_argument('--page-step', default=1, type=int, help='page step')

        parser.add_argument('--sleep', default=10, type=float, help='sleep time')
        parser.add_argument('--request-timeout', default=320, type=float, help='request timeout')

        # optional
        parser.add_argument('--overwrite', action='store_true', default=False, help='(optional) 덮어쓰기')

        parser.add_argument('--mapping', default=None, type=str, help='(optional) 인덱스 맵핑 파일 정보')

        parser.add_argument('--verbose', default=-1, type=int, help='(optional) verbose 모드: 1=INFO')

        return vars(parser.parse_args()), vars(parser.parse_args([]))


if __name__ == '__main__':
    WebNewsCrawler().batch()
