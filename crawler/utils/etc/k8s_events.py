#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import re
import sys
from glob import glob
from os import remove, rename, sync
from os.path import isfile

import pandas as pd
import pytz
from dateutil.parser import parse as parse_date
from tqdm import tqdm


class K8sEvents(object):

    def __init__(self):
        self.timezone = pytz.timezone('Asia/Seoul')

    def merge_events(self) -> None:
        data, file_list = self.load_events()

        self.save_data(data=data)
        self.delete_events(file_list=file_list)

        return

    def load_events(self) -> (list, list):
        file_list = []
        data = self.load_data()

        title = [data[0]] if len(data) != 0 else []
        data = set(data[1:])

        p_bar = tqdm(sorted(glob('events/*.log.bz2')))
        for filename in p_bar:
            p_bar.set_description('load_events:' + filename)

            with bz2.open(filename, 'rb') as fp:
                for line in fp:
                    line = line.decode('utf-8').strip()

                    if len(title) == 0:
                        title = [line]
                        continue

                    if line in data or line == title[0]:
                        continue

                    data.add(line)

            file_list.append(filename)

        return title + list(data), file_list

    @staticmethod
    def delete_events(file_list: list) -> None:
        for filename in file_list:
            remove(filename)

        return

    def save_data(self, data: list) -> None:
        fps = {}

        title = data[0] + '\n'
        title = title.encode('utf-8')

        file_list = []

        for line in data[1:]:
            try:
                dt = parse_date(re.sub(r' \s+', '\t', line).split('\t')[1])
                dt = dt.astimezone(tz=self.timezone).isoformat().split('T')[0]
            except Exception as e:
                print(e, line)
                continue

            filename = f'data/{dt}.log.bz2'
            if filename not in fps:
                if isfile(filename) is True:
                    back_filename = filename + '.bak'
                    if isfile(back_filename) is True:
                        remove(back_filename)
                        sync()

                    rename(filename, back_filename)
                    sync()

                fps[filename] = bz2.open(filename, 'wb')
                fps[filename].write(title)

            line += '\n'
            fps[filename].write(line.encode('utf-8'))

            file_list.append(filename)

        for i, fp in fps.items():
            fp.flush()
            fp.close()

        return

    @staticmethod
    def load_data() -> list:
        p_bar = tqdm(sorted(glob('data/*.log.bz2')))

        title = []
        data = set()
        for filename in p_bar:
            p_bar.set_description('load_data: ' + filename)

            with bz2.open(filename, 'rb') as fp:
                for line in fp:
                    line = line.decode('utf-8').strip()

                    if len(title) == 0:
                        title = [line]
                        continue

                    if line in data or line == title[0]:
                        continue

                    data.add(line)

        return title + list(data)

    @staticmethod
    def get_sizeof(data: list) -> int:
        return int(sys.getsizeof(data) // 1024.0)

    def to_dataframe(self, data: list) -> pd.DataFrame:
        title = re.sub(r' \s+', '\t', data[0]).split('\t')
        rows = []

        for line in data[1:]:
            token = re.sub(r' \s+', '\t', line).split('\t')
            if len(title) != len(token):
                continue

            val = dict(zip(title, token))
            try:
                val['Date'] = parse_date(val['Date']).astimezone(tz=self.timezone)
            except Exception as e:
                print(e, val)
                continue

            rows.append(val)

        df_full = pd.DataFrame(rows)

        df_full['Date'] = pd.to_datetime(df_full['Date']).dt.tz_convert('Asia/Seoul')

        return df_full


if __name__ == '__main__':
    events = K8sEvents()
    events.merge_events()
