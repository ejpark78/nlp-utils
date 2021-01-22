#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import yaml
import json
from os.path import isdir, exists
from glob import glob


class Json2Yaml(object):

    def __init__(self):
        super().__init__()

    @staticmethod
    def change_comments(data: dict) -> dict:
        result = {}

        for k in data:
            if k[0] != '#':
                result[k] = data[k]
                continue

            if 'descriptions' not in result:
                result['descriptions'] = {}

            result['descriptions'][k[1:]] = data[k]

        return result

    def merge(self, path: str) -> None:
        data = {}

        filename = '{path}/jobs.json'.format(path=path)
        if exists(filename) is True:
            with open(filename, 'r') as fp:
                jobs = json.load(fp=fp)
                if 'trace_list' in jobs:
                    data['jobs'] = jobs['trace_list']
                    if isinstance(data['jobs'], dict):
                        data['jobs'] = self.change_comments(data=data['jobs'])
                else:
                    data.update(jobs)

        filename = '{path}/parsing.json'.format(path=path)
        if exists(filename) is True:
            with open(filename, 'r') as fp:
                parsing = json.load(fp=fp)

                if 'trace_list' in parsing:
                    data['parsing'] = parsing['trace_list']
                    data['parsing'] = self.change_comments(data=data['parsing'])
                else:
                    data.update(parsing)

        with open('{}.yaml'.format(path), 'w') as fp:
            yaml.dump(
                data=data,
                stream=fp,
                default_flow_style=False,
                allow_unicode=True,
                explicit_start=True,
            )

        return

    def batch(self) -> None:
        for path in glob('config/udemy/*'):
            if isdir(path) is False:
                continue

            print(path)
            self.merge(path=path)

        return


if __name__ == '__main__':
    Json2Yaml().batch()
