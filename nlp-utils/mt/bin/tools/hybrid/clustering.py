#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import numpy as np
import os
import pandas as pd
import pickle
import sys
import time

from ClusteringUtil import ClusteringUtil

from sklearn.cluster import KMeans
from sklearn.cluster import MiniBatchKMeans

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding("utf-8")

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    util = ClusteringUtil()

    # get host name ex) roh, emily
    hostname = util.get_host_name()
    logging.info('current host name is %s', hostname)

    # Set File Name
    argv = util.parse_args(
        sys.argv, ['runtype', 'corpus', 'num_clusters', 'tag', 'algorithm'])

    filename_corpus = argv['corpus']

    dbase, filename_corpus = os.path.split(filename_corpus)

    fbase, fext = os.path.splitext(filename_corpus)
    fbase, fext = os.path.splitext(fbase)

    logging.info(
        "dbase: %s, fbase: %s, filename: %s", dbase, fbase, filename_corpus)

    # set word vector file name
    filename_w2v = []
    if argv['runtype'] == 'makefeature':
        if hostname == 'roh':
            filename_w2v = [
                ('ko_tm2M_base', 'pos ko', 'base', 'model_w2v/pos_ko.tm-2M.base.w2v'),
                ('ko_tm2M_N_V', 'pos ko', 'N_V', 'model_w2v/pos_ko.tm-2M.N_V.w2v'),
                ('ko_tm2M_N', 'pos ko', 'N', 'model_w2v/pos_ko.tm-2M.N.w2v'),
                ('ko_tm2M_V', 'pos ko', 'V', 'model_w2v/pos_ko.tm-2M.V.w2v')
            ]
        elif hostname == 'emily':
            filename_w2v = [
                ('en_tm2M_base', 'pos en', 'base', 'model_w2v/pos_en.tm-2M.base.w2v'),
                ('en_tm2M_N_V', 'pos en', 'N_V', 'model_w2v/pos_en.tm-2M.N_V.w2v'),
                ('en_tm2M_N', 'pos en', 'N', 'model_w2v/pos_en.tm-2M.N.w2v'),
                ('en_tm2M_V', 'pos en', 'V', 'model_w2v/pos_en.tm-2M.V.w2v')
            ]
    else:
        filename_w2v = [
            ('ko_tm2M_base', 'pos ko', 'base', 'model_w2v/pos_ko.tm-2M.base.w2v'),
            ('ko_tm2M_N_V', 'pos ko', 'N_V', 'model_w2v/pos_ko.tm-2M.N_V.w2v'),
            ('ko_tm2M_N', 'pos ko', 'N', 'model_w2v/pos_ko.tm-2M.N.w2v'),
            ('ko_tm2M_V', 'pos ko', 'V', 'model_w2v/pos_ko.tm-2M.V.w2v'),
            # ('en_tm2M_base', 'pos en', 'base', 'model_w2v/pos_en.tm-2M.base.w2v'),
            # ('en_tm2M_N_V', 'pos en', 'N_V', 'model_w2v/pos_en.tm-2M.N_V.w2v'),
            # ('en_tm2M_N', 'pos en', 'N', 'model_w2v/pos_en.tm-2M.N.w2v'),
            # ('en_tm2M_V', 'pos en', 'V', 'model_w2v/pos_en.tm-2M.V.w2v')
        ]

    # load word2vec when makefeature, clustering
    bigram = {}
    w2v_model = {}

    logging.info('load word2vec')

    for w2vname, colname, pos, filename in filename_w2v:
        w2v_model[w2vname], bigram[w2vname] = util.build_word_vector(
            filename_cache=filename)

    # make feature
    logging.info('make feature')

    corpus = util.read_corpus(
        path=dbase, cache=dbase, filename=filename_corpus)

    featrues = []
    for w2vname, colname, pos, filename in filename_w2v:
        # filename: ex) model_w2v/pos_ko.tm-2M.N.w2v
        ftag = os.path.split(filename)[1]
        ftag = os.path.splitext(ftag)[0]

        allow_tags = util.parse_allow_tags(tags=pos)

        featrues.append(
            util.make_feature(
                filename_cache="%s/%s.%s.pickle" % (dbase, fbase, ftag),
                langs=[w2vname], sentences={w2vname: corpus[colname]},
                model=w2v_model, bigram=bigram, allow_tags=allow_tags,
                ncore=12))

    features_train = np.concatenate(featrues, axis=1)

    logging.info("Corpus Shape: %s", corpus.shape)
    logging.info("Features Train Shape: %s", features_train.shape)

    # clustering
    if argv['runtype'] == 'clustering':
        num_clusters = int(argv['num_clusters'])
        tag = argv['tag']

        filename_kmeans = "%s/%s.%s.clustering.kmeans.k-%d" % (
            dbase, fbase, tag, num_clusters)
        filename_predict = "%s/%s.%s.clustering.predict.k-%d" % (
            dbase, fbase, tag, num_clusters)

        logging.info(
            "filename kmeans, predict: %s, %s",
            filename_kmeans, filename_predict)

        start = time.time()  # Start time

        logging.info(
            "Running K means : n_cluster: %d, voca: %d",
            num_clusters, features_train.shape[0])

        if argv['algorithm'] == 'kmeans':
            kmeans = KMeans(n_clusters=num_clusters, n_jobs=1)
        else:
            kmeans = MiniBatchKMeans(n_clusters=num_clusters, batch_size=20000)

        kmeans_predict = kmeans.fit_predict(features_train)

        logging.info(
            "Time taken for K Means clustering %d seconds.",
            time.time() - start)

        pickle.dump(kmeans, open(filename_kmeans, 'wb'))
        pickle.dump(kmeans_predict, open(filename_predict, 'wb'))

        # save result
        predict = pd.DataFrame(data=kmeans_predict, columns=['predict'])

        if corpus is None:
            corpus = util.read_corpus(
                path=dbase, cache=dbase, filename=filename_corpus)

        corpus = pd.concat([predict, corpus], axis=1)
        corpus.to_csv(
            "%s.tcsv" % filename_predict,
            sep='\t', encoding='utf-8', header=True, index=False)
