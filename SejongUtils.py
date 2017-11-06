#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import bz2
import json


class SejongUtils:
    """
    세종 말뭉치 변환 관련 유틸
    """

    def __init__(self):
        pass

    def convert_corpus(self, filename):
        """
        코퍼스를 읽어 드림
        """
        print('read corpus: {}'.format(filename))

        fp_out = open('result.json', 'w', encoding='utf-8')
        fp_err = open('error.txt', 'w', encoding='utf-8')
        fp_dict = open('result.dict.json', 'w', encoding='utf-8')

        morph_dict = []

        buf_dict = []
        with bz2.open(filename, 'rt') as fp:
            count = 0
            for line in fp:
                line = line.strip()

                if line == '':
                    continue

                # 원문과 태깅 결과 분리
                token = line.split('\t')

                sentence = token[0].strip()
                pos_tagged = token[1].strip()

                # try:
                sentence, pos_tagged, word_buf = \
                    self.get_syllable_based_result(sentence, pos_tagged, morph_dict=morph_dict, fp_err=fp_err)

                if len(word_buf) == 0:
                    continue

                item = {
                    'sentence': sentence,
                    'pos_tagged': {
                        'morph': pos_tagged,
                        'syllable': ' '.join(word_buf)
                    }
                }

                # 결과 저장
                str_item = json.dumps(item, ensure_ascii=False, sort_keys=True)
                fp_out.write('{}\n'.format(str_item))

                count += 1
                if count % 1000 == 0:
                    fp_out.flush()

                    str_dict = json.dumps(morph_dict, ensure_ascii=False)
                    fp_dict.write('{}\n'.format(str_dict))
                    fp_dict.flush()

                    morph_dict = []

                    print('.', end='', flush=True)

        fp_out.flush()
        fp_out.close()

        fp_err.flush()
        fp_err.close()

        # 사전 저장
        if len(morph_dict) > 0:
            str_dict = json.dumps(morph_dict, ensure_ascii=False)
            fp_dict.write('{}\n'.format(str_dict))

        fp_dict.flush()
        fp_dict.close()

        print('\n', flush=True)
        print('train set size: {:,}'.format(count), flush=True)

        return

    def get_syllable_based_result(self, sentence, pos_tagged, morph_dict=None, fp_err=None):
        """
        """

        # 이중 공백 제거
        sentence = re.sub(r'\s+', ' ', sentence)
        pos_tagged = re.sub(r'\s+', ' ', pos_tagged)

        # 공백 단위 단어 분리
        sentence_list = sentence.split(' ')
        pos_tagged_list = pos_tagged.split(' ')

        # 음절 단위 문장 생성
        word_buf = []
        for i in range(len(sentence_list)):
            try:
                source = sentence_list[i]
                target = pos_tagged_list[i]

                new_word = self.align_syllable(source, target, morph_dict)
                word_buf.append(new_word)
            except Exception as err:
                # 에러 사전 출력
                if fp_err is not None:
                    fp_err.write('{}\t{}\t{}\t{}\n'.format(sentence, pos_tagged, source, target))
                else:
                    print('{}\t{}\t{}\t{}'.format(sentence, pos_tagged, source, target), flush=True)

                return sentence, pos_tagged, []

        return sentence, pos_tagged, word_buf

    def align_syllable(self, source, target, morph_dict=None):
        """
        입력:
            word_source:
                그럼에도
            word_target:
                그렇/vj+ㅁ/en+에/pa+도/px

        형태소/품사 분리:
            morph_list:
                ['그렇', 'ㅁ', '에', '도']
            pos_list:
                ['vj', 'en', 'pa', 'px']

        출력:

        """
        # 형태소와 품사 분리
        morph_list, pos_list, _ = self.remove_tag(target)

        # backword
        source_end, morph_end = len(source) - 1, len(morph_list) - 1

        tail = []
        for i in range(source_end):
            l = len(morph_list[morph_end])

            word = source[source_end - l + 1:source_end + 1]
            if word == morph_list[morph_end]:
                tail.append('{}/{}'.format(word, pos_list[morph_end]))
                source_end -= l
                morph_end -= 1
            else:
                break

        tail.reverse()

        # forword
        # 선생님한텐  :::  선생님한테ㄴ   선생/NNG+님/XSN+한테/JKB+ㄴ/JX
        # 선생/NNG  님/XSN  한텐/JKB~JX

        head = []

        source_start, morph_start = 0, 0
        for i in range(source_end):
            l = len(morph_list[morph_start])

            word = source[source_start:source_start + l]
            if word == morph_list[morph_start]:
                head.append('{}/{}'.format(word, pos_list[morph_start]))
                source_start += l
                morph_start += 1
            else:
                break

        original_morph = []
        for i in range(morph_start, morph_end + 1):
            original_morph.append('{}/{}'.format(
                morph_list[i],
                pos_list[i]))

        complex_morph = '{}/{}~{}'.format(
            source[source_start:source_end + 1],
            pos_list[morph_start],
            pos_list[morph_end])

        if morph_dict is not None:
            if len(original_morph) > 0:
                morph_dict.append({complex_morph: '+'.join(original_morph)})

        return '+'.join(head + [complex_morph] + tail)


    @staticmethod
    def remove_tag(word):
        """
        입력:
            선생/NNG+님/XSN+한테/JKB+ㄴ/JX
        출력:
            morph_list:
                ['선생', '님', '한테', ㄴ']
            pos_list:
                ['NNG', 'XSN', 'JKB', 'JX']
            token_list:
                ['선생/NNG', '님/XSN', '한테/JKB', 'ㄴ/JX']
        """
        morph_list = []
        pos_list = []

        token_list = word.split('+')
        for token in token_list:
            morph, pos = token.rsplit('/', maxsplit=1)

            morph_list.append(morph)
            pos_list.append(pos)

        return morph_list, pos_list, token_list


if __name__ == '__main__':
    util = SejongUtils()

    # util.convert_corpus('data/sejong/test.bz2')
    # util.convert_corpus('data/sejong/sejong.sample.bz2')
    util.convert_corpus('data/sejong/sejong.bz2')
