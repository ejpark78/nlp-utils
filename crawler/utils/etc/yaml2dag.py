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

        self.alias = [
            {'text': '해외야구', 'to': 'wbaseball'},
            {'text': '해외축구', 'to': 'wfootball'},
            {'text': '국방외교', 'to': 'national-defense'},
            {'text': '국회정당', 'to': 'national-assembly'},
            {'text': '자동차시승기', 'to': 'car'},
            {'text': '중동아프리카', 'to': 'mideast'},
            {'text': '패션뷰티', 'to': 'beauty'},
            {'text': '여행', 'to': 'travel'},
            {'text': '공연전시', 'to': 'art'},
            {'text': 'SNS', 'to': 'sns'},
            {'text': '건강정보', 'to': 'health'},
            {'text': '게임', 'to': 'game'},
            {'text': '골프', 'to': 'golf'},
            {'text': '영화', 'to': 'movie'},
            {'text': '과학', 'to': 'science'},
            {'text': '교육', 'to': 'education'},
            {'text': '글로벌', 'to': 'global'},
            {'text': '금융', 'to': 'finance'},
            {'text': '날씨', 'to': 'forecast'},
            {'text': '노동', 'to': 'labor'},
            {'text': '농구', 'to': 'basketball'},
            {'text': '뉴미디어', 'to': 'new-media'},
            {'text': '도로교통', 'to': 'traffic'},
            {'text': '레저', 'to': 'tour'},
            {'text': '리뷰', 'to': 'review'},
            {'text': '모바일', 'to': 'mobile'},
            {'text': '미국', 'to': 'usa'},
            {'text': '중남미', 'to': 'western'},
            {'text': '배구', 'to': 'volleyball'},
            {'text': '벤처', 'to': 'venture'},
            {'text': '부동산', 'to': 'estate'},
            {'text': '북한', 'to': 'north-korea'},
            {'text': '사건사고', 'to': 'incident'},
            {'text': '생활', 'to': 'living'},
            {'text': '식품의료', 'to': 'medical'},
            {'text': '아시아호주', 'to': 'asia'},
            {'text': '야구', 'to': 'baseball'},
            {'text': '언론', 'to': 'media'},
            {'text': '유럽', 'to': 'europe'},
            {'text': '음식맛집', 'to': 'food'},
            {'text': '인권복지', 'to': 'human-right'},
            {'text': '인물', 'to': 'person'},
            {'text': '재계', 'to': 'industry'},
            {'text': '종교', 'to': 'religion'},
            {'text': '증권', 'to': 'stock'},
            {'text': '지역', 'to': 'local'},
            {'text': '책', 'to': 'book'},
            {'text': '청와대', 'to': 'blue-house'},
            {'text': '축구', 'to': 'football'},
            {'text': '컴퓨터', 'to': 'computer'},
            {'text': '해킹', 'to': 'security'},
            {'text': '행정', 'to': 'administration'},
            {'text': '환경', 'to': 'environment'},
            {'text': '경제', 'to': 'economy'},
            {'text': '기업', 'to': 'company'},
            {'text': '창업', 'to': 'startup'},
            {'text': '사람들', 'to': 'people'},
            {'text': '종합', 'to': 'total'},
            {'text': '문화', 'to': 'culture'},
            {'text': '일반', 'to': 'etc'},
            {'text': '스포츠', 'to': 'sports'},
            {'text': '사회', 'to': 'society'},
            {'text': '마켓', 'to': 'market'},
            {'text': '산업', 'to': 'industry'},
            {'text': '하이테크', 'to': 'hitech'},
            {'text': '차이나포커스', 'to': 'china-focus'},
            {'text': '철강', 'to': 'steel'},
            {'text': '유통', 'to': 'distribution'},
            {'text': '바이오', 'to': 'bio'},
            {'text': '외교', 'to': 'diplomacy'},
            {'text': '국회', 'to': 'national-assembly'},
            {'text': '정당', 'to': 'party'},
            {'text': '정치', 'to': 'politics'},
            {'text': '연예', 'to': 'entertainment'},
            {'text': '상품', 'to': 'product'},
            {'text': '금융', 'to': 'finance'},
            {'text': '보험', 'to': 'insurance'},
            {'text': '이슈', 'to': 'issue'},
            {'text': '오피니언', 'to': 'opinion'},

        ]

    @staticmethod
    def open_config(filename: str) -> dict:
        with open(filename, 'r') as fp:
            data = yaml.load(stream=fp, Loader=yaml.FullLoader)
            return dict(data)

    def get_task_id(self, name: str, i: int, category: str) -> str:
        task_id = '{}-{}'.format(name, i)

        for x in self.alias:
            if x['text'] not in category:
                continue

            return '{}-{}'.format(name, x['to'])

        return task_id

    def batch(self) -> None:
        stop_list = '/_,-reply,blog,cafe,terms'.split(',')
        for filename in glob('config/world_news/upi.yaml'):
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

                task_id = self.get_task_id(i=item['category'], name=category, category=item['category'])

                conf.append({
                    # 'category': task_id.split('-', maxsplit=1)[-1],
                    'category': item['category'],
                    'name': item['category'],
                    'task_id': task_id,
                    'config': '/' + filename
                })

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
