#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

import pandas as pd
import sys
import pytz
from tqdm.autonotebook import tqdm

from module.elasticsearch_utils import ElasticSearchUtils

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')

logging_opt = {
    'level': MESSAGE,
    'format': '%(message)s',
    'handlers': [logging.StreamHandler(sys.stderr)],
}
logging.basicConfig(**logging_opt)


class BbsDump(object):
    """크롤러"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.timezone = pytz.timezone('Asia/Seoul')

    @staticmethod
    def dump_docs(cafe=True):
        host_info = {
            'host': 'https://corpus.ncsoft.com:9200',
            'http_auth': 'elastic:nlplab',
            'index': 'crawler-bbs-naver'
        }

        utils = ElasticSearchUtils(**host_info)

        query = {
            'query': {
                'bool': {
                    'must': {
                        'match': {
                            'blog_name': '쿠치레'
                        }
                    }
                }
            }
        }

        if cafe is True:
            query = {
                'query': {
                    'bool': {
                        'must': {
                            'match': {
                                'clubid': 29846718
                            }
                        }
                    }
                }
            }

        doc_list = utils.dump(query=query)

        df = pd.DataFrame(doc_list)

        df.fillna('', inplace=True)

        print('{:,}'.format(len(df)))

        return df

    def batch(self):
        from weasyprint import HTML

        cafe = False

        df = self.dump_docs(cafe=cafe)

        if cafe is True:
            target_df = df[df['bbs_name'].str.contains('제작기')]
        else:
            target_df = df[df['category'] == '쿠치레제작기']

        for i, row in tqdm(target_df.iterrows(), total=len(target_df)):
            filename = 'data/blog/{}.html'.format(row['title'])
            if cafe is True:
                filename = 'data/blog/cafe-{}.html'.format(row['title'])

            with open(filename, 'w') as fp:
                fp.write(row['html_content'])

            pdf_filename = filename.replace('.html', '.pdf')
            HTML(string=row['html_content']).write_pdf(pdf_filename)

        return


def main():
    """"""
    BbsDump().batch()
    return


if __name__ == '__main__':
    main()
