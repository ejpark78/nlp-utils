#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import urllib3

from nlplab.minio_utils import MinioUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class Youtube(object):

    def __init__(self):
        self.minio = MinioUtils()

    def push(self):
        self.minio.push(
            local='data/youtube/replies/mtd.json.bz2',
            remote='youtube/replies/mtd.json.bz2',
        )

        self.minio.push(
            local='data/youtube/replies/news.json.bz2',
            remote='youtube/replies/news.json.bz2',
        )
        return


if __name__ == "__main__":
    Youtube().push()
