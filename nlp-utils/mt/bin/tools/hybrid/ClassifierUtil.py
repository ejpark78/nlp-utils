#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import numpy as np
import os
import pandas as pd
import pickle
import sys
import time

from sklearn import svm

from MyBaseUtil import MyBaseUtil

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding("utf-8")


class ClassifierUtil(MyBaseUtil):
    def __init__(self):
        MyBaseUtil.__init__(self)

    def make_target(self, domains=[]):
        # Make Target
        targets = None
        if len(domains) > 0:
            class_info = self.get_class_info()
            targets = np.zeros((len(domains), ), dtype="float32")

            for i, domain in enumerate(domains):
                if domain in class_info.keys():
                    targets[i] = class_info[domain]

        return targets


    def save_predict_to_text(self, predict, filename, header=False):
        class_info = self.get_class_info()
        class_index = dict(zip(class_info.values(), class_info.keys()))

        predict_csv = pd.DataFrame(columns=['predict'])
        for i, c in enumerate(predict):
            predict_csv.loc[i] = [class_index[c]]

        # predict_csv = pd.concat([predict_csv, test], axis=1)
        logging.info("save_predict_to_text: %s", filename)
        predict_csv.to_csv(
            filename, sep='\t', encoding='utf-8', header=header, index=False)

        return predict_csv


    def train_svm(self, features, targets, filename_cache=None):
        start = time.time()  # Start time

        if filename_cache is not None and os.path.isfile(filename_cache):
            logging.info("Use Previous Classifier Model: %s", filename_cache)

            svm_model = pickle.load(open(filename_cache, 'rb'))
        else:
            h = .02  # step size in the mesh
            C = 1.0  # SVM regularization parameter
            gamma = 0.7
            cache_size = 60000

            logging.info(
                "Train Classifier: h=%f, c=%f, gamma=%f, cache_size=%f",
                h, C, gamma, cache_size)

            svm_model = svm.SVC(
                kernel='rbf', cache_size=cache_size, gamma=gamma, C=C).fit(
                    features, targets)

            if filename_cache is not None:
                pickle.dump(svm_model, open(filename_cache, 'wb'))

        logging.info(
            "Time taken for train_svm: %.2f seconds.", time.time() - start)

        return svm_model


    def get_class_info(self):
        class_info = {
            u'공항': 0., u'긴급': 1., u'일반': 2., u'호텔': 3., u'식사': 4., u'쇼핑':
            5., u'관광': 6., u'교통': 7., u'취미': 8., u'통신': 9.}

        return class_info


    def predict_svm(self, model, features, filename_cache=None):
        start = time.time()  # Start time

        if filename_cache is not None and os.path.isfile(filename_cache):
            logging.info("Use pickle: %s", filename_cache)

            predict = pickle.load(open(filename_cache, 'rb'))
        else:
            logging.info("Predict SVM: %s", features.shape)

            predict = model.predict(features)
            
            if filename_cache is not None:
                pickle.dump(predict, open(filename_cache, 'wb'))

        logging.info(
            "Time taken for PredictSVM: %.2f seconds.", time.time() - start)

        return predict


    def evaluate_predict_old(self, predicts, targets):
        logging.info("Evaluate Predict")

        count_total = 0

        count = {}
        count_wrong = {}
        count_correct = {}
        for i, c in enumerate(predicts):
            self.increase(data=count, key=c)

            if c == targets[i]:
                count_total += 1
                self.increase(data=count_correct, key=c)
            else:
                self.increase(data=count_wrong, key=c)

        count_targets = {}
        for i, c in enumerate(targets):
            self.increase(data=count_targets, key=c)

        correct = float(count_total * 100)/float(len(predicts))
        print("%.2f%% = %d / %d" % (correct, count_total, len(predicts)))

        for c in sorted(count):
            domain = c

            print(
                '%s\t%.2f%% = %d / %d (wrong: %d)' % (
                    domain,
                    float(count_correct[c]) / float(count_targets[c]) * 100.,
                    count_correct[c], count_targets[c], count_wrong[c]))     


    def evaluate_predict(self, predicts, targets):
        logging.info("Evaluate Predict")

        tp = 0
        tn = 0
        fp = 0
        fn = 0

        for i, c in enumerate(predicts):
            if targets[i] == 1:
                # true
                if c == 1:
                    tp += 1
                else:
                    tn += 1
            else:
                # false
                if c == 1:
                    fp += 1
                else:
                    fn += 1

        precision = 0.
        recall = 0.
        fmeasure = 0.

        if (tp + fp) > 0:
            precision = tp / (tp + fp) * 100

        if (tp + fn) > 0:
            recall = tp / (tp + fn) * 100
        
        if (precision + recall) > 0:
            fmeasure = 2 * (precision * recall) / (precision + recall)

        print(
            'precision: %.2f, recall: %.2f, F-measure: %0.2f' % 
            (precision, recall, fmeasure,))
        
        print(
            '(tp: %d, tn: %d, fp: %d, fn: %d)' % 
            (tp, tn, fp, fn))

        return (precision, recall, tp, tn, fp, fn)


def main():
    pass


if __name__ == '__main__':
    main()

