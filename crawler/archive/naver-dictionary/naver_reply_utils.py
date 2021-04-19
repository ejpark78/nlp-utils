#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import sys

import pandas as pd
import urllib3
from tqdm.autonotebook import tqdm

from crawler.utils.elasticsearch_utils import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MESSAGE = 25

logging_opt = {
    'level': MESSAGE,
    'format': '%(message)s',
    'handlers': [logging.StreamHandler(sys.stderr)],
}

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(**logging_opt)

logger = logging.getLogger()


class NaverNewsReplyUtils(object):
    """뉴스 댓글 병합 유틸"""

    def __init__(self):
        """생성자"""
        self.index = {
            'news': [
                'crawler-naver-sports-2018',
                'crawler-naver-sports-2019',
            ],
            'reply': [
                'crawler-naver-sports-reply-2018',
                'crawler-naver-sports-reply-2019',
            ],
        }

        self.elastic = None

    def dump_data(self, host, auth, index_list, doc_type):
        """뉴스 본문이나 댓글을 덤프 받는다."""
        self.elastic = ElasticSearchUtils(host=host, http_auth=auth)

        if doc_type == 'news':
            query = {
                "_source": [
                    "aid", "oid", "section", "category", "title", "date", "datetime", "url", "content"
                ]
            }
        else:
            query = {
                '_source': [
                    'aid', 'oid', 'sectionName', 'officeName', 'title',
                    'reply_list.contents', 'reply_list.userName', 'reply_list.regTime', 'reply_list.maskedUserId'
                ]
            }

        result = []
        for index in index_list:
            self.elastic.export(
                index=index,
                query=query,
                result=result,
            )

        return result

    @staticmethod
    def dump_reply(index):
        """뉴스 본문이나 댓글을 덤프 받는다."""
        elastic = ElasticSearchUtils(
            host='https://corpus.ncsoft.com:9200',
            http_auth='elastic:nlplab',
        )

        query = {
            "_source": [
                'aid', 'oid', 'sectionName', 'officeName', 'title', 'url', 'reply_list'
            ],
            'query': {
                'bool': {
                    'must_not': {
                        'exists': {
                            'field': 'date'
                        }
                    }
                }
            }
        }

        result = []
        elastic.export(
            index=index,
            query=query,
            result=result,
        )

        return result

    @staticmethod
    def flatten_reply(reply_list):
        """ """
        reply_idx = {}
        reply_data = []

        for reply in tqdm(reply_list):
            if 'oid' not in reply or 'aid' not in reply:
                continue

            if isinstance(reply['oid'], int):
                reply['oid'] = '{:03d}'.format(reply['oid'])

            if isinstance(reply['aid'], int):
                reply['aid'] = '{:010d}'.format(reply['aid'])

            common = {
                'doc_id': '{oid}-{aid}'.format(**reply),
                'title': reply['title'],
                'section': reply['sectionName'] + '/' + reply['officeName'],
            }

            reply['user_count'] = 0
            reply['reply_count'] = 0

            if 'reply_list' in reply:
                reply['reply_count'] = len(reply['reply_list'])

                user_count = {}
                for item in reply['reply_list']:
                    item.update(common)

                    user_name = item['userName'] + ' (' + item['maskedUserId'] + ')'
                    item['user_name'] = user_name
                    del item['userName']
                    del item['maskedUserId']

                    if user_name not in user_count:
                        user_count[user_name] = 0
                    user_count[user_name] += 1

                    reply_data.append(item)

                reply['user_count'] = len(list(user_count.keys()))

            reply_idx[common['doc_id']] = reply

        return {
            'data': reply_data,
            'docs': reply_list,
            'index': reply_idx,
        }

    @staticmethod
    def query_news_list(id_list, index, source, result, reply_idx, elastic):
        """ 댓글에 해당하는 뉴스 원문을 가져온다."""
        doc_list = []
        elastic.get_by_ids(
            index=index,
            source=source,
            result=doc_list,
            id_list=id_list,
        )

        for doc in doc_list:
            doc_id = '{oid}-{aid}'.format(**doc)
            doc['doc_id'] = doc_id

            # 댓글 정보 업데이트
            if doc_id in reply_idx:
                doc['reply_count'] = reply_idx[doc_id]['reply_count']
                doc['user_count'] = reply_idx[doc_id]['user_count']

            result.append(doc)

        return

    def get_news(self, host, auth, index, reply_idx, reply_list):
        """ 댓글에 해당하는 뉴스 원문 덤프 """
        import pandas as pd

        elastic = ElasticSearchUtils(host=host, http_auth=auth)

        source = [
            'aid', 'oid', 'title', 'date', 'content'
        ]

        id_list = []
        news_list = []
        for reply in tqdm(reply_list):
            if 'oid' not in reply or 'aid' not in reply:
                continue

            if isinstance(reply['oid'], int):
                reply['oid'] = '{:03d}'.format(reply['oid'])

            if isinstance(reply['aid'], int):
                reply['aid'] = '{:010d}'.format(reply['aid'])

            id_list.append('{oid}-{aid}'.format(**reply))
            if len(id_list) > 100:
                self.query_news_list(
                    index=index,
                    source=source,
                    result=news_list,
                    id_list=id_list,
                    elastic=elastic,
                    reply_idx=reply_idx,
                )

                id_list = []

        self.query_news_list(
            index=index,
            source=source,
            result=news_list,
            id_list=id_list,
            elastic=elastic,
            reply_idx=reply_idx,
        )

        # 판다로 변환
        news_df = pd.DataFrame(news_list)

        news_df.fillna('', inplace=True)

        for s in ['“', '”']:
            news_df['title'] = news_df['title'].apply(lambda x: x.replace(s, '"'))
            news_df['content'] = news_df['content'].apply(lambda x: x.replace(s, '"'))

        for s in ['‘', '’']:
            news_df['title'] = news_df['title'].apply(lambda x: x.replace(s, "'"))
            news_df['content'] = news_df['content'].apply(lambda x: x.replace(s, "'"))

        return news_df

    @staticmethod
    def save_doc(index, data):
        """문서 저장한다."""
        import pickle

        filename = 'data/{index}.pkl'.format(index=index)
        with open(filename, 'wb') as fp:
            pickle.dump(data, fp)

    @staticmethod
    def read_doc(index):
        """문서 저장한다."""
        import pickle

        filename = 'data/{index}.pkl'.format(index=index)
        with open(filename, 'rb') as fp:
            result = pickle.load(fp)

        return result

    @staticmethod
    def save_json(df, filename):
        """json 형태로 저장한다."""
        df = df.reset_index()

        if 'index' in df.columns:
            df = df.drop(columns='index')

        df.to_json(
            filename,
            force_ascii=False,
            compression='bz2',
            orient='records',
            lines=True,
            date_format='iso',
        )
        return

    @staticmethod
    def read_json(filename):
        """json 형태의 파일을 읽어드린다."""
        df = pd.read_json(
            filename,
            compression='bz2',
            orient='records',
            lines=True,
        )
        return df

    @staticmethod
    def init_plt():
        """폰트를 초기화한다."""
        # 라이브러리 불러오기
        import matplotlib.pyplot as plt

        # matplotlib 한글 폰트 오류 문제 해결
        from matplotlib import font_manager, rc
        font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'  # 폰트파일의 위치
        font_name = font_manager.FontProperties(fname=font_path).get_name()
        rc('font', family=font_name)

        # 스타일 서식 지정
        plt.style.use('ggplot')

        plt.figure(figsize=(15, 10))

        return

    @staticmethod
    def merge_reply(news_list, reply_list):
        """뉴스 본문 병합"""
        # make doc index
        news_idx = {}
        for d in tqdm(news_list, desc='인덱스 생성'):
            if 'datetime' in d:
                if 'date' not in d:
                    d['date'] = d['datetime']

                del d['datetime']

            if 'section' in d:
                if 'category' not in d:
                    d['category'] = d['section']

                del d['section']

            k = '{oid}-{aid}'.format(**d)
            news_idx[k] = d

        # merge
        count = 0
        for d in tqdm(reply_list, desc='댓글 병합'):
            if 'oid' not in d or 'aid' not in d:
                print('error: ', d)
                continue

            news_id = '{oid}-{aid}'.format(**d)

            if news_id not in news_idx:
                count += 1
                continue

            news_idx[news_id].update(d)

        print('missing doc count: {:,}'.format(count))

        return

    @staticmethod
    def get_simple_reply(doc_list):
        """댓글 정보에서 필요한 것만 추출한다."""
        for doc in tqdm(doc_list):
            if 'reply_list' not in doc:
                continue

            result = []
            for reply in doc['reply_list']:
                item = {}
                for k in ['commentNo', 'contents', 'regTime', 'userName']:
                    if k in reply:
                        item[k] = reply[k]

                result.append(item)

            doc['reply_count'] = len(result)
            doc['reply_list'] = result

        return

    @staticmethod
    def insert_date(news_list, reply_list):
        """댓글에 날짜를 삽입한다."""
        news_idx = {}
        for d in tqdm(news_list, desc='인덱스 생성'):
            if 'datetime' in d:
                if 'date' not in d:
                    d['date'] = d['datetime']

                del d['datetime']

            if 'section' in d:
                if 'category' not in d:
                    d['category'] = d['section']

                del d['section']

            k = '{oid}-{aid}'.format(**d)
            news_idx[k] = d

        # date 삽입
        count = 0
        for d in tqdm(reply_list, desc='댓글 병합'):
            if 'oid' not in d or 'aid' not in d:
                continue

            news_id = '{oid}-{aid}'.format(**d)

            if news_id not in news_idx:
                count += 1
                continue

            d['date'] = news_idx[news_id]['date']

        print('missing doc: ', count)

        return reply_list

    def get_reply_info(self, kbo_df, dt_range):
        """ """
        import numpy as np

        # 날자로 변경
        kbo_df['date'] = pd.to_datetime(kbo_df['date'], utc=True)

        # 댓글이 있는 기사만 추출
        dt_df = kbo_df[kbo_df['reply_count'] > 0]

        if dt_range is None:
            dt_range = {
                'start': dt_df['date'].min().strftime('%Y-%m-%d'),
                'end': dt_df['date'].max().strftime('%Y-%m-%d'),
            }

        # 날자 범위 추출
        kbo_df = kbo_df[
            (kbo_df['date'] >= pd.to_datetime(dt_range['start'], utc=True))
            &
            (kbo_df['date'] <= pd.to_datetime(dt_range['end'], utc=True))
            ]

        # 결과 저장
        filename = 'data/naver-baseball-reply-{start}~{end}.json.bz2'.format(**dt_range)
        self.save_json(
            df=kbo_df,
            filename=filename,
        )

        reply_count = kbo_df[['date', 'reply_count']]
        reply_count.fillna(value=0, inplace=True)

        # 날짜만 추출한다.
        reply_count['date'] = reply_count['date'].apply(
            lambda x: x.strftime('%Y-%m-%d'))

        c_df = reply_count.groupby(by=['date']).describe()
        c_df = c_df['reply_count'].drop(columns=['25%', '50%', '75%', 'min'])
        c_df = c_df.astype({'count': 'int32', 'max': 'int32'})

        # 병합
        reply_info = pd.concat(
            [
                c_df,
                reply_count[reply_count['reply_count']
                            > 0].groupby(by='date').count()
            ],
            axis=1
        )
        reply_info.columns = ['기사수', '평균', '표준편차', '최대 댓글', '댓글이 있는 기사']

        reply_info.fillna(value=0, inplace=True)
        reply_info = reply_info.astype({'댓글이 있는 기사': 'int32'})

        reply_info['댓글 비율'] = reply_info['기사수'] / reply_info['댓글이 있는 기사']
        reply_info['댓글 비율'] = reply_info['댓글 비율'].replace(np.inf, 0)

        reply_info.at['합계/평균', '기사수'] = reply_info['기사수'].sum()
        reply_info.at['합계/평균', '댓글이 있는 기사'] = reply_info['댓글이 있는 기사'].sum()
        reply_info.at['합계/평균', '평균'] = reply_info['평균'].mean()
        reply_info.at['합계/평균', '표준편차'] = reply_info['표준편차'].mean()
        reply_info.at['합계/평균', '댓글 비율'] = reply_info['댓글 비율'].mean()
        reply_info.at['합계/평균', '최대 댓글'] = reply_info['최대 댓글'].max()

        return {
            'kbo_df': kbo_df,
            'dt_range': dt_range,
            'reply_info': reply_info,
        }
