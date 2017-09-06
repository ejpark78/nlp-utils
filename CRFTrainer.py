#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import time
import pycrfsuite

from CRFUtils import CRFUtils
from CRFFeature import CRFFeature


class NCNamedEntityTrainer:
    """
    개체명 인식 학습기
    """
    def __init__(self):
        pass

    @staticmethod
    def train(train_set, filename, algorithm, param):
        """
        CRF 모델 학습 함수
        """
        start_time = time.time()

        feature = CRFFeature()

        print('자질 추출', flush=True)
        x_train = [feature.sentence2features(s) for s in train_set]
        y_train = [feature.sentence2labels(s) for s in train_set]

        del train_set

        # init trainer
        crf_trainer = pycrfsuite.Trainer(algorithm=algorithm, verbose=True)
        crf_trainer.set_params(param)

        for x_seq, y_seq in zip(x_train, y_train):
            crf_trainer.append(x_seq, y_seq)

        # train model
        print('모델 학습: {}'.format(filename), flush=True)
        crf_trainer.train(filename)

        print("학습 시간: {:,} sec".format(time.time() - start_time))
        return

    @staticmethod
    def parse_argument():
        """
        프로그램 실행 인자 설정
        """
        import argparse

        arg_parser = argparse.ArgumentParser(description='개체명 인식 학습기')

        # train
        arg_parser.add_argument('-train_set', type=str, help='학습셋 파일명',
                                default='data/named_entity/baseball/train.json.bz2')

        arg_parser.add_argument('-model_name', type=str, help='모델 이름',
                                default='model/baseball.16.model')

        arg_parser.add_argument('-c1', type=float, help='c1', default=1.0)
        arg_parser.add_argument('-c2', type=float, help='c2', default=1e-3)
        arg_parser.add_argument('-max_iterations', type=int, help='max iterations', default=50)
        arg_parser.add_argument('-algorithm', type=str, choices=['lbfgs', 'l2sgd', 'ap', 'pa', 'arow'],
                                help='algorithm: {lbfgs, l2sgd, ap, pa, arow}', default='lbfgs')

        return arg_parser.parse_args()


if __name__ == '__main__':
    trainer = NCNamedEntityTrainer()
    args = trainer.parse_argument()

    util = CRFUtils()

    param = {
        'c1': args.c1,
        'c2': args.c2,
        'max_iterations': args.max_iterations,
        'feature.possible_transitions': True
    }

    if not os.path.isfile(args.model_name):
        # read corpus
        corpus = util.read_train_set(filename=args.train_set)

        # 모델 학습
        trainer.train(train_set=corpus, filename=args.model_name, algorithm=args.algorithm, param=param)
    else:
        print("model file: {} is already exists.".format(args.model_name))
