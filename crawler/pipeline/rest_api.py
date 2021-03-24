#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API Center 는 NLP 기반 기술인 형태소 분석, 개체명 인식, 질문 의도 분류 등의 기술을 REST API 형태로 서비스하는
Flask-restplus 기반 웹 어플리케이션이다.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from http import HTTPStatus

from flask import request
from flask_restplus import Api, Resource
from flask_restplus.namespace import Namespace

from config import config
from logging_format import LogMessage as LogMsg
from utils.corpus_pipeline_utils import CorpusPipelineUtils

title = '코퍼스 전처리'
model = None

corpus_processor_utils = CorpusPipelineUtils()

# 코퍼스 처리 배치 처리 큐
batch_thread = None
thread_lock = False

MESSAGE = 25
logger = logging.getLogger('rest_api')

ns = Namespace(title, description=title)
health_check_ns = Namespace('health check', description='health check')


@health_check_ns.route('')
class HealthCheck(Resource):
    """ health check """

    @health_check_ns.doc('health check')
    def get(self):
        """health check"""
        return {'msg': 'Service ready.'}, HTTPStatus.OK, {}


@ns.route('/batch')
class Batch(Resource):
    """ 코퍼스 전처리 """

    @ns.param('data', '전처리 문서 정보', _in='body', required=True, schema='json')
    def post(self):
        """코퍼스 전처리

        입력 예시::

            # web news
            {
                "elastic": {
                  "host": "https://corpus.ncsoft.com:9200",
                  "index": "corpus_process-naver-economy",
                  "http_auth": "crawler:crawler2019",
                  "split_index": true
                },
                "document": [{
                    "title" : "LG화학 등 2차전지株 '재충전'…파트론 등 휴대폰 부품株도 주목",
                    "url" : "https://news.naver.com/main/read.nhn?mode=LS2D&mid=shm&sid1=101&sid2=258&oid=015&aid=0004155554",
                    "category" : "경제/증권",
                    "content" : "美 금리 인하 기대 커지는데…수혜주는 어디\\n美 통화정책 완화 현실화되면\\n경기부양 효과로 증시 반등 기대[ 임근호 기자 ] 코스피지수는 올 들어 지난 6일까지 1.38% 오르는 데 그쳤다. 미·중 무역분쟁이 재점화하며 지난 5월 7.34% 급락한 탓이다. 투자자들은 채권 등 안전자산으로 몰렸다. 주식시장에 남은 투자자들도 배당주나 가치주로 피신했다. 금융정보업체 에프앤가이드에 따르면 순수가치지수는 올 들어 0.40% 올랐지만 순수성장지수는 4.03% 떨어졌다.\\n\\n이런 흐름이 조만간 바뀔 것이란 기대가 커지고 있다. 제롬 파월 미국 중앙은행(Fed) 의장이 금리 인하를 시사한 것이 기폭제가 됐다. 미국의 금리 인하가 증시 하락을 멈출 ‘안전판’이 될 것이란 분석이다.\\n\\n세계 각국이 금리 인하에 동참하면서 경기 부양 효과는 하반기로 갈수록 커질 것이란 관측이 나온다. 김용구 하나금융투자 연구원은 “미국의 통화정책이 더욱 완화적으로 바뀌고 있다”며 “증시가 바닥을 딛고 상승할 확률이 높아지고 있다”고 말했다.\\n\\n금리 인하로 성장주 수혜 기대\\n\\n전문가들은 “앞으로 금리 인하가 현실화될 것으로 본다면 성장주와 경기민감주 비중을 높일 필요가 있다”고 말한다. 성장주는 현재 가진 자산보다 먼 미래의 기대 이익이 높은 가치를 인정받아 금리에 민감한 반응을 보이는 경향이 있다.\\n\\n김병연 NH투자증권 연구원은 “완화적 통화정책의 혜택을 받을 수 있는 성장주로는 5세대(5G) 이동통신, 인터넷, 미디어, 게임주 등이 있다”고 말했다. 원화 약세 수혜를 받을 수 있는 정보기술(IT)주와 자동차주 등에도 관심을 둘 필요가 있다는 진단이다. 미국이 금리를 인하하면 달러 강세가 누그러지는 효과가 있다.\\n\\n삼성SDI와 LG화학 등 2차전지주는 대표적인 성장주로 꼽힌다. 전기차 시대가 열릴 것이란 기대로 높은 밸류에이션(실적 대비 주가수준)을 부여받고 있다. 금융정보업체 에프앤가이드에 따르면 삼성SDI의 올해 예상 영업이익은 7935억원이지만 2021년엔 1조3228억원에 이를 것으로 전망된다.\\n\\nLG화학도 올해 1조9311억원으로 예상되는 영업이익이 2021년엔 3조1887억원으로 늘어날 전망이다. 김지산 키움증권 연구원은 “전기차 시장이 고성장하고 있고, 에너지저장장치(ESS) 화재 후유증에서도 벗어나고 있어 2차전지주의 전망이 밝다”고 했다.\\n\\n셀트리온도 실적 회복기에 들어선 가운데 금리까지 하락한다면 주가 반등 폭이 클 것이란 분석이 나온다. 셀트리온의 올해 영업이익 컨센서스(증권사 전망치 평균)는 4169억원으로 2017년 5078억원에는 못 미칠 전망이다.\\n\\n하지만 2021년엔 영업이익이 7600억원으로 뛸 것으로 기대된다. 한병화 유진투자증권 연구원은 “미국과 유럽 시장에 성공적으로 진출한다면 램시마 등 4개 약품으로만 2023년 3조7000억원대 매출을 달성할 수 있을 것”이라며 “제2의 성장기가 기대된다”고 말했다.\\n\\n삼성전자·파트론 등 IT주 유망\\n\\n한국경제TV 전문가들도 금리 하락으로 성장주에 다시 기회가 찾아올 것으로 보고 있다. 강동진 파트너는 “금리 인하를 통한 유동성 공급은 기본적으로 고(高) 베타주(시장 대비 주가 등락이 큰 종목)인 성장주와 투기적 요소가 강한 테마주에 유리하다”며 “삼성전자와 카카오, NICE평가정보, 단기 낙폭이 컸던 KG케미칼이 유망해 보인다”고 말했다.\\n\\n박완필 파트너는 성장주 중에서도 IT 부품주를 추천했다. 미국이 중국 화웨이에 제재를 가하면서 삼성전자와 LG전자 등 국내 업체들이 반사 이익을 얻을 수 있다는 논리다. 그는 파트론과 서진시스템, 아나패스 등을 이런 종목으로 꼽았다.\\n\\n박 파트너는 “파트론은 삼성전자 스마트폰 카메라 분야 최대 수혜주”라고 했다. 서진시스템은 통신장비 등 IT 전반을 아우르는 제품 라인업으로 5G 이동통신 테마주로도 분류된다.\\n\\n안인기 파트너도 IT주인 파트론과 삼성전자, AP시스템을 추천했다. 삼성전자는 한국 대표주이자 IT업종 대표주인 까닭에 금리 인하로 외국인 자금이 국내 증시로 유입된다면 삼성전자를 사지 않을 수 없다는 설명이다. 그는 “AP시스템은 반도체 장비 대장주로, 업황이 살아나면 함께 실적 개선이 기대된다”고 말했다.\\n\\n감은숙 파트너의 추천주는 GS건설과 키움증권, 휠라코리아다. 금리 인하로 부동산 시장이 살아나면 건설주가 혜택을 받을 수 있기 때문이다. 키움증권도 금리 인하로 인한 증시 상승, 거래세 인하에 따른 긍정적 영향이 예상된다는 분석이다.\\n\\n임근호 기자 eigen@hankyung.com\\n\\n\\n\\n▶ 네이버에서 '한국경제' 구독하고 비씨카드·한경레이디스컵 KLPGA 입장권 받자\\n ▶ 한경닷컴 바로가기 ▶ 모바일한경 구독신청 \\n\\nⓒ 한국경제 & hankyung.com, 무단전재 및 재배포 금지",
                    "date" : "2019-06-09T16:13:00+09:00",
                    "image_list" : [
                      {
                        "caption" : "Getty Images Bank",
                        "image" : "https://imgnews.pstatic.net/image/015/2019/06/09/0004155554_001_20190609161302397.jpg?type=w647"
                      },
                      {
                        "image" : "https://imgnews.pstatic.net/image/015/2019/06/09/0004155554_002_20190609161302423.jpg?type=w647"
                      }
                    ]
                }]
            }

            # nlu wrapper
            {
                "module": [
                  {
                    "name": "nlu_wrapper",
                    "option": {
                      "domain": "economy",
                      "style": "literary",
                      "module": ["SBD", "POS", "NER"]
                    },
                    "column": "content",
                    "result": "nlu_wrapper"
                  }
                ],
                "document": [{
                    "title" : "LG화학 등 2차전지株 '재충전'…파트론 등 휴대폰 부품株도 주목",
                    "url" : "https://news.naver.com/main/read.nhn?mode=LS2D&mid=shm&sid1=101&sid2=258&oid=015&aid=0004155554",
                    "category" : "경제/증권",
                    "content" : "美 금리 인하 기대 커지는데…수혜주는 어디\\n美 통화정책 완화 현실화되면\\n경기부양 효과로 증시 반등 기대[ 임근호 기자 ] 코스피지수는 올 들어 지난 6일까지 1.38% 오르는 데 그쳤다. 미·중 무역분쟁이 재점화하며 지난 5월 7.34% 급락한 탓이다. 투자자들은 채권 등 안전자산으로 몰렸다. 주식시장에 남은 투자자들도 배당주나 가치주로 피신했다. 금융정보업체 에프앤가이드에 따르면 순수가치지수는 올 들어 0.40% 올랐지만 순수성장지수는 4.03% 떨어졌다.\\n\\n이런 흐름이 조만간 바뀔 것이란 기대가 커지고 있다. 제롬 파월 미국 중앙은행(Fed) 의장이 금리 인하를 시사한 것이 기폭제가 됐다. 미국의 금리 인하가 증시 하락을 멈출 ‘안전판’이 될 것이란 분석이다.\\n\\n세계 각국이 금리 인하에 동참하면서 경기 부양 효과는 하반기로 갈수록 커질 것이란 관측이 나온다. 김용구 하나금융투자 연구원은 “미국의 통화정책이 더욱 완화적으로 바뀌고 있다”며 “증시가 바닥을 딛고 상승할 확률이 높아지고 있다”고 말했다.\\n\\n금리 인하로 성장주 수혜 기대\\n\\n전문가들은 “앞으로 금리 인하가 현실화될 것으로 본다면 성장주와 경기민감주 비중을 높일 필요가 있다”고 말한다. 성장주는 현재 가진 자산보다 먼 미래의 기대 이익이 높은 가치를 인정받아 금리에 민감한 반응을 보이는 경향이 있다.\\n\\n김병연 NH투자증권 연구원은 “완화적 통화정책의 혜택을 받을 수 있는 성장주로는 5세대(5G) 이동통신, 인터넷, 미디어, 게임주 등이 있다”고 말했다. 원화 약세 수혜를 받을 수 있는 정보기술(IT)주와 자동차주 등에도 관심을 둘 필요가 있다는 진단이다. 미국이 금리를 인하하면 달러 강세가 누그러지는 효과가 있다.\\n\\n삼성SDI와 LG화학 등 2차전지주는 대표적인 성장주로 꼽힌다. 전기차 시대가 열릴 것이란 기대로 높은 밸류에이션(실적 대비 주가수준)을 부여받고 있다. 금융정보업체 에프앤가이드에 따르면 삼성SDI의 올해 예상 영업이익은 7935억원이지만 2021년엔 1조3228억원에 이를 것으로 전망된다.\\n\\nLG화학도 올해 1조9311억원으로 예상되는 영업이익이 2021년엔 3조1887억원으로 늘어날 전망이다. 김지산 키움증권 연구원은 “전기차 시장이 고성장하고 있고, 에너지저장장치(ESS) 화재 후유증에서도 벗어나고 있어 2차전지주의 전망이 밝다”고 했다.\\n\\n셀트리온도 실적 회복기에 들어선 가운데 금리까지 하락한다면 주가 반등 폭이 클 것이란 분석이 나온다. 셀트리온의 올해 영업이익 컨센서스(증권사 전망치 평균)는 4169억원으로 2017년 5078억원에는 못 미칠 전망이다.\\n\\n하지만 2021년엔 영업이익이 7600억원으로 뛸 것으로 기대된다. 한병화 유진투자증권 연구원은 “미국과 유럽 시장에 성공적으로 진출한다면 램시마 등 4개 약품으로만 2023년 3조7000억원대 매출을 달성할 수 있을 것”이라며 “제2의 성장기가 기대된다”고 말했다.\\n\\n삼성전자·파트론 등 IT주 유망\\n\\n한국경제TV 전문가들도 금리 하락으로 성장주에 다시 기회가 찾아올 것으로 보고 있다. 강동진 파트너는 “금리 인하를 통한 유동성 공급은 기본적으로 고(高) 베타주(시장 대비 주가 등락이 큰 종목)인 성장주와 투기적 요소가 강한 테마주에 유리하다”며 “삼성전자와 카카오, NICE평가정보, 단기 낙폭이 컸던 KG케미칼이 유망해 보인다”고 말했다.\\n\\n박완필 파트너는 성장주 중에서도 IT 부품주를 추천했다. 미국이 중국 화웨이에 제재를 가하면서 삼성전자와 LG전자 등 국내 업체들이 반사 이익을 얻을 수 있다는 논리다. 그는 파트론과 서진시스템, 아나패스 등을 이런 종목으로 꼽았다.\\n\\n박 파트너는 “파트론은 삼성전자 스마트폰 카메라 분야 최대 수혜주”라고 했다. 서진시스템은 통신장비 등 IT 전반을 아우르는 제품 라인업으로 5G 이동통신 테마주로도 분류된다.\\n\\n안인기 파트너도 IT주인 파트론과 삼성전자, AP시스템을 추천했다. 삼성전자는 한국 대표주이자 IT업종 대표주인 까닭에 금리 인하로 외국인 자금이 국내 증시로 유입된다면 삼성전자를 사지 않을 수 없다는 설명이다. 그는 “AP시스템은 반도체 장비 대장주로, 업황이 살아나면 함께 실적 개선이 기대된다”고 말했다.\\n\\n감은숙 파트너의 추천주는 GS건설과 키움증권, 휠라코리아다. 금리 인하로 부동산 시장이 살아나면 건설주가 혜택을 받을 수 있기 때문이다. 키움증권도 금리 인하로 인한 증시 상승, 거래세 인하에 따른 긍정적 영향이 예상된다는 분석이다.\\n\\n임근호 기자 eigen@hankyung.com\\n\\n\\n\\n▶ 네이버에서 '한국경제' 구독하고 비씨카드·한경레이디스컵 KLPGA 입장권 받자\\n ▶ 한경닷컴 바로가기 ▶ 모바일한경 구독신청 \\n\\nⓒ 한국경제 & hankyung.com, 무단전재 및 재배포 금지",
                    "date" : "2019-06-09T16:13:00+09:00",
                    "image_list" : [
                      {
                        "caption" : "Getty Images Bank",
                        "image" : "https://imgnews.pstatic.net/image/015/2019/06/09/0004155554_001_20190609161302397.jpg?type=w647"
                      },
                      {
                        "image" : "https://imgnews.pstatic.net/image/015/2019/06/09/0004155554_002_20190609161302423.jpg?type=w647"
                      }
                    ]
                  }]
            }

        """
        from datetime import datetime

        data = request.get_json(silent=True, force=True)

        result = corpus_processor_utils.batch(payload=data)

        for doc in result:
            for k in doc:
                item = doc[k]

                if isinstance(item, datetime):
                    doc[k] = item.isoformat()

        msg = {
            'level': 'MESSAGE',
            'message': '코퍼스 전처리 성공',
        }
        logger.log(level=MESSAGE, msg=LogMsg(msg))

        return result, HTTPStatus.OK


def rest_api():
    """Flask 실행"""
    from flask import Flask
    from flask_cors import CORS

    app = Flask(__name__)

    # cross domain 접근 설정
    CORS(app, supports_credentials=True)

    api = Api(app=app, version='1.0', title=title, description=title)

    # 네임스페이스 등록
    api.add_namespace(health_check_ns, path='/_health_check')
    api.add_namespace(ns, path='/v1.0')

    # response 헤더에서 Server 정보 삭제
    @app.after_request
    def remove_header_info(response):
        response.headers['Server'] = ''

        return response

    # app 시작
    app.run(host='0.0.0.0', port=config['port'], debug=config['debug'])

    return
