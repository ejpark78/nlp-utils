import json

import requests


def nlu_wrapper(text, url='http://172.20.40.142:80/'):
    """분석후 결과를 반환한다."""

    req_data = {
        "nlu_wrapper": {
            "option": {
                "domain": "baseball",
                "style": "literary",
                "module": ["SBD_crf", "POS", "NER"],
            }
        },
        "doc": [{
            "contents": text
        }]
    }

    meta = None
    result = []
    try:
        resp = requests.post(url=url, json=req_data, timeout=10)

        print('status_code: ', resp.status_code)

        nlu_resp = resp.json()
        if 'nlu_wrapper' in nlu_resp:
            meta = nlu_resp['nlu_wrapper']

        print('nlu_resp: ', nlu_resp)

        # 단순화시킨다.
        for doc in nlu_resp['doc']:
            for sentence in doc['sentences']:
                item = {
                    'text': '',
                    'morp_str': '',
                    'ne_str': '',
                    'depen_str': [],
                    'time_results': [],
                }

                for k in item.keys():
                    if k not in sentence:
                        continue

                    item[k] = sentence[k]

                # 시간 필드 변경
                if len(item['time_results']) > 0:
                    item['times'] = item['time_results']

                del item['time_results']

                # depen_str 변환
                if len(item['depen_str']) > 0:
                    depen = []
                    for dep in item['depen_str']:
                        depen.append(dict(zip(['index', 'head', 'morp', 'pos', 'func'], dep)))

                    item['depen'] = depen

                del item['depen_str']

                result.append(item)

        return result, meta
    except Exception as e:
        print('error: ', e)

    return result, meta


text = '''
지난해 출생아 수가 30만명대에 턱걸이하면서 합계출산율이 사상 최저인 0.98명으로 떨어졌다. 청년층의 결혼 기피 현상이 심화하는 데다 기혼 여성의 출산 연령이 높아지면서 출산율이 급락하고 있다. 올해는 상황이 더욱 심각하다. 2분기 합계출산율 잠정치는 0.91명으로 곤두박질했다. 올해 출생아 수는 30만명 선마저 붕괴할 것이 확실시된다.

통계청이 28일 발표한 2018년 출생 통계(확정)를 보면 지난해 출생아 수는 32만6800명으로 집계됐다. 1년 전보다 8.7% 줄어든 수치로, 1970년 관련 통계 작성 이래 최저다.

합계출산율은 사상 처음 1.0명 선이 무너졌다. 합계출산율은 여성 1명이 평생 낳을 것으로 예상되는 평균 출생아 수를 뜻한다. 인구 유지를 위해 필요한 합계출산율이 2.1명인 점을 감안하면, 절반에도 미치지 못한다는 얘기다. 경제협력개발기구(OECD) 36개 회원국의 평균(2017년 기준 1.65명)에 크게 미달할 뿐 아니라 맨 꼴찌다.
'''

text = "NC 다이노스의 테임즈는 오늘 시즌 10호 홈런을 쳤다."
text = "85년생 35살 입니다."

text = "[OSEN=기장(부산)박준형 기자] 30일 오후 부산 기장군 기장현대차드림볼파크에서 제29회 WBSC 기장 세계청소년야구선수권대회(18세 이하)' 일본과 스페인의 경기가 진행됐다.\n\n7회말 실점위기를 무실점으로 막은 스페인 선발투수 저스틴 루나가 동료들과 하이파이브를 하고 있다. / soul1014@osen.co.kr"

r = nlu_wrapper(text=text)

print(json.dumps(r, ensure_ascii=False, indent=4))
