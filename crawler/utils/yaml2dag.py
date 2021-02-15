#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
from glob import glob

import yaml


class Yaml2Dag(object):

    def __init__(self):
        super().__init__()

        self.index = {
            '일반': 'etc',
            'SNS': 'sns',
            '건강정보': 'health',
            '게임': 'game',
            '골프': 'golf',
            '공연전시': 'art',
            '영화': 'movie',
            '과학': 'science',
            '교육': 'education',
            '국방외교': 'national-defense',
            '국회정당': 'national-assembly',
            '글로벌': 'global',
            '금융': 'finance',
            '날씨': 'forecast',
            '노동': 'labor',
            '농구': 'basketball',
            '뉴미디어': 'new-media',
            '도로교통': 'traffic',
            '레저': 'tour',
            '리뷰': 'review',
            '모바일': 'mobile',
            '미국': 'usa',
            '중남미': 'western',
            '배구': 'volleyball',
            '벤처': 'venture',
            '부동산': 'estate',
            '북한': 'north-korea',
            '사건사고': 'incident',
            '생활': 'living',
            '식품의료': 'medical',
            '아시아호주': 'asia',
            '야구': 'baseball',
            '언론': 'media',
            '유럽': 'europe',
            '음식맛집': 'food',
            '인권복지': 'human-right',
            '인물': 'person',
            '자동차시승기': 'car',
            '재계': 'industry',
            '종교': 'religion',
            '중동아프리카': 'mideast',
            '증권': 'stock',
            '지역': 'local',
            '책': 'book',
            '청와대': 'blue-house',
            '축구': 'football',
            '컴퓨터': 'computer',
            '패션뷰티': 'beauty',
            '해외야구': 'wbaseball',
            '해외축구': 'wfootball',
            '해킹': 'security',
            '행정': 'administration',
            '환경': 'environment',
            '경제': 'economy',
            '기업': 'company',
            '창업': 'startup',
        }

    @staticmethod
    def open_config(filename: str) -> dict:
        with open(filename, 'r') as fp:
            data = yaml.load(stream=fp, Loader=yaml.FullLoader)
            return dict(data)

    def batch(self) -> None:
        stop_list = '/_,-reply,blog,cafe,terms'.split(',')
        for filename in glob('config/news/*.yaml'):
            skip = False
            for x in stop_list:
                if x in filename:
                    skip = True
                    break

            if skip is True:
                continue

            category = filename.split('/')[-1].split('.')[0]

            data = self.open_config(filename=filename)
            if 'jobs' not in data:
                continue

            jobs = data['jobs'][0]['list']

            conf = []
            for i, item in enumerate(jobs):
                if 'category' not in item:
                    continue

                task_id = category

                # task_id = '{}-{}'.format(category, i)

                # for x in self.index.keys():
                #     if x not in item['category']:
                #         continue
                #
                #     task_id = '{}-{}'.format(category, self.index[x])
                #     break

                conf.append({
                    # 'name': item['category'],
                    'task_id': task_id,
                    # 'category': category,
                    'config': '/' + filename
                })
                break

            yaml.dump(
                data=conf,
                stream=sys.stdout,
                default_flow_style=False,
                allow_unicode=True,
                explicit_start=True,
            )

        return


if __name__ == '__main__':
    Yaml2Dag().batch()
