#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import numpy as np
import os
import pandas as pd
import pickle
import re
import sys
import linecache

from scipy import spatial

from sklearn.cluster import MiniBatchKMeans

from MyBaseUtil import MyBaseUtil

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding("utf-8")


class ClusteringUtil(MyBaseUtil):
    """ClusteringUtil class """


    def __init__(self):
        """__init__ """
        MyBaseUtil.__init__(self)


    def read_clustering_model(self, filename_a, filename_b, encoding=''):
        if encoding == '':
            kmeans_a = pickle.load(open(filename_a, 'rb'))
        else: 
            kmeans_a = pickle.load(open(filename_a, 'rb'), encoding=encoding)

        if not os.path.isfile(filename_b):
            cluster_centers = kmeans_a.cluster_centers_

            n_clusters = kmeans_a.cluster_centers_.shape[0]
        else:
            if encoding == '':
                kmeans_b = pickle.load(open(filename_b, 'rb'))
            else:
                kmeans_b = pickle.load(open(filename_b, 'rb'), encoding=encoding)

            cluster_centers = np.concatenate(
                (kmeans_a.cluster_centers_, kmeans_b.cluster_centers_),
                axis=0)

            n_clusters = kmeans_a.cluster_centers_.shape[0]
            n_clusters += kmeans_b.cluster_centers_.shape[0]

        kmeans = MiniBatchKMeans(n_clusters=n_clusters, batch_size=20000)
        kmeans.cluster_centers_ = cluster_centers

        return kmeans


    def save_predict(self, predicts, filename):
        logging.info("save_predict: %s", filename)

        # save result
        pd_predicts = pd.DataFrame(data=predicts, columns=['predict'])

        pd_predicts.loc[pd_predicts.predict == -1] = 'all'

        pd_predicts.to_csv(
            filename,
            sep='\t', encoding='utf-8', header=True, index=False)


    def get_clean_features(self, features, predicts, targets):
        clean_targets = np.zeros((len(targets), ), dtype=np.int)
        clean_features = np.zeros((len(features), len(features[0])), dtype="float32")
        
        j = 0
        for i, cluster in enumerate(predicts):
            if str(targets[i]) == str(cluster):
                clean_targets[j] = targets[i]
                clean_features[j] = features[i]
                
                j += 1

        clean_targets = np.resize(clean_targets, (j, ))
        clean_features = np.resize(clean_features, (j, len(clean_features[0])))

        return (clean_features, clean_targets)
        

    def evaluate_predict(self, predicts, targets):
        up_correct = {}
        predict_count = {}

        for i, cluster in enumerate(predicts):
            if cluster not in predict_count.keys():
                predict_count[cluster] = 1

            predict_count[cluster] += 1

            if str(targets[i]) == str(cluster):
                if cluster not in up_correct.keys():
                    up_correct[cluster] = 0

                up_correct[cluster] += 1

        correct_count = 0
        for cluster in predict_count:
            if cluster not in up_correct.keys():
                up_correct[cluster] = 0

            correct_count += up_correct[cluster]

            print("cluster: %s predict: %d correct: %.2f, %d" % (
                cluster, predict_count[cluster],
                up_correct[cluster] / predict_count[cluster],
                up_correct[cluster])
            )

        print("%.2f = %d / %d" % (
            correct_count / len(predicts),
            correct_count, len(predicts))
        )


    def predict_cluster_id(
            self, ngram_count, similarity, unk_count, tm_count):

        unk_cluster = self.sort_by_value(unk_count)

        if 0 not in unk_cluster.keys():
            return -1

        # all: 0.5473, 0.5551

        # ngram_count[10] -= 0.05 # 0.5529
        # ngram_count[10] -= 0.03 # 0.5563
        # ngram_count[10] -= 0.02 # 0.5578, 0.58 = 2903 / 5000, 464.1004
        # ngram_count[10] -= 0.01 # 0.5573
        # ngram_count[10] -= 0.04

        max_ngram = self.sort_by_value(ngram_count)
        max_similarity = self.sort_by_value(similarity)

        tm_flag = None
        if tm_count is not None:
            tm_flag = self.sort_by_value(tm_count)

        # prior
        # - tm
        # - unk_count
        # - ngram_count
        # - cosine simiarity

        cluster = -1

        if tm_flag is not None:
            for tm in sorted(tm_flag, reverse=True):
                set_stop = set(tm_flag[tm])
                if len(set_stop) == 1:
                    cluster = set_stop.pop()
                    break

                for ngram_w in sorted(max_ngram, reverse=True):
                    commons = []
                    commons.append(set(tm_flag[tm]))
                    commons.append(set(unk_cluster[0]))
                    commons.append(set(max_ngram[ngram_w]))

                    set_stop = commons[0]

                    # check commons
                    for i in range(1, len(commons)):
                        set_stop = set_stop & commons[i]

                    if len(set_stop) == 0:
                        continue

                    if len(set_stop) == 1:
                        cluster = set_stop.pop()
                        break

                    for sim in sorted(max_similarity, reverse=True):
                        commons = []
                        commons.append(set(tm_flag[tm]))
                        commons.append(set(unk_cluster[0]))
                        commons.append(set(max_ngram[ngram_w]))
                        commons.append(set(max_similarity[sim]))

                        set_stop = commons[0]

                        # check commons
                        for i in range(1, len(commons)):
                            set_stop = set_stop & commons[i]

                        if len(set_stop) > 0:
                            cluster = set_stop.pop()
                            break

                    if cluster != -1:
                        break
        else:
            for ngram_w in sorted(max_ngram, reverse=True):
                commons = []
                commons.append(set(unk_cluster[0]))
                commons.append(set(max_ngram[ngram_w]))

                set_stop = commons[0]

                # check commons
                for i in range(1, len(commons)):
                    set_stop = set_stop & commons[i]

                if len(set_stop) == 0:
                    continue

                if len(set_stop) == 1:
                    cluster = set_stop.pop()
                    break

                for sim in sorted(max_similarity, reverse=True):
                    commons = []
                    commons.append(set(unk_cluster[0]))
                    commons.append(set(max_ngram[ngram_w]))
                    commons.append(set(max_similarity[sim]))

                    set_stop = commons[0]

                    # check commons
                    for i in range(1, len(commons)):
                        set_stop = set_stop & commons[i]

                    if len(set_stop) > 0:
                        cluster = set_stop.pop()
                        break

                if cluster != -1:
                    break

        if cluster == 10:
            cluster = -1

        return cluster


    def merge_predict_features(
            self, ngram_count, similarity, unk_count, tm_count, feature_size):

        clusters = sorted(tm_count.keys())

        features = np.zeros((feature_size, ), dtype="float32")

        i = 0
        for c in clusters:
            if tm_count[c] is True:
                features[i] = 1
            i += 1

            if not np.isnan(unk_count[c]):
                features[i] = unk_count[c]
            i += 1

            if not np.isnan(ngram_count[c]):
                features[i] = ngram_count[c]
            i += 1

            for s in similarity[c]:
                if not np.isnan(s):
                    features[i] = s
                i += 1

        return features


    def get_predict_features(
            self, tok_sentences, cluster_centers,
            train_log, phrase_count, tst, feature_count):

        tm_key = ' '.join(tok_sentences)
        tm_key = self.get_tm_key(tm_key)

        unigram = tok_sentences
        ngrams = self.get_ngram(words=tok_sentences, n=7)

        parts_tst = np.hsplit(tst, feature_count)

        ret_similarity = {}

        tm_count = {}
        unk_count = {}
        similarity = {}
        ngram_count = {}
        for cluster, center in enumerate(cluster_centers):
            # check unk phrase exits
            tm_count[cluster] = False
            unk_count[cluster] = 0
            ngram_count[cluster] = 0.

            if train_log is not None:
                if tm_key != "" and cluster in train_log.keys():
                    # check sentecne in train set
                    if tm_key in train_log[cluster].keys():
                        tm_count[cluster] = True

            if cluster in phrase_count.keys():
                # check unk
                for w in unigram:
                    if w not in phrase_count[cluster].keys():
                        unk_count[cluster] += 1

                # get ngram count
                for w in ngrams:
                    if w in phrase_count[cluster].keys():
                        ngram_count[cluster] += 1.

                if len(ngrams) > 0:
                    ngram_count[cluster] = ngram_count[cluster]/len(ngrams)

            # get similarity
            if cluster not in similarity.keys():
                similarity[cluster] = []

            sim = 1. - spatial.distance.cosine(center, tst)
            if np.isnan(sim):
                sim = 0.
            similarity[cluster].append(sim)

            parts_center = np.hsplit(center, feature_count)

            for i in range(len(parts_center)):
                sim = 1. - spatial.distance.cosine(parts_center[i], parts_tst[i])
                if np.isnan(sim):
                    sim = 0.

                similarity[cluster].append(sim)

            # print(cluster, similarity[cluster])

        return(tm_count, unk_count, similarity, ngram_count)


    def PrintException(self):
        exc_type, exc_obj, tb = sys.exc_info()

        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)

        print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))


    def predict_cluster(
            self, cluster_centers, features_tst, tok_sentences, phrase_count,
            train_log, feature_count):

        feature_size = (4 + feature_count) * len(cluster_centers)

        predict_features = np.zeros(
            (len(features_tst), feature_size), dtype="float32")

        kmeans_predict = np.zeros(len(features_tst), dtype=np.int)

        print('len tok_sentences: ', len(tok_sentences), len(features_tst))
        print('len cluster_centers: ', len(cluster_centers[0]), feature_count)
        print('len tst: ', len(features_tst[0]))

        for i, tst in enumerate(features_tst):
            # try:
            (tm_count, unk_count, similarity, ngram_count) = \
                self.get_predict_features(
                    tok_sentences=tok_sentences[i], tst=tst,
                    cluster_centers=cluster_centers, train_log=train_log,
                    phrase_count=phrase_count, feature_count=feature_count)
            # except:
            #     # print(i, len(tok_sentences), type(tok_sentences), tok_sentences)
            #     # print(sys.exc_info()[0])
            #     self.PrintException()

            #     sys.exit(0)

            # get maximum cosine similarity cluster id
            predict_features[i] = self.merge_predict_features(
                ngram_count=ngram_count, similarity=similarity,
                unk_count=unk_count, tm_count=tm_count,
                feature_size=feature_size)

            if len(similarity) == 0:
                kmeans_predict[i] = -1
            else:
                # sum similarity
                similarity_single_value = {}
                for cluster in similarity.keys():
                    similarity_single_value[cluster] = 0

                    for sim in similarity[cluster]:
                        similarity_single_value[cluster] += sim

                kmeans_predict[i] = self.predict_cluster_id(
                    ngram_count=ngram_count, similarity=similarity_single_value,
                    unk_count=unk_count, tm_count=tm_count)

        return (kmeans_predict, predict_features)


    def make_feature_unit(
            self, w2vname, colname, pos, filename, 
            dname, fname, corpus, w2v_model, bigram):
        ftag = os.path.split(filename)[1]
        ftag = os.path.splitext(ftag)[0]

        allow_tags = self.parse_allow_tags(tags=pos)

        # check sentences
        if colname in corpus.keys():
            sentences = corpus[colname]
        else:
            sentences = corpus

        # make cache file name
        if dname is None or fname is None:
            filename_cache = None
        else:
            filename_cache = "%s/%s.%s.%s.pickle" % (dname, fname, colname.replace(' ', '_'), ftag)

        logging.info(
            'make_feature_unit dname: %s, %s, %s', dname, fname, ftag)
        logging.info(
            'make_feature_unit cache: %s, %s, %s', filename_cache, colname, len(sentences))

        return self.make_feature(
            filename_cache=filename_cache,
            langs=[w2vname], sentences={w2vname: sentences},
            model=w2v_model, bigram=bigram, allow_tags=allow_tags,
            ncore=12)


    def make_turn_features(
            self, filename_w2v, corpus, w2v_model, bigram,
            dname=None, fname=None):
        logging.info('make clustering feature')

        featrues_a = []
        featrues_b = []
        for w2vname, colname_a, colname_b, pos, filename in filename_w2v:
            # filename: ex) model_w2v/pos_ko.tm-2M.N.w2v
            featrues_a.append(
                self.make_feature_unit(
                    w2vname=w2vname, colname=colname_a, pos=pos, filename=filename,
                    dname=dname, fname=fname, corpus=corpus, w2v_model=w2v_model, bigram=bigram)
            )

            featrues_b.append(
                self.make_feature_unit(
                    w2vname=w2vname, colname=colname_b, pos=pos, filename=filename,
                    dname=dname, fname=fname, corpus=corpus, w2v_model=w2v_model, bigram=bigram)
            )

        return (np.concatenate(featrues_a, axis=1), np.concatenate(featrues_b, axis=1))


    def make_clustering_features(
            self, filename_w2v, corpus, w2v_model, bigram,
            dname=None, fname=None):
        logging.info('make clustering feature')

        featrues = []
        for w2vname, colname, pos, filename in filename_w2v:
            featrues.append(
                self.make_feature_unit(
                    w2vname=w2vname, colname=colname, pos=pos, filename=filename,
                    dname=dname, fname=fname, corpus=corpus, w2v_model=w2v_model, bigram=bigram)
            )

        logging.info('make_clustering_features: %s, %s', len(featrues), len(featrues[0]))

        return np.concatenate(featrues, axis=1)


def main():
    """main """


if __name__ == '__main__':
    main()

