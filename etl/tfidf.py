#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer

from tqdm import tqdm

logging.basicConfig(
    format="[%(levelname)-s] %(message)s",
    handlers=[logging.StreamHandler()],
    level=logging.INFO,
)


def read_docs(index):
    doc_list = []
    with open('data/{}.json.bz2'.format(index), 'r') as fp:
        for line in tqdm(fp.readlines()):
            doc = json.loads(line)
            doc_list.append(doc['token'])

    return doc_list


def main():
    """"""
    index_list = [
        'corpus_process-naver-economy-2010',
        'corpus_process-naver-economy-2011',
        'corpus_process-naver-economy-2012',
        'corpus_process-naver-economy-2013',
        'corpus_process-naver-economy-2014',
        'corpus_process-naver-economy-2015',
        'corpus_process-naver-economy-2016',
        'corpus_process-naver-economy-2017',
        'corpus_process-naver-economy-2018',
        'corpus_process-naver-economy-2019',
    ]

    vect_type = 'tf'
    ngram_range = (1, 3)

    for index in tqdm(list(reversed(index_list))):
        corpus = read_docs(index=index)

        if vect_type == 'tf':
            vect = CountVectorizer(
                min_df=2,
                ngram_range=ngram_range,
            )
        else:
            vect = TfidfVectorizer(
                min_df=2,
                use_idf=True,
                ngram_range=ngram_range,
                sublinear_tf=True,
            )

        vect.fit(corpus)

        with open('data/{}.{}.csv'.format(index, vect_type), 'w') as fp:
            if vect_type == 'tf':
                for w in vect.vocabulary_:
                    fp.write('{word}\t{score}\n'.format(word=w, score=vect.vocabulary_[w]))
            else:
                # 버전 0.15 이후 각 기능의 tf-idf 점수는 TfidfVectorizer 객체의 속성 idf_를 통해 검색 할 수 있습니다.
                scores = vect.idf_

                for i, f in enumerate(vect.get_feature_names()):
                    fp.write('{feature}\t{score}\n'.format(feature=f, score=scores[i]))

    return


if __name__ == "__main__":
    main()
