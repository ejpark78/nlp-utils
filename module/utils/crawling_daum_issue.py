#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys
import json
import requests

from time import sleep


def curl_issue():
    """ 다음 이슈 크롤링 """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/39.0.2171.95 Safari/537.36'
    }

    url = 'http://media.daum.net/proxy/api/mc2/clusters/more.json?clusterId={id}&page={page}'

    issue_list = [
        {'168501': '세월호 침몰 사고'},
        {'263643': '삼성 뇌물 혐의 재판'},
        {'389886': '북한 핵/미사일 도발'},
        {'250306': '북한 김정남 피살 사건'},
        {'213228': '위안부 합의 갈등'},
        {'216391': '미세먼지의 습격'},
        {'318462': '5/18 진상규명 추진'},
        {'329562': '국정원/군 정치 개입 의혹'},
        {'487192': '세력 잃어가는 IS'},
        {'318219': '문재인 정부'},
        {'206510': '트럼프 러시아 스캔들'},
        {'182937': '브렉시트 협상'},
        {'215679': 'AI 스피커 전쟁'}
    ]

    for issue in issue_list:
        c_id = list(issue.keys())[0]

        page = 1

        result = {}
        while True:
            curl_url = url.format(id=c_id, page=page)
            page += 1

            page_html = requests.get(curl_url, headers=headers, allow_redirects=True, timeout=60)
            ret = page_html.json()

            if len(result) == 0:
                result = ret
            else:
                result['data'] += ret['data']

            try:
                for data in ret['data']:
                    for contents in data['contents']:
                        print(contents['id'], contents['title'])
            except Exception as e:
                pass

            if ret['hasNext'] is False:
                break

            sleep(10)

        with open('data/daum_issue/{}.json'.format(c_id), 'w') as fp:
            str_result = json.dumps(result, ensure_ascii=False, indent=4, sort_keys=True)
            fp.write(str_result + '\n')
            fp.flush()

    return True


def merge_documents(issue_id, issue_title):
    """"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/39.0.2171.95 Safari/537.36'
    }

    from bs4 import BeautifulSoup
    from pymongo import MongoClient
    from datetime import datetime

    from language_utils.language_utils import LanguageUtils

    util = LanguageUtils()

    dictionary_path = 'language_utils/dictionary'
    config_path = '.'

    util.open(engine='sp_utils/pos_tagger', path='{}/rsc'.format(dictionary_path))

    # "B"=야구 "E"=경제 "T"=야구 용어
    util.open(engine='sp_utils/ne_tagger', config='{}/sp_config.ini'.format(config_path), domain='E')

    connect = MongoClient('mongodb://frodo:27018')

    db = {
        'daum_culture': None,
        'daum_society': None,
        'daum_international': None,
        'daum_economy': None,
        'daum_politics': None,
        'daum_it': None
    }

    for db_name in db:
        db[db_name] = connect.get_database(db_name)

    # 이슈 목록 오픈
    with open('data/daum_issue/list/{}.json'.format(issue_id), 'r') as fp:
        issue = json.loads(''.join(fp.readlines()))

    # csv 핸들 파일 오픈
    fp_csv = open('data/daum_issue/{} ({}).csv'.format(issue_id, issue_title), 'w')

    contents_list = []
    for doc in issue['data']:
        for content in doc['contents']:
            item = {
                'modiDt': datetime.fromtimestamp(doc['modiDt'] / 1e3).strftime('%Y-%m-%d %H:%M:%S')
            }

            for k in content:
                if k in ['cpKorName', 'id', 'regDt', 'title']:
                    item[k] = content[k]

            dt = datetime.fromtimestamp(float(item['regDt']) / 1e3)
            collection_name = dt.strftime('%Y-%m')

            item['regDt'] = dt.strftime('%Y-%m-%d %H:%M:%S')

            for db_name in db:
                collection = db[db_name].get_collection(collection_name)

                article = collection.find_one({'_id': item['id']})
                if article is None:
                    cache_filename = 'data/daum_issue/html/{}.html'.format(item['id'])
                    if os.path.isfile(cache_filename) is True:
                        with open(cache_filename, 'r') as fp:
                            html_body = ''.join(fp.readlines())
                            soup = BeautifulSoup(html_body, 'lxml')
                    else:
                        curl_url = 'http://v.media.daum.net/v/{}'.format(item['id'])
                        html_result = requests.get(curl_url, headers=headers, allow_redirects=True, timeout=60)
                        html_body = html_result.content

                        soup = BeautifulSoup(html_body, 'lxml')

                        with open(cache_filename, 'w') as fp:
                            fp.write(str(html_result.content, encoding='utf-8'))
                            fp.flush()

                        print('curl sleep', flush=True)

                        sleep(3)

                    title = soup.select('#cSub > div.head_view > h3')
                    html_content = soup.select('#harmonyContainer')

                    article = {
                        'title': title[0].text,
                        'html_content': str(html_content[0])
                    }

                # print(article)
                article = util.spark_batch(article)
                for k in ['title', 'paragraph', 'pos_tagged', 'named_entity']:
                    if k not in article:
                        break

                    item[k] = article[k]

                break

            if 'paragraph' not in item or 'pos_tagged' not in item or 'named_entity' not in item:
                print('error: ', issue_id, item['id'], item['title'])
                # raise ValueError
                continue

            print(issue_id, item['id'], item['title']['sentence'], flush=True)

            paragraph = item['paragraph']
            pos_tagged = item['pos_tagged']
            named_entity = item['named_entity']

            for i in range(len(paragraph)):
                for j in range(len(paragraph[i])):
                    try:
                        fp_csv.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(
                            item['id'],
                            item['cpKorName'],
                            item['modiDt'],
                            item['regDt'],
                            item['title']['sentence'],
                            item['title']['pos_tagged'],
                            i+1,
                            j+1,
                            paragraph[i][j],
                            pos_tagged[i][j],
                            named_entity[i][j]
                        ))
                        fp_csv.flush()
                    except Exception as e:
                        print(e, flush=True)

            contents_list.append(item)

    fp_csv.close()

    # json 형태 저장
    with open('data/daum_issue/{} ({}).json'.format(issue_id, issue_title), 'w') as fp:
        fp.write(json.dumps(contents_list, ensure_ascii=False, sort_keys=True, indent=4))

    connect.close()

    return True


def main():
    """"""

    issue_list = [
        {'168501': '세월호 침몰 사고'},
        {'250306': '북한 김정남 피살 사건'},
        {'213228': '위안부 합의 갈등'},
        {'216391': '미세먼지의 습격'},
        {'318462': '5-18 진상규명 추진'},
        {'329562': '국정원-군 정치 개입 의혹'},
        {'487192': '세력 잃어가는 IS'},
        {'318219': '문재인 정부'},
        {'206510': '트럼프 러시아 스캔들'},
        {'182937': '브렉시트 협상'},
        {'215679': 'AI 스피커 전쟁'},
        {'263643': '삼성 뇌물 혐의 재판'},
        {'389886': '북한 핵-미사일 도발'}
    ]

    for issue in issue_list:
        for c_id in issue:
            merge_documents(c_id, issue[c_id])

    return True


if __name__ == "__main__":
    main()
