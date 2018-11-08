#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import re
import sys

from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date


class HtmlParserBase(object):
    """"""

    @staticmethod
    def remove_attribute(soup, attribute_list):
        """ 속성을 삭제한다.

        :param soup: html 객체
        :param attribute_list: [onclick, style, ...]
        :return:
        """

        for tag in soup.findAll(True):
            if len(tag.attrs) == 0:
                continue

            new_attribute = {}
            for name in tag.attrs:
                if name in attribute_list:
                    continue

                if 'javascript' in tag.attrs[name] or 'void' in tag.attrs[name] or '#' in tag.attrs[name]:
                    continue

                new_attribute[name] = tag.attrs[name]

            tag.attrs = new_attribute

        return soup

    @staticmethod
    def parse_url(url):
        """ url 에서 쿼리문을 반환

        :param url: url 주소
        :return: url 쿼리 파싱 결과 반환
        """
        from urllib.parse import urlparse, parse_qs

        url_info = urlparse(url)
        result = parse_qs(url_info.query)
        for key in result:
            result[key] = result[key][0]

        base_url = '{}://{}{}'.format(url_info.scheme, url_info.netloc, url_info.path)
        return result, base_url, url_info


class MlbParkUtils(HtmlParserBase):
    """"""

    def parse_mlbpark(self, document):
        """html 문서를 파싱한다.

        :param document:

        입력 문서 구조::

            {
              "_id": "201803130014626193",
              "nick_photo": "http://dimg.donga.com/ugc/WWW/Profile/y/o/o/n/s/o/o/0/5/1/1/@/yoonsoo0511@@d.png",
              "title_header": "두산",
              "title": "17일 시범경기 티켓팅 완료했네용",
              "html_content": "<div class=\"ar_txt\" id=\"contentDetail\">블루석 예매하려고 하다가 테이블도 남았겠지? 하고 눌러보는 순간 테이블은 올 아웃.. ㅎㄷㄷ<br/>\n결국 블루 두 장 했네요.. 시범경기부터 치열할 줄이야.. ㅜㅜ</div>",
              "url": {
                "full": "http://mlbpark.donga.com/mp/b.php?id=201803130014626193&p=301&b=kbotown&m=view&select=&query=&user=&site=donga.com",
                "simple": "",
                "query": {
                  "id": "201803130014626193",
                  "m": "view",
                  "p": "301",
                  "site": "donga.com",
                  "b": "kbotown"
                }
              },
              "view_count": "363",
              "nick": "안타박건우",
              "date": {
                "$date": "2018-03-13T11:04:00.000Z"
              },
              "curl_date": {
                "$date": "2018-03-13T13:35:36.908Z"
              },
              "meta": {
                "description": "블루석 예매하려고 하다가 테이블도 남았겠지? 하고 눌러보는 순간 테이블은 올 아웃.. ㅎ…",
                "keywords": "MLBPARK",
                "writer": "안타박건우",
                "og:description": "블루석 예매하려고 하다가 테이블도 남았겠지? 하고 눌러보는 순간 테이블은 올 아웃.. ㅎ…",
                "og:title": "17일 시범경기 티켓팅 완료했네용 : MLBPARK"
              },
              "reply_count": "5",
              "reply_list": "<div class=\"reply_list\"><div class=\"other_con\" id=\"reply_12993095\"><span class=\"photo\"><a data-uid=\"caligari\" data-unick=\"%EC%B9%B4%EB%A0%88%EC%A1%B0%EC%95%84\" data-usite=\"donga.com\" href=\"#\" onclick=\"javascript:wz_usericon($(this));return false;\"><img alt=\"\" onerror=\"javascript:repairImg(this); return false;\" src=\"http://dimg.donga.com/ugc/WWW/Profile/c/a/l/i/g/a/r/i/@/@/@/@/caligari@@@@@d.png\" title=\"\"/> </a></span><div class=\"other_reply\"><div class=\"txt_box\"><div class=\"txt reply_caligari\"><span class=\"icon_arr\"></span><a alt=\"리플보기\" href=\"#\" onclick='javascript:return viewReply(\"reply_caligari\");' title=\"리플보기\"><span class=\"name\">카레조아</span><span class=\"date\">2018-03-13 11:09</span><span class=\"ip\">IP: 221.147.*.197</span></a><span class=\"re_txt\">저도 블루 ㅠ.ㅠ</span></div></div></div></div><div class=\"other_con\" id=\"reply_12993101\"><span class=\"photo\"><a data-uid=\"88seonhong\" data-unick=\"%EC%83%B7%EA%B1%B4%EC%9A%B0\" data-usite=\"donga.com\" href=\"#\" onclick=\"javascript:wz_usericon($(this));return false;\"><img alt=\"\" onerror=\"javascript:repairImg(this); return false;\" src=\"http://dimg.donga.com/ugc/WWW/Profile/8/8/s/e/o/n/h/o/n/g/@/@/88seonhong@@@d.png\" title=\"\"/> </a></span><div class=\"other_reply\"><div class=\"txt_box\"><div class=\"txt reply_88seonhong\"><span class=\"icon_arr\"></span><a alt=\"리플보기\" href=\"#\" onclick='javascript:return viewReply(\"reply_88seonhong\");' title=\"리플보기\"><span class=\"name\">샷건우</span><span class=\"date\">2018-03-13 11:09</span><span class=\"ip\">IP: 125.141.*.132</span></a><span class=\"re_txt\">축하드려요 두산이 1루 쪽인가요?</span></div></div></div></div><div class=\"other_con\" id=\"reply_12993341\"><span class=\"photo\"><a data-uid=\"freeong7\" data-unick=\"%EC%83%A4%EB%9E%84%EB%9D%BC%EB%9D%BC\" data-usite=\"donga.com\" href=\"#\" onclick=\"javascript:wz_usericon($(this));return false;\"><img alt=\"\" onerror=\"javascript:repairImg(this); return false;\" src=\"http://dimg.donga.com/ugc/WWW/Profile/f/r/e/e/o/n/g/7/@/@/@/@/freeong7@@@@@d.png\" title=\"\"/> </a></span><div class=\"other_reply\"><div class=\"txt_box\"><div class=\"txt reply_freeong7\"><span class=\"icon_arr\"></span><a alt=\"리플보기\" href=\"#\" onclick='javascript:return viewReply(\"reply_freeong7\");' title=\"리플보기\"><span class=\"name\">샤랄라라</span><span class=\"date\">2018-03-13 11:10</span><span class=\"ip\">IP: 211.196.*.209</span></a><span class=\"re_txt\">인기좌석들은 시범경기때도 먼저 나가죠~~</span></div></div></div></div><div class=\"other_con\" id=\"reply_12995924\"><span class=\"photo\"><a data-uid=\"kiss0070\" data-unick=\"%EB%91%90%EC%95%BC%EC%82%B0%EC%95%84%21%21\" data-usite=\"donga.com\" href=\"#\" onclick=\"javascript:wz_usericon($(this));return false;\"><img alt=\"\" onerror=\"javascript:repairImg(this); return false;\" src=\"http://dimg.donga.com/ugc/WWW/Profile/k/i/s/s/0/0/7/0/@/@/@/@/kiss0070@@@@@d.png\" title=\"\"/> </a></span><div class=\"other_reply\"><div class=\"txt_box\"><div class=\"txt reply_kiss0070\"><span class=\"icon_arr\"></span><a alt=\"리플보기\" href=\"#\" onclick='javascript:return viewReply(\"reply_kiss0070\");' title=\"리플보기\"><span class=\"name\">두야산아!!</span><span class=\"date\">2018-03-13 11:28</span><span class=\"ip\">IP: 211.40.*.161</span></a><span class=\"re_txt\">블루도 좋은데는 없..............<br/>\n걍, 자동배정 ㅠㅠ</span></div></div></div></div><div class=\"other_con\" id=\"reply_12996365\"><span class=\"photo\"><a data-uid=\"insertsmk\" data-unick=\"%EC%97%98%EC%A7%80%EC%95%84%EB%8B%88%EC%BF%A4\" data-usite=\"donga.com\" href=\"#\" onclick=\"javascript:wz_usericon($(this));return false;\"><img alt=\"\" onerror=\"javascript:repairImg(this); return false;\" src=\"http://dimg.donga.com/ugc/WWW/Profile/i/n/s/e/r/t/s/m/k/@/@/@/insertsmk@@@@d.png\" title=\"\"/> </a></span><div class=\"other_reply\"><div class=\"txt_box\"><div class=\"txt reply_insertsmk\"><span class=\"icon_arr\"></span><a alt=\"리플보기\" href=\"#\" onclick='javascript:return viewReply(\"reply_insertsmk\");' title=\"리플보기\"><span class=\"name\">엘지아니쿤</span><span class=\"date\">2018-03-13 11:31</span><span class=\"ip\">IP: 152.99.*.7</span></a><span class=\"re_txt\">저는 3루 블루~</span></div></div></div></div></div>"
            }

        :return:
        """
        if 'html_content' not in document:
            return None

        # 헤더가 없는 경우 추출
        if 'title_header' not in document:
            document['title_header'] = ''

        if document['title_header'] == '' and document['title_header'].find('[') > 0:
            document['title_header'] = re.sub(r'^\[(.+?)\].+$', '\g<1>', document['title']).strip()

        document['title'] = re.sub(r'^\[(.+?)\]', '', document['title']).strip()

        simple_id = document['_id']
        for t in simple_id.split('.'):
            if t.isdigit():
                simple_id = int(t)
                break

        document['_id'] = simple_id

        if 'date' in document:
            # mongoepoxrt 데이터일 경우 날짜 변환
            if '$date' in document['date']:
                document['date'] = document['date']['$date']

            dt = parse_date(document['date'])
            document['date'] = dt.strftime('%Y-%m-%d %H:%M:%S')

        if 'view_count' in document:
            view_count = document['view_count'].replace(',', '')
            document['view_count'] = int(view_count)

        # body
        soup = BeautifulSoup(document['html_content'], 'lxml')

        # 텍스트 본문
        document['contents'] = soup.get_text()

        self.remove_attribute(soup, ['onclick', 'onerror', 'role', 'style',
                                     'data-unick', 'data-uid', 'id', 'alt', 'src'])
        document['html_content'] = soup.prettify()

        # 댓글
        html_reply = document['reply_list']
        document['reply_list'], html_reply = self.parse_reply(html_reply=html_reply)

        document['html_reply'] = html_reply

        document['reply_count'] = len(document['reply_list'])

        return document

    def parse_reply(self, html_reply):
        """html 형태의 댓글을 파싱해서 반환한다.

        :param html_reply:
            댓글::

                ""
        :return:
        """
        result = []

        soup = BeautifulSoup(html_reply, 'lxml')

        for tag in soup.find_all('div', attrs={'class': 'txt_box'}):
            nick = tag.find('span', attrs={'class': 'name'}).get_text().strip()
            date = tag.find('span', attrs={'class': 'date'}).get_text().strip()

            reply_to = ''
            re_txt = []
            for txt in tag.find_all('span', attrs={'class': 're_txt'}):
                str_txt = txt.get_text()
                str_txt = re.sub(r'[/]+', '//', str_txt)

                token = str_txt.split('//', maxsplit=1)

                if len(token) == 1:
                    str_txt = token[0].strip()
                else:
                    reply_to = token[0].strip()
                    str_txt = token[1].strip()

                re_txt.append(str_txt.strip())

            # simple
            dt = parse_date(date)
            item = {
                'nick': nick,
                'date': dt.strftime('%Y-%m-%d %H:%M:%S'),
                'reply_to': reply_to,
                're_txt': ' '.join(re_txt)
            }

            result.append(item)

        self.remove_attribute(soup, ['onclick', 'onerror', 'role', 'style',
                                     'data-unick', 'data-uid', 'id', 'alt', 'src'])
        html_reply = soup.prettify()

        return result, html_reply

    def convert_mlbpark(self):
        """mlbpark 데이터 변환

        :return:
            True/False
        """
        import json

        for line in sys.stdin:
            document = json.loads(line)

            result = self.parse_mlbpark(document=document)

            if result is None:
                continue

            msg = json.dumps(result, ensure_ascii=False, sort_keys=True)
            print(msg, flush=True)

        return True


