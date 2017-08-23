#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import os
import sys

import dateutil.parser
from urllib.parse import urljoin

from datetime import datetime
from dateutil.relativedelta import relativedelta

from NCNlpUtil import NCNlpUtil
from NCUrlIndexDB import NCUrlIndexDB
from NCCrawlerUtil import NCCrawlerUtil


class NCCrawler:
    """
    뉴스를 크롤링
    """
    def __init__(self):
        self.parameter = None
        self.job_info = None
        self.scheduler_db_info = None

        self.parsing_info = None

        self.url_index_db = None

        self.db_info = None
        # self.result_db = None
        # self.collection_name = None

        self.duplicated_url_count = 0

        self.page_url_cache = []

        self.crawler_util = NCCrawlerUtil()

    def get_collection_name(self, article, response_type='html'):
        """
        컬랙션 이름
        """
        collection = self.db_info['mongo']['collection']

        # date 컬럼을 날짜 형식으로 변환
        if 'date' in article and article['date'] is not None:
            date, collection = self.crawler_util.parse_date(article['date'])
            if date is None:
                del article['date']
            else:
                article['date'] = date
        elif response_type == 'json':
            if 'season' in article and isinstance(article['season'], str) is True:
                collection = article['season']

            if 'section' in article and isinstance(article['section'], str) is True:
                collection = article['section']

        if collection is None:
            collection = 'error'

        # 만약 컬렉션 이름이 None 일 경우 date를 조회해서 컬렉션 이름 생성
        if collection != 'error':
            self.set_new_collection(collection)

        return collection

    def curl_article(self, article, response_type='html'):
        """
        기사 본문을 웹에서 가져와서 디비에 저장하는 함수
        """
        str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        target_tags = None
        if 'article_page' in self.parsing_info:
            target_tags = self.parsing_info['article_page']

        # url 을 단순한 형태로 변환 및 _id 설정
        self.crawler_util.make_simple_url(article, self.parsing_info)

        # 다운로드 받은 URL이 있는지 검사
        url = self.crawler_util.get_url(article['url'])
        if self.url_index_db is not None and self.url_index_db.check_url(url) is True:
            self.duplicated_url_count += 1
            NCNlpUtil().print('{}\turl exists {:,}: {}'.format(str_now, self.duplicated_url_count, url))

            if self.db_info['mongo']['upsert'] is False:
                # const value 삽입
                if 'const_value' in self.parameter:
                    article.update(self.parameter['const_value'])

                # 섹션 정보 저장
                if 'section' in article:
                    collection = self.get_collection_name(article, response_type)

                    self.crawler_util.save_section_info(
                        document=article, mongodb_info=self.db_info['mongo'],
                        collection_name='section_{}'.format(collection))

                return True

        # 인코딩 명시
        encoding = None
        if 'encoding' in self.parsing_info:
            encoding = self.parsing_info['encoding']

        # 헤더 명시
        headers = None
        if 'headers' in self.parsing_info:
            headers = self.parsing_info['headers']

        # 기사 본문을 크롤링
        json_type = False
        if response_type == 'json':
            json_type = True

        # if 'parsing_type' in self.parsing_info and self.parsing_info['parsing_type'] == 'json':
        #     json_type = True

        soup = self.crawler_util.curl_html(
            article['url'], encoding=encoding, json=json_type,
            delay=self.parameter['delay'], min_delay=self.parameter['min_delay'], headers=headers)

        if soup is None:
            return True

        if json_type is True:
            article.update(soup)
        else:
            # 필요없는 테그 제거: 주석, 자바스크립트, 스타일 정보 등
            self.crawler_util.remove_comment(soup)
            self.crawler_util.replace_tag(soup, ['script', 'javascript', 'style'])

            # 저장할 테그 추출
            article_list = []

            # 메타 테그 저장
            self.crawler_util.get_meta_value(soup, article_list)

            # html에서 정보 추출
            article = self.crawler_util.parse_html(article, soup, target_tags, article_list)
            if article is None:
                return False

        # const value 삽입
        if 'const_value' in self.parameter:
            article.update(self.parameter['const_value'])

        # 컬랙션 이름 추출
        collection = self.get_collection_name(article, response_type)

        if json_type is not True:
            # html 내용이 없을 필드가 있는 경우
            if 'html_content' not in article:
                collection = 'error'
                article['raw_html'] = str(soup)
                NCNlpUtil().print({'INFO': 'missing html_content use entire html'})

            if 'title' not in article or 'date' not in article or article['date'] is None:
                collection = 'error'
                NCNlpUtil().print({'ERROR': 'missing column', 'article': article})

        # 기사 본문 저장
        article['curl_date'] = datetime.now()
        result = self.crawler_util.save_article(document=article, db_info=self.db_info)

        # 다운로드 받은 URL을 인덱스 디비에 저장
        if result is True and self.url_index_db is not None:
            self.url_index_db.save_url(article['url'])

        return True

    def save_section_list(self, curl_url, subject_list):
        """
        섹션 정보 저장
        """
        # url 에서 불용어 제거
        section = self.parameter['const_value']['section']

        if 'L2' not in section:
            collection = '{L1}'.format(**section)
        else:
            collection = '{L1}-{L2}'.format(**section)

        query, _ = self.crawler_util.get_query(curl_url)
        if 'page' not in query:
            query['page'] = 1

        if 'date' not in query:
            query['date'] = 'unknown'

        log = []

        # 섹션 정보만 저장
        for subject in subject_list:
            # const value 삽입
            if 'const_value' in self.parameter:
                subject.update(self.parameter['const_value'])

            # url 을 단순한 형태로 변환 및 _id 설정
            self.crawler_util.make_simple_url(subject, self.parsing_info)

            # 저장
            self.crawler_util.save_section_info(
                document=subject, mongodb_info=self.db_info['mongo'], collection_name=collection)

            url_info = subject['url']

            line = '{}\t{}\t{}\t{}\t{}'.format(collection, url_info['query']['oid'], url_info['query']['aid'],
                                               subject['title'], url_info['simple'])
            log.append(line)

        return

    def curl_article_list(self, curl_url):
        """
        패이지 목록에서 기사 목록을 가져옴
        """
        if curl_url.find('javascript') > 0:
            return

        str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        NCNlpUtil().print('{}\tcurl article list: {}'.format(str_now, curl_url))

        # page 주소 중복 체크: 오류가 있음. 마지막 페이지인 경우 중복으로 크롤링
        # if curl_url not in self.page_url_cache:
        #     self.page_url_cache.append(curl_url)
        # else:
        #     NCNlpUtil().print({'INFO': 'already curled page: {}'.format(curl_url)})
        #     return None

        # 인코딩 명시
        encoding = None
        if 'encoding' in self.parsing_info:
            encoding = self.parsing_info['encoding']

        # 1. get subject list
        soup = self.crawler_util.curl_html(curl_url, delay=self.parameter['delay'],
            min_delay=self.parameter['min_delay'], encoding=encoding)

        if soup is None:
            return None

        subject_list = []
        target_tags = self.parsing_info['subject_page']
        self.crawler_util.get_target_value(soup, target_tags, subject_list, curl_url)

        # 2. get article
        if 'article_page' in self.parsing_info:
            # 기사 본문 크롤링
            for article in subject_list:
                self.curl_article(article=article)

                if 'related_url' not in self.parameter:
                    continue

                for related_url in self.parameter['related_url']:
                    if related_url not in article:
                        continue

                    url_list = []
                    if isinstance(article[related_url], str):
                        url_list.append(article[related_url])

                    if isinstance(article[related_url], list):
                        url_list = article[related_url]

                    for extra_crawling_url in url_list:
                        for key in ['title', 'html_content']:
                            if key not in article:
                                continue

                            del article[key]

                        article['url'] = extra_crawling_url
                        self.curl_article(article=article)
        else:
            self.save_section_list(curl_url, subject_list)

        return soup

    def curl_json_article_list(self, domain_url, article_list, json_key_mapping):
        """
        개별 패이지 목록에서 기사를 가져옴
        """
        NCNlpUtil().print('curl json article list')

        # 개별 기사 URL
        for article in article_list:
            self.crawler_util.change_key(article, json_key_mapping)

            if isinstance(json_key_mapping['_article_base_url'], str) is True:
                url = json_key_mapping['_article_base_url'].format(**article)
                article['url'] = urljoin(domain_url, url)

                response_type = 'html'
                if '_response_type' in json_key_mapping and json_key_mapping['_response_type'] == 'json':
                    response_type = 'json'

                self.curl_article(article=article, response_type=response_type)
            else:
                for url_frame in json_key_mapping['_article_base_url']:
                    url = url_frame['url'].format(**article)

                    document = dict(article)
                    document['url'] = urljoin(domain_url, url)

                    if 'tag' in url_frame:
                        document['tag'] = url_frame['tag']

                    self.curl_article(article=document, response_type=url_frame['response_type'])

        return

    def curl_all_pages_json(self, page_url, page=1):
        """
        json 형태의 페이지 목록과 기사 본문을 수집
        """
        # json의 키값 매핑 정보를 가져온다.
        json_key_mapping = None
        if 'json_key_mapping' in self.parsing_info:
            json_key_mapping = self.parsing_info['json_key_mapping']

        if json_key_mapping is None:
            NCNlpUtil().print('error no json key mapping info')
            return

        # 헤더 명시
        headers = None
        if 'headers' in self.parsing_info:
            headers = self.parsing_info['headers']

        # 첫 기사 목록
        url = page_url
        if page_url.find('{page}') > 0:
            url = page_url.format(page=page)

        NCNlpUtil().print('curl all pages: {}'.format(url))
        page_soup = self.crawler_util.curl_html(
            url, delay=self.parameter['delay'], min_delay=self.parameter['min_delay'], json=True, headers=headers)
        if page_soup is None:
            return

        section_info = page_soup

        if isinstance(section_info, dict) is True:
            self.crawler_util.change_key(section_info, json_key_mapping)

            list_key = 'list'
            if 'list' in json_key_mapping:
                list_key = json_key_mapping['list']

            if list_key in section_info:
                self.curl_json_article_list(page_url, section_info[list_key], json_key_mapping)

                if 'total_pages' in section_info and page <= section_info['total_pages']:
                    page += 1
                    self.curl_all_pages_json(page_url, page=page)
            else:
                # 기사 본문 저장
                # self.crawler_util.save_article(
                #     document=section_info, result_db=self.result_db,
                #     db_name=self.parameter['result_db_name'], collection=self.collection_name)
                self.crawler_util.save_article(document=section_info, db_info=self.db_info)

        if isinstance(section_info, list) is True:
            self.curl_json_article_list(page_url, section_info, json_key_mapping)

        return

    def trace_index_tag(self, page_tag, page_url, curl_type):
        """
        페이지 목록 크롤링: 1~10 등
        """
        parsing_info = self.parsing_info['page_list']

        for a_tag in page_tag.findAll(
                parsing_info['index']['tag_name'],
                attrs=self.crawler_util.get_value(parsing_info['index'], 'attr')):
            if a_tag.has_attr('href') is False:
                NCNlpUtil().print({'ERROR': 'missing href', 'tag': str(a_tag)})
                continue

            url = urljoin(page_url, a_tag['href'])
            if url.find('javascript') > 0:
                continue

            # 인덱스 크롤링시 재귀적으로 호출
            if 'index_recursion' in self.parameter:
                self.curl_all_pages(url, curl_type)
            else:
                self.curl_article_list(url)

            # 상태 갱신
            if curl_type == 'by_id':
                self.crawler_util.update_state_by_id(
                    state='running', url=url, query_key_mapping=self.parsing_info['query_key_mapping'],
                    job_info=self.job_info, scheduler_db_info=self.scheduler_db_info)

        return

    def trace_next_tag(self, page_tag, page_url, curl_type):
        """
        페이지가 넘어가는 부분이 있는 경우 재귀적으로 호출
        """
        from bs4 import Tag

        parsing_info = self.parsing_info['page_list']

        if page_tag is None:
            return

        for next_page in page_tag.findAll(
                parsing_info['next']['tag_name'],
                attrs=self.crawler_util.get_value(parsing_info['next'], 'attr')):

            print('next_page: ', next_page)

            if next_page is None:
                continue

            if 'parent' in parsing_info['next'] and next_page.previous_element is not None:
                next_page = next_page.previous_element

            if 'next_tag' in parsing_info['next']:
                next_tag_info = parsing_info['next']['next_tag']
                next_tag = next_page.find(
                    next_tag_info['tag_name'], attrs=self.crawler_util.get_value(next_tag_info, 'attr'))

                if next_tag is not None:
                    next_page = next_tag

            # next 테그에서 url 정보 추출
            url = None
            if isinstance(next_page, Tag) is True and next_page.has_attr('href') is True:
                url = urljoin(page_url, next_page['href'])

            if url is None:
                continue

            # 상태 갱신
            if curl_type == 'by_id':
                # end 확인후 end 까지만 실행
                if 'end' in self.parameter:
                    end = int(self.parameter['end'])
                    query, _ = self.crawler_util.get_query(url)
                    self.crawler_util.change_key(query, self.parsing_info['query_key_mapping'])

                    if end < int(query['start']):
                        continue

                self.crawler_util.update_state_by_id(
                    state='running', url=url, query_key_mapping=self.parsing_info['query_key_mapping'],
                    job_info=self.job_info, scheduler_db_info=self.scheduler_db_info)

            # 다음 페이지 크롤링
            self.curl_all_pages(url, curl_type)

        return

    def curl_all_pages(self, page_url, curl_type='by_date'):
        """
        페이지 목록과 기사 본문을 수집
        """
        if page_url.find('javascript') > 0:
            return

        str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        NCNlpUtil().print('{}\tcurl all pages: {}'.format(str_now, page_url))

        page_soup = self.curl_article_list(page_url)
        if page_soup is None:
            return

        if 'page_list' not in self.parsing_info:
            NCNlpUtil().print({'ERROR': 'no page list in parsing_info'})
            return

        parsing_info = self.parsing_info['page_list']

        if 'panel' in parsing_info:
            # 페이지 목록 부분만 추출
            page_tag = page_soup.find(
                parsing_info['panel']['tag_name'],
                attrs=self.crawler_util.get_value(parsing_info['panel'], 'attr'))

            if page_tag is None:
                NCNlpUtil().print({'ERROR': 'article list panel is empty'})
                return

            # 페이지 목록 추출 1~10 등
            if 'index' in parsing_info:
                self.trace_index_tag(page_tag, page_url, curl_type)

            # 페이지가 넘어가는 부분이 있는 경우 재귀적으로 호출,
            if 'next' in parsing_info:
                self.trace_next_tag(page_tag, page_url, curl_type)

        return

    def get_date_range(self):
        """
        크롤링 날자 범위 반환
        """
        date_step = 'day'
        if 'start_month' in self.parameter and 'end_month' in self.parameter:
            date_step = 'month'

        # 시작 날짜와 마지막 날짜 가져오기
        if date_step == 'day':
            start_date = NCNlpUtil().parse_date_string(self.parameter['start_date'])
            end_date = NCNlpUtil().parse_date_string(self.parameter['end_date'], is_end_date=True)
        else:
            start_date = NCNlpUtil().parse_date_string(self.parameter['start_month'])
            end_date = NCNlpUtil().parse_date_string(self.parameter['end_month'], is_end_date=True)

        original_start_date = start_date

        # 마지막 날짜 갱신
        if date_step == 'day':
            self.parameter['start_date'] = start_date.strftime('%Y-%m-%d')
            self.parameter['end_date'] = end_date.strftime('%Y-%m-%d')

        # state 확인
        if 'state' in self.job_info['state']:
            if self.job_info['state']['state'] == 'done':
                return

            # status, date/progress 정보를 확인하여 마지막 날짜부터 이어서 크롤링 시작
            # 하루 전 기사부터 다시 시작
            if 'running' in self.job_info['state'] and self.job_info['state']['running'] != '':
                date = NCNlpUtil().parse_date_string(self.job_info['state']['running'])

                if self.job_info['group'].find('daemon') < 0:
                    if date_step == 'day':
                        date += relativedelta(days=-1)
                    else:
                        date += relativedelta(months=-1)

                if original_start_date < date < end_date:
                    start_date = date

        return start_date, end_date, original_start_date, date_step

    def curl_by_date(self):
        """
        날짜 기준으로 크롤링
        """

        # 시작 날짜와 끝날짜 쿼리
        start_date, end_date, original_start_date, date_step = self.get_date_range()

        # 기간 내의 기사 크롤링
        date = start_date
        while date <= end_date:
            # 오늘 날짜가 아닌 경우 초기화
            if date.strftime('%Y-%m-%d') != datetime.today().strftime('%Y-%m-%d'):
                self.duplicated_url_count = 0

            if 'max_skip' in self.parameter and 0 < self.parameter['max_skip'] < self.duplicated_url_count:
                break

            # 오늘 날짜 확인, date 가 오늘보다 크면 종료
            if date > datetime.today():
                break

            # 시작전 상태 변경: ready => working
            self.crawler_util.update_state(
                state='running', current_date=date, start_date=original_start_date, end_date=end_date,
                job_info=self.job_info, scheduler_db_info=self.scheduler_db_info)

            NCNlpUtil().print({'crawling date': date})

            # 특정 날자의 기사를 수집
            url_list = self.parameter['url_frame']
            if isinstance(url_list, str) is True:
                url_list = [{'url': url_list}]

            # url을 만든다.
            year_flag = False
            for url_info in url_list:
                page_url = url_info['url']

                # const_value 속성 복사
                if 'const_value' in url_info:
                    self.parameter['const_value'] = url_info['const_value']

                if date_step == 'day':
                    if page_url.find('{date}') > 0:
                        page_url = page_url.format(date=date.strftime('%Y%m%d'))
                    elif page_url.find('{date2}') > 0:
                        page_url = page_url.format(date2=date.strftime('%Y-%m-%d'))
                    elif page_url.find('{year}') > 0:
                        page_url = page_url.format(year=date.strftime('%Y'))
                else:
                    to_date = date + relativedelta(months=1) + relativedelta(days=-1)
                    page_url = page_url.format(start_date=date.strftime('%Y%m%d'), end_date=to_date.strftime('%Y%m%d'))

                if 'parsing_type' in self.parsing_info and self.parsing_info['parsing_type'] == 'json':
                    self.curl_all_pages_json(page_url, 1)
                else:
                    self.curl_all_pages(page_url)

                # const_value 속성 삭제
                if 'const_value' in url_info:
                    del self.parameter['const_value']

                if page_url.find('{year}') > 0:
                    year_flag = True

            if year_flag is True:
                date = end_date
                break

            # 날짜를 증가 시킨다.
            if date_step == 'day':
                date += relativedelta(days=1)
            else:
                date += relativedelta(months=1)

        # 현재 진행 상태를 갱신한다.
        if date < end_date:
            if date_step == 'day':
                date += relativedelta(days=-1)
            else:
                date += relativedelta(months=-1)

            if self.job_info['group'].find('daemon') < 0:
                self.crawler_util.update_state(
                    state='ready', current_date=date, start_date=original_start_date, end_date=end_date,
                    job_info=self.job_info, scheduler_db_info=self.scheduler_db_info)
        else:
            self.crawler_util.update_state(
                state='done', current_date=None, start_date=None, end_date=None,
                job_info=self.job_info, scheduler_db_info=self.scheduler_db_info)

        return

    def set_new_collection(self, new_collection_name):
        """
        컬렉션 이름이 변경되었을 경우, 인덱스를 업데이트 한다.
        """
        if self.db_info['mongo'] is None or self.db_info['mongo']['collection'] != new_collection_name:
            print('make new collection index', flush=True)
            self.db_info['mongo']['collection'] = new_collection_name

            # 만약 collection 이 변경되었다면, 인덱스 재성성
            self.make_url_index_db()

        return

    def curl_by_page_id(self):
        """
        아이디 기준으로 크롤링
        """
        print('curl by page id', flush=True)

        year = None
        start = None

        if 'year' in self.parameter:
            year = self.parameter['year']

        if 'start' in self.parameter:
            start = self.parameter['start']

        # 데몬 모드일 경우 항상 start에서 시작
        if self.job_info['group'].find('daemon') < 0:
            # 만약 진행 상태에 년도 정보가 있으면 가져와서 그 년도 부터 다시 크롤링 시작
            if 'year' in self.job_info['state'] and self.job_info['state']['year'] != '':
                year = self.job_info['state']['year']

                # 신문 고유 번호 기반 크롤링시 저장 디비의 컬렉션을 맞게 변경
                self.set_new_collection(year)

            # 진행 상태에서 start 가 있으면 그 번호부터 다시 크롤링
            if 'start' in self.job_info['state'] and self.job_info['state']['start'] != '':
                start = self.job_info['state']['start']

        # url 주소 생성
        NCNlpUtil().print({'year': year, 'start': start})

        # 쿼리 매핑 정보 추출
        query_key_mapping = None
        if 'query_key_mapping' in self.parsing_info:
            query_key_mapping = self.parsing_info['query_key_mapping']

        if 'page_list' in self.parsing_info:
            # 페이지 목록이 있을 경우

            # end까지 반복 실행
            start = int(start)
            end = start + 1

            if 'end' in self.parameter:
                end = int(self.parameter['end'])

            step = 1
            if 'step' in self.parameter:
                step = int(self.parameter['step'])

            for i in range(start, end, step):
                if 'max_skip' in self.parameter and 0 < self.parameter['max_skip'] < self.duplicated_url_count:
                    break

                url_list = self.parameter['url_frame']
                if isinstance(url_list, str) is True:
                    url_list = [{'url': url_list}]

                # url을 만든다.
                for url_info in url_list:
                    query = {'year': year, 'start': i}

                    page_url = url_info['url'].format(**query)

                    # const_value 속성 복사
                    if 'const_value' in url_info:
                        self.parameter['const_value'] = url_info['const_value']

                    # 본문 수집
                    self.curl_all_pages(page_url, curl_type='by_id')

                    # 상태 갱신
                    self.crawler_util.update_state_by_id(
                        state='running', url=page_url, query_key_mapping=query_key_mapping,
                        job_info=self.job_info, scheduler_db_info=self.scheduler_db_info)
        else:
            # elif 'article_page' in self.parsing_info:
            # 페이지 목록이 없을 경우 본문만 저장
            start = int(start)

            end = start + 100000
            if 'end' in self.parameter:
                end = int(self.parameter['end']) + 1

            for i in range(start, end):
                if 'max_skip' in self.parameter and 0 < self.parameter['max_skip'] < self.duplicated_url_count:
                    break

                url_list = self.parameter['url_frame']
                if isinstance(url_list, str) is True:
                    url_list = [{'url': url_list}]

                # url을 만든다.
                for url_info in url_list:
                    # const_value 속성 복사
                    if 'const_value' in url_info:
                        self.parameter['const_value'] = url_info['const_value']

                    page_url = url_info['url']

                    # 본문 수집
                    article = {'url': page_url.format(start=i)}

                    if 'parsing_type' in self.parsing_info and self.parsing_info['parsing_type'] == 'json':
                        self.curl_all_pages_json(article['url'], 1)
                    else:
                        self.curl_article(article=article)

                    # 상태 갱신
                    self.crawler_util.update_state_by_id(
                        state='running', url=article['url'], query_key_mapping=query_key_mapping,
                        job_info=self.job_info, scheduler_db_info=self.scheduler_db_info)

        return

    def update_article_by_date(self):
        """
        기사 본문 재 크롤링
        """
        start_date, end_date, original_start_date, date_step = self.get_date_range()

        curl_date = None
        if 'curl_date' in self.parameter:
            curl_date = NCNlpUtil().parse_date_string(self.parameter['curl_date'])

        mongodb_info = self.db_info['mongo']

        if 'collection' not in mongodb_info or mongodb_info['collection'] is None:
            print('ERROR no collection in db info', flush=True)
            return

        # 숫자일 경우 문자로 변경
        if isinstance(mongodb_info['collection'], int) is True:
            mongodb_info['collection'] = str(mongodb_info['collection'])

        if 'port' not in mongodb_info:
            mongodb_info['port'] = 27017

        # 디비 연결
        connect, mongodb = NCCrawlerUtil().open_db(
            host=mongodb_info['host'], db_name=mongodb_info['name'], port=mongodb_info['port'])

        collection = mongodb.get_collection(mongodb_info['collection'])

        # 1차 날짜 기준 필터링
        print('date range: {} ~ {}'.format(start_date, end_date), flush=True)
        cursor = collection.find({
            'date': {
                '$gte': start_date,
                '$lte': end_date
            }
        })[:]

        document_list = []
        for document in cursor:
            date = document['date']
            if end_date < date < start_date:
                continue

            if curl_date is not None and 'curl_date' in document and curl_date < document['curl_date']:
                continue

            document_list.append(document)

        cursor.close()

        connect.close()

        # 크롤링 시작
        count = 0
        total = len(document_list)
        print('{:,}'.format(total), flush=True)
        for document in document_list:
            self.curl_article(article=document)

            str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            paper = ''
            if 'paper' in document:
                paper = document['paper']

            print('{}\t{:,}/{:,}\t{}'.format(str_now, count, total, paper), flush=True)
            count += 1

        return

    def make_url_index_db(self):
        """
        크롤링 완료된 url 목록을 인덱스 디비로 생성
        """
        NCNlpUtil().print('update index db')

        self.url_index_db = NCUrlIndexDB()
        self.url_index_db.open_db('/tmp/{}.sqlite3'.format(self.job_info['_id']), delete=True)

        self.url_index_db.update_url_list(mongodb_info=self.db_info['mongo'])

        return

    def _init_variable(self, scheduler_db_info, job_info):
        """
        변수 및 환경 설정 초기화
        """
        self.duplicated_url_count = 0

        self.job_info = job_info
        self.scheduler_db_info = scheduler_db_info

        self.crawler_util.job_info = self.job_info

        NCNlpUtil().print({'job_info': self.job_info})

        self.parameter = job_info['parameter']
        if 'delay' not in self.parameter:
            self.parameter['delay'] = 6

        if 'min_delay' not in self.parameter:
            self.parameter['min_delay'] = 3

        # 디비 연결
        self.db_info = self.parameter['db_info']

        # 섹션/파싱 정보 가져오기
        if self.parsing_info is None:
            section_info, parsing_info = self.crawler_util.get_parsing_information(scheduler_db_info)

            if 'parsing_info' in self.parameter:
                self.parsing_info = parsing_info[self.parameter['parsing_info']]

        NCNlpUtil().print({
            'parameter': self.parameter,
            'parsing_info': self.parsing_info
        })

        # 인덱스 디비 생성
        if 'update_article' not in self.parameter:
            self.make_url_index_db()

        return

    def run(self, scheduler_db_info, job_info):
        """
        NCCrawler 실행
        """
        self._init_variable(scheduler_db_info, job_info)

        # 크롤링 방식에 따른 실행: 날짜 기준 크롤링 or 기사 고유 아이디 기준 크롤링
        if 'start_date' in self.parameter or 'start_month' in self.parameter:
            if 'update_article' in self.parameter:
                self.update_article_by_date()
            else:
                self.curl_by_date()
        else:
            # start in self.parameter
            self.curl_by_page_id()

        return

    def debug(self, scheduler_db_info, job_info, args):
        """
        디버깅, 하나의 URL을 입력 받아 실행
        """
        self._init_variable(scheduler_db_info, job_info)

        if args.article_list is True:
            self.curl_all_pages(args.url)

        if args.article is True:
            article = {'url': args.url}
            self.curl_article(article=article)

        return

    def parse_error(self, scheduler_db_info, job_info, args):
        """
        에러 테이블에 있는 raw_html 을 다시 파싱
        """
        # from bs4 import BeautifulSoup
        # from pymongo import errors
        #
        # self._init_variable(scheduler_db_info, job_info)
        #
        # connect, self.result_db = self.crawler_util.open_db(
        #     db_name=self.parameter['result_db_name'],
        #     host=self.parameter['result_db_host'],
        #     port=self.parameter['result_db_port'])
        #
        # if 'article_page' in self.parsing_info:
        #     target_tags = self.parsing_info['article_page']
        #
        # cursor = self.result_db[args.db_collection].find({})
        #
        # cursor = cursor[:]
        # for document in cursor:
        #     if 'raw_html' not in document:
        #         print('ERROR no raw_html value', document['_id'])
        #
        #         if 'url' in document:
        #             self.curl_article(document)
        #             pass
        #
        #         continue
        #
        #     soup = BeautifulSoup(document['raw_html'], 'lxml')
        #
        #     # 저장할 테그 추출
        #     article_list = []
        #
        #     # html에서 정보 추출
        #     document = self.crawler_util.parse_html(document, soup, target_tags, article_list)
        #
        #     if 'html_content' not in document or 'date' not in document or 'title' not in document:
        #         print('ERROR', document['_id'])
        #         continue
        #
        #     del document['raw_html']
        #
        #     collection = document['date'].strftime('%Y')
        #
        #     try:
        #         print(
        #             self.parameter['result_db_host'],
        #             self.parameter['result_db_name'],
        #             args.db_collection,
        #             '->',
        #             self.parameter['result_db_host'],
        #             self.parameter['result_db_name'],
        #             collection,
        #             ' : ',
        #             document['_id']
        #         )
        #
        #         # self.result_db[collection].insert_one(document)
        #         self.result_db[collection].replace_one({'_id': document['_id']}, document, upsert=True)
        #         self.result_db[args.db_collection].remove({'_id': document['_id']})
        #     except errors.DuplicateKeyError:
        #         print(
        #             'remove',
        #             self.parameter['result_db_host'],
        #             self.parameter['result_db_name'],
        #             args.db_collection,
        #             document['_id']
        #         )
        #         self.result_db[args.db_collection].remove({'_id': document['_id']})
        #     except Exception:
        #         print('ERROR', self.parameter['result_db_host'], self.parameter['result_db_name'])
        #
        # cursor.close()
        #
        # if connect is not None:
        #     connect.close()

        return

    @staticmethod
    def parse_argument():
        """"
        옵션 설정
        """
        import argparse

        arg_parser = argparse.ArgumentParser(description='crawling web news articles')

        arg_parser.add_argument('-document_id', help='document id', default=None)

        arg_parser.add_argument('-scheduler_db_host', help='db server host name', default='gollum01')
        arg_parser.add_argument('-scheduler_db_port', help='db server port', default=27017)
        arg_parser.add_argument('-scheduler_db_name', help='job db name', default='crawler')
        arg_parser.add_argument('-scheduler_db_collection', help='job collection name', default='schedule')

        arg_parser.add_argument('-url', help='url', default=None)
        arg_parser.add_argument('-article_list', help='', action='store_true', default=False)
        arg_parser.add_argument('-article', help='', action='store_true', default=False)

        # 에러 테이블에 있는 기사를 재파싱
        arg_parser.add_argument('-parse_error', help='', action='store_true', default=False)

        arg_parser.add_argument('-db_host', help='db server host name', default='gollum01')
        arg_parser.add_argument('-db_port', help='db server port', default=27017)
        arg_parser.add_argument('-db_name', help='job db name', default='daum_baseball')
        arg_parser.add_argument('-db_collection', help='job collection name', default='error')

        return arg_parser.parse_args()

# end of NCCrawler


if __name__ == '__main__':
    crawler = NCCrawler()
    args = crawler.parse_argument()

    from NCDockerClusterScheduler import NCDockerClusterScheduler

    nc_curl = NCDockerClusterScheduler()
    scheduler_db_info = {
        'document_id': args.document_id,
        'scheduler_db_host': args.scheduler_db_host,
        'scheduler_db_port': args.scheduler_db_port,
        'scheduler_db_name': args.scheduler_db_name,
        'scheduler_db_collection': args.scheduler_db_collection
    }

    job_info = nc_curl.get_job_info(scheduler_db_info)

    if args.parse_error is True:
        crawler.parse_error(scheduler_db_info, job_info, args)
    else:
        crawler.debug(scheduler_db_info, job_info, args)

# end of __main__
