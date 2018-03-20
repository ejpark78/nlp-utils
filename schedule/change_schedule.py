#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json


def change_schedule():
    """

    :return:
    """
    import os

    from os.path import isfile

    data_dir = 'list'

    for fname in os.listdir(data_dir):
        file_name = '{}/{}'.format(data_dir, fname)

        if isfile(file_name) is not True:
            continue

        with open(file_name, 'r') as fp:
            document = json.loads(''.join(fp.readlines()))

        document_id = document['_id']
        print(document_id, flush=True)

        schedule = document['schedule']

        schedule['sleep'] = '20'
        schedule['sleep_range'] = '03,04'

        print(schedule)

        str_document = json.dumps(document, indent=4, ensure_ascii=False, sort_keys=True)
        print(str_document, flush=True)

        # with open(file_name, 'w') as fp:
        #     fp.write(str_document + '\n')
        #     fp.flush()

    return


if __name__ == '__main__':
    change_schedule()
