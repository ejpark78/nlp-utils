#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

from datetime import datetime
from urllib.parse import urljoin

from dateutil.relativedelta import relativedelta

from utils import Utils
from url_index_db import UrlIndexDB


class Crawler(Utils):
    """
    크롤러
    """

    def __init__(self):
        """
        생성자
        """
        super().__init__()

        self.parameter = None
        self.scheduler_db_info = None

        self.parsing_info = None

        self.url_index_db = None

        self.db_info = None

        self.duplicated_url_count = 0

        self.page_url_cache = []

    def get_collection_name(self, article, response_type):
        """
        컬랙션 이름 반환

        :param article:
            기사 본문

        :param response_type:
            입력된 기사의 타입: html, json

        :return:
            컬랙션 이름
        """
        collection = 'error'
        if 'mongo' not in self.db_info:
            return 'unknown'

        if 'collection' in self.db_info['mongo']:
            collection = self.db_info['mongo']['collection']

        # date 컬럼을 날짜 형식으로 변환
        if 'date' in article and article['date'] is not None:
            date, collection = self.get_date_collection_name(article['date'])
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

    def is_url_exists(self, url, article, response_type):
        """
        url 중복 체크, 섹션 정보 저장

        :return:
            True/False
        """
        if self.url_index_db is None:
            return False

        if self.url_index_db.check_url(url) is False:
            return False

        self.duplicated_url_count += 1
        print('url exists: ', '{:,}'.format(self.duplicated_url_count), url, flush=True)

        if 'mongo' not in self.db_info:
            return False

        if 'update' in self.db_info['mongo'] and self.db_info['mongo']['update'] is False:
            # const value 삽입
            if 'const_value' in self.parameter:
                article.update(self.parameter['const_value'])

            # 섹션 정보 저장
            if 'section' in article:
                collection = self.get_collection_name(article, response_type)

                self.save_section_info(document=article, mongodb_info=self.db_info['mongo'],
                                       collection_name='section_{}'.format(collection))

            return True

        return False

    def curl_article(self, article, response_type='html'):
        """
        기사 본문을 웹에서 가져와서 디비에 저장하는 함수

        :param article:
            기사 본문

        :param response_type:
            기사 본문 형식

        :return:
            True/False
        """
        target_tags = None
        if 'article_page' in self.parsing_info:
            target_tags = self.parsing_info['article_page']

        # url 을 단순한 형태로 변환 및 _id 설정
        self.make_simple_url(article, self.parsing_info)

        # 다운로드 받은 URL이 있는지 검사
        if 'url' not in article:
            print('ERROR: 다운 받을 url 주소가 없음.', article, flush=True)
            return

        # url 중복 체크, 섹션 정보 저장
        url = self.get_url(article['url'])
        if self.debug_mode is False and self.is_url_exists(url, article, response_type):
            return

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

        soup = self.curl_html(article['url'], encoding=encoding,
                              json_type=json_type, delay=self.parameter['delay'], headers=headers)

        if soup is None:
            return True

        if json_type is True:
            article.update(soup)
        else:
            # 필요없는 테그 제거: 주석, 자바스크립트, 스타일 정보 등
            self.remove_comment(soup)
            self.replace_tag(soup, ['script', 'javascript', 'style'])

            # 저장할 테그 추출
            article_list = []

            # 메타 테그 저장
            self.get_meta_value(soup, article_list)

            # html 에서 정보 추출
            article = self.parse_html(article, soup, target_tags, article_list)
            if article is None:
                return False

        # const value 삽입
        if 'const_value' in self.parameter:
            article.update(self.parameter['const_value'])

        # 컬랙션 이름 추출
        self.get_collection_name(article, response_type)

        if json_type is not True:
            # html 내용이 없을 필드가 있는 경우
            if 'html_content' not in article:
                article['raw_html'] = str(soup)
                print('INFO: missing html_content use entire html', flush=True)

            if 'title' not in article or 'date' not in article or article['date'] is None:
                print('ERROR missing column', article, flush=True)

        # 기사 본문 저장
        article['curl_date'] = datetime.now()
        result = self.save_article(document=article, db_info=self.db_info)

        # 다운로드 받은 URL 을 인덱스 디비에 저장
        if result is True and self.url_index_db is not None:
            self.url_index_db.save_url(article['url'])

        return True

    def save_section_list(self, curl_url, subject_list):
        """
        섹션 정보 저장

        :param curl_url:
            크롤링 웹 주소

        :param subject_list:

        :return:
            True/False
        """
        # url 에서 불용어 제거
        section = self.parameter['const_value']['section']

        if 'L2' not in section:
            collection = '{l1}'.format(**section)
        else:
            collection = '{l1}-{l2}'.format(**section)

        query, _, _ = self.get_query(curl_url)
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
            self.make_simple_url(subject, self.parsing_info)

            # 저장
            self.save_section_info(document=subject, mongodb_info=self.db_info['mongo'],
                                   collection_name=collection)

            url_info = subject['url']

            line = '{}\t{}\t{}\t{}\t{}'.format(collection, url_info['query']['oid'], url_info['query']['aid'],
                                               subject['title'], url_info['simple'])
            log.append(line)

        return True

    def curl_article_list(self, curl_url):
        """
        패이지 목록에서 기사 목록을 가져옴

        :param curl_url:
            웹 주소

        :return:
        """
        if curl_url.find('javascript') > 0:
            return

        print('curl article list: ', curl_url, flush=True)

        # page 주소 중복 체크: 오류가 있음. 마지막 페이지인 경우 중복으로 크롤링
        # if curl_url not in self.page_url_cache:
        #     self.page_url_cache.append(curl_url)
        # else:
        #     print({'INFO': 'already curled page: {}'.format(curl_url)})
        #     return None

        # 인코딩 명시
        encoding = None
        if 'encoding' in self.parsing_info:
            encoding = self.parsing_info['encoding']

        # 1. get subject list
        soup = self.curl_html(curl_url, delay=self.parameter['delay'], encoding=encoding)

        if soup is None:
            return None

        subject_list = []
        target_tags = self.parsing_info['subject_page']
        self.get_target_value(soup, target_tags, subject_list, curl_url)

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

        :param domain_url:
        :param article_list:
        :param json_key_mapping:
        :return:
        """
        print('curl json article list', flush=True)

        # 개별 기사 URL
        for article in article_list:
            self.change_key(article, json_key_mapping)

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

                    # 주석 제외
                    if url[0] == '#':
                        continue

                    document = dict(article)
                    document['url'] = urljoin(domain_url, url)

                    if 'tag' in url_frame:
                        document['tag'] = url_frame['tag']

                    self.curl_article(article=document, response_type=url_frame['response_type'])

        return

    def curl_all_pages_json(self, page_url, page=1):
        """
        json 형태의 페이지 목록과 기사 본문을 수집

        :param page_url:
        :param page:
        :return:
        """
        # json의 키값 매핑 정보를 가져온다.
        json_key_mapping = None
        if 'json_key_mapping' in self.parsing_info:
            json_key_mapping = self.parsing_info['json_key_mapping']

        if json_key_mapping is None:
            print('error no json key mapping info', flush=True)
            return

        # 헤더 명시
        headers = None
        if 'headers' in self.parsing_info:
            headers = self.parsing_info['headers']

        # 첫 기사 목록
        url = page_url
        if page_url.find('{page}') > 0:
            url = page_url.format(page=page)

        print('curl all pages: ', url, flush=True)
        page_soup = self.curl_html(url, delay=self.parameter['delay'], json_type=True, headers=headers)
        if page_soup is None:
            return

        section_info = page_soup

        if isinstance(section_info, dict) is True:
            self.change_key(section_info, json_key_mapping)

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
                # self.save_article(
                #     document=section_info, result_db=self.result_db,
                #     db_name=self.parameter['result_db_name'], collection=self.collection_name)
                self.save_article(document=section_info, db_info=self.db_info)

        if isinstance(section_info, list) is True:
            self.curl_json_article_list(page_url, section_info, json_key_mapping)

        return

    def trace_index_tag(self, page_tag, page_url, curl_type):
        """
        페이지 목록 크롤링: 1~10 등
        """
        parsing_info = self.parsing_info['page_list']

        for a_tag in page_tag.findAll(parsing_info['index']['tag_name'],
                                      attrs=self.get_value(parsing_info['index'], 'attr')):
            if a_tag.has_attr('href') is False:
                print('ERROR: missing href', str(a_tag), flush=True)
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
            if curl_type == 'by_id' and 'query_key_mapping' in self.parsing_info:
                self.update_state_by_id(str_state='running', url=url,
                                        query_key_mapping=self.parsing_info['query_key_mapping'],
                                        job_info=self.job_info, scheduler_db_info=self.scheduler_db_info)

        return

    def trace_next_tag(self, page_tag, page_url, curl_type):
        """
        페이지가 넘어가는 부분이 있는 경우 재귀적으로 호출

        :param page_tag:
        :param page_url:
        :param curl_type:
        :return:
        """
        from bs4 import Tag

        parsing_info = self.parsing_info['page_list']

        if page_tag is None:
            return

        for next_page in page_tag.findAll(parsing_info['next']['tag_name'],
                                          attrs=self.get_value(parsing_info['next'], 'attr')):

            print('next_page: ', next_page, flush=True)

            if next_page is None:
                continue

            if 'parent' in parsing_info['next'] and next_page.previous_element is not None:
                next_page = next_page.previous_element

            if 'next_tag' in parsing_info['next']:
                next_tag_info = parsing_info['next']['next_tag']
                next_tag = next_page.find(next_tag_info['tag_name'],
                                          attrs=self.get_value(next_tag_info, 'attr'))

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
                    query, _, _ = self.get_query(url)

                    if 'query_key_mapping' in self.parsing_info:
                        self.change_key(query, self.parsing_info['query_key_mapping'])

                    if end < int(query['start']):
                        continue

                if 'query_key_mapping' in self.parsing_info:
                    self.update_state_by_id(str_state='running', url=url, job_info=self.job_info,
                                            scheduler_db_info=self.scheduler_db_info,
                                            query_key_mapping=self.parsing_info['query_key_mapping'])

            # 다음 페이지 크롤링
            self.curl_all_pages(url, curl_type)

        return

    def curl_all_pages(self, page_url, curl_type='by_date'):
        """
        페이지 목록과 기사 본문을 수집

        :param page_url:
        :param curl_type:
        :return:
        """
        if page_url.find('javascript') > 0:
            return

        print('curl all pages: ', page_url, flush=True)

        page_soup = self.curl_article_list(page_url)
        if page_soup is None:
            return

        if 'page_list' not in self.parsing_info:
            print('ERROR no page list in parsing_info', flush=True)
            return

        parsing_info = self.parsing_info['page_list']

        if 'panel' in parsing_info:
            # 페이지 목록 부분만 추출
            page_tag = page_soup.find(
                parsing_info['panel']['tag_name'],
                attrs=self.get_value(parsing_info['panel'], 'attr'))

            if page_tag is None:
                print('ERROR article list panel is empty', flush=True)
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

        :return:
        """
        date_step = 'day'
        if 'start_month' in self.parameter and 'end_month' in self.parameter:
            date_step = 'month'

        # 시작 날짜와 마지막 날짜 가져오기
        if date_step == 'day':
            start_date = self.parse_date_string(self.parameter['start_date'])
            end_date = self.parse_date_string(self.parameter['end_date'], is_end_date=True)
        else:
            start_date = self.parse_date_string(self.parameter['start_month'])
            end_date = self.parse_date_string(self.parameter['end_month'], is_end_date=True)

        original_start_date = start_date

        # 마지막 날짜 갱신
        if date_step == 'day':
            self.parameter['start_date'] = start_date.strftime('%Y-%m-%d')
            self.parameter['end_date'] = end_date.strftime('%Y-%m-%d')

        # state 확인
        state = self.job_info['state']
        if 'state' in state:
            if state['state'] == 'done':
                return

            # status, date/progress 정보를 확인하여 마지막 날짜부터 이어서 크롤링 시작
            # 하루 전 기사부터 다시 시작
            if 'running' in state and state['running'] != '':
                date = self.parse_date_string(state['running'])

                if self.job_info['schedule']['mode'] != 'daemon':
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

        :return:
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
            self.update_state(str_state='running', current_date=date, start_date=original_start_date,
                              end_date=end_date, job_info=self.job_info, scheduler_db_info=self.scheduler_db_info)

            print('crawling date: ', date, flush=True)

            # 특정 날자의 기사를 수집
            url_list = self.parameter['url_frame']
            if isinstance(url_list, str) is True:
                url_list = [{'url': url_list}]

            # url 을 만든다.
            year_flag = False
            for url_info in url_list:
                page_url = url_info['url']

                # 주석 제외
                if page_url[0] == '#':
                    continue

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

            if self.job_info['schedule']['group'].find('daemon') < 0:
                self.update_state(
                    str_state='ready', current_date=date, start_date=original_start_date, end_date=end_date,
                    job_info=self.job_info, scheduler_db_info=self.scheduler_db_info)
        else:
            self.update_state(
                str_state='done', current_date=None, start_date=None, end_date=None,
                job_info=self.job_info, scheduler_db_info=self.scheduler_db_info)

        return

    def set_new_collection(self, new_collection_name):
        """
        컬렉션 이름이 변경되었을 경우, 인덱스를 업데이트 한다.

        :param new_collection_name:
        :return:
        """
        if self.db_info['mongo'] is None \
                or 'collection' not in self.db_info['mongo'] \
                or self.db_info['mongo']['collection'] != new_collection_name:
            print('make new collection index', flush=True)
            self.db_info['mongo']['collection'] = new_collection_name

            # 만약 collection 이 변경되었다면, 인덱스 재성성
            self.make_url_index_db()

        return

    @staticmethod
    def _get_page_range(params, start):
        """
        파라메터에서 start, end, step 정보 반환

        :param params:

        :param start:
            default start

        :return:
        """

        end = start + 1
        if 'end' in params:
            end = int(params['end']) + 1

        step = 1
        if 'step' in params:
            step = int(params['step'])

        return start, end, step

    def curl_by_page_id(self):
        """
        아이디 기준으로 크롤링

        :return:
        """
        print('curl by page id', flush=True)

        year = None
        start = None

        if 'year' in self.parameter:
            year = self.parameter['year']

        if 'start' in self.parameter:
            start = self.parameter['start']

        # 데몬 모드일 경우 항상 start 에서 시작
        if self.job_info['schedule']['group'].find('daemon') < 0:
            state = self.job_info['state']

            # 만약 진행 상태에 년도 정보가 있으면 가져와서 그 년도 부터 다시 크롤링 시작
            if 'year' in state and state['year'] != '':
                year = state['year']

                # 신문 고유 번호 기반 크롤링시 저장 디비의 컬렉션을 맞게 변경
                self.set_new_collection(year)

            # 진행 상태에서 start 가 있으면 그 번호부터 다시 크롤링
            if 'start' in state and state['start'] != '':
                start = state['start']

        # url 주소 생성
        start = int(start)
        print({'year': year, 'start': start}, flush=True)

        # 쿼리 매핑 정보 추출
        query_key_mapping = None
        if 'query_key_mapping' in self.parsing_info:
            query_key_mapping = self.parsing_info['query_key_mapping']

        # 시작전 상태 변경: ready => working
        self.update_state_by_id(str_state='running', url='', job_info=self.job_info,
                                scheduler_db_info=self.scheduler_db_info,
                                query_key_mapping=query_key_mapping)

        if 'page_list' in self.parsing_info:
            # 페이지 목록이 있을 경우

            # end 까지 반복 실행
            start, end, step = self._get_page_range(self.parameter, start=start)

            url_list = self.parameter['url_frame']
            if isinstance(url_list, str) is True:
                url_list = [{'url': url_list}]

            # url 을 만든다.
            for url_info in url_list:
                # 주석 제외
                if url_info['url'][0] == '#':
                    continue

                # end 까지 반복 실행
                start, end, step = self._get_page_range(url_info, start=start)

                for i in range(start, end, step):
                    query = {'year': year, 'start': i}

                    page_url = url_info['url'].format(**query)

                    if 'max_skip' in self.parameter and 0 < self.parameter['max_skip'] < self.duplicated_url_count:
                        break

                    # const_value 속성 복사
                    if 'const_value' in url_info:
                        self.parameter['const_value'] = url_info['const_value']

                    # 본문 수집
                    self.curl_all_pages(page_url, curl_type='by_id')

                    # 상태 갱신
                    self.update_state_by_id(str_state='running', url=page_url, job_info=self.job_info,
                                            scheduler_db_info=self.scheduler_db_info,
                                            query_key_mapping=query_key_mapping)
        else:
            # 페이지 목록이 없을 경우 본문만 저장
            end = start + 100000
            if 'end' in self.parameter:
                end = int(self.parameter['end']) + 1

            for i in range(start, end):
                if 'max_skip' in self.parameter and 0 < self.parameter['max_skip'] < self.duplicated_url_count:
                    break

                url_list = self.parameter['url_frame']
                if isinstance(url_list, str) is True:
                    url_list = [{'url': url_list}]

                # url 을 만든다.
                for url_info in url_list:
                    # const_value 속성 복사
                    if 'const_value' in url_info:
                        self.parameter['const_value'] = url_info['const_value']

                    page_url = url_info['url']

                    # 주석 제외
                    if page_url[0] == '#':
                        continue

                    # 본문 수집
                    article = {'url': page_url.format(start=i)}

                    if 'parsing_type' in self.parsing_info and self.parsing_info['parsing_type'] == 'json':
                        self.curl_all_pages_json(article['url'], 1)
                    else:
                        self.curl_article(article=article)

                    # 상태 갱신
                    self.update_state_by_id(str_state='running', url=article['url'], job_info=self.job_info,
                                            scheduler_db_info=self.scheduler_db_info,
                                            query_key_mapping=query_key_mapping)

        return

    def update_article_by_date(self):
        """
        기사 본문 재 크롤링

        :return:
        """
        start_date, end_date, original_start_date, date_step = self.get_date_range()

        curl_date = None
        if 'curl_date' in self.parameter:
            curl_date = self.parse_date_string(self.parameter['curl_date'])

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
        connect, mongodb = self.open_db(host=mongodb_info['host'],
                                        db_name=mongodb_info['name'], port=mongodb_info['port'])

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

            paper = ''
            if 'paper' in document:
                paper = document['paper']

            print('{:,}/{:,}\t{}'.format(count, total, paper), flush=True)
            count += 1

        return

    def make_url_index_db(self):
        """
        크롤링 완료된 url 목록을 인덱스 디비로 생성

        :return:
            None
        """
        print('update index db', flush=True)

        self.url_index_db = UrlIndexDB()

        file_name = '/tmp/{}.sqlite3'.format(self.job_info['_id'])
        self.url_index_db.open_db(file_name, delete=True)

        if 'mongo' in self.db_info:
            self.url_index_db.update_url_list(mongodb_info=self.db_info['mongo'])

        return

    def _init_variable(self, scheduler_db_info, job_info):
        """
        변수 및 환경 설정 초기화

        :param scheduler_db_info:
            스케쥴러 디비 정보

        :param job_info:
            스케쥴 정보

        :return:
            None
        """
        self.duplicated_url_count = 0

        self.job_info = job_info
        self.scheduler_db_info = scheduler_db_info

        debug = os.getenv('DEBUG', 'False')
        if debug == 'true' or debug == 'True' or debug == '1':
            self.debug_mode = True

        print('job_info: ', self.job_info, flush=True)

        self.parameter = job_info['parameter']
        if 'delay' not in self.parameter:
            self.parameter['delay'] = '6~9'

        # 디비 연결
        self.db_info = self.parameter['db_info']

        # 파싱 정보 가져오기
        if self.parsing_info is None and 'parsing_info' in self.parameter:
            self.parsing_info = self.get_parsing_information(scheduler_db_info, self.parameter['parsing_info'])

        print('parameter: ', self.parameter, 'parsing_info: ', self.parsing_info, flush=True)

        # 인덱스 디비 생성
        if 'update_article' not in self.parameter:
            self.make_url_index_db()

        return

    def run(self, scheduler_db_info, job_info):
        """
        크롤링 시작

        :param scheduler_db_info:
            스케쥴러 디비 정보

        :param job_info:
            스케쥴 정보

        :return:
            None
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

        :param scheduler_db_info:
            스케쥴러 디비 정보

        :param job_info:
            스케쥴 정보

        :param args:

        :return:
            None
        """
        self._init_variable(scheduler_db_info, job_info)

        if args.article_list is True:
            self.curl_all_pages(args.url)

        if args.article is True:
            article = {'url': args.url}
            self.curl_article(article=article)

        return


if __name__ == '__main__':
    pass
