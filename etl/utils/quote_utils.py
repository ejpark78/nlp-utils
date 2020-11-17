#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import pickle
import re
import sys
from copy import deepcopy
from pprint import pprint

import pandas as pd
import urllib3
from tqdm.autonotebook import tqdm

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


class BaseUtils(object):
    """베이스 유틸"""

    def __init__(self):
        """생성자"""
        super().__init__()

        self.debug = False

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
    def save_pickle(data, filename):
        """pickle 로 저장한다."""
        with open(filename, 'wb') as fp:
            pickle.dump(data, fp)

        return

    @staticmethod
    def read_pickle(filename):
        """pickle 을 읽는다."""

        with open(filename, 'rb') as fp:
            result = pickle.load(fp)

        return result


class QuoteUtils(BaseUtils):
    """인용문 추출 유틸"""

    def __init__(self):
        """생성자"""
        super().__init__()

        self.player_info = None

        self.p_head_list = [
            re.compile(r'(.+)[ ]?(감독 대행|사무 총장|홍보 팀장|신임 회장)은 '),
            re.compile(r'(.+)[ ]?(구단 대표|코칭 스태프)는 '),
            re.compile(
                r'(.+)[ ]?(감독|팀장|단장|총장|고문|대행|총괄|군산지청장|해설위원|대전시장|시장|위원장|위원|지도자들|이사장|대외협력실장|관계자들|지사장|부사장|사무총장|회장)은 '),
            re.compile(r'(.+)[ ]?(대표|코치|관계자|대표이사|매체|총리|매니저|지도자|변호사|아나운서)는 '),
            re.compile(r'(.+)[은는이가] '),
        ]

        self.p_quote = re.compile(r'"([^"]+)"')

        self.ne_tags = ['PER', 'ORG', 'LOC']
        self.p_ne = re.compile(r'<([^:]+?):([A-Z_]+?)>')

    @staticmethod
    def import_quote(quote_df, host, auth, index='corpus-naver_sports_quote-2019'):
        """"""
        from utils.elasticsearch_utils import ElasticSearchUtils

        elastic = ElasticSearchUtils(host=host, index=index, http_auth=auth)

        for i, row in tqdm(quote_df.iterrows(), total=len(quote_df)):
            doc = dict(row)
            doc['_id'] = doc['doc_id']

            elastic.save_document(document=doc)

        elastic.flush()
        return

    @staticmethod
    def export_news(host, auth, index_list):
        """뉴스 본문이나 댓글을 덤프 받는다."""
        from utils.elasticsearch_utils import ElasticSearchUtils

        elastic = ElasticSearchUtils(host=host, http_auth=auth)

        # https://www.elastic.co/guide/kr/elasticsearch/reference/current/gs-executing-searches.html
        query = {
            "_source": [
                "aid", "oid", "section", "category", "title", "date", "datetime", "url", "content",
                "nlu_wrapper.*.text", "nlu_wrapper.*.ne_str"
            ],
            "query": {
                "bool": {
                    "should": [
                        {
                            "match": {
                                "section": "야구"
                            }
                        },
                        {
                            "match": {
                                "category": "야구"
                            }
                        }
                    ]
                }
            }
        }

        result = []
        for index in index_list:
            elastic.export(
                index=index,
                query=query,
                result=result,
            )

        return result

    @staticmethod
    def export_reply(host, auth, index_list):
        """뉴스 본문이나 댓글을 덤프 받는다."""
        from utils.elasticsearch_utils import ElasticSearchUtils

        elastic = ElasticSearchUtils(host=host, http_auth=auth)

        query = {
            '_source': [
                'aid', 'oid', 'sectionName', 'officeName', 'title',
                'reply_list.contents', 'reply_list.userName', 'reply_list.regTime', 'reply_list.maskedUserId'
            ]
        }

        result = []
        for index in index_list:
            elastic.export(
                index=index,
                query=query,
                result=result,
            )

        return result

    @staticmethod
    def remove_low_freq(df, by, min_freq):
        """빈도가 낮은 who, verb를 삭제한다."""
        freq = df.groupby(by=by).size().to_frame()

        low_freq = freq[freq[0] <= min_freq]

        clean_df = df.set_index(by).drop(low_freq.index).reset_index()

        return {
            'freq': freq,
            'size': len(low_freq),
            'low_freq': low_freq,
            'clean_df': clean_df,
        }

    @staticmethod
    def info(news_df, reply_df, quote_df):
        """ """
        pd.set_option('precision', 0)
        pd.options.display.float_format = '{:,.0f}'.format

        quote_include = news_df[
            (news_df['content'].str.contains('"(.+?)"', regex=True))
        ]

        size = {
            '뉴스수': len(news_df),
            '뉴스당 댓글수': round(len(reply_df) / len(news_df) * 100, 2),
            '뉴스당 인터뷰수': round(len(quote_df) / len(quote_include) * 100, 2),
            '인터뷰 포함 뉴스 비율': round(len(quote_include) / len(news_df) * 100, 2),
            '댓글수': len(reply_df),
            '인터뷰수': len(quote_df),
            '인터뷰 포함 기사수': len(quote_include),
        }

        return pd.DataFrame(size, index=['size']).transpose()

    @staticmethod
    def extract_nlu_wrapper(df):
        """ NLU wrapper 추출한다."""
        p_ne = re.compile(r'<([^:]+?):([A-Z_]+?)>')

        data_list = []
        for i, row in tqdm(df.iterrows(), total=len(df)):
            for item in row['nlu_wrapper']:
                item['doc_id'] = row['doc_id']

                ne_idx = {}

                ne_list = list(re.finditer(p_ne, item['ne_str']))
                for m in ne_list:
                    w, t = (m.group(1), m.group(2))

                    if t not in ne_idx:
                        ne_idx[t] = []

                    if w not in ne_idx[t]:
                        ne_idx[t].append(w)

                item['ne_idx'] = ne_idx

                data_list.append(item)

        return pd.DataFrame(data_list).drop(columns=['morp_str'])

    @staticmethod
    def clean_text(text):
        """ 유니코드를 변환한다."""
        text = text.replace(u'\xa0', ' ')
        text = text.replace('다.', '다. ')
        text = text.replace(' -', '\n-')

        for s in ['“', '”']:
            text = text.replace(s, '"')

        for s in ['‘', '’']:
            text = text.replace(s, "'")

        text = re.sub(r'\t+', '\n', text)
        text = re.sub(r'[ ]+', ' ', text)

        return text

    def get_quote(self, news_df, player_info, ne_idx):
        """인용구를 추출한다."""
        self.player_info = player_info

        result = []
        player_list = []

        for i, row in tqdm(news_df.iterrows(), total=len(news_df)):
            ne_info = ne_idx[row['doc_id']]

            contents = []
            for j, text in enumerate(row['text_list']):
                text = text.strip()

                if text.find('"') < 0:
                    continue

                self.guess_player_info(text=text, player_list=player_list)

                # 인용문 추출
                quote_list = self.get_simple_quote(
                    text=text,
                    common={
                        'url': row['url'],
                        'date': row['date'],
                        'doc_id': row['doc_id'],
                        'raw_text': text,
                    },
                )

                # 인명 사전으로 발화자 예측
                for quote in quote_list:
                    who_list = []
                    self.guess_player_info(text=quote['who'], player_list=who_list)

                    if len(who_list) > 0:
                        quote['who'] = who_list[0]['name']
                        quote['position'] = ','.join([x['position'] for x in who_list])
                        continue

                    who = self.get_player(
                        ne_list=ne_info[:j + 1],
                        position=quote['position'],
                        player_list=player_list,
                    )

                    if len(who) > 0:
                        quote['who'] = who[0]['name']
                        quote['position'] = who[0]['position']

                contents += quote_list
                if len(quote_list) > 0:
                    player_list = []

            # 발화자 추정
            result += self.fill_empty_who(quote_list=contents)

        return pd.DataFrame(result)

    @staticmethod
    def fill_empty_who(quote_list):
        """ 다음 발화를 모를 경우, 앞의 발화자로 채운다."""
        # empty 발화자 처리
        for i, item in enumerate(quote_list):
            if len(quote_list) < i + 2:
                break

            next_item = quote_list[i + 1]
            if item['who'] != '' and next_item['who'] == '':
                next_item['who'] = item['who']
                next_item['position'] = item['position']

        return quote_list

    @staticmethod
    def get_player(player_list, position, ne_list):
        """ 선수/감독의 포지션 정보에 해당하는 값을 반환한다."""
        result = []

        # pprint({'ne_list': ne_list})

        ner_p = position
        if ner_p == '':
            ner_p = '감독'

        # 개체명 정보 확인
        for ne_info in reversed(ne_list):
            if 'position' not in ne_info:
                continue

            if ner_p not in ne_info['position']:
                continue

            if len(ne_info['position'][ner_p]) == 0:
                continue

            result.append({
                'name': ne_info['position'][ner_p][0],
                'position': ner_p,
            })

            return result

        # ngram 정보 확인
        for item in player_list:
            if item['position'] == position:
                result.append(item)

        return result

    def guess_player_info(self, text, player_list):
        """선수 정보로 발화자를 추정한다."""
        from nltk import ngrams

        if text == '':
            return

        for n in range(self.player_info['name_min'], self.player_info['name_max'] + 1, 1):
            for ngram in ngrams(text, n=n):
                name = ''.join(ngram)
                if name not in self.player_info['index']:
                    continue

                pos = text.find(name) + len(name)
                if text.find('기자') - pos == 1:
                    player_list += [{
                        'name': name,
                        'position': '기자',
                    }]
                    continue

                player_list += self.player_info['index'][name]

        return

    def get_simple_quote(self, common, text):
        """ 본문에서 인용문을 추출한다."""
        if self.debug:
            pprint({'common': common})

        text = text.replace(u'\xa0', ' ')
        text = re.sub(r'^\[[^]]+?\]', '', text)

        result = []

        prev_m = None
        quote_list = list(re.finditer(self.p_quote, text))

        for i, m in enumerate(quote_list):
            middle = ''
            if len(quote_list) - 1 > i:
                next_m = quote_list[i + 1]

                middle = text[m.end():next_m.start()]

            start_pos = 0
            if prev_m is not None:
                start_pos = prev_m.end()

            head = text[start_pos:m.start()].split('"')[-1].rsplit('.')[-1].strip() + ' '
            tail = text[m.end():].split('"')[-1].rsplit('.')[0].strip()

            prev_m = m

            quote = m.group(1)

            if self.debug:
                pprint({
                    'quote': {
                        # 'start': m.start(),
                        # 'end': m.end(),
                        'head': head.strip(),
                        'tail': tail.strip(),
                        'quote': quote.strip(),
                        'middle': middle.strip(),
                    }
                })

            # 주어 추출
            subject = ''
            position = ''
            for p_head in self.p_head_list:
                m_head = re.search(p_head, self.remove_punctuation(subject=head))

                if m_head:
                    subject = m_head.group(1).strip()

                    if m_head.lastindex > 1:
                        position = m_head.group(2).strip()

                    break

            item = {
                'who': subject.strip(),
                'position': position.strip(),
                'text': quote.strip(),
                'verb': tail.strip(),
            }
            item.update(common)

            result.append(item)

        return result

    @staticmethod
    def remove_punctuation(subject):
        """문장 부호 이전 텍스트를 삭제한다."""
        # 문미 기호 이전 문장 삭제
        mark_list = ['.', '!', '?', '-', ',', ')', ']', '=', '(', '<', '>']

        for mark in mark_list:
            if subject.rfind(mark) >= 0:
                subject = subject.rsplit(mark, maxsplit=1)[-1]

        if subject.rfind("'") >= 0:
            subject = subject.rsplit("'", maxsplit=1)[-1]

        return subject

    @staticmethod
    def get_content_len_index(text_list):
        """ 본문을 길이 단위로 분리한 정보를 저장한다."""
        len_index = []

        for p in text_list:
            if len(len_index) == 0:
                len_index.append(len(p))
                continue

            len_index.append(len(p) + len_index[-1])

        return len_index

    def update_ne_idx(self, ne_str, result, player_idx, remove_quote=True, only_person=True):
        """ 개체명 인덱스를 버퍼링한다. """
        if 'position' not in result:
            result['position'] = {
                '감독': [],
                '*': [],
            }

        # 인용구 삭제
        if remove_quote is True:
            quote_str = re.sub(self.p_quote, r'\g<1>', ne_str)
            if ne_str != quote_str:
                ne_str = ne_str.replace(quote_str, '')

        # 개체명 목록 추출
        ne_list = list(re.finditer(self.p_ne, ne_str))
        for m in ne_list:
            w, t = (m.group(1), m.group(2))

            l1 = t[:3]
            if only_person is True:
                if l1 != 'PER':
                    continue
            else:
                if l1 not in self.ne_tags:
                    continue

                if t not in result:
                    result[t] = []

                if w not in result[t]:
                    result[t].append(w)

            if w in player_idx:
                for x in player_idx[w]:
                    # 감독인 경우
                    if x['position'] in result['position']:
                        result['position'][x['position']].append(w)
                        continue

                    # 선수인 경우
                    result['position']['*'].append(w)

        # 중복 제거
        for p in result['position']:
            result['position'][p] = list(set(result['position'][p]))

        return

    def get_nlu_quote_index(self, nlu, quote_news_df, player_idx):
        """nlu wrapper 에서 ne index 를 추출한다."""
        result = {}

        for i, row in tqdm(quote_news_df.iterrows(), total=len(quote_news_df)):
            doc_id = row['doc_id']

            ne_str = ''
            paragraph = []

            len_index = self.get_content_len_index(text_list=row['text_list'])

            i = 0
            len_sum = 0
            for item in nlu[doc_id]:
                item['doc_id'] = doc_id

                len_sum += len(item['text'].strip())
                if len_index[i] < len_sum:
                    # 개체명 목록을 추출한다.
                    ne_idx = {}
                    self.update_ne_idx(
                        result=ne_idx,
                        ne_str=ne_str,
                        player_idx=player_idx,
                    )

                    paragraph.append(deepcopy(ne_idx))

                    i += 1
                    ne_str = ''

                if 'ne_str' not in item:
                    continue

                ne_str += ' ' + item['ne_str']

            if ne_str != '':
                ne_idx = {}
                self.update_ne_idx(
                    result=ne_idx,
                    ne_str=ne_str,
                    player_idx=player_idx,
                )

                paragraph.append(deepcopy(ne_idx))

            result[doc_id] = deepcopy(paragraph)

        return result

    def get_player_info(self, filename='data/interview/player_basic.20190927.json'):
        """선수 정보를 읽어온다."""
        with open(filename, 'r') as fp:
            player_list = json.load(fp)

        df = pd.DataFrame(player_list)

        df.fillna('', inplace=True)
        df.columns = [col.split('.')[-1] for col in df.columns]

        idx = {}
        result = {
            'name_min': 100,
            'name_max': 0,
        }

        for i, row in df.iterrows():
            name = row['name']

            if result['name_max'] < len(name):
                result['name_max'] = len(name)

            if result['name_min'] > len(name):
                result['name_min'] = len(name)

            if name not in idx:
                idx[name] = []

            idx[name].append(dict(row))

        result.update({
            'df': df,
            'index': idx
        })

        self.player_info = result

        return self.player_info

    def dump_corpus(self, index, path='data/interview'):
        """ 코퍼스를 덤프 받아 저장한다."""
        host = 'https://corpus.ncsoft.com:9200'
        auth = 'crawler:crawler2019'

        doc_list = self.export_news(host, auth, [index])

        filename = '{path}/{index}.json'.format(path=path, index=index)
        with open(filename, 'w') as fp:
            for n in tqdm(doc_list):
                line = json.dumps(n, ensure_ascii=False) + '\n'
                fp.write(line)

        return

    @staticmethod
    def get_news_df(news):
        """ 데이터프레임으로 변환한다."""
        news_df = pd.DataFrame(news)

        news_df.fillna('', inplace=True)

        news_df['date'] = pd.to_datetime(news_df['date'])
        news_df['day'] = news_df['date'].apply(lambda x: x.strftime('%Y-%m-%d'))

        news_df['doc_id'] = news_df.apply(lambda x: '{}-{}'.format(x['oid'], x['aid']), axis=1)

        # 인용문있는 기사 분리
        quote_news_df = news_df[
            (news_df['content'].str.contains('"(.+?)"', regex=True))
        ]

        quote_news_df['text_list'] = quote_news_df.apply(
            lambda x: [v.strip() for v in x['content'].split('\n') if v.strip() != ''],
            axis=1
        )

        return {
            'news_df': news_df,
            'quote_news_df': quote_news_df,
        }

    def read_nlu_wrapper_data(self, filename):
        """ 전처리 결과와 뉴스 정보를 분리한다."""
        nlu = {}
        news = []
        with open(filename, 'r') as fp:
            for line in tqdm(fp.readlines()):
                doc = json.loads(line)

                if 'content' not in doc['nlu_wrapper']:
                    continue

                doc_id = doc['id'] = '{oid}-{aid}'.format(**doc)

                for x in doc['nlu_wrapper']['content']:
                    for k in ['ne_str', 'text']:
                        x[k] = self.clean_text(x[k])

                nlu[doc_id] = doc['nlu_wrapper']['content']
                del doc['nlu_wrapper']

                doc['content'] = self.clean_text(doc['content'])
                news.append(doc)

        return {
            'nlu': nlu,
            'news': news,
        }
