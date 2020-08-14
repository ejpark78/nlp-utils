#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime
from time import sleep
from urllib.parse import urljoin, urlencode

import requests
import urllib3

from module.dictionary_utils import DictionaryUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DictionaryEntrySearchCrawler(DictionaryUtils):
    """사전 엔트리 수집기"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.sleep_time = 5

    def get_entry_list(self, category):
        """ """
        query = {
            '_source': ['entry', 'document_id'],
            'query': {
                'bool': {
                    'must': [
                        {
                            'match': {
                                'category': category
                            }
                        },
                        {
                            'exists': {
                                'field': 'entry'
                            }
                        }
                    ],
                    'must_not': [
                        {
                            'exists': {
                                'field': 'entry_search'
                            }
                        }
                    ]
                }
            }
        }

        return self.elastic.dump(index=self.env.index, query=query)

    def extend_entry(self, entry, meta, url_info):
        """ """
        query = {
            'query': entry,
            'm': 'pc',
            'range': 'word',
            'lang': 'ko',
            'articleAnalyzer': 'true',
        }

        headers = {
            'Referer': url_info['referer']
        }
        headers.update(self.headers)

        page = 1
        max_page = 10

        while page < max_page:
            url = '{site}?{query}&page={page}'.format(
                page=page,
                site=url_info['site'],
                query=urlencode(query),
            )
            resp = requests.get(url, headers=headers, timeout=60, verify=False).json()
            if page == 1:
                max_page = resp['pagerInfo']['totalPages'] + 1

            item_list = resp['searchResultMap']['searchResultListMap']['WORD']['items']

            self.logger.log(msg={
                'message': 'extend entry',
                'entry': entry,
                'length': len(item_list),
                'current': '{:,}/{:,}'.format(page, max_page),
            })

            page += 1
            for item in item_list:
                doc = {}
                doc.update(meta)

                for k in item:
                    if k in ['rank', 'matchType', 'sourceDictnameLink', 'sourceDictnameOri', 'exactMatch',
                             'searchPhoneticSymbolList']:
                        continue

                    if item[k] is None or item[k] is 0 or item[k] is '':
                        continue

                    if isinstance(item[k], int) is False and len(item[k]) == 0:
                        continue

                    doc[k] = item[k]

                doc['_id'] = doc['entryId']

                if 'handleEntry' in doc:
                    doc['entry'] = doc['handleEntry']
                else:
                    doc['entry'] = doc['expEntry'].replace('</strong>', '').replace('<strong>', '').strip()

                doc['curl_date'] = datetime.now(self.timezone).isoformat()
                doc['destinationLink'] = urljoin(headers['Referer'], doc['destinationLink'])

                self.elastic.save_document(index=self.env.index, document=doc, delete=False)

            self.elastic.flush()
            sleep(self.sleep_time)

        return

    def read_config(self, category):
        """ """
        result = {
            '중국어': {
                'site': 'https://zh.dict.naver.com/api3/zhko/search',
                'referer': 'https://zh.dict.naver.com/',
            },
            '일본어': {
                'site': 'https://ja.dict.naver.com/api3/jako/search',
                'referer': 'https://ja.dict.naver.com/',
                'char_set': '''
                    あ い う え お か き く け こ さ し す せ そ た ち つ て と な に ぬ ね の は ひ ふ へ ほ ま み む
                    め も や ゆ よ ら り る れ ろ わ を ん が ぎ ぐ げ ご ざ じ ず ぜ ぞ だ ぢ づ で ど ば び ぶ べ ぼ
                    ぱ ぴ ぷ ぺ ぽ
                    きゃ きゅ きょ しゃ しゅ しょ ちゃ ちゅ ちょ にゃ にゅ にょ ひゃ ひゅ ひょ みゃ みゅ みょ りゃ りゅ
                    りょ ぎゃ ぎゅ ぎょ じゃ じゅ じょ びゃ びゅ びょ ぴゃ ぴゅ ぴょ
                    ア イ ウ エ オ カ キ ク ケ コ サ シ ス セ ソ タ チ ツ テ ト ナ ニ ヌ ネ ノ ハ ヒ フ ヘ ホ マ ミ ム
                    メ モ ヤ ユ ヨ ラ リ ル レ ロ ワ ヲ ン ガ ギ グ ゲ ゴ ザ
                    ジ ズ ゼ ゾ ダ ヂ ヅ デ ド バ ビ ブ ベ ボ パ ピ プ ペ ポ
                    キャ キュ キョ シャ シュ ショ チャ チュ チョ ニャ ニュ ニョ ヒャ ヒュ ヒョ ミャ ミュ ミョ
                    リャ リュ リョ ギャ ギュ ギョ ジャ ジュ ジョ ビャ ビュ ビョ ピャ ピュ ピョ
                ''',
            },
            '베트남어': {
                'site': 'https://dict.naver.com/api3/viko/search',
                'referer': 'https://dict.naver.com/',
                'char_set': '''
                    a ă â b c d đ e ê g h i k l m n o ô ơ p q r s t u ư v x y
                    A Ă Â B C D Đ E Ê G H I K L M N O Ô Ơ P Q R S T U Ư V X Y
                ''',
            },
            '인도네시아어': {
                'site': 'https://dict.naver.com/api3/idko/search',
                'referer': 'https://dict.naver.com/',
                'char_set': '''
                    A B C D E F G H I J K KH L M N NG NY O P Q R S SY T U V W X Y Z
                ''',
            },
            '태국어': {
                'site': 'https://dict.naver.com/api3/thko/search',
                'referer': 'https://dict.naver.com/',
                'char_set': '''
                    ๐ ๑ ๒ ๓ ๔ ๕ ๖ ๗ ๘ ๙ ก กอ ก๎อ กะ กั กัว กา กํา กิ กี กึ กือ กุ กู เก เก๎ เกย เกอ เกอะ เกะ เกา เกาะ
                    เกิ เกีย เกือ แก แก๎ แกะ โก โกะ ใก ไก ข ฃ ค ฅ ฆ ง จ ฉ ช ซ ฌ ญ ฎ ฏ ฐ ฑ ฒ ณ ด ต ถ ท ธ
                    น บ ป ผ ฝ พ ฟ ภ ม ย ร ฤ ฤๅ ล ฦ ฦๅ ว ศ ษ ส ห ฬ อ ฮ
                ''',
            },
            '한국어': {
                'site': 'https://ko.dict.naver.com/api3/koko/search',
                'referer': 'https://ko.dict.naver.com/',
                'char_set': '''
                    ㄱ 가 갸 거 겨 고 교 구 규 그 기 ㄲ
                    ㄴ 나 냐 너 녀 노 뇨 누 뉴 느 니
                    ㄷ 다 댜 더 뎌 도 됴 두 듀 드 디 ㄸ
                    ㄹ 라 랴 러 려 로 료 루 류 르 리
                    ㅁ 마 먀 머 며 모 묘 무 뮤 므 미
                    ㅂ 바 뱌 버 벼 보 뵤 부 뷰 브 비 ㅃ
                    ㅅ 사 샤 서 셔 소 쇼 수 슈 스 시 ㅆ
                    ㅇ 아 야 어 여 오 요 우 유 으 이
                    ㅈ 자 쟈 저 져 조 죠 주 쥬 즈 지 ㅉ
                    ㅊ 차 챠 처 쳐 초 쵸 추 츄 츠 치
                    ㅋ 카 캬 커 켜 코 쿄 쿠 큐 크 키
                    ㅌ 타 탸 터 텨 토 툐 투 튜 트 티
                    ㅍ 파 퍄 퍼 펴 포 표 푸 퓨 프 피
                    ㅎ 하 햐 허 혀 호 효 후 휴 흐 히
                    ㅀ ㅄ ㄳ ㄵ ㄶ ㄺ ㄻ ㄼ ㄽ ㄾ ㄿ
                    ㅏ ㅐ ㅑ ㅒ ㅓ ㅔ ㅕ ㅖ ㅗ ㅘ ㅙ ㅚ ㅛ ㅜ ㅝ ㅞ ㅟ ㅠ ㅡ ㅢ ㅣ
                ''',
            },
            '러시아어': {
                'site': 'https://dict.naver.com/api3/ruko/search',
                'referer': 'https://dict.naver.com/',
                'char_set': '''
                    Ё А Б В Г Д Е Ж З И Й К Л М Н О П
                    Р С Т У Ф Х Ц Ч Ш Щ Ъ Ы Ь Э Ю Я
                    а б в г д е ж з и й к л м н о п р
                    с т у ф х ц ч ш щ ъ ы ь э ю я ё
                ''',
            },
            '독일어': {
                'site': 'https://dict.naver.com/api3/deko/search',
                'referer': 'https://dict.naver.com/',
                'char_set': '''
                    A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
                    a b c d e f g h i j k l m n o p q r s t u v w x y z
                    Ä Ö Ü ß ä ö ü
                ''',
            },
            '프랑스어': {
                'site': 'https://dict.naver.com/api3/frko/search',
                'referer': 'https://dict.naver.com/',
                'char_set': '''
                    A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
                    a b c d e f g h i j k l m n o p q r s t u v w x y z
                ''',
            },
            '터키어': {
                'site': 'https://dict.naver.com/api3/trko/search',
                'referer': 'https://dict.naver.com/',
                'char_set': '''
                    A B C D E F G H I J K L M N O P R S T U V Y Z
                    a b c d e f g h i j k l m n o p r s t u v y z
                    Ç Ö Ü ç ö ü Ğ ğ İ ı Ş ş
                ''',
            },
            '이탈리아어': {
                'site': 'https://dict.naver.com/api3/itko/search',
                'referer': 'https://dict.naver.com/',
                'char_set': '''
                    0 1 2 3 4 5 6 7 8 9
                    A B C D E F G H I J L M N O P Q R S T U V Z
                    a b c d e f g h i j l m n o p q r s t u v z
                ''',
            },
            '스페인어': {
                'site': 'https://dict.naver.com/api3/esko/search',
                'referer': 'https://dict.naver.com/',
                'char_set': '''
                    0 1 2 3 4 5 6 7 8 9
                    A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
                    a b c d e f g h i j k l m n o p q r s t u v w x y z
                    Ñ ñ
                ''',
            },
            '우크라이나어': {
                'site': 'https://dict.naver.com/api3/ukko/search',
                'referer': 'https://dict.naver.com/',
                'char_set': '''
                    0 1 2 3 4 5 6 7 8 9
                    Є І Ї А Б В Г Д Е Ж З И Й К Л М Н О П
                    Р С Т У Ф Х Ц Ч Ш Щ Ь Ю Я а б в г д
                    е ж з и й к л м н о п р с т у ф х ц ч
                    ш щ ь ю я є і ї Ґ ґ
                ''',
            },
            '폴란드어': {
                'site': 'https://dict.naver.com/api3/plko/search',
                'referer': 'https://dict.naver.com/',
                'char_set': '''
                    0 1 2 3 4 5 6 7 8 9
                    A B C D E F G H I J K L M N O P R S T U W Y Z
                    a b c d e f g h i j k l m n o p r s t u w y z
                    Ó ó Ą ą Ć ć Ę ę Ł ł Ń ń Ś ś Ź ź Ż ż
                ''',
            },
            '루마니아어': {
                'site': 'https://dict.naver.com/api3/roko/search',
                'referer': 'https://dict.naver.com/',
                'char_set': '''
                    0 1 2 3 4 5 6 7 8 9
                    IA a b c d e ea f g g h i i i ia ia iu j k l m n o o p r s t u v z
                    â î în ă ș șt ț І Џ
                    А Б В Г Д Е Ж З И Й К Л М Н О П Р С Т У Ф Х Ц Ч
                    Ш Щ Ъ Ы Ь Ю а б в г д е ж з и и к л м н о о п р
                    с т у ф х ц ч ш шт ы ын ь э ю я я я
                    Ѡ Ѣ Ѧ Ѫ Ѯ Ѱ Ѳ Ѵ ӂ Ꙟ
                ''',
            },
            '영어': {
                'site': 'https://dict.naver.com/api3/enen/search',
                'referer': 'https://dict.naver.com/',
                'char_set': '''
                    0 1 2 3 4 5 6 7 8 9
                    a b c d e f g h i j k l m n o p q r s t u v w x y z
                    A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
                ''',
            }
        }

        return result[category], list(result.keys())

    def batch(self):
        """"""
        self.env = self.init_arguments()

        self.open_db(index=self.env.index)

        url_info, lang_pairs = self.read_config(category=self.env.category)

        if self.env.char_set is False or 'char_set' not in url_info:
            entry_list = self.get_entry_list(category=self.env.category)
        else:
            entry_list = [{'entry': c.strip()} for c in url_info['char_set'].split(' ') if c.strip() != '']

        i = 0

        for entry in entry_list:
            self.logger.log(msg={
                'entry': entry['entry'],
                'current': '{:,}/{:,}'.format(i, len(entry_list)),
            })

            i += 1

            self.extend_entry(
                entry=entry['entry'],
                meta={'category': self.env.category},
                url_info=url_info,
            )

            if 'document_id' not in entry:
                continue

            self.set_as_done(doc=entry, column='state')

            sleep(self.sleep_time)

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--index', default='crawler-dictionary-entry-naver', help='')
        parser.add_argument('--category', default='중국어', help='')

        parser.add_argument('--char_set', action='store_true', default=False, help='')

        return parser.parse_args()


if __name__ == '__main__':
    DictionaryEntrySearchCrawler().batch()