class HtmlParser(MlbParkUtils):
    """
    html 파서, 네이트 야구 뉴스를 파싱해서 기사 본문 추출
    """

    def __init__(self):
        self.args = None

        self.replace_word_list = {
            '깜짞': '깜짝',
            '솓는듯': '솟는 듯',
            '춥파츕스': '츄파춥스',
            '괞찮네': '괜찮네',
            '싪패': '실패',
            '루탘': '루타',
            '홓수비': '호수비',
            '설 ��다': '설렌다',
            '설 ��네요': '설레네요',
            '궃은': '궂은',
            '� �려내': '때려내',
            '� �스케': '슌스케',
            '규 � � 미야자키': '규슌 미야자키',
            '이�z날': '이틑날',
            '결정��다': '결정했다',
            '마��다': '마쳤다',
            '예고��다': '예고했다',
            'ʺ': '"',
            ',': ',',
            '…': '...',
            '–': '-',
            '•': '-',
            '・': '-',
            '‧': '-',
            '“': '"',
            '”': '"',
            '‛': '\'',
            'ʼ': '\'',
            'ʻ': '\'',
            '‘': '\'',
            '’': '\'',
            '`': '\'',
            '「': '[',
            '」': ']',
            '『': '[',
            '』': ']',
            '〈': '<',
            '〉': '>',
            '【': '[',
            '】': ']',
            '~': '~',
            '∼': '~',
            '◇': '-',
            '―': '-',
            '○': '-',
            '·': '-',
            '●': '-',
            '▲': '-',
            '󰋮': '-'
        }

        self.related_article_pattern = [
            '(Copyright ⓒ',
            '(끝)',
            '(대한민국 중심언론',
            '(문의_',
            '(서울=뉴스1)',
            '- \'대중경제문화지\'',
            '- Copyrights ⓒ ',
            '- Copyrightsⓒ',
            '- NO1.뉴미디어 실시간뉴스 마이데일리',
            '- 대한민국 희망언론!',
            '- 언제나 즐거운 마이데일리',
            '-무단전제 및 재배포 금지',
            '<한겨레 인기기사>',
            '[ | 페이스북]',
            '[ 인기기사 ]',
            '[[_RELATED_ARTICLE_]]',
            '[Copyright ⓒ',
            '[Copyrightⓒ',
            '[HOT NEWS]',
            '[I-Hot]',
            '[J-Hot]',
            '[YTN 화제의 뉴스]',
            '[ⓒ 뉴스1코리아(',
            '[ⓒ 매일경제',
            '[ⓒ 엑스포츠뉴스,',
            '[☞ 웹신문 보러가기]',
            '[관련 뉴스]',
            '[관련기사/많이본기사]',
            '[관련기사]',
            '[뉴스핌 Newspim]',
            '[디지털뉴스국]',
            '[머니위크 주요뉴스]',
            '[머니투데이 핫뉴스]',
            '[베스트 클릭!',
            '[본 기사는 ',
            '[사진 영상 제보받습니다]',
            '[사진] SK 와이번스 제공',
            '[서울신문 다른기사 보러가기]',
            '[스포츠조선 바로가기]',
            '[연관기사]',
            '[이 시각 많이 본 기사]',
            '[이투데이/',
            '[인기기사]',
            '[인기뉴스]',
            '[전자신문 인기 뉴스 Best 5]',
            '[최근 주요기사]',
            '[파이낸셜뉴스 핫뉴스]',
            '[한경닷컴 바로가기]',
            '[핫클릭]',
            'Copyright by ',
            'Copyrights ⓒ',
            'copyrightⓒ',
            'GoodNews paper ⓒ ',
            'IT는 아이뉴스24,',
            'MBN 화제뉴스',
            'OBS경인TV',
            'ⓒ \"젊은 파워, 모바일 넘버원 아시아투데이\"',
            'ⓒ \'젊은 파워, 모바일 넘버원 아시아투데이\'',
            'ⓒ 동아일보 & donga.com',
            'ⓒ 세계일보＆세계닷컴',
            'ⓒ 한겨레(',
            'ⓒAFPBBNews = News1',
            '▶ 관련기사 ◀',
            '▶디지털타임스 추천 주요기사',
            '▶오늘은? ',
            '◇ 관련 기사 바로가기',
            '★관련기사',
            '갓 구워낸 바삭바삭한 뉴스',
            '경향신문 [오늘의 인기뉴스]',
            '관련기사',
            '기사 제보 및 보도자료',
            '기사제보 및 보도자료',
            '뉴스1 관련뉴스',
            '뉴시스 뉴스',
            '데일리한국 인기기사',
            '사진/연합뉴스',
            '사진/연합뉴스',
            '서프라이즈(미국 애리조나주)=',
            '온라인 이슈팀',
            '온라인뉴스부',
            '한경닷컴 뉴스룸',
            '한국아이닷컴 인기기사'
        ]

    @staticmethod
    def _get_quoted_count(sentence):
        """따옴표 개수 반환

        :param sentence: 입력 문장
        :return: 따옴포의 개수
        """
        count = 0
        position = sentence.find('"')
        while position >= 0:
            count += 1
            sentence = sentence[position + 1:]
            position = sentence.find('"')

        return count

    @staticmethod
    def remove_author_header(sentence):
        """작가 헤더 제거

        :param sentence: 문장
        :return: 헤더가 제거된 문장

            예::

                (서울=연합뉴스) 김승욱 기자 =
                [스포티비뉴스=홍지수 기자]
        """
        if sentence.find('기자') < 0:
            return sentence

        import re

        result = sentence.strip()

        result = re.sub('^.{5,50}기자 =', '', result)
        result = re.sub('^\[.{5,50}기자\]', '', result)

        result = re.sub('^\[.{5,50}특파원\]', '', result)

        return result.strip()

    def split_sentence(self, paragraph):
        """ 문장 분리

        :param paragraph: 문단
        :return: 리스트 형태의 문장 분리 결과
        """
        import re
        paragraph = paragraph.strip()

        paragraph = re.sub(r'\r', '', paragraph, flags=re.MULTILINE)

        paragraph = re.sub(r'\n+', '\n', paragraph, flags=re.MULTILINE)

        paragraph = re.sub(r'[↓↑←→]', '', paragraph, flags=re.MULTILINE)
        paragraph = re.sub(r'[．]', '.', paragraph, flags=re.MULTILINE)
        paragraph = re.sub(r'[“”]', '"', paragraph, flags=re.MULTILINE)
        paragraph = re.sub(r'[‘’]', '\'', paragraph, flags=re.MULTILINE)

        paragraph = re.sub(r'(https?://.*?)(\s|\n)', '\n\g<1>\n', paragraph, flags=re.MULTILINE)
        paragraph = re.sub(r'([.?!]+)', '\g<1>\n', paragraph, flags=re.MULTILINE)
        paragraph = re.sub(r'(\[]+)', '\n\g<1>', paragraph, flags=re.MULTILINE)

        # 소숫점 처리
        max_try = 10
        pattern = re.compile(r'(\d+\.)\n+(\d+)', flags=re.MULTILINE)
        while re.search(pattern, paragraph):
            paragraph = re.sub(pattern, '\g<1>\g<2>', paragraph)
            if max_try < 0:
                break
            max_try -= 1

        paragraph = re.sub(r'(\(.+?)\n+(.+?\))', '\g<1>\g<2>', paragraph, flags=re.MULTILINE)

        pattern = re.compile(r'([0-9a-zA-Z]\.)\n+([0-9a-zA-Z])', flags=re.MULTILINE)
        max_try = 10
        while re.search(pattern, paragraph):
            paragraph = re.sub(pattern, '\g<1>\g<2>', paragraph)

            if max_try < 0:
                break
            max_try -= 1

        paragraph = re.sub(r'([.?!\]])\n+([\'\"])([,])', '\g<1>\g<2>\g<3>', paragraph, flags=re.MULTILINE)
        paragraph = re.sub(r'([.?!\]])\n+([\'\"])', '\g<1>\g<2>\n', paragraph, flags=re.MULTILINE)

        paragraph = re.sub(r'\n+([?.!]}\)])', '\g<1>', paragraph, flags=re.MULTILINE)

        # 특혜(?\n)
        paragraph = re.sub(r'([?.!])\n+(\))', '\g<1>\g<2>', paragraph, flags=re.MULTILINE)

        # 숫자 복원
        pattern = re.compile(r'(/[0-9.]+/)', flags=re.MULTILINE)
        max_try = 10
        while re.search(pattern, paragraph):
            paragraph = re.sub(pattern, r'\g<1>\n', paragraph)

            if max_try < 0:
                break
            max_try -= 1

        paragraph = paragraph.strip()

        sentence_list = []

        # 인용구 복원
        for single_sentence in paragraph.split('\n'):
            single_sentence = single_sentence.strip()
            if single_sentence == '':
                continue

            # 첫번째 문장
            if len(sentence_list) == 0:
                sentence_list.append(single_sentence)
                continue

            # 이전 문장의 qoute 개수
            count = self._get_quoted_count(sentence_list[len(sentence_list) - 1])
            if count % 2 == 1:
                # 홀수라면 합침
                sentence_list[len(sentence_list) - 1] += ' {}'.format(single_sentence)
            else:
                # 짝수거나 0 이라면 추가
                sentence_list.append(single_sentence)

        result = []
        for single_sentence in sentence_list:
            single_sentence = single_sentence.strip()

            if single_sentence != '':
                single_sentence = self.remove_author_header(single_sentence)
                result.append(single_sentence)

        return result

    def remove_article_tail(self, content_text):
        """
        관련 기사 제거

        :param content_text:
        :return:
        """
        content = content_text.strip()

        # remove tail: ad., comment, etc.
        for i, stop in enumerate(self.related_article_pattern):
            stop_position = content.find(stop)
            if stop_position > 0:
                content = content[0:stop_position]
                content = content.strip()

        return content

    def parse_content(self, content_text):
        """
        기사 본문에서 머릿말과 꼬리말 제거후 본문만 추출

        :param content_text:
        :return:
        """
        content_text = self.remove_article_tail(content_text)
        content_text = content_text.strip()

        # 인코딩 변환시 깨지는 문자 치환
        for needle in self.replace_word_list:
            if content_text.find(needle) >= 0:
                content_text = content_text.replace(needle, self.replace_word_list[needle])

        return content_text, '', ''

    def remove_link_tag(self, soup):
        """
        광고, 관련 기사 등을 제거
        관련 기사 등의 특징은 문장 전체가 링크로 이뤄진 경우가 많음.

        에러) http://sports.news.nate.com/view/20100404n06086
        본문에 링크가 있는 경우가 있음.

        :param soup:
        :return:
        """
        for tag in soup.find_all('a'):
            tag_text = tag.get_text()

            # 본문 중간의 URL 링크
            if tag_text.find('www') > 0 or tag_text.find('http') > 0:
                continue

            len_tag = len(tag_text)

            if tag.previous_element is not None:
                len_previous_element = len(self.get_tag_text(tag.previous_element))
                if len_previous_element - len_tag < 10:
                    tag = tag.previous_element

            if len_tag > 10:
                tag.replace_with('[[_RELATED_ARTICLE_]]')

        return

    @staticmethod
    def get_tag_text(tag):
        """
        텍스트 반환
        :param tag:
        :return:
        """
        import bs4

        if tag is None:
            return ''

        if isinstance(tag, bs4.element.NavigableString) is True:
            return str(tag).strip()

        return tag.get_text().strip()

    def extract_image(self, soup, delete_caption=False):
        """
        기사 본문에서 이미지와 캡션 추출

        :param soup:
        :param delete_caption:
        :return:
        """

        result = []
        for tag in soup.find_all('img'):
            next_element = tag.next_element
            # 광고일 경우 iframe 으로 text 가 널이다.
            limit = 10
            if next_element is not None:
                str_next_element = self.get_tag_text(next_element)

                try:
                    while str_next_element == '':
                        limit -= 1
                        if limit < 0:
                            break

                        if next_element.next_element is None:
                            break

                        next_element = next_element.next_element
                        str_next_element = self.get_tag_text(next_element)

                    if len(str_next_element) < 200 and str_next_element.find('\n') < 0:
                        str_caption = str_next_element

                        sentence_list = self.util.split_sentence(str_caption)
                        for sentence in sentence_list:
                            result.append({'image': tag['src'], 'caption': sentence})
                    else:
                        next_element = None
                        result.append({'image': tag['src'], 'caption': ''})
                except Exception as e:
                    logging.error('', exc_info=e)

                    print(
                        'error at extract_image',
                        sys.exc_info()[0], tag, next_element, str_next_element,
                        file=sys.stderr)
            else:
                result.append({'image': tag['src'], 'caption': ''})

            # 캡션을 본문에서 삭제
            if delete_caption is True:
                try:
                    if next_element is not None:
                        next_element.replace_with('')

                    tag.replace_with('')
                except Exception as e:
                    logging.error('', exc_info=e)

                    print('error at extract_image: remove tag', sys.exc_info()[0], tag, file=sys.stderr)

        return result

    @staticmethod
    def replace_tag(html_tag, tag_list, replacement='', attribute=None):
        """ html 태그 중 특정 태그를 삭제한다. ex) script, caption, style, ...

        :param html_tag: html 본문
        :param tag_list: 제거할 태그 목록
        :param replacement: 치환할 문자
        :param attribute: 특정 속성값 포함 여부
        :return: True/False
        """
        if html_tag is None:
            return False

        for tag_name in tag_list:
            for tag in html_tag.find_all(tag_name, attrs=attribute):
                if replacement == '':
                    tag.extract()
                else:
                    tag.replace_with(replacement)

        return True

    def get_article_body(self, html_content):
        """
        html 본문에서 텍스트만 추출 해서 반환
        관련 기사 목록 제거

        :param html_content:
        :return:
        """
        html_content = html_content.replace('</tr>', '</tr>\n')
        html_content = html_content.replace('</TR>', '</TR>\n')

        html_content = html_content.replace('</p>', '</p>\n')
        html_content = html_content.replace('</P>', '</P>\n')

        html_content = html_content.replace('<table', '\n<table')
        html_content = html_content.replace('<TABLE', '\n<TABLE')

        article_contents = BeautifulSoup(html_content, 'lxml')

        self.replace_tag(article_contents, ['caption'])
        self.replace_tag(article_contents, ['br', 'dl', 'BR', 'DL'], '\n')

        self.remove_link_tag(article_contents)

        image_list = self.extract_image(article_contents)

        content_text = article_contents.get_text()

        if content_text.find('[[_RELATED_ARTICLE_]]') > 0:
            content_text = content_text[0:content_text.find('[[_RELATED_ARTICLE_]]')]

        return content_text, image_list


def init_arguments():
    """
    옵션 설정
    :return:
    """
    import argparse

    parser = argparse.ArgumentParser(description='html parser')

    parser.add_argument('-parse_mlbpark', help='', action='store_true', default=False)

    return parser.parse_args()


def main():
    """
    :return:
    """
    args = init_arguments()

    utils = HtmlParser()

    if args.parse_mlbpark:
        utils.convert_mlbpark()

    return


if __name__ == '__main__':
    main()
