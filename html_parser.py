#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import logging

from bs4 import BeautifulSoup

from crawler_utils import NCCrawlerUtil
from language_utils.language_utils import LanguageUtils


class NCHtmlParser:
    """
    html 파서, 네이트 야구 뉴스를 파싱해서 기사 본문 추출
    """
    def __init__(self):
        self.util = LanguageUtils()
        
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

        NCCrawlerUtil().replace_tag(article_contents, ['caption'])
        NCCrawlerUtil().replace_tag(article_contents, ['br', 'dl', 'BR', 'DL'], '\n')
        
        self.remove_link_tag(article_contents)

        image_list = self.extract_image(article_contents)

        content_text = article_contents.get_text()

        if content_text.find('[[_RELATED_ARTICLE_]]') > 0:
            content_text = content_text[0:content_text.find('[[_RELATED_ARTICLE_]]')]

        return content_text, image_list


if __name__ == '__main__':
    pass
