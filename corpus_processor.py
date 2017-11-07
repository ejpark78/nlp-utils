#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import json
import logging

from html_parser import NCHtmlParser
from crawler_utils import NCCrawlerUtil
from keyword_extractor import NCKeywordExtractor

from language_utils.language_utils import LanguageUtils


class NCCorpusProcessor:
    """
    웹 신문 기사에 형태소분석, 개체명 인식 정보를 부착
    """

    def __init__(self):
        self.util = None
        self.parser = None

        self.keywords_extractor = None

    def get_text(self, document):
        """
        html 문서에서 텍스트를 추출하고 문장 분리 및 이미지 추출 결과 반환

        :param document:
        :return:
        """
        if self.util is None:
            self.util = LanguageUtils()

        if self.parser is None:
            self.parser = NCHtmlParser()

        if 'html_content' in document:
            content, document['image_list'] = self.parser.get_article_body(document['html_content'])

            document['content'], document['header'], document['tail'] = self.parser.parse_content(content)
            document['paragraph'], _ = self.util.split_document(document['content'])

        if '_id' not in document:
            document['_id'] = NCCrawlerUtil().get_document_id(document['url'])

        return document

    def spark_batch(self, document, max_length=2048):
        """
        스파크 전처리 모듈

        :param document:
            입력 기사

        :param max_length:
            형태소 분석시 한 문장의 최대 길이

        :return:
            전처리된 기사
        """
        try:
            document = self.get_text(document)
        except Exception as e:
            logging.error('', exc_info=e)
            msg = 'get text: {}, {}'.format(document['url'], document['_id'])
            print(msg, file=sys.stderr, flush=True)
            return {'ERROR': msg}

        pos_tagged_buffer = []

        if 'title' in document and document['title'] != '':
            sentence = document['title']

            pos_tagged, _ = self.util.run_sentence(engine='pos_tagger', sentence=sentence,
                                                   max_length=max_length)
            named_entity = {}

            if pos_tagged != '':
                named_entity = self.util.run_sentence(engine='sp_ne_tagger', sentence=sentence,
                                                      pos_tagged=pos_tagged)
                pos_tagged_buffer.append([pos_tagged])

            document['title'] = {
                'sentence': sentence,
                'pos_tagged': pos_tagged,
                'named_entity': named_entity
            }

        if 'image_list' in document:
            buf = []
            for item in document['image_list']:
                if 'caption' in item and item['caption'] != '':
                    sentence = item['caption']

                    pos_tagged, _ = self.util.run_sentence(engine='pos_tagger', sentence=sentence,
                                                           max_length=max_length)
                    named_entity = {}

                    if pos_tagged != '':
                        named_entity = self.util.run_sentence(engine='sp_ne_tagger', sentence=sentence,
                                                              pos_tagged=pos_tagged)
                        buf.append(pos_tagged)

                    document['caption'] = {
                        'sentence': sentence,
                        'pos_tagged': pos_tagged,
                        'named_entity': named_entity
                    }

            if len(buf) > 0:
                pos_tagged_buffer.append(buf)

        if 'paragraph' in document:
            document['pos_tagged'] = []
            document['named_entity'] = {}

            """
            named_entity {
                E [
                    [
                    ],
                ],
                B [
                
                ],
                T [
                
                ]
            }
            """

            for paragraph in document['paragraph']:
                pos_tagged_buf = []

                named_entity_buf = {}

                for sentence in paragraph:
                    if sentence == '':
                        continue

                    named_entity = {}
                    pos_tagged, _ = self.util.run_sentence(engine='pos_tagger', sentence=sentence,
                                                           max_length=max_length)

                    if pos_tagged != '':
                        named_entity = self.util.run_sentence(engine='sp_ne_tagger', sentence=sentence,
                                                              pos_tagged=pos_tagged)

                    pos_tagged_buf.append(pos_tagged)

                    for domain in named_entity:
                        if domain not in named_entity_buf:
                            named_entity_buf[domain] = []

                        named_entity_buf[domain].append(named_entity[domain])

                document['pos_tagged'].append(pos_tagged_buf)

                for domain in named_entity_buf:
                    if domain not in document['named_entity']:
                        document['named_entity'][domain] = []

                    document['named_entity'][domain].append(named_entity_buf[domain])

                pos_tagged_buffer.append(pos_tagged_buf)

        if self.keywords_extractor is not None and len(pos_tagged_buffer) > 0:
            words, _, _ = self.keywords_extractor.extract_keywords(pos_tagged_buffer, 'by_sentence')
            document['keywords'] = {'words': words}

        return document

    @staticmethod
    def restore_date(document):
        """
        날짜 변환, mongodb 의 경우 날짜가 $date 안에 들어가 있음.

        :param document:
            입력 기사

        :return:
            $date 가 제거된 기사
        """
        for k in document:
            try:
                if '$date' in document[k]:
                    document[k] = document[k]['$date']
            except Exception as e:
                logging.error('', exc_info=e)
                pass

        return document

    def spark_batch_stdin(self):
        """
        스파크에서 전처리 모듈 테스트, 하둡 스트리밍에서 사용

        :return:
        """
        config_path = '.'
        # parser_path = 'language_utils/parser'
        dictionary_path = 'language_utils/dictionary'

        self.util = LanguageUtils()

        # self.util.open(engine='reviser', config='{}/reviser.ini'.format(config_path))
        self.util.open(engine='pos_tagger', path='{}/rsc'.format(dictionary_path))
        # self.util.open(engine='parser', path='{}'.format(parser_path))

        # "B"=야구 "E"=경제 "T"=야구 용어
        self.util.open(engine='sp_ne_tagger', config='{}/sp_config.ini'.format(config_path), domain='E')
        self.util.open(engine='sp_ne_tagger', config='{}/sp_config.ini'.format(config_path), domain='B')
        self.util.open(engine='sp_ne_tagger', config='{}/sp_config.ini'.format(config_path), domain='T')

        # 학습 기반 개체명 인식기 오픈
        self.util.open(engine='crf_ne_tagger', model='{}/model/ner.josa.model'.format(dictionary_path))

        self.keywords_extractor = NCKeywordExtractor(entity_file_name='{}/keywords/nc_entity.txt'.format(dictionary_path))

        for line in sys.stdin:
            try:
                document = json.loads(line)
            except Exception as e:
                logging.error('', exc_info=e)
                msg = 'ERROR at json parsing: {}'.format(line)
                print(msg, file=sys.stderr, flush=True)
                continue

            document = self.restore_date(document)

            # 전처리 시작
            result = self.spark_batch(document)

            if 'date' in result and 'insert_date' not in result:
                result['insert_date'] = result['date']

            try:
                str_result = json.dumps(result, ensure_ascii=False, default=self.util.json_serial)
            except Exception as e:
                logging.error('', exc_info=e)
                msg = 'ERROR at json dumps: {}, {}'.format(document['url'], document['_id'])
                print(msg, file=sys.stderr, flush=True)
                continue

            print(str_result, flush=True)

        return


def main():
    """

    :return:
    """
    manager = NCCorpusProcessor()
    manager.spark_batch_stdin()

    return


if __name__ == "__main__":
    main()
