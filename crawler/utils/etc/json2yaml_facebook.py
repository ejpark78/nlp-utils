#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from glob import glob

import yaml

with open('21-06-01.yaml', 'r') as fp:
    index_mapping = dict(yaml.load(stream=fp, Loader=yaml.FullLoader))['index_mapping']

for f in glob('*.json'):
    with open(f, 'r') as fp:
        data = json.load(fp)

    data['jobs'] = data['list']
    del data['list']

    data['index'] = {
        'page': 'crawler-facebook-page',
        'post': 'crawler-facebook-post',
        'reply': 'crawler-facebook-reply',
    }
    data['index_mapping'] = index_mapping

    for x in data['jobs']:
        x.update(x['meta'])

        for k in 'site,index,reply_index,meta'.split(','):
            if k in x:
                del x[k]

    with open(f.replace('.json', '.yaml'), 'w') as fp:
        yaml.dump(
            data=data,
            stream=fp,
            default_flow_style=False,
            allow_unicode=True,
            explicit_start=True,
            sort_keys=False,
        )
