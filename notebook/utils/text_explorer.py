#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from wordcloud import WordCloud
import webdav.client as dav_client

from utils import ElasticSearchUtils


class TextExplorer(object):
    """ """

    def __init__(self):
        """ """
        wd_options = {
            'webdav_hostname': 'https://mt_pipeline:nlplab2020@corpus.ncsoft.com:8080',
            'webdav_root': '/remote.php/webdav/',
            'webdav_verbose': 1,
        }

        self.wd_client = dav_client.Client(wd_options)

        self.wd_client.default_options.update({
            'SSL_VERIFYPEER': 0,
            'SSL_VERIFYHOST': 0
        })

        host_info = {
            'host': 'https://corpus.ncsoft.com:9200',
            'http_auth': 'elastic:nlplab',
        }

        self.utils = ElasticSearchUtils(**host_info)

        self.set_plt_font()

        pd.set_option('precision', 0)

        self.stop_words = {
            'english_token': 'in,the,but,to,is,of,it,you,There,are,or,will,be,have,think,from,do,n\'t,and,which,let,me,'
                             'if,would,did,like,that,her,he,please,made,can,get,because,'
                             'has,been,my,too,may,by,wa,one,when,seem,also,had,as,not,could,said'.split(','),
            'korean_token': '은,는,이,가,ㅂ니다,에요,습니다,어요,당신,어서,ㄴ데,에서,으시,아니,다면,ㄴ가요,어야,아요,'
                            'ㄴ다,으면,라는,다고,나요,까지,으니,은데,에게,네요,지만,라고,ㄴ다면,으로,니까,ㄹ게요,'
                            'ㅂ니까,을까,으로,으며,ㄴ다고,다는,ㄴ다는,아도,라서,부터,이렇,ㄹ까요'.split(','),
        }

        self.cache = {}

    @staticmethod
    def set_plt_font():
        """matplotlib 한글 폰트 설정"""
        from matplotlib import font_manager, rc

        # 한글 폰트 설정
        font_path = '/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf'

        font_name = font_manager.FontProperties(fname=font_path).get_name()
        rc('font', family=font_name)

        return

    def exports(self):
        """ """
        index = 'corpus-bitext'

        query = {
            "_source": ["korean", "english", "korean_token", "english_token"],
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "source": {
                                    "query": "aihub",
                                    "zero_terms_query": "all"
                                }
                            }
                        },
                        {
                            "bool": {
                                "should": [{
                                    "match": {
                                        "style": {
                                            "query": "구어체",
                                            "zero_terms_query": "none"
                                        }
                                    }
                                },
                                    {
                                        "match": {
                                            "style": {
                                                "query": "대화체",
                                                "zero_terms_query": "none"
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }

        doc_list = []
        self.utils.export(index=index, query=query, result=doc_list)

        return doc_list

    @staticmethod
    def text_length_corr(df, title):
        """ """
        import seaborn as sns
        import matplotlib.pyplot as plt

        plt.figure(figsize=(7, 7))

        count_df = df[['BLEU', 'NIST']]

        count_df['token'] = df['src'].apply(lambda x: len(x.split(' ')))
        count_df['length'] = df['src'].apply(lambda x: len(x))

        count_df['src_tgt'] = df.apply(lambda x: len(x['src']) - len(x['tgt']), axis=1)
        count_df['src_tst'] = df.apply(lambda x: len(x['src']) - len(x['tst']), axis=1)
        count_df['tgt_tst'] = df.apply(lambda x: len(x['tgt']) - len(x['tst']), axis=1)

        sns.heatmap(
            data=count_df.corr(method='pearson'),
            annot=True,
            fmt='.2f',
            linewidths=.5,
            cmap='Blues'
        )

        plt.title(title)
        plt.show()

        return

    @staticmethod
    def describe(score):
        """길이 정보를 반환한다."""
        return {
            '최대': np.max(score),
            '최소': np.min(score),
            '평균': np.mean(score),
            '중간': np.median(score),
            '표준편차': np.std(score),
            '분산': np.var(score),
            '25%': np.percentile(score, 25),
            '50%': np.percentile(score, 50),
            '75%': np.percentile(score, 75),
        }

    def text_length(self, text, labels=('길이', '어절')):
        """길이 정보를 반환한다."""
        text_list = [str(r).split() for r in text]

        text_length = {
            'text': [len(t) for t in text_list],
            'token': [len(str(s).replace(' ', '')) for s in text],
        }

        doc_list = {
            labels[0]: self.describe(text_length['text']),
            labels[1]: self.describe(text_length['token']),
        }

        pd.set_option('precision', 2)

        df = pd.DataFrame(doc_list).transpose()

        return {
            'table': df,
            'text_length': text_length,
        }

    @staticmethod
    def display_hist(scores):
        """ """
        plt.rcParams.update({'font.size': 15})

        plt.figure(figsize=(20, 10))

        for k in scores:
            plt.hist(scores[k], bins=50, alpha=0.5, color='r', label=k)

        plt.yscale('log', nonposy='clip')

        # 그래프 제목
        plt.title('텍스트 길이 히스토그램')

        # 그래프 x 축 라벨
        plt.xlabel('텍스트 길이')

        # 그래프 y 축 라벨
        plt.ylabel('빈도')

        return

    @staticmethod
    def display_plot(scores, title):
        """ """
        plt.figure(figsize=(20, 10))

        sns.distplot(scores, rug=True)

        plt.title(title)
        plt.show()

        return

    @staticmethod
    def display_joint_plot(scores, x, y, title):
        """ """
        sns.jointplot(
            data=scores,
            x=x, y=y,
            kind='kde',
            space=0,
            zorder=0,
            n_levels=6,
            height=10,
        )

        plt.title(title)
        plt.show()

        return

    @staticmethod
    def display_box_plot(scores, labels, title):
        """ """
        plt.rcParams.update({'font.size': 15})

        fig1, ax1 = plt.subplots(figsize=(20, 5))

        ax1.set_title(title)
        ax1.boxplot(scores, labels=labels, showmeans=True, vert=False)

        return

    @staticmethod
    def display_wordcloud(word_list, stop_words):
        """워드 클라우드를 그려서 반환한다."""
        if len(word_list) == 0:
            return

        font_path = '/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf'

        wc = WordCloud(
            width=800,
            height=600,
            font_path=font_path,
            stopwords=stop_words,
            background_color='black',
        ).generate(' '.join([str(s) for s in list(word_list)]))

        plt.figure(figsize=(20, 15))
        plt.imshow(wc)

        return

    @staticmethod
    def get_topic_model(doc_list, stop_words=None):
        """LDA를 실행한다."""
        from sklearn.decomposition import LatentDirichletAllocation
        from sklearn.feature_extraction.text import CountVectorizer

        if len(doc_list) == 0:
            return None

        tf_vectorizer = CountVectorizer(
            max_df=0.95,
            min_df=1,
            max_features=10,
            stop_words=stop_words,
        )
        tf = tf_vectorizer.fit_transform(doc_list)

        # 토픽 개수
        n_components = int(len(doc_list) / 10) + 1

        # 토픽 추출
        lda_model = LatentDirichletAllocation(
            n_components=n_components,
            max_iter=10,
            learning_method='online',
            learning_offset=50.,
            random_state=0,
        ).fit(tf)

        return {
            'tf': tf,
            'lda_model': lda_model,
            'tf_vectorizer': tf_vectorizer,
        }

    @staticmethod
    def get_topic_list(model, feature_names, no_top_words):
        """토픽을 반환한다."""
        # self.topic_mapping(
        #     model=lda,
        #     no_top_words=20,
        #     feature_names=tf_vectorizer.get_feature_names(),
        # )

        result = {}
        for topic_idx, topic in enumerate(model.components_):
            for i in topic.argsort()[:-no_top_words - 1:-1]:
                f_name = feature_names[i]
                if f_name not in result:
                    result[f_name] = 0

                result[f_name] += topic[i]

        for f_name in result:
            result[f_name] = round(result[f_name], 2)

        return result

    @staticmethod
    def read_json(filename):
        """ """
        return pd.read_json(
            filename,
            compression='bz2',
            orient='records',
            lines=True,
        )

    @staticmethod
    def to_json(df, filename):
        """파일로 저장한다."""
        df.to_json(
            filename,
            force_ascii=False,
            compression='bz2',
            orient='records',
            lines=True,
            index=False,
        )

        return

    def download_file(self, local_filename, remote_filename):
        """ """
        self.wd_client.pull(
            local_directory=local_filename,
            remote_directory=remote_filename,
        )

        return

    def get_file_list(self, remote_path):
        """ """
        return self.wd_client.list(remote_directory=remote_path)

    def get_summary(self, df, columns, title):
        """ """
        tl_list = []
        for k in columns:
            tl = self.text_length(text=df[k], labels=['길이', '어절'])
            tl_list.append(tl)

            sub_title = '길이 ({})'.format(k)

            count = tl['text_length']
            for k in count:
                self.display_box_plot(title=sub_title, scores=[count[k]], labels=[k])

            self.display_plot([count['text']], title=sub_title)

        pd.set_option('precision', 1)

        # 취합
        len_summary = pd.concat(
            {
                '길이': pd.DataFrame([self.describe(tl['text_length']['text']) for tl in tl_list]).transpose(),
                '어절': pd.DataFrame([self.describe(tl['text_length']['token']) for tl in tl_list]).transpose()
            },
            axis=1
        ).rename(columns={0: 'src', 1: 'tgt', 2: 'tst'})

        # BLEU
        bleu_summary = None
        if 'BLEU' in df:
            doc_list = {
                'BLEU': self.describe(df['BLEU']),
                'NIST': self.describe(df['NIST']),
            }

            bleu_summary = pd.DataFrame(doc_list).transpose()

            self.display_box_plot([df['BLEU']], ['BLEU'], title=title)

            self.display_plot(df['BLEU'], title=title)

            self.display_joint_plot(
                df[['BLEU', 'NIST']],
                x='BLEU',
                y='NIST',
                title=title
            )

        self.text_length_corr(df, title='{} (상관 계수)'.format(title))

        return {
            'bleu': bleu_summary,
            'length': len_summary,
            'text_length_list': tl_list,
        }

    def get_bleu_range(self, df):
        """ """
        bleu_range = {
            '0.1~0.2': self.describe_range(df=df, column='src', min_value=0.1, max_value=0.2, sample=20),
            '0.5~0.6': self.describe_range(df=df, column='src', min_value=0.5, max_value=0.6, sample=20),
            '0.8~0.9': self.describe_range(df=df, column='src', min_value=0.8, max_value=0.9, sample=20),
        }

        summary = pd.concat(
            {
                '길이': pd.DataFrame(
                    [self.describe(bleu_range[k]['text_length']['text']) for k in bleu_range]
                ).transpose(),
                '어절': pd.DataFrame(
                    [self.describe(bleu_range[k]['text_length']['token']) for k in bleu_range]
                ).transpose()
            },
            axis=1
        ).rename(columns={i: k for i, k in enumerate(bleu_range.keys())})

        return summary

    def describe_range(self, df, column, min_value, max_value, sample=20):
        from IPython.display import display

        search_df = df[(df['BLEU'] > min_value) & (df['BLEU'] < max_value)]

        display('BLEU: {:0.4f} ~ {:0.4f}, size: {:,}'.format(min_value, max_value, len(search_df)))

        title = '{}~{}'.format(min_value, max_value)
        summary = self.get_summary(df=search_df, columns=[column], title=title)

        for k in {'bleu', 'length'}:
            display(summary[k].style.set_caption(k + ': ' + title))

        sample_df = search_df.sample(n=sample).sort_values(by=['BLEU', 'NIST'], ascending=False)
        display(sample_df.style.set_caption(title))

        pd.set_option('display.precision', 1)
        pd.set_option('display.max_colwidth', 0)

        tl = summary['text_length_list'][0]

        tl.update({
            'search_df': search_df,
            'sample_df': sample_df,
        })

        return tl
