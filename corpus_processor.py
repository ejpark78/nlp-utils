#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys
import json
import logging

# pwd = os.path.dirname(os.path.realpath(__file__))
# # sys.path.append('{}/language_utils'.format(pwd))
#
# print(pwd, file=sys.stderr)
# print(sys.path, file=sys.stderr)
#
# p = '{}'.format(pwd)
# print(p, file=sys.stderr)
# for f in os.walk(p):
#     print(f, file=sys.stderr)
#
# p = '{}/crawler'.format(pwd)
# print(p, file=sys.stderr)
# for f in os.walk(p):
#     print(f, file=sys.stderr)
#
# p = '{}/language_utils'.format(pwd)
# print(p, file=sys.stderr)
# for f in os.walk(p):
#     print(f, file=sys.stderr)

from language_utils.language_utils import LanguageUtils
from language_utils.keyword_extractor import KeywordExtractor


class CorpusProcessor:
    """
    웹 신문 기사에 형태소분석, 개체명 인식 정보를 부착
    """

    def __init__(self):
        self.util = None
        self.parser = None

        self.keywords_extractor = None

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
            if isinstance(document[k], dict) and '$date' in document[k]:
                document[k] = document[k]['$date']

        return document

    def spark_batch_stdin(self):
        """
        스파크에서 전처리 모듈 테스트, 하둡 스트리밍에서 사용

        :return:
        """
        pwd = os.path.dirname(os.path.realpath(__file__))

        # parser_path = 'parser'
        dictionary_path = 'dictionary'
        sp_config = '{}/sp_config.ini'.format(pwd)

        self.util = LanguageUtils()

        # self.util.open(engine='reviser', config='{}/reviser.ini'.format(config_path))
        self.util.open(engine='sp_utils/pos_tagger', path='{}/rsc'.format(dictionary_path))
        # self.util.open(engine='parser', path='{}'.format(parser_path))

        # "B"=야구 "E"=경제 "T"=야구 용어
        self.util.open(engine='sp_utils/ne_tagger', config=sp_config, domain='E')
        # self.util.open(engine='sp_utils/ne_tagger', config=sp_config, domain='B')
        # self.util.open(engine='sp_utils/ne_tagger', config=sp_config, domain='T')

        # 학습 기반 개체명 인식기 오픈
        # self.util.open(engine='crf_ne_tagger', model='{}/model/ner.josa.model'.format(dictionary_path))

        self.keywords_extractor = KeywordExtractor(
            entity_file_name='{}/keywords/nc_entity.txt'.format(dictionary_path))

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
            result = self.util.spark_batch(document)

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
    manager = CorpusProcessor()
    manager.spark_batch_stdin()

    return


if __name__ == "__main__":
    main()
