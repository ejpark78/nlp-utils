#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import sys

from gensim import corpora
from gensim.utils import simple_preprocess
from tqdm import tqdm

logging_opt = {
    'level': logging.INFO,
    'format': '%(message)s',
    'handlers': [logging.StreamHandler(sys.stderr)],
}

logging.basicConfig(**logging_opt)


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

    corpus = []
    for index in tqdm(index_list):
        documents = read_docs(index=index)

        my_dict = corpora.Dictionary([simple_preprocess(line) for line in documents])
        corpus += [my_dict.doc2bow(simple_preprocess(line)) for line in documents]

    # for doc in corpus:
    #     print([[mydict[id], freq] for id, freq in doc])

    # Create the TF-IDF model
    # tfidf = models.TfidfModel(corpus, smartirs='ntc')

    # Show the TF-IDF weights
    # for doc in tfidf[corpus]:
    #     print([[my_dict[id], np.around(freq, decimals=2)] for id, freq in doc])

    # with open('data/{}.tfidf.csv'.format(index), 'w') as fp:
    #     idfs = vec.idf_
    #
    #     for i, f in enumerate(vec.get_feature_names()):
    #         fp.write('{feature}\t{idf}\n'.format(feature=f, idf=idfs[i]))

    return


if __name__ == "__main__":
    main()
