#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import sys
import json
import os.path

# from NCNlpUtil import NCNlpUtil


class NCNewsKeywords:
    """
    뉴스 코퍼스에서 키워드 추출
    """

    def __init__(self, entity_file_name='dictionary/keywords/nc_entity.txt'):
        self._WORD = 0
        self._TAG = 1
        self._NE = 2

        self.entity_file_name = entity_file_name
        self.entity_dictionary = None

    def load_dictionary(self):
        """
        사전 로딩
        """
        file_name = self.entity_file_name
        if os.path.exists(file_name) is not True:
            return None

        result = {}
        with open(file_name, 'r') as fp:
            for line in fp:
                line = line.strip()
                token = line.split('\t')
                word, l1, l2 = token[0:3]

                if word not in result:
                    result[word] = []

                result[word].append('{}_{}'.format(l1, l2))

                if len(token) > 3:
                    for w in token[3:]:
                        if w not in result:
                            result[w] = []

                        result[w].append('{}_{}'.format(l1, l2))

        self.entity_dictionary = result
        return result

    def merge_entity(self, word_list):
        """
        입력된 단어 리스트에서 사전에 있는 것은 최대 길이로 매칭이 되면 합쳐서 반환
        """
        if len(word_list) < 2 or word_list[-1] is None:
            return word_list

        for i in range(0, len(word_list)):
            if i > 0:
                w = word_list[0:-i]
            else:
                w = word_list

            w_key = ''
            w_key_space = ''
            for t in w:
                up_w = t[self._WORD].upper()

                w_key += up_w
                w_key_space += up_w + ' '

            w_key_space = w_key_space.strip()

            value = None
            if self.entity_dictionary is not None and w_key in self.entity_dictionary:
                value = self.entity_dictionary[w_key]

            if self.entity_dictionary is not None and w_key_space in self.entity_dictionary:
                w_key = w_key_space
                value = self.entity_dictionary[w_key_space]

            if value is not None:
                result = [w_key, 'NNP', ','.join(value)]
                return [result] + word_list[len(word_list)-i:]

        return word_list

    def attach_single_morph(self, morph_list):
        """
        개발 형태소 중 시간을 테깅
        """
        dictionary = {
            'DATE': ['오후', '어제', '오늘', '오전']
        }

        for i, morph in enumerate(morph_list):
            for tag in dictionary:
                if morph[self._WORD] in dictionary[tag]:
                    morph[self._NE] = tag
                    morph[self._TAG] = 'NNP'

        return morph_list

    def merge_morph(self, morph_list):
        """
        의존 형태소 병합
        """
        digit_dictionary = {
            'PRICE': ['억', '원', '천', '만'],
            'SPEED': ['㎞'],
            'DATE': ['일', '월', '년', '회말']
        }

        result = []
        for i, morph in enumerate(morph_list):
            if i + 1 == len(morph_list):
                result.append(morph)
                continue

            next_morph = morph_list[i + 1]

            # 22/SN+일/NNB  140/SN+㎞/SW  1/SN+군/NNG
            if morph[self._WORD].isdigit() is True and next_morph[self._TAG] in ['NNB', 'NNG', 'SW', 'NR']:
                for tag in digit_dictionary:
                    if next_morph[self._WORD] in digit_dictionary[tag]:
                        next_morph[self._WORD] = '{}{}'.format(morph[self._WORD], next_morph[self._WORD])
                        next_morph[self._NE] = tag
                        next_morph[self._TAG] = 'NNP'
                continue

            # 병합: NN + NN + 사전, NN + X/V => V
            if morph[self._TAG][0] in ['N'] and next_morph[self._TAG][0] in ['X', 'V']:
                next_morph[self._WORD] = '{}{}'.format(morph[self._WORD], next_morph[self._WORD])
                continue

            # 승리/NNG+투수/NNG
            if morph[self._TAG] in ['NNG', 'NNP'] and next_morph[self._TAG] in ['NNG', 'NNP']:
                next_morph[self._TAG] = 'NNP'
                next_morph[self._WORD] = '{}{}'.format(morph[self._WORD], next_morph[self._WORD])
                continue

            result.append(morph)

        return result

    def merge_namaed_entity(self, words):
        """
        NE 가 연속되면 합침
        """
        result = []
        for i, w in enumerate(words):
            if i + 1 == len(words):
                result.append(w)
                continue

            next_word = words[i + 1]
            if w[self._NE] != '':
                if w[self._NE] == next_word[self._NE]:
                    next_word[self._WORD] = '{} {}'.format(w[self._WORD], next_word[self._WORD])
                    continue

                common = list(set(w[self._NE].split(',')).intersection(set(next_word[self._NE].split(','))))
                if len(common) > 0:
                    next_word[self._WORD] = '{} {}'.format(w[self._WORD], next_word[self._WORD])
                    next_word[self._NE] = ','.join(common)
                    continue

            result.append(w)

        return result

    def attach_entity(self, morph_list):
        """
        단일 워드의 개체명이 사전에 있는지 검사
        """
        result = []
        for morph in morph_list:
            key_morph = morph[self._WORD].upper()

            if self.entity_dictionary is not None and key_morph in self.entity_dictionary:
                morph[self._NE] = ','.join(self.entity_dictionary[key_morph])

            result.append(morph)

        return result

    def merge_word(self, word_list):
        """
        복함 명사 형태의 개체명 합침
        """
        buf = []
        for i in range(1, len(word_list)):
            morph_list = [word_list[i-1], word_list[i]]
            morph_list = self.merge_entity(morph_list)

            if len(morph_list) == 1:
                word_list[i] = morph_list[0]
            else:
                buf.append(word_list[i-1])

        buf.append(word_list[-1])

        return buf

    def split_sentence(self, sentence):
        """
        문장 분리
        """
        word_list = []
        for word in sentence.split(' '):
            morph = re.sub(r'(/[A-Z]{2,3})\+', '\g<1> ', word)

            morph_list = []
            for str_morph in morph.split(' '):
                morph = str_morph.split(r'/', maxsplit=1) + ['']
                morph_list.append(morph)

            morph_list = self.attach_single_morph(morph_list)
            morph_list = self.merge_morph(morph_list)
            morph_list = self.merge_entity(morph_list)
            morph_list = self.attach_entity(morph_list)

            word_list += morph_list

        # 후처리 동일한 NE 가 연속되면 합침 예) DATE
        word_list = self.merge_namaed_entity(word_list)

        # 복합 개체명 합침
        word_list = self.merge_word(word_list)

        # 튜플 형태로 변환
        result = []
        for word in word_list:
            result.append(tuple(word))

        return result

    def filter_collocations(self, collocation_list, ngram_type):
        """
        형태소 및 개체명에 따른 필터링
        """
        result = []
        for word, _ in collocation_list:
            ne_list = []
            w_list = []
            tag_list = []
            tag_header_list = []
            for w in word:
                if w is None:
                    continue

                if w[self._NE] != '':
                    ne_list.append(w[self._NE])
                else:
                    ne_list.append(None)

                w_list.append(w[self._WORD])
                tag_list.append(w[self._TAG])
                tag_header_list.append(w[self._TAG][0])

            if ngram_type == 2:
                if len(w_list[1]) < 2:
                    continue

                if ne_list[0] is None:
                    continue

                if tag_header_list[1] in ['J', 'E', 'M', 'S', 'V', 'X']:
                    continue

                if tag_list[1] in ['NNB']:
                    continue

            if ngram_type == 3:
                if len(w_list[2]) < 2:
                    continue

                if ne_list[0] is None:
                    continue

                if tag_list[1] not in ['JKO', 'JKS', 'JX'] or tag_list[2] not in ['VV', 'XSV', 'VX']:
                    continue

            result.append(word)

        return result

    def get_collocations(self, words, ngram_type, window_size, min_freq):
        """
        단어 리스트에서 연어 정보 추출
        """
        from nltk.collocations import BigramCollocationFinder, TrigramCollocationFinder, BigramAssocMeasures

        finder = None
        if ngram_type == 2:
            finder = BigramCollocationFinder.from_words(words, window_size=window_size)
        elif ngram_type == 3:
            finder = TrigramCollocationFinder.from_words(words, window_size=window_size)

        if finder is not None:
            finder.apply_freq_filter(min_freq)
            collocation = finder.score_ngrams(BigramAssocMeasures().pmi)
        else:
            collocation = [((x, None), 1) for x in words]

        return self.filter_collocations(collocation, ngram_type)

    def get_keywords(self, word_list):
        """
        명사 키워드 추출
        """
        result = []
        for word in word_list:
            if word[self._TAG] in ['NNP', 'NNG']:
                if len(word[self._WORD]) == 1:
                    continue

                result.append(word[self._WORD])

        return result

    def get_collocations_from_document(self, pos_tagged, collocation_unit, ngram_list=list()):
        """
        문서를 입력 받아 키워드와 연어 정보를 반환
        """
        sentence_count = 0
        document_words_buffer = []

        result = []
        keyword_list = []
        for i, paragraph in enumerate(pos_tagged):
            paragraph_words_buffer = []

            sentence_count += len(paragraph)
            for j, sentence in enumerate(paragraph):
                words = self.split_sentence(sentence)
                keyword_list += self.get_keywords(words)

                if len(ngram_list) > 0:
                    paragraph_words_buffer += words
                    document_words_buffer += words

                if collocation_unit.find('by_sentence') >= 0:
                    for ngram_type in ngram_list:
                        if len(words) <= ngram_type:
                            continue

                        result += self.get_collocations(
                            words=words, ngram_type=ngram_type, window_size=len(words) - 1, min_freq=1)

        #     if collocation_unit.find('by_paragraph') >= 0:
        #         for ngram_type in ngram_list:
        #             result += self.get_collocations(
        #                 words=paragraph_words_buffer, ngram_type=ngram_type,
        #                 window_size=len(paragraph_words_buffer) - 1, min_freq=1)
        #
        # if collocation_unit.find('by_document') >= 0:
        #     avg_paragraph = int(len(document_words_buffer) / sentence_count)
        #
        #     for ngram_type in ngram_list:
        #         result += self.get_collocations(
        #             words=document_words_buffer, ngram_type=ngram_type, window_size=avg_paragraph, min_freq=1)

        return result, keyword_list

    def simplify_collocations(self, collocations):
        """
        """
        simple_form = []
        collocation_index = {}
        for collocation in collocations:
            buf = []
            for word in collocation:
                if word is None:
                    continue

                if word[self._WORD] == '':
                    continue

                buf.append(word[self._WORD])
                if word[self._NE] != '':
                    for ne_tag in word[self._NE].split(','):
                        if ne_tag not in collocation_index:
                            collocation_index[ne_tag] = {}

                        collocation_index[ne_tag][word[self._WORD]] = 1

            if len(buf) == 0:
                continue
            elif len(buf) == 1:
                element = buf[0]
            else:
                element = '({})'.format(', '.join(buf))

            simple_form.append(element)

        result = {}
        for ne_tag in collocation_index:
            simple_ne_tag = ne_tag.split('_')[0]
            result[simple_ne_tag] = list(collocation_index[ne_tag].keys())

        return simple_form, result

    def extract_keywords(self, pos_tagged, collocation_unit='by_sentence', ngram_list=list()):
        """
        문서를 입력 받아 연어 정보 추가
        """
        if self.entity_dictionary is None:
            if self.load_dictionary() is None:
                msg = 'ERROR at load dictionary: {}'.format(self.entity_file_name)
                print(msg, file=sys.stderr, flush=True)
                return None, None, None

        try:
            collocations, keyword_list = self.get_collocations_from_document(pos_tagged, collocation_unit, ngram_list)

            # 문서에 첨부할 정보를 추출
            simple_form, collocations_index = self.simplify_collocations(collocations)

            return list(set(keyword_list)), simple_form, collocations_index
        except Exception:
            msg = 'ERROR at get_collocations_from_document'
            print(msg, file=sys.stderr, flush=True)

        return None, None, None

    def extract_keywords_stdin(self, collocation_unit='by_sentence'):
        """
        """
        for line in sys.stdin:
            line = line.strip()

            try:
                document = json.loads(line)
            except Exception:
                print(line, flush=True)
                continue

            if 'pos_tagged' not in document:
                print(line, flush=True)
                continue

            words, collocations, collocations_index = self.extract_keywords(
                document['pos_tagged'], collocation_unit, [1])
            print(words, collocations_index)

    @staticmethod
    def parse_argument():
        """
        파라메터 옵션 정의
        """
        import argparse

        arg_parser = argparse.ArgumentParser(description='')

        # 연어 정보 추출
        arg_parser.add_argument('-extract_keywords', help='', action='store_true', default=False)
        arg_parser.add_argument(
            '-unit', help='추출 단위 by_sentence, by_paragraph, by_document', default='by_sentence')

        return arg_parser.parse_args()


if __name__ == "__main__":
    keyword_extractor = NCNewsKeywords()
    keyword_extractor.extract_keywords_stdin()
