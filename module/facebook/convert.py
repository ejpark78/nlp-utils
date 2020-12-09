#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
import sys
from urllib.parse import unquote

from module.facebook.cache_utils import CacheUtils


class FBConvertData(object):

    def __init__(self):
        super().__init__()

    @staticmethod
    def posts():
        cache = 'data/facebook/facebook.db'

        db = CacheUtils(filename=cache)

        for l in sys.stdin:
            doc = json.loads(l)

            date = doc['curl_date'].replace('T', ' ').split('.')[0]
            del doc['curl_date']

            db.save_post(
                document=doc,
                account_id=doc['page'],
                post_id=doc['top_level_post_id'],
                date=date
            )

        return

    @staticmethod
    def reply():
        cache = 'data/facebook/facebook.db'

        db = CacheUtils(filename=cache)

        # with bz2.open('data/facebook/dev.json.bz2', 'rb') as fp:
        #     for l in fp.readlines():
        #         doc = json.loads(l.decode('utf-8'))

        for l in sys.stdin:
            doc = json.loads(l)

            date = doc['curl_date'].replace('T', ' ').split('.')[0]
            del doc['curl_date']

            del doc['document_id']

            page, doc['post_id'] = unquote(doc['post_id']).rsplit('-', maxsplit=1)

            db.save_replies(document=doc, post_id=doc['post_id'], reply_id=doc['reply_id'], date=date)

        return


if __name__ == '__main__':
    FBConvertData().reply()
