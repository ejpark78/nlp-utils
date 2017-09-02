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
                space['uni'].append('S_UNI[%+d]=%s' % (k, self._get_ngram(sentences, j, 1, 'BI_TAG')))
                space['bi'].append('S_BI[%+d]=%s' % (k, self._get_ngram(sentences, j, 2, 'BI_TAG')))
                space['tri'].append('S_TRI[%+d]=%s' % (k, self._get_ngram(sentences, j, 3, 'BI_TAG')))

                ngram['uni'].append('UNI[%+d]=%s' % (k, self._get_ngram(sentences, j, 1, 'WORD')))
                ngram['bi'].append('BI[%+d]=%s' % (k, self._get_ngram(sentences, j, 2, 'WORD')))
                ngram['tri'].append('TRI[%+d]=%s' % (k, self._get_ngram(sentences, j, 3, 'WORD')))
            else:
                space['uni'].append('S_UNI[%+d]=' % k)
                space['bi'].append('S_BI[%+d]=' % k)
                space['tri'].append('S_TRI[%+d]=' % k)

                ngram['uni'].append('UNI[%+d]=' % k)
                ngram['bi'].append('BI[%+d]=' % k)
                ngram['tri'].append('TRI[%+d]=' % k)

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
        return ['{:s}-{:s}'.format(feature['BI_TAG'], feature['NE_TAG']) for feature in raw_sentence]

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
        result = []

        # 어절 단위로 분리
        for token in sentence.split(' '):
            # 단어의 띄어쓰기 정보를 BI 태깅
            for i in range(0, len(token)):
                if i == 0:
                    result.append({'BI_TAG': 'B', 'WORD': token[i], 'NE_TAG': ''})
                else:
                    result.append({'BI_TAG': 'I', 'WORD': token[i], 'NE_TAG': ''})

        return result

    @staticmethod
    def merge_tagging_result(sentence_spaced, tagger_result):
        """
        태깅 입력 자질과 태깅 결과를 합침
        """
        result = []
        for i in range(0, len(tagger_result)):
            bi_tag, tag = tagger_result[i].split('-')
            result.append({
                'BI_TAG': sentence_spaced[i]['BI_TAG'],
                'WORD': sentence_spaced[i]['WORD'],
                'NE_TAG': tag})

        return result


if __name__ == '__main__':
    pass
