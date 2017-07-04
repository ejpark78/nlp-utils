#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import os
import sys
import time
import pycrfsuite

sys.path.append(os.path.dirname(__file__))

from NCNlpUtil import NCNlpUtil


class NCNamedEntity:
    """
    개체명 인식기
    """
    def __init__(self):
        self.args = None
        self.tagger = None

        self.util = NCNlpUtil()

    @staticmethod
    def get_ngram(raw_sentence, offset, n_count, feature_type):
        """
        음절 ngram 반환
        """
        buf = []
        for i in range(n_count):
            if offset+i < len(raw_sentence):
                buf.append(raw_sentence[offset+i][feature_type])

        return ''.join(buf)

    def word2features(self, sentences, i):
        """
        어절 단위 자질 추출
        """
        ngram = {'uni': [], 'bi': [], 'tri': []}
        space = {'uni': [], 'bi': [], 'tri': []}

        k = -2
        for j in range(i-2, i+3, 1):
            if 0 <= j < len(sentences):
                space['uni'].append('S_UNI[%+d]=%s' % (k, self.get_ngram(sentences, j, 1, 'BI_TAG')))
                space['bi'].append('S_BI[%+d]=%s' % (k, self.get_ngram(sentences, j, 2, 'BI_TAG')))
                space['tri'].append('S_TRI[%+d]=%s' % (k, self.get_ngram(sentences, j, 3, 'BI_TAG')))

                ngram['uni'].append('UNI[%+d]=%s' % (k, self.get_ngram(sentences, j, 1, 'WORD')))
                ngram['bi'].append('BI[%+d]=%s' % (k, self.get_ngram(sentences, j, 2, 'WORD')))
                ngram['tri'].append('TRI[%+d]=%s' % (k, self.get_ngram(sentences, j, 3, 'WORD')))
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

    def sent2features(self, raw_sentence):
        """
        문장 단위 자질 추출
        """
        return [self.word2features(raw_sentence, i) for i in range(len(raw_sentence))]

    @staticmethod
    def sent2labels(raw_sentence):
        """
        문장 단위 레이블 반환
        """
        return ['{:s}-{:s}'.format(feature['BI_TAG'], feature['NE_TAG']) for feature in raw_sentence]

    @staticmethod
    def save_features(x_train, y_train, f_name):
        """
        자질을 파일로 저장
        """
        with open("%s.feature" % f_name, "w") as f:
            for x_seq, y_seq in zip(x_train, y_train):
                for i in range(0, len(x_seq)):
                    f.write("%s\t%s\n" % (y_seq[i], '\t'.join(x_seq[i])))
        return

    def train_model(self, train_sentences, filename_model, params=None):
        """
        CRF 모델 학습 함수
        """
        if params is None:
            params = {'c1': 1.0, 'c2': 1e-3, 'max_iterations': 50, 'feature.possible_transitions': True}

        if not os.path.isfile(filename_model):
            train_time = time.time()

            x_train = [self.sent2features(s) for s in train_sentences]
            y_train = [self.sent2labels(s) for s in train_sentences]

            del train_sentences

            # save feature file
            # self.save_features(x_train, y_train, filename_model)

            # init trainer
            # algorithm : {'lbfgs', 'l2sgd', 'ap', 'pa', 'arow'}
            trainer = pycrfsuite.Trainer(algorithm='lbfgs', verbose=True)
            trainer.set_params(params)

            for x_seq, y_seq in zip(x_train, y_train):
                trainer.append(x_seq, y_seq)

            # train model
            trainer.train(filename_model)
            print("train time: {}".format(self.util.sec2time(time.time()-train_time)))
        else:
            print("model file: {} is already exists.".format(filename_model))

        return

    def parse_xml_format(self, ne_tagged):
        """
        NE xml 형식을 변환

        입력:
            ESPN <QuotID=1> <NE L1="PERSON" L2="PIT">류현진</NE>이 체인지업 외에도 또 하나의 <QuotID=2>을 지니게 됐다.
        출력:
            [{'WORD': ESPN}]
            [{'WORD': 류현진, 'L1': 'PERSON', 'L2': 'PIT'}, {'WORD': 이}]
            [{'WORD': 체인지업}]
            ...
        """
        token_list = self.split_xml_sentence(ne_tagged)

        # "ESPN",
        # "<QuotID=1>",
        # "<NE L1=\"PERSON\" L2=\"PIT\">류현진</NE>이",
        # "체인지업",

        result = []
        for token in token_list:
            buf = []
            if token.find('</NE>') > 0:
                # "<NE L1=\"PERSON\" L2=\"PIT\">류현진</NE>이",
                tag_start = False

                xml_tag = ''
                l1 = ''
                l2 = ''

                i = 0
                while i < len(token):
                    if token[i:i+4] == '<NE ':
                        tag_start = True
                        xml_tag = ''

                    if tag_start is True and token[i] == '>':
                        ne_tag = re.sub(r'<NE L1="(.+?)" L2="(.+?)">', '\g<1>\t\g<2>', xml_tag + token[i])
                        l1, l2 = ne_tag.split('\t')

                        xml_tag = ''
                        tag_start = False
                        i += 1
                        continue

                    if token[i:i+5] == '</NE>':
                        i += 5
                        continue

                    if tag_start is True:
                        xml_tag += token[i]
                        i += 1
                        continue

                    buf.append({'WORD': token[i], 'L1': l1, 'L2': l2})
                    i += 1

                continue

            if token[0] == '<' and token[-1] == '>':
                buf.append({'WORD': token})
                continue

            buf.append({'WORD': token})
            result.append(buf)

        return result

    @staticmethod
    def split_xml_sentence(ne_tagged):
        """
        입력문장을 어절 단위로 분리
        """
        result = []

        tag_start = False
        for token in ne_tagged.split(' '):
            if tag_start is True:
                result[len(result) - 1] += ' ' + token
            else:
                result.append(token)

            if token == '<NE':
                tag_start = True
            elif token.find('</NE>') > 0:
                tag_start = False

        return result

    def split_ne_tag(self, ne_tagged):
        """
        NE tag 분리

        입력:
            ESPN <QuotID=1> <NE L1="PERSON" L2="PIT">류현진</NE>이 체인지업 외에도 또 하나의 <QuotID=2>을 지니게 됐다.
        출력:
            {'BI_TAG': 'B', 'WORD': <QuotID=1>, 'NE_TAG':O}

            {'BI_TAG': 'B', 'WORD': 류, 'NE_TAG': PERSON_PIT}
            {'BI_TAG': 'I', 'WORD': 현, 'NE_TAG': PERSON_PIT}
            {'BI_TAG': 'I', 'WORD': 진, 'NE_TAG': PERSON_PIT}
            {'BI_TAG': 'I', 'WORD': 이, 'NE_TAG': O}

        """
        token_list = self.split_xml_sentence(ne_tagged)

        # "ESPN",
        # "<QuotID=1>",
        # "<NE L1=\"PERSON\" L2=\"PIT\">류현진</NE>이",
        # "체인지업",

        result = []
        for token in token_list:
            bi_tag = 'B'

            if token.find('</NE>') > 0:
                # "<NE L1=\"PERSON\" L2=\"PIT\">류현진</NE>이",

                tag_start = False

                xml_tag = ''
                ne_tag = 'O'

                i = 0
                while i < len(token):
                    if token[i:i+4] == '<NE ':
                        tag_start = True
                        ne_tag = 'O'
                        xml_tag = ''

                    if tag_start is True and token[i] == '>':
                        ne_tag = re.sub(r'<NE L1="(.+?)" L2="(.+?)">', '\g<1>_\g<2>', xml_tag + token[i])

                        xml_tag = ''
                        tag_start = False
                        i += 1
                        continue

                    if token[i:i+5] == '</NE>':
                        i += 5
                        ne_tag = 'O'
                        continue

                    if tag_start is True:
                        xml_tag += token[i]
                        i += 1
                        continue

                    result.append({'BI_TAG': bi_tag, 'WORD': token[i], 'NE_TAG': ne_tag})
                    bi_tag = 'I'
                    i += 1

                continue

            if token[0] == '<' and token[-1] == '>':
                result.append({'BI_TAG': bi_tag, 'WORD': token, 'NE_TAG': 'O'})
                continue

            for i in range(len(token)):
                result.append({'BI_TAG': bi_tag, 'WORD': token[i], 'NE_TAG': 'O'})
                bi_tag = 'I'

        return result

    def read_corpus(self, host_name, port, db_name, collection_name, sample_size=-1):
        """
        학습셋 말뭉치 디비에서 학습셋을 읽음.
        """
        from pymongo import MongoClient

        connect = MongoClient('mongodb://{}:{}'.format(host_name, port))
        db = connect[db_name]

        cursor = db[collection_name].find({})

        corpus = []
        for document in cursor:
            corpus.append(self.split_ne_tag(document['ne_tagged']))

        cursor.close()
        connect.close()

        return corpus

    # def read_corpus_set(self, corpus_set_dir, filename_corpus, sample_size, max_fold):
    #     """
    #     데이터 베이스에서 읽어온 학습셋 집합을 5개(max_fold)로 나눠 피클로 저장
    #     """
    #     import pickle
    #     import numpy
    #
    #     filename_corpus_sets = "{}/corpus_sets.pickle".format(corpus_set_dir)
    #
    #     if not os.path.isfile(filename_corpus_sets):
    #         corpus = self.read_corpus(filename_corpus, sample_size)
    #
    #         if max_fold > 0:
    #             corpus_sets = numpy.array_split(corpus, max_fold)
    #         else:
    #             corpus_sets = corpus
    #
    #         pickle.dump(corpus_sets, open(filename_corpus_sets, 'wb'))
    #     else:
    #         corpus_sets = pickle.load(open(filename_corpus_sets, 'rb'))
    #
    #     return corpus_sets
    #
    #     return None

    @staticmethod
    def get_model_tag_name(n, params):
        """
        프로그램 실행 인자로 파일명 생성
        """
        return "fold={},c1={},c2={},max_itr={}".format(
            n, params['c1'], params['c2'], params['max_iterations'])

    @staticmethod
    def get_model_filename(model_dir, model_tag_name, n=-1):
        """
        인자에 따른 모델 저장 위치 및 파일명 반환
        """
        if n == -1:
            return '%s/%s-full.model' % (model_dir, model_tag_name)

        return '%s/%s.model' % (model_dir, model_tag_name)

    def train_single_model(self):
        """
        단일 모델 학습
        """
        model_dir = 'model/sample_size={}/algorithm={}'.format(self.args.sample_size, self.args.algorithm)

        # create model dir.
        if not os.path.exists(model_dir):
            try:
                os.makedirs(model_dir)
            except:
                pass

        # params
        params = {
            'c1': self.args.c1,
            'c2': self.args.c2,
            'max_iterations': self.args.max_iterations,
            'feature.possible_transitions': True
        }

        # read corpus set
        corpus_sets = self.read_corpus(host_name='gollum', port=27017,
                                       db_name='named_entity', collection_name='baseball',
                                       sample_size=self.args.sample_size)
        model_tag_name = self.get_model_tag_name(-1, params)
        filename_model = self.get_model_filename(model_dir, model_tag_name, -1)

        self.train_model(corpus_sets, filename_model, params)
        return

    def train_cross_validation(self, corpus_sets, model_dir, max_fold, params):
        """
        n-fold 크로스 학습 및 평가
        """
        from multiprocessing import Process

        jobs = []

        # n-fold
        for i in range(0, max_fold):
            train_sentences = []
            for j in range(max_fold):
                if i != j:
                    train_sentences.extend(corpus_sets[j])

            model_tag_name = self.get_model_tag_name(i, params)
            filename_model = self.get_model_filename(model_dir, model_tag_name, i)

            jobs.append(Process(
                target=self.train_model,
                args=(train_sentences, filename_model, params)
            ))

        # full set
        train_sentences = []
        for i in range(max_fold):
            train_sentences.extend(corpus_sets[i])

        model_tag_name = self.get_model_tag_name('full', params)
        filename_model = self.get_model_filename(model_dir, model_tag_name)

        jobs.append(Process(
            target=self.train_model,
            args=(train_sentences, filename_model, params)
        ))

        # run
        for j in jobs:
            j.start()

        for j in jobs:
            j.join()

        return

    def evaluate_model(self, filename_model, test_sentences, process_id=None, process_return=None):
        """
        모델 평가
        """
        self.open(filename_model)

        # evaluation: https://ko.wikipedia.org/wiki/정밀도와_재현율
        count_tf, count_fp, count_tn, count_fn = 0, 0, 0, 0
        total, count_correct = 0, 0
        for i in range(0, len(test_sentences)):
            y_test = self.sent2labels(test_sentences[i])

            x_test = self.sent2features(test_sentences[i])
            result = self.tagger.tag(x_test)

            for j in range(0, len(result)):
                x_bi_tag, x_ne_tag = result[j].split('-')
                y_bi_tag, y_ne_tag = y_test[j].split('-')

                total += 1
                if x_ne_tag != 'O':
                    if result[j] == y_test[j]:
                        count_tf += 1
                    else:
                        count_fp += 1
                else:
                    if y_ne_tag != 'O':
                        count_fn += 1
                    else:
                        count_tn += 1

            # print
            tagged_sentence = self.merge_tagging_result(test_sentences[i], result)
            target_sentence = self.merge_tagging_result(test_sentences[i], y_test)

            if target_sentence != tagged_sentence:
                print('{}\n{}\n'.format(self.to_string(target_sentence), self.to_string(tagged_sentence)))

        precision = count_tf / (count_tf + count_fp) if (count_tf + count_fp) > 0 else 0
        recall = count_tf / (count_tf + count_fn) if (count_tf + count_fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        # save result
        with open("{}.score".format(filename_model), "w") as f:
            msg = 'precision: {:.2f}%, recall: {:.2f}%, f1: {:.2f}%, count: {:,} total: {:,}'.format(
                precision * 100, recall * 100, f1 * 100, count_tf + count_tn, len(test_sentences))

            f.write(msg)
            print(msg)

        # multi-core return
        if process_return is not None:
            process_return.append((process_id, precision, recall, f1))

        return precision, recall, f1

    def eval_cross_validation_model(self, model_dir, corpus_sets, max_fold, params):
        """
        cross 검증
        """
        from multiprocessing import Manager
        from multiprocessing import Process

        start_time = time.time()

        # run multi-core
        jobs = []
        manager = Manager()
        return_results = manager.list()

        # n-fold
        total = 0
        for i in range(0, max_fold):
            total += len(corpus_sets[i])

            model_tag_name = self.get_model_tag_name(i, params)
            filename_model = self.get_model_filename(model_dir, model_tag_name, i)

            jobs.append(Process(
                target=self.evaluate_model,
                args=(filename_model, corpus_sets[i], i, return_results)
            ))

        # run
        for j in jobs:
            j.start()

        for j in jobs:
            j.join()

        # merge result
        model_tag_name = self.get_model_tag_name('full', params)
        with open("{}/{}.score".format(model_dir, model_tag_name), "w") as f:
            cnt = 0
            total = {'precision': 0, 'recall': 0, 'f1': 0}

            for result in sorted(return_results):
                cnt += 1
                process_id, precision, recall, f1 = result

                total['precision'] += precision
                total['recall'] += recall
                total['f1'] += f1

                msg = 'process: {} = precision: {:.2f}% recall: {:.2f}% f1: {:.2f}%'.format(
                    process_id, precision * 100, recall * 100, f1 * 100)

                f.write(msg)
                print(msg)

            # 평균 계산
            if cnt > 0:
                total['precision'] = total['precision'] / cnt * 100
                total['recall'] = total['recall'] / cnt * 100
                total['f1'] = total['f1'] / cnt * 100

            msg = 'total => precision: {:.2f}% recall: {:.2f}% f1: {:.2f}%, time: %s'.format(
                total['precision'], total['recall'], total['f1'], self.util.sec2time(time.time()-start_time))

            f.write(msg)
            print(msg)

        return

    def cross_evaluation(self):
        model_dir = 'model/sample_size={}/algorithm={}'.format(self.args.sample_size, self.args.algorithm)
        corpus_set_dir = 'model/sample_size={}'.format(self.args.sample_size)

        # create model dir.
        if not os.path.exists(model_dir):
            try:
                os.makedirs(model_dir)
            except:
                pass

        # params
        params = {
            'c1': self.args.c1,
            'c2': self.args.c2,
            'max_iterations': self.args.max_iterations,
            'feature.possible_transitions': True
        }

        # # read corpus set
        # corpus_sets = self.read_corpus_set(
        #     corpus_set_dir, self.args.corpus, self.args.sample_size, self.args.max_fold)
        #
        # # train
        # self.train_cross_validation(
        #     corpus_sets, model_dir, self.args.max_fold, params)
        #
        # # eval
        # self.eval_cross_validation_model(
        #     model_dir, corpus_sets, self.args.max_fold, params)

        return

    @staticmethod
    def to_string(raw_sentence, ne_info=None):
        """
        CRF 태깅 결과를 텍스트 형태로 반환

            {'BI_TAG': 'B', 'WORD': 루, 'NE_TAG': PERSON_PIT}
            {'BI_TAG': 'I', 'WORD': 크, 'NE_TAG': PERSON_PIT}
            {'BI_TAG': 'B', 'WORD': 스, 'NE_TAG': PERSON_PIT}
            {'BI_TAG': 'I', 'WORD': 캇, 'NE_TAG': PERSON_PIT}
            {'BI_TAG': 'I', 'WORD': 이, 'NE_TAG': O}

            {'BI_TAG': 'B', 'WORD': 루크 스캇, 'NE_TAG': PERSON_PIT}
            {'BI_TAG': 'I', 'WORD': 이, 'NE_TAG': O}

            <NE L1="PERSON" L2="PIT">루크 스캇</NE>이
        """
        prev = ''
        buf = []
        for token in raw_sentence:
            if token['NE_TAG'] != 'O' and token['NE_TAG'] == prev:
                if token['BI_TAG'] == 'B':
                    buf[len(buf)-1]['WORD'] += ' ' + token['WORD']
                else:
                    buf[len(buf)-1]['WORD'] += token['WORD']

                prev = token['NE_TAG']
                continue

            prev = token['NE_TAG']
            buf.append(token)

        buf_sentence = []
        for token in buf:
            if token['BI_TAG'] == 'B':
                buf_sentence.append(' ')

            if token['NE_TAG'] == 'O':
                buf_sentence.append(token['WORD'])
            else:
                l1, l2 = token['NE_TAG'].split('_')
                buf_sentence.append('<NE L1="{}" L2="{}">{}</NE>'.format(l1, l2, token['WORD']))

                if ne_info is not None:
                    if l1 not in ne_info:
                        ne_info[l1] = {}

                    if token['WORD'] not in ne_info[l1]:
                        ne_info[l1][token['WORD']] = 0

                    ne_info[l1][token['WORD']] += 1

                    # if l2 not in ne_info[l1]:
                    #     ne_info[l1][l2] = []
                    #
                    # ne_info[l1][l2].append(token['WORD'])

        return "".join(buf_sentence)

    @staticmethod
    def to_string_kangwon_form(raw_sentence):
        """
        CRF 태깅 결과를 텍스트 형태로 반환
        """
        buf_sentence = []
        prev = {'BI_TAG': '', 'WORD': '', 'NE_TAG': ''}

        for token in raw_sentence:
            word_start = True
            if prev['NE_TAG'] != '' and prev['NE_TAG'] != token['NE_TAG']:
                word_start = False

                if prev['NE_TAG'] != 'O':
                    buf_sentence.append('{%s}' % prev['NE_TAG'])

                if buf_sentence[-1] != ' ':
                    buf_sentence.append(' ')

            if prev['WORD'] != '' and token['BI_TAG'] == 'B':
                if word_start is True and prev['NE_TAG'] != 'O':
                    buf_sentence.append('{%s}' % prev['NE_TAG'])

                if buf_sentence[-1] != ' ':
                    buf_sentence.append(' ')

            buf_sentence.append(token['WORD'])
            prev = {'BI_TAG': token['BI_TAG'], 'WORD': token['WORD'], 'NE_TAG': token['NE_TAG']}

        if prev['NE_TAG'] != 'O':
            buf_sentence.append('{%s}' % prev['NE_TAG'])

        return "".join(buf_sentence)

    @staticmethod
    def space_tagging(raw_sentence):
        """
        어절 단위 BI 태그 부착

        입력 예
            2014 04 01 19:45 SK 외국인 타자 루크 스캇이 SK 최정에게 원포인트 레슨을 했다.
        """
        result = []

        for token in raw_sentence.split(' '):
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
            bi_tag, ne_tag = tagger_result[i].split('-')
            result.append({
                'BI_TAG': sentence_spaced[i]['BI_TAG'],
                'WORD': sentence_spaced[i]['WORD'],
                'NE_TAG': ne_tag})

        return result

    def tag_sentence(self, raw_sentence, ne_info=None):
        """
        하나의 문장을 태깅
        """
        sentence_spaced = self.space_tagging(raw_sentence.strip())

        x_test = self.sent2features(sentence_spaced)
        tagger_result = self.tagger.tag(x_test)

        sentence_spaced = self.merge_tagging_result(sentence_spaced, tagger_result)

        return self.to_string(sentence_spaced, ne_info)

    def open(self, model_filename):
        """
        crfsuite 열기
        """
        self.tagger = pycrfsuite.Tagger()
        self.tagger.open(model_filename)

        return self.tagger

    def tagging_by_dictionary(self):
        """
        """

        # 사전 로드
        title = ['text', 'l1', 'l2', 'text2']

        path = 'dictionary/NESet'
        for filename in ['LOCATION.txt', 'ORGANIZATION.txt', 'PERSON.txt']:
            with open('{}/{}'.format(path, filename), 'r', encoding='utf-8') as fp:
                for line in fp.readlines():
                    token = line.split('\t', maxsplit=3)

                    row = dict(zip(title, token))

                    print(row)

        # 적용
        # for line in sys.stdin:
        #     line = line.strip()
        #
        #     pass

        return

    def parse_argument(self):
        """
        프로그램 실행 인자 설정
        """
        import argparse

        arg_parser = argparse.ArgumentParser(description='Named Entity Train & Tagger')

        # train
        arg_parser.add_argument('-cross_evaluation', help='cross evaluation', action='store_true', default=False)
        arg_parser.add_argument('-sample_size', help='sample_size', type=int, default=-1)
        arg_parser.add_argument('-max_fold', type=int, help='max fold', default=5)
        arg_parser.add_argument('-corpus', type=str, help='corpus file name', default="data/baseball.L2.train.db")

        arg_parser.add_argument('-c1', type=float, help='c1', default=1.0)
        arg_parser.add_argument('-c2', type=float, help='c2', default=1e-3)
        arg_parser.add_argument('-max_iterations', type=int, help='max iterations', default=50)
        arg_parser.add_argument('-algorithm', type=str, choices=['lbfgs', 'l2sgd', 'ap', 'pa', 'arow'],
                                help='algorithm: {lbfgs, l2sgd, ap, pa, arow}', default='lbfgs')

        # run tagger
        arg_parser.add_argument('-stdin', help='taging with stdin', action='store_true', default=False)
        arg_parser.add_argument('-model', type=str, help='model file name',
                                default="model/sample_size=-1/algorithm=lbfgs/"
                                        "fold=full,c1=1.0,c2=0.001,max_itr=50-full.model")

        arg_parser.add_argument('-train_single_model', help='train single model', action='store_true', default=False)

        arg_parser.add_argument('-eval', help='eval', action='store_true', default=False)
        arg_parser.add_argument('-get_features', help='get_features', action='store_true', default=False)

        arg_parser.add_argument('-tagging_by_dictionary', help='tagging_by_dictionary', action='store_true', default=False)

        self.args = arg_parser.parse_args()
        return self.args


if __name__ == '__main__':
    ne_tagger = NCNamedEntity()
    args = ne_tagger.parse_argument()

    if args.cross_evaluation is True:
        ne_tagger.cross_evaluation()
    elif args.train_single_model is True:
        ne_tagger.train_single_model()
    elif args.eval is True:
        eval_sentences = []
        for line in sys.stdin:
            eval_sentences.append(ne_tagger.split_ne_tag(line.strip()))

        ne_tagger.evaluate_model(args.model, eval_sentences)
    elif args.get_features is True:
        # 스텐포드 NER 학습용 자질 추출
        eval_sentences = []
        for line in sys.stdin:
            sentence = ne_tagger.split_ne_tag(line.strip())

            for word, tag in sentence:
                print('{}\t{}'.format(word, tag))
    elif args.stdin is True:
        ne_tagger.open(args.model)

        # load model
        for line in sys.stdin:
            line = line.strip()
            tagged = ne_tagger.tag_sentence(line)

            print('{}\t{}'.format(line, tagged))
    elif args.tagging_by_dictionary is True:
        ne_tagger.tagging_by_dictionary()
