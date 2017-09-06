#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


class CRFFeature:
    """
    개체명 자질 추출
    """
    def __init__(self):
        pass

    @staticmethod
    def _get_ngram(raw_sentence, offset, n_count, feature_type):
        """
        음절 ngram 반환
        """
        buf = []
        for i in range(n_count):
            if offset+i < len(raw_sentence):
                word = raw_sentence[offset+i]
                if feature_type in word:
                    buf.append(word[feature_type])

        return ''.join(buf)

    def _word2features(self, sentences, i):
        """
        어절 단위 자질 추출
        """
        ngram = {'uni': [], 'bi': [], 'tri': []}
        space = {'uni': [], 'bi': [], 'tri': []}

        k = -2
        for j in range(i-2, i+3, 1):
            if 0 <= j < len(sentences):
                space['uni'].append('S_UNI[{:+d}]={}'.format(k, self._get_ngram(sentences, j, 1, 'BI_TAG')))
                space['bi' ].append('S_BI[{:+d}]={}'.format(k, self._get_ngram(sentences, j, 2, 'BI_TAG')))
                space['tri'].append('S_TRI[{:+d}]={}'.format(k, self._get_ngram(sentences, j, 3, 'BI_TAG')))

                ngram['uni'].append('UNI[{:+d}]={}'.format(k, self._get_ngram(sentences, j, 1, 'WORD')))
                ngram['bi' ].append('BI[{:+d}]={}'.format(k, self._get_ngram(sentences, j, 2, 'WORD')))
                ngram['tri'].append('TRI[{:+d}]={}'.format(k, self._get_ngram(sentences, j, 3, 'WORD')))
            else:
                space['uni'].append('S_UNI[{:+d}]='.format(k))
                space['bi' ].append('S_BI[{:+d}]='.format(k))
                space['tri'].append('S_TRI[{:+d}]='.format(k))

                ngram['uni'].append('UNI[{:+d}]='.format(k))
                ngram['bi' ].append('BI[{:+d}]='.format(k))
                ngram['tri'].append('TRI[{:+d}]='.format(k))

            k += 1

        features = ngram['uni'] + ngram['bi'] + ngram['tri'] + space['uni'] + space['bi'] + space['tri']

        if i == 0:
            features.append('BOS')
        elif i == len(sentences)-1:
            features.append('EOS')

        return features

    def sentence2features(self, raw_sentence):
        """
        문장 단위 자질 추출
        """
        return [self._word2features(raw_sentence, i) for i in range(len(raw_sentence))]

    @staticmethod
    def sentence2labels(raw_sentence):
        """
        문장 단위 레이블 반환
        """
        return ['{:s}-{:s}'.format(feature['BI_TAG'], feature['TAG']) for feature in raw_sentence]

    @staticmethod
    def save_features(x_train, y_train, f_name):
        """
        자질을 파일로 저장
        """
        print('save features: {}'.format(f_name), flush=True)

        with open('{}.feature'.format(f_name), 'w') as f:
            for x_seq, y_seq in zip(x_train, y_train):
                for i in range(0, len(x_seq)):
                    f.write('%s\t%s\n' % (y_seq[i], '\t'.join(x_seq[i])))
        return

    @staticmethod
    def tag_space(sentence):
        """
        어절 단위 BI 태그 부착

        입력 예
            2014 04 01 19:45 SK 외국인 타자 루크 스캇이 SK 최정에게 원포인트 레슨을 했다.
        """
        import re

        result = []

        # 어절 단위로 분리
        for word in sentence.split(' '):
            # if re.search(r'^\d+(\.+\d+)*$', word) is not None:
            #     result.append({'BI_TAG': 'B', 'WORD': word, 'TAG': '', 'RESERVED': 'NUMBER'})
            #     continue
            # elif re.search(r'^\d+(,+\d+)*$', word) is not None:
            #     result.append({'BI_TAG': 'B', 'WORD': word, 'TAG': '', 'RESERVED': 'NUMBER'})
            #     continue

            # 단어의 띄어쓰기 정보를 BI 태깅
            for i in range(0, len(word)):
                if i == 0:
                    result.append({'BI_TAG': 'B', 'WORD': word[i], 'TAG': ''})
                else:
                    result.append({'BI_TAG': 'I', 'WORD': word[i], 'TAG': ''})

        return result

    @staticmethod
    def _append_token(bi_tag, prev_tag, result, buf):
        """
        """
        if bi_tag == 'I' and len(result) > 0:
            result[-1].append({
                'WORD': ''.join(buf),
                'TAG': prev_tag
            })
        else:
            result.append([{
                'WORD': ''.join(buf),
                'TAG': prev_tag
            }])

        return []

    def merge_tagging_result(self, sentence_spaced, crf_result):
        """
        태깅 입력 자질과 태깅 결과를 병합

        입력:
            crf_result:
                B-PERSON_PIT
                I-PERSON_PIT
                B-PERSON_PIT
                I-PERSON_PIT
                I-O
                B-O
            sentence_spaced:
                {'BI_TAG': 'B', 'WORD': 루, 'TAG': }
                {'BI_TAG': 'I', 'WORD': 크, 'TAG': }
                {'BI_TAG': 'B', 'WORD': 스, 'TAG': }
                {'BI_TAG': 'I', 'WORD': 캇, 'TAG': }
                {'BI_TAG': 'I', 'WORD': 이, 'TAG': }

        중간 출력:
            {'BI_TAG': 'B', 'WORD': 루, 'TAG': PERSON_PIT}
            {'BI_TAG': 'I', 'WORD': 크, 'TAG': PERSON_PIT}
            {'BI_TAG': 'B', 'WORD': 스, 'TAG': PERSON_PIT}
            {'BI_TAG': 'I', 'WORD': 캇, 'TAG': PERSON_PIT}
            {'BI_TAG': 'I', 'WORD': 이, 'TAG': O}

        최종 출력:
            [{'WORD': '루크 스캇', 'TAG': 'PERSON_PIT'}, {'WORD': 이}]
        """

        # crf 태깅 결과와 입력문 병합
        mid_result = []
        for i in range(0, len(crf_result)):
            bi_tag, tag = crf_result[i].split('-')

            mid_result.append({
                'BI_TAG': sentence_spaced[i]['BI_TAG'],
                'WORD': sentence_spaced[i]['WORD'],
                'TAG': tag})

        # BI_TAG 삭제
        prev_tag = mid_result[0]['TAG']

        result = []

        buf_bi = ''
        buf = []
        for token in mid_result:
            if len(buf) == 0:
                buf_bi = token['BI_TAG']
                buf.append(token['WORD'])
                continue

            # 같은 개체명 태그인 경우 합침
            if prev_tag != 'O' and token['TAG'] == prev_tag:
                buf.append(token['WORD'])
                continue

            # 같은 태그인 경우
            if token['TAG'] != prev_tag:
                buf = self._append_token(buf_bi, prev_tag, result, buf)

            # 띄어쓰기 분리
            if len(buf) > 0 and token['BI_TAG'] == 'B':
                buf = self._append_token(buf_bi, prev_tag, result, buf)

            # 버퍼링
            if len(buf) == 0:
                buf_bi = token['BI_TAG']

            buf.append(token['WORD'])
            prev_tag = token['TAG']

        # 마지막 어절
        if len(buf) > 0:
            self._append_token(buf_bi, prev_tag, result, buf)

        return result


if __name__ == '__main__':
    pass
