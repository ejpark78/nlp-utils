#!./venv/bin/python3
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from collections import defaultdict

import pytz
import requests
import urllib3

from crawler.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'


class NLUWrapper(object):

    def __init__(self):
        self.url = 'http://172.20.92.249:32001'

        self.options = {
            'domain': 'economy',
            'style': 'literary',
            'module': [
                'SBD_crf',
                'POS',
                'NER'
            ]
        }

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

    @staticmethod
    def simplify(doc_list: list) -> list:
        """ 결과를 파싱한다."""
        dep_columns = 'index,head,morp,pos,func'.split(',')
        result_columns = set('text,morp_str,ne_str,depen_str,time_results'.split(','))

        result = []
        for doc in doc_list:
            for sent in doc['sentences']:
                item = defaultdict(str)
                for k in result_columns:
                    if k not in sent:
                        continue

                    item[k] = sent[k]

                # 결과 변환: 시간 필드 변경
                if len(item['time_results']) > 0:
                    item['times_str'] = json.dumps(item['time_results'], ensure_ascii=False)

                del item['time_results']

                # depen_str 변환
                if len(item['depen_str']) > 0:
                    depen = [dict(zip(dep_columns, dep)) for dep in item['depen_str']]
                    item['depen_str'] = json.dumps(depen, ensure_ascii=False)

                del item['depen_str']

                if 'meta' not in doc:
                    doc['meta'] = {}

                result.append({**doc['meta'], **item})

        return result

    @staticmethod
    def buf_doc(text: str, options: dict, meta: dict) -> list:
        text_list = [text]
        if isinstance(text, list):
            text_list = text

        # POST 메세지
        if 'SBD' in options['module'] or 'SBD_crf' in options['module']:
            return [{
                'meta': meta,
                'contents': x.replace(r'\n', ' '),
            } for x in text_list]

        return [{
            'sentences': [{
                'meta': meta,
                'text': x,
            }]
        } for x in text_list]

    def send(self, doc: list, url: str, options: dict, timeout: int = 5) -> list:
        """nlu wrapper 호출"""
        post_data = {
            'nlu_wrapper': {
                'option': options
            },
            'doc': doc
        }

        # rest api 호출
        try:
            resp = requests.post(url=url, json=post_data, timeout=timeout).json()
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'NLU Wrapper 호출 에러',
                'url': url,
                'post_data': post_data,
                'exception': str(e),
            })

            return []

        # 결과 취합
        try:
            return self.simplify(doc_list=resp['doc'])
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'NLU Wrapper 결과 취합 에러',
                'url': url,
                'resp': resp,
                'post_data': post_data,
                'exception': str(e),
            })

        return []

    def fit_document(self, document: dict, domain: str) -> list:
        """하나의 기사를 코퍼스 전처리 한다."""
        self.options['domain'] = domain

        meta_columns = set('_id,paper,date,source,category'.split(','))

        # 제목 처리
        doc = []
        if 'title' in document and document['title'] != '':
            doc += self.buf_doc(
                meta={
                    'position': 'title',
                    **{x: document[x] for x in meta_columns if x in document}
                },
                text=document['title'],
                options=self.options,
            )

        # 이미지 자막 처리
        if 'image_list' in document:
            for item in document['image_list']:
                if 'caption' not in item or item['caption'] == '':
                    continue

                text_list = [item['caption']]
                if isinstance(item['caption'], list):
                    text_list = item['caption']

                for text in [x for x in text_list if x != '']:
                    doc += self.buf_doc(
                        meta={
                            'position': 'caption',
                            **{x: document[x] for x in meta_columns if x in document}
                        },
                        text=text,
                        options=self.options,
                    )

        # 기사 본문 처리
        if 'content' in document:
            for text in document['content'].split('\n'):
                text = text.strip()
                if text == '':
                    continue

                doc += self.buf_doc(
                    meta={
                        'position': 'content',
                        **{x: document[x] for x in meta_columns if x in document}
                    },
                    text=text,
                    options=self.options,
                )

        return self.send(doc=doc, options=self.options, url=self.url)

    def batch(self) -> None:
        document = {
            "_id": "015-0004155554",
            "title": "LG화학 등 2차전지株 '재충전'…파트론 등 휴대폰 부품株도 주목",
            "url": "https://news.naver.com/main/read.nhn?mode=LS2D&mid=shm&sid1=101&sid2=258&oid=015&aid=0004155554",
            "paper": "0면",
            "category": "경제/증권",
            "content": "美 금리 인하 기대 커지는데…수혜주는 어디\\n美 통화정책 완화 현실화되면\\n경기부양 효과로 증시 반등 기대[ 임근호 기자 ] 코스피지수는 올 들어 지난 6일까지 1.38% 오르는 데 그쳤다. 미·중 무역분쟁이 재점화하며 지난 5월 7.34% 급락한 탓이다. 투자자들은 채권 등 안전자산으로 몰렸다. 주식시장에 남은 투자자들도 배당주나 가치주로 피신했다. 금융정보업체 에프앤가이드에 따르면 순수가치지수는 올 들어 0.40% 올랐지만 순수성장지수는 4.03% 떨어졌다.\\n\\n이런 흐름이 조만간 바뀔 것이란 기대가 커지고 있다. 제롬 파월 미국 중앙은행(Fed) 의장이 금리 인하를 시사한 것이 기폭제가 됐다. 미국의 금리 인하가 증시 하락을 멈출 ‘안전판’이 될 것이란 분석이다.\\n\\n세계 각국이 금리 인하에 동참하면서 경기 부양 효과는 하반기로 갈수록 커질 것이란 관측이 나온다. 김용구 하나금융투자 연구원은 “미국의 통화정책이 더욱 완화적으로 바뀌고 있다”며 “증시가 바닥을 딛고 상승할 확률이 높아지고 있다”고 말했다.\\n\\n금리 인하로 성장주 수혜 기대\\n\\n전문가들은 “앞으로 금리 인하가 현실화될 것으로 본다면 성장주와 경기민감주 비중을 높일 필요가 있다”고 말한다. 성장주는 현재 가진 자산보다 먼 미래의 기대 이익이 높은 가치를 인정받아 금리에 민감한 반응을 보이는 경향이 있다.\\n\\n김병연 NH투자증권 연구원은 “완화적 통화정책의 혜택을 받을 수 있는 성장주로는 5세대(5G) 이동통신, 인터넷, 미디어, 게임주 등이 있다”고 말했다. 원화 약세 수혜를 받을 수 있는 정보기술(IT)주와 자동차주 등에도 관심을 둘 필요가 있다는 진단이다. 미국이 금리를 인하하면 달러 강세가 누그러지는 효과가 있다.\\n\\n삼성SDI와 LG화학 등 2차전지주는 대표적인 성장주로 꼽힌다. 전기차 시대가 열릴 것이란 기대로 높은 밸류에이션(실적 대비 주가수준)을 부여받고 있다. 금융정보업체 에프앤가이드에 따르면 삼성SDI의 올해 예상 영업이익은 7935억원이지만 2021년엔 1조3228억원에 이를 것으로 전망된다.\\n\\nLG화학도 올해 1조9311억원으로 예상되는 영업이익이 2021년엔 3조1887억원으로 늘어날 전망이다. 김지산 키움증권 연구원은 “전기차 시장이 고성장하고 있고, 에너지저장장치(ESS) 화재 후유증에서도 벗어나고 있어 2차전지주의 전망이 밝다”고 했다.\\n\\n셀트리온도 실적 회복기에 들어선 가운데 금리까지 하락한다면 주가 반등 폭이 클 것이란 분석이 나온다. 셀트리온의 올해 영업이익 컨센서스(증권사 전망치 평균)는 4169억원으로 2017년 5078억원에는 못 미칠 전망이다.\\n\\n하지만 2021년엔 영업이익이 7600억원으로 뛸 것으로 기대된다. 한병화 유진투자증권 연구원은 “미국과 유럽 시장에 성공적으로 진출한다면 램시마 등 4개 약품으로만 2023년 3조7000억원대 매출을 달성할 수 있을 것”이라며 “제2의 성장기가 기대된다”고 말했다.\\n\\n삼성전자·파트론 등 IT주 유망\\n\\n한국경제TV 전문가들도 금리 하락으로 성장주에 다시 기회가 찾아올 것으로 보고 있다. 강동진 파트너는 “금리 인하를 통한 유동성 공급은 기본적으로 고(高) 베타주(시장 대비 주가 등락이 큰 종목)인 성장주와 투기적 요소가 강한 테마주에 유리하다”며 “삼성전자와 카카오, NICE평가정보, 단기 낙폭이 컸던 KG케미칼이 유망해 보인다”고 말했다.\\n\\n박완필 파트너는 성장주 중에서도 IT 부품주를 추천했다. 미국이 중국 화웨이에 제재를 가하면서 삼성전자와 LG전자 등 국내 업체들이 반사 이익을 얻을 수 있다는 논리다. 그는 파트론과 서진시스템, 아나패스 등을 이런 종목으로 꼽았다.\\n\\n박 파트너는 “파트론은 삼성전자 스마트폰 카메라 분야 최대 수혜주”라고 했다. 서진시스템은 통신장비 등 IT 전반을 아우르는 제품 라인업으로 5G 이동통신 테마주로도 분류된다.\\n\\n안인기 파트너도 IT주인 파트론과 삼성전자, AP시스템을 추천했다. 삼성전자는 한국 대표주이자 IT업종 대표주인 까닭에 금리 인하로 외국인 자금이 국내 증시로 유입된다면 삼성전자를 사지 않을 수 없다는 설명이다. 그는 “AP시스템은 반도체 장비 대장주로, 업황이 살아나면 함께 실적 개선이 기대된다”고 말했다.\\n\\n감은숙 파트너의 추천주는 GS건설과 키움증권, 휠라코리아다. 금리 인하로 부동산 시장이 살아나면 건설주가 혜택을 받을 수 있기 때문이다. 키움증권도 금리 인하로 인한 증시 상승, 거래세 인하에 따른 긍정적 영향이 예상된다는 분석이다.\\n\\n임근호 기자 eigen@hankyung.com\\n\\n\\n\\n▶ 네이버에서 '한국경제' 구독하고 비씨카드·한경레이디스컵 KLPGA 입장권 받자\\n ▶ 한경닷컴 바로가기 ▶ 모바일한경 구독신청 \\n\\nⓒ 한국경제 & hankyung.com, 무단전재 및 재배포 금지",
            "date": "2019-06-09T16:13:00+09:00"
        }

        result = self.fit_document(document=document, domain='economy')
        return


if __name__ == '__main__':
    NLUWrapper().batch()
