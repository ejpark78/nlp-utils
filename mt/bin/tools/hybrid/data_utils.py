#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
import logging
import numpy as np
import os
import pandas as pd
import pickle
import platform
import re
import sys
import time
import nltk

from sklearn.cross_validation import train_test_split

from nltk.tag import pos_tag_sents 
from nltk.tokenize import word_tokenize 

from np_extractor import NPExtractor

from multiprocessing import Manager
from multiprocessing import Process

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding("utf-8")


class DataUtils(object):
    alias_word = {}
    stop_word_set = None


    def __init__(self):
        self.alias_word = {"is": "'s", "'m": 'am', "'d": 'would', "n't": "not"}

        stop_word = {}
        for w in [
                '/', '"', '\'', ',', ';', ':', '~', '.', '!', '?',
                '(', ')', '[', ']', '*', '-', '=', '+', '...', "''", '``',
                '`', '--']:
            stop_word[w] = 1

        self.stop_word_set = set(stop_word.keys())


    def parse_filename(self, filename):
        # ex) predict_up/try-9/tuning-set/textbook.tcsv.gz

        # dbase: predict_up/try-9/tuning-set
        # fbase: textbook
        # fname: textbook.tcsv.gz

        dbase, fname = os.path.split(filename)

        fbase, fext = os.path.splitext(fname)
        fbase, fext = os.path.splitext(fbase)

        return (dbase, fbase, fname)


    def get_host_name(self):
        return platform.node()


    def parse_args(self, args, seqs):
        ret = {}
        for i in range(1, len(args)):
            if i > len(seqs):
                break

            ret[seqs[i-1]] = args[i]

        return ret


    def read_corpus(self, path, filename, cache=''):
        logging.info("Read Corpus: %s", filename)

        start = time.time()  # Start time

        if cache == '':
            cache = path

        fname, fext = os.path.splitext(filename)
        filename_pickle = "%s/%s.pickle" % (cache, fname)

        if not os.path.isfile(filename_pickle):
            compression = 'infer'
            if fext == '.gz':
                compression = 'gzip'

            corpus = pd.read_csv(
                os.path.join(os.path.dirname(__file__), path, filename),
                header=0, delimiter="\t", quoting=3, encoding="utf-8",
                compression=compression)

            pickle.dump(corpus, open(filename_pickle, 'wb'))
        else:
            logging.info("Use pickle: %s", filename_pickle)

            corpus = pickle.load(open(filename_pickle, 'rb'))

        logging.info(
            "Time taken for ReadCorpus: %.2f seconds.",
            (time.time() - start))

        return (corpus)


    def increase(self, data, key):
        if key in data.keys():
            data[key] += 1
        else:
            data[key] = 1


    def get_phrase_model(self, filename_cache=None, sentences=None):
        logging.info("Get Phrase Model.")

        from gensim.models import Phrases

        bigram = Phrases(min_count=5, threshold=10.0, max_vocab_size=40000000)

        if filename_cache is not None and os.path.isfile(filename_cache):
            bigram.load(filename_cache)
        else:
            if sentences is not None:
                for words in sentences:
                    bigram.add_vocab([words])

                if filename_cache is not None:
                    bigram.save(filename_cache)

        return bigram


    def build_word_vector(
            self, filename_cache, sentences=None, num_features=300,
            min_word_count=1, num_workers=12, context=5, downsampling=1e-3):

        from gensim.models import Word2Vec

        logging.info("Build Word Vector: %s", filename_cache)

        fname, fext = os.path.splitext(filename_cache)
        bigram = self.get_phrase_model(
            filename_cache="%s.bigram" % (fname),
            sentences=sentences)

        if not os.path.isfile(filename_cache):
            if sentences is not None:
                logging.info("Training Word2Vec model (%d)...", len(sentences))

                model = Word2Vec(
                    bigram[sentences], workers=num_workers, size=num_features,
                    min_count=min_word_count, window=context,
                    sample=downsampling, seed=1)

                model.init_sims(replace=True)

                if filename_cache is not None:
                    if fext == '.pickle':
                        pickle.dump(model, open(filename_cache, 'wb'))
                    elif fext == '.bin':
                        model.save_word2vec_format(filename_cache, binary=True)
                    else:
                        model.save(filename_cache)
            else:
                logging.error("Sentences is None at BuildWordVector")
        else:
            logging.info(
                "Use Word Vector Model: %s fext: %s", filename_cache, fext)

            if fext == '.pickle':
                model = pickle.load(open(filename_cache, 'rb'))
            elif fext == '.bin':
                model = Word2Vec.load_word2vec_format(
                    filename_cache, binary=True)
            else:
                model = Word2Vec.load(filename_cache)

        logging.info("Word Vector Model Size: %s", model.syn0.shape)

        return model, bigram


    def get_sentence_to_w2v(self, bigrams, model, pos_list, topn={}):
        feature_list = []
        word_set = set(model.index2word)

        # sum featrue vector
        for word in bigrams:
            if word in word_set:
                feature_list.append(model[word])

        # extend word
        if len(topn) > 0:
            for word in bigrams:
                # only NN extend feature

                ntop = 0
                if len(pos_list) > 0 and word in pos_list:
                    f_stop = 1
                    for p in topn:
                        if pos_list[word].find(p) != -1:
                            f_stop = 0
                            ntop = topn[p]
                            break

                    if f_stop == 1:
                        continue

                if ntop > 0 and word in word_set:
                    most_similar_words = model.most_similar_cosmul(
                        positive=[word], negative=[], topn=ntop)

                    for t_w in most_similar_words:
                        feature_list.append(model[t_w[0]])

        nwords = len(feature_list)
        featureVec = np.sum(feature_list, axis=0)

        # avg. features
        if nwords > 0.:
            featureVec = np.divide(featureVec, nwords)

        if np.isnan(featureVec).any():
            logging.error(
                "get_sentence_to_w2v: %d, %s",
                nwords, " ".join(bigrams))

        return featureVec


    def get_words_from_pos(self, sentence, limit_pos):
        w_list = []
        p_list = {}

        for unit in sentence.split(' '):
            # unit = re.sub(u'/[^ ]+?/', u'/', unit)
            # unit = re.sub(u'/\/.+\//', u'/', unit)
            # unit = re.sub(u'/\/+/', u'/', unit)

            try:
                token = unit.split('/')
                w = token[0]
                pos = token.pop()

                if w in self.alias_word.keys():
                    w = self.alias_word[w]

            except Exception:
                logging.error("get_words_from_pos: %s", unit)
                continue

            b_append = False
            if w in self.stop_word_set:
                b_append = False
            elif len(limit_pos) == 0 or pos in limit_pos.keys():
                b_append = True
            else:
                # substring matching
                for tag in limit_pos:
                    if pos.find(tag) == 0:
                        b_append = True
                        break

            if b_append is True:
                w_list.append(w)
                p_list[w] = pos

        return (w_list, p_list)


    def tokenize_sentences_single(
            self, sentences, allow_tags={}, pos=None, ret=None):
        tok_sentences = []
        pos_list = []

        for i, sent in enumerate(sentences):
            if (i % 10000.) == 0.:
                logging.info(
                    "Tokenize Sentences Review %d of %d", i, len(sentences))

            (words, poss) = self.get_words_from_pos(sent, allow_tags)
            tok_sentences.append(words)
            pos_list.append(poss)

        if ret is not None:
            ret.append((pos, tok_sentences, pos_list))

        return (tok_sentences, pos_list)


    def tokenize_sentences_multi(self, sentences, allow_tags={}, ncore=12):
        jobs = []
        manager = Manager()
        output = manager.list()

        size = int(len(sentences) / ncore) + 1

        i_start = 0
        for i in range(0, ncore):
            i_end = size + size * i
            if i_end > len(sentences):
                i_end = len(sentences)

            p = Process(
                target=self.tokenize_sentences_single,
                args=(sentences[i_start:i_end], allow_tags, i, output)
            )
            jobs.append(p)

            i_start = i_end

        for j in jobs:
            j.start()

        for j in jobs:
            j.join()

        # merge result
        tok_sentences = []
        pos_list = []

        logging.info("tokenize_sentences_multi merge")

        for i in sorted(output):
            logging.info("tokenize_sentences_multi merge: %s", i[0])

            tok_sentences += i[1]
            pos_list += i[2]

        return (tok_sentences, pos_list)


    def tokenize_sentences(self, sentences, 
                           filename_cache=None, allow_tags={}, ncore=12):
    
        tok_sentences = []
        pos_list = []

        if filename_cache is None or not os.path.isfile(filename_cache):
            if ncore > 1:
                (tok_sentences, pos_list) = self.tokenize_sentences_multi(
                    sentences=sentences, allow_tags=allow_tags)
            else:
                (tok_sentences, pos_list) = self.tokenize_sentences_single(
                    sentences=sentences, allow_tags=allow_tags)

            if filename_cache is not None:
                pickle.dump(
                    (tok_sentences, pos_list), open(filename_cache, 'wb'))
        else:
            logging.info("Use Cache File: %s", filename_cache)

            if filename_cache is not None:
                (tok_sentences, pos_list) = pickle.load(
                    open(filename_cache, 'rb'))

        return (tok_sentences, pos_list)


    def approx(self, model, data, base=2):
        if base == 2:
            return [(k, '%.2f' % v) for k, v in model.most_similar([data])]

        return [(k, '%.4f' % v) for k, v in model.most_similar([data])]


    def top_N_to_string(self, topn={}):
        tag_topn = []
        for p in topn:
            tag_topn.append("%s-%d" % (p, topn[p]))

        return ",".join(tag_topn)


    def get_sentence_feature(
            self, sentences, model, bigram, allow_tags={},
            topn={}, pos=None, ret=None):
        (tok_sentences, pos_list) = self.tokenize_sentences(
            sentences=sentences, allow_tags=allow_tags)

        features = np.zeros(
            (len(tok_sentences), model.syn0.shape[1]), dtype="float32")

        for i, words in enumerate(tok_sentences):
            if (i % 1000.) == 0.:
                logging.info(
                    "Make Feature Review %d of %d", i, len(tok_sentences))

            features[i] = self.get_sentence_to_w2v(
                bigrams=bigram[words], model=model, topn=topn,
                pos_list=pos_list[i])

        if ret is not None:
            ret.append((pos, features))

        return features


    def get_sentence_feature_multi(
            self, sentences, model, bigram, allow_tags={}, topn={}, ncore=12):
        jobs = []
        manager = Manager()
        output = manager.list()

        size = int(len(sentences) / ncore) + 1

        i_start = 0
        for i in range(0, ncore):
            i_end = size + size * i
            if i_end > len(sentences):
                i_end = len(sentences)

            p = Process(
                target=self.get_sentence_feature,
                args=(
                    sentences[i_start:i_end], model, bigram,
                    allow_tags, topn, i, output)
            )
            jobs.append(p)

            i_start = i_end

        for j in jobs:
            j.start()

        for j in jobs:
            j.join()

        # merge result
        features_train = None

        logging.info("get_sentence_feature_multi merge")

        for i in sorted(output):
            logging.info("get_sentence_feature_multi merge: %s", i[0])

            if features_train is None:
                features_train = i[1]
            else:
                features_train = np.concatenate((features_train, i[1]), axis=0)

        return features_train


    def parse_allow_tags(self, tags):
        allow_tags = {}
        if tags == 'base':
            allow_tags = {}
        elif tags == 'NN' or tags == 'VV' or tags == 'N' or tags == 'V':
            allow_tags = {tags: tags}
        elif tags.find('_'):
            # ex) NN_VV, N_V, NN_VB
            for t in tags.split('_'):
                allow_tags[t] = t

        return allow_tags


    def make_feature(
            self, langs, sentences, model, bigram,
            filename_cache=None, ncore=12, allow_tags={}, topn={}):
        logging.info("At MakeFeature Cache File: %s", filename_cache)

        if filename_cache is not None and os.path.isfile(filename_cache):
            logging.info("Use Cache File: %s", filename_cache)
            features = pickle.load(open(filename_cache, 'rb'))
        else:
            num_features = 0
            for lang in langs:
                num_features += model[lang].syn0.shape[1]

            features = None
            for lang in langs:
                if ncore > 1:
                    col_features = self.get_sentence_feature_multi(
                        sentences=sentences[lang], model=model[lang],
                        bigram=bigram[lang], allow_tags=allow_tags,
                        topn=topn, ncore=ncore)
                else:
                    col_features = self.get_sentence_feature(
                        sentences=sentences[lang], model=model[lang],
                        bigram=bigram[lang], allow_tags=allow_tags, topn=topn)

                if features is None:
                    features = col_features
                else:
                    features = np.concatenate((features, col_features), axis=1)

            logging.info("Features Shape: %s", features.shape)

            if filename_cache is not None:
                pickle.dump(features, open(filename_cache, 'wb'))

        return features


    def prepare_training(
            self, path, cache, filename_w2v, filename_w2v_corpus,
            allow_tags={}):

        sentences = self.read_corpus(
            path=path, cache=cache, filename=filename_w2v_corpus)

        fname, fext = os.path.splitext(filename_w2v_corpus)
        filename_cache = "%s/%s.ko.pickle" % (cache, fname)

        (sentences, poss) = self.tokenize_sentences(
            filename_cache=filename_cache, sentences=sentences,
            allow_tags=allow_tags)
        model, bigram = self.build_word_vector(
            sentences=sentences,
            filename_cache="%s/%s" % (cache, filename_w2v))

        return model, bigram


    def read_train_test_set(self, fname, tag):
        train = pickle.load(open("%s.train-%s.pickle" % (fname, tag), 'rb'))
        test = pickle.load(open("%s.test-%s.pickle" % (fname, tag), 'rb'))

        logging.info("Read Train & Test Set Train: %s", train.shape)
        logging.info("Read Train & Test Set Test: %s", test.shape)

        return train, test


    def sampling_tuning_corpus(
            self, corpus, filename_cache=None, sample_size=10000):

        group_sample = None
        if filename_cache is not None and os.path.isfile(filename_cache):
            group_sample = pickle.load(open(filename_cache, 'rb'))
        else:
            group_sample = pd.DataFrame(columns=list(corpus))

            gb = corpus.groupby('domain')
            for domain, gp in gb:
                train, sample = train_test_split(gp, test_size=sample_size)

                logging.info(
                    "Size of Group: domain=%s, gp=%s, train=%s, sample=%s",
                    domain, gp.shape, train.shape, sample.shape)

                pd_sample = pd.DataFrame.from_records(
                    data=sample, columns=list(corpus))

                group_sample = pd.concat([group_sample, pd_sample], ignore_index=True)

                logging.info(
                    "Size of Group: group_sample=%s", group_sample.shape)

            logging.info("filename_sample: %s", filename_cache)

            if filename_cache is not None:
                pickle.dump(group_sample, open(filename_cache, 'wb'))

        # group_sample.to_csv(
        #     'sampling.tcsv',
        #     sep='\t', encoding='utf-8', header=True, index=False)

        return group_sample


    def split_train_test_set(
            self, corpus, filename, test_size=200, tag="baseline"):

        group_train = pd.DataFrame(columns=list(corpus))
        group_test = pd.DataFrame(columns=list(corpus))

        gb = corpus.groupby('domain')
        for domain, gp in gb:
            train, test = train_test_split(gp, test_size=test_size)

            logging.info(
                "Size of Group: domain=%s, gp=%s, train=%s, test=%s",
                domain, gp.shape, train.shape, test.shape)

            pd_train = pd.DataFrame.from_records(
                data=train, columns=list(corpus))
            pd_test = pd.DataFrame.from_records(
                data=test, columns=list(corpus))

            group_train = pd.concat([group_train, pd_train], ignore_index=True)
            group_test = pd.concat([group_test, pd_test], ignore_index=True)

        logging.info(
            "Size of Group: group_train=%s, group_test=%s",
            group_train.shape, group_test.shape)

        fname, fext = os.path.splitext(filename)

        # tag = "exclude_general"
        logging.info("Tag is %s", tag)

        filename_train = "%s.train-%s.pickle" % (fname, tag)
        filename_test = "%s.test-%s.pickle" % (fname, tag)

        logging.info("filename_train: %s", filename_train)
        logging.info("filename_test: %s", filename_test)

        pickle.dump(group_train, open(filename_train, 'wb'))
        pickle.dump(group_test,  open(filename_test,  'wb'))


    def split_train_test_set_random(
            self, corpus, filename, test_size=.1, tag="random"):

        train, test = train_test_split(corpus, test_size=test_size)

        logging.info(
            "Size of Group: train=%s, test=%s", train.shape, test.shape)

        fname, fext = os.path.splitext(filename)

        logging.info("Tag is %s", tag)

        filename_train = "%s.train-%s.pickle" % (fname, tag)
        filename_test = "%s.test-%s.pickle" % (fname, tag)

        logging.info("filename_train: %s", filename_train)
        logging.info("filename_test: %s", filename_test)

        pd_train = pd.DataFrame.from_records(data=train,  columns=list(corpus))
        pd_test = pd.DataFrame.from_records(data=test,  columns=list(corpus))

        pd_test.to_csv(
            "%s.tcsv" % filename_test,
            sep='\t', encoding='utf-8', header=False, index=False)

        pickle.dump(pd_train, open(filename_train, 'wb'))
        pickle.dump(pd_test,  open(filename_test,  'wb'))


    def get_tm_key(self, key):
        # tm_key = re.sub(u'[^ㄱ-ㅣ가-힣a-zA-Z|0-9]', '', tm_key)
        try:
            return re.sub(u'[ .,|!:;()]', '', key)
        except:
            print('error: ', key)
            pass

        return key


    def read_train_log(self, dname, filename='try-9.sent_bleu.tcsv.gz'):
        f = "%s/%s" % (dname, filename)

        train_log = {}
        dname, fname = os.path.split(f)
        fbase, fext = os.path.splitext(fname)

        filename_cache = "%s/%s.train_log.pickle" % (dname, fbase)

        if not os.path.isfile(filename_cache):
            corpus = self.read_corpus(
                path=dname, cache=dname, filename=fname)

            # corpus.loc[corpus.domain == 'all'] = -1

            for j, w in enumerate(corpus['tok ko']):
                w = self.get_tm_key(w)

                cluster_id = -1
                if corpus['domain'][j] != 'all':
                    cluster_id = int(corpus['domain'][j])

                if cluster_id not in train_log.keys():
                    train_log[cluster_id] = {w: 1}
                else:
                    train_log[cluster_id][w] = 1

            pickle.dump(train_log, open(filename_cache, 'wb'))
        else:
            logging.info("read_train_log cache: %s", filename_cache)
    
            train_log = pickle.load(
                open(filename_cache, 'rb'))

        return train_log


    def read_phrase_count(self, model_path, filename='phrase_count.reduced.gz'):
        f_list = glob.glob("%s/*/%s" % (model_path, filename))

        filename_phrase_count = "%s/%s.pickle" % (model_path, filename)
        logging.info("read_phrase_count: %s", filename_phrase_count)

        phrase_count = {}
        if not os.path.isfile(filename_phrase_count):
            for i, f in enumerate(f_list):
                dname, fname = os.path.split(f)

                filename_cache = "%s/%s.pickle" % (dname, fname)
                logging.info("read_phrase_count cache: %s", filename_cache)

                cluster_id = dname.split('/').pop()
                if cluster_id == 'all':
                    cluster_id = -1

                cluster_id = int(cluster_id)

                if not os.path.isfile(filename_cache):
                    phrase_count[cluster_id] = dict(
                        (w, 1) for w in pd.read_csv(
                            os.path.join(
                                os.path.dirname(__file__), dname, fname),
                            header=-1, delimiter="\t", quoting=3,
                            encoding="utf-8", compression="gzip")[0]
                        )

                    pickle.dump(
                        phrase_count[cluster_id], open(filename_cache, 'wb'))
                else:
                    phrase_count[cluster_id] = pickle.load(
                        open(filename_cache, 'rb'))

            pickle.dump(phrase_count, open(filename_phrase_count, 'wb'))
        else:
            logging.info(
                "read_phrase_count phrase count cache: %s",
                filename_phrase_count)

            phrase_count = pickle.load(open(filename_phrase_count, 'rb'))

        return phrase_count


    def get_ngram(self, words, n=-1):
        if n < 0 or n > len(words):
            n = len(words)

        n += 1

        ngram = {}
        for i in range(len(words)):
            for j in range(1, n):
                ngram[" ".join(words[i:i+j])] = 0

        return ngram


    def split_sentence(self, words, phrase, left=''):
        sep = '\t'

        if left == '':
            phrase[" ".join(words)] = 1

        for i in range(1, len(words)):
            str_a = " ".join(words[0:i])
            words_b = words[i:len(words)+1]

            next_left = "%s%s%s" % (left, sep, str_a)
            self.split_sentence(left=next_left, words=words_b, phrase=phrase)

            p = next_left + sep + " ".join(words_b)
            p = p.strip(sep).strip()

            phrase[p] = 1


    def sort_by_value(self, data):
        v = {}

        for key, value in sorted(data.items()):
            value = '%.4f' % value
            v.setdefault(float(value), []).append(key)

        return v

    # slu(dialogue act) feature extraction


    def dialogue_act_features(self, post):
        features = {}
        for word in nltk.word_tokenize(post):
            features['contains({})'.format(word.lower())] = True
        return features


    def get_slu_model(self, filename_cache=None, evaluation=False):
        if os.path.isfile(filename_cache):
            (slu, slu_class) = pickle.load(open(filename_cache, 'rb'))
        else:
            posts = nltk.corpus.nps_chat.xml_posts()

            slu_class = {}
            feature_sets = []
            for post in posts:
                slu_class[post.get('class')] = 1
                feature_sets.append((self.dialogue_act_features(post.text), post.get('class')))

            # train
            slu = None
            if evaluation is True:
                size = int(len(feature_sets) * 0.1)

                train_set, test_set = feature_sets[size:], feature_sets[:size]
                slu = nltk.NaiveBayesClassifier.train(train_set)

                print('%.2f' % nltk.classify.accuracy(slu, test_set))    
            else:
                slu = nltk.NaiveBayesClassifier.train(feature_sets)
                
            # slu class
            i = 1
            for k in sorted(slu_class.keys()):
                slu_class[k] = i
                i += 1

            # save model
            if filename_cache is not None:
                pickle.dump((slu, slu_class), open(filename_cache, 'wb'))

        return (slu, slu_class)
            

    # Named Entity Extraction
    def get_ne_lable_values(self, labels, ne_labels):
        v_label = 0x00
        for l in labels:
            if l in ne_labels.keys():
                v_label = v_label | ne_labels[l]

        return v_label


    def get_ne_lables(self):
        # http://www.nltk.org/book/ch07.html
        # http://nlp.stanford.edu/software/CRF-NER.shtml#Models

        # lables = ['ORGANIZATION', 'PERSON', 'LOCATION', 'DATE', 'TIME', 'MONEY', 'PERCENT', 'FACILITY', 'GPE']

        # i = 0x01
        # ne_lables = {}
        # for l in sorted(lables):
        #     ne_lables[l] = i
        #     i = i << 1

        # return ne_lables

        i = 0x01
        return {
            'DATE': i << 0,
            'FACILITY': i << 1,
            'GPE': i << 2,
            'LOCATION': i << 3,
            'MONEY': i << 4,
            'ORGANIZATION': i << 5,
            'PERCENT': i << 6,
            'PERSON': i << 7,
            'TIME': i << 8
        }


    def extract_entity_names(self, t):
        entity_names = []

        if hasattr(t, 'label') and t.label:
            if t.label() == 'NE':
                entity_names.append(' '.join([child[0] for child in t]))
            else:
                for child in t:
                    entity_names.extend(self.extract_entity_names(child))

        return entity_names


    def extract_entity_types(self, t):
        entity_types = []

        if hasattr(t, 'label') and t.label:
            if t.label() != 'S':
                entity_types.append(t.label())
            
            for child in t:
                entity_types.extend(self.extract_entity_types(child))

        return entity_types


    def get_ne_features(self, s):
        sent_pos = pos_tag_sents([word_tokenize(s.strip())])[0]

        ne_chunk = nltk.ne_chunk(sent_pos, binary=True)
        ne_names = self.extract_entity_names(ne_chunk)

        ne_chunk = nltk.ne_chunk(sent_pos)
        ne_types = self.extract_entity_types(ne_chunk)
        
        np_extractor = NPExtractor(s)
        np_list = np_extractor.extract()
        
        all_ne_names = dict([(ne, 1) for ne in ne_names + np_list])

        return (ne_types, list(all_ne_names.keys()))


    # split
    def split_train_test(self, x, y, index, test_size=0.25):
        # merge a & b
        features = np.concatenate([index, y, x], axis=1)

        # split train & tst
        train, test = train_test_split(features, test_size=test_size)

        # split train
        train_split = np.hsplit(train, [1])

        train_index = train_split[0].transpose()[0]

        trains = np.hsplit(train_split[1], [1])

        train_y = trains[0].transpose()[0]
        train_x = trains[1]

        # split test
        test_split = np.hsplit(test, [1])

        test_index = test_split[0].transpose()[0]

        tests = np.hsplit(test_split[1], [1])

        test_y = tests[0].transpose()[0]
        test_x = tests[1]
        
        print('x:', x.shape, 'y:', y.shape, 'train x: ', train_x.shape, 'test x: ', test_x.shape)

        return (train_x, train_y, train_index, test_x, test_y, test_index)


    def get_dialogue_act(self, sentence, slu, slu_class):
        da = slu.classify(self.dialogue_act_features(sentence))

        if da in slu_class.keys():
            return slu_class[da]
        
        return 0


def main():
    """main """


if __name__ == '__main__':
    main()

