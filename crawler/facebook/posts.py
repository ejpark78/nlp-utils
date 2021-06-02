#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from base64 import decodebytes
from datetime import datetime
from time import sleep

from crawler.facebook.core import FacebookCore
from crawler.utils.es import ElasticSearchUtils
from crawler.utils.selenium import SeleniumUtils


class FacebookPosts(FacebookCore):

    def __init__(self, params: dict):
        super().__init__(params=params)

    def trace_post_list(self, job: dict) -> int:
        """하나의 계정을 조회한다."""
        self.selenium.open_driver()

        url = f'''https://m.facebook.com/{job['page']}'''

        self.selenium.driver.get(url)
        self.selenium.driver.implicitly_wait(10)

        i, count = 0, 0

        for _ in range(self.params['max_page']):
            stop = self.selenium.page_down(count=10, sleep_time=3)
            self.selenium.driver.implicitly_wait(25)

            sleep(self.params['sleep'])
            i += 1

            try:
                post_list = self.parser.parse_post(url=url, html=self.selenium.driver.page_source)
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'post 목록 조회 에러',
                    'exception': str(e),
                })
                continue

            count += len(post_list)

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': 'trace post list',
                'page': f'''{i:,}/{self.params['max_page']:,}''',
                'count': f'{len(post_list):,}/{count:,}',
            })

            if post_list is None or len(post_list) == 0:
                break

            for doc in post_list:
                self.save_post(doc=doc, job=job)

            if self.es is not None:
                self.es.flush()

            # 태그 삭제
            self.delete_post()

            if stop is True:
                break

        self.selenium.close_driver()

        return count

    def save_post(self, doc: dict, job: dict) -> None:
        """추출한 정보를 저장한다."""
        doc['page'] = job['page']
        if 'page' not in doc or 'top_level_post_id' not in doc:
            return

        doc_id = doc['_id'] = f'''{doc['page'].replace('/', '-')}-{doc['top_level_post_id']}'''

        if 'meta' in job:
            doc.update(job['meta'])

        doc['reply_count'] = -1
        doc['@crawl_date'] = datetime.now(self.timezone).isoformat()

        self.es.save_document(document=doc, delete=False, index=self.config['index']['post'])

        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': '문서 저장 성공',
            'url': self.es.get_doc_url(index=self.config['index']['post'], document_id=doc_id),
            'contents': doc['contents'],
        })

        return

    def delete_post(self) -> None:
        """이전 포스트를 삭제한다."""
        script = 'document.querySelectorAll("article").forEach(function(ele) {ele.remove();})'

        try:
            self.selenium.driver.execute_script(script)
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'delete post',
                'exception': str(e),
            })
            return None

        self.selenium.driver.implicitly_wait(10)

        return

    def save_page(self, job: dict, job_id: str) -> None:
        self.es.conn.index(
            index=self.config['index']['page'],
            id=job_id,
            body={
                **job
            },
            refresh=True,
        )

        return

    def update_page(self, job_id: str, count: int) -> None:
        dt = datetime.now(self.timezone).isoformat()

        self.es.conn.update(
            index=self.config['index']['page'],
            id=job_id,
            body={
                'doc': {
                    'post_count': count,
                    '@crawl_date': dt
                }
            },
            refresh=True,
        )

        return

    def batch(self) -> None:
        self.config = self.read_config(filename=self.params['config'])

        self.es = ElasticSearchUtils(
            host=self.params['host'],
            http_auth=decodebytes(self.params['auth_encoded'].encode('utf-8')).decode('utf-8')
        )

        self.create_index(index=self.config['index']['page'])
        self.create_index(index=self.config['index']['post'])

        self.selenium = SeleniumUtils(
            login=self.params['login'],
            headless=self.params['headless'],
            user_data_path=self.params['user_data'],
        )

        for job in self.config['jobs']:
            job_id = job['page'].replace('/', '-')
            self.save_page(job=job, job_id=job_id)

            count = self.trace_post_list(job=job)

            self.update_page(count=count, job_id=job_id)

        return
