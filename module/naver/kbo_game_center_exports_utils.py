#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
import logging
from os import makedirs
from os.path import isfile, dirname, isdir

import pandas as pd
import urllib3
from tqdm.autonotebook import tqdm

from utils import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

logger = logging.getLogger()

MESSAGE = 25

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(format='%(message)s')
logger.setLevel(MESSAGE)


class NaverKBOGameCenterExportUtils(ElasticSearchUtils):
    """ 응원 댓글 수집 유틸 """

    def __init__(self):
        """ """
        super().__init__()
        return

    def open_elasticsearch(self):
        """ 엘라스틱서치에 연결한다."""
        self.es = {
            'comments': ElasticSearchUtils(host=self.host, index=self.index['comments'], split_index=True, tag='2019'),
            'game_info': ElasticSearchUtils(host=self.host, index=self.index['game_info'], split_index=False),
            'relay_text': ElasticSearchUtils(host=self.host, index=self.index['relay_text'], split_index=False),
        }

        return

    def exports_game_info(self):
        """ 게임 정보를 덤프한다. """
        game_info = self.es['game_info'].dump()

        game_info_df = pd.DataFrame(game_info)

        game_info_df['aScore'] = game_info_df['score'].apply(lambda x: x['aScore'])
        game_info_df['hScore'] = game_info_df['score'].apply(lambda x: x['hScore'])

        game_info_df.drop(columns=['score', 'baseInfo'], inplace=True)

        return game_info_df.fillna('')

    def exports_relay_text(self):
        """ 문자 중계를 덤프한다. """
        # 문자 중계
        relay_text = self.es['relay_text'].dump()

        result = [k for x in relay_text for v in x['relayTexts'].values() for k in v if isinstance(k, dict)]

        return result

    def exports_comments(self, done_df=None, data_path=None):
        """ 응원글을 덤프한다. """
        # 전체 데이터 덤프
        if done_df is None:
            comments = self.es['comments'].dump()

            return pd.DataFrame(comments)

        count = []
        result = []
        for i, row in tqdm(done_df.iterrows(), total=len(done_df)):
            game_id = row['gameId']
            g_date = str(row['gdate'])

            # 파일 이름
            filename = '{}/{}-{}/{}.json.bz2'.format(data_path, g_date[:4], g_date[4:6], game_id)
            if data_path is not None:
                if isfile(filename) is True:
                    continue

                # 경로 생성
                if isdir(dirname(filename)) is False:
                    makedirs(dirname(filename))

            query = {
                'query': {
                    'bool': {
                        'must': [
                            {
                                'match': {
                                    'object_id': game_id
                                }
                            }
                        ]
                    }
                }
            }

            self.es['comments'].index = self.es['comments'].get_target_index(
                tag=g_date[:4],
                index=self.es['comments'].index,
                split_index=True,
            )

            data = self.es['comments'].dump(
                query=query,
            )

            if len(data) == 0:
                continue

            count.append({
                'game_id': data[0]['object_id'],
                'date': data[0]['game_date'],
                'home_team': data[0]['home_team'],
                'away_team': data[0]['away_team'],
                'count': len(data),
            })

            # 결과 저장
            if data_path is not None:
                with bz2.open(filename, 'wb') as fp:
                    line = json.dumps(data, ensure_ascii=False, indent=4)
                    fp.write(line.encode('utf-8'))
            else:
                result.append(data)

        count_df = pd.DataFrame(count)

        return {
            'count': count_df,
            'result': result,
        }

    @staticmethod
    def to_json(df, filename):
        """파일로 저장한다."""
        df.reset_index().to_json(
            filename,
            force_ascii=False,
            compression='bz2',
            orient='records',
            lines=True,
        )
        return

    @staticmethod
    def read_json(filename):
        """파일로 저장한다."""
        df = pd.read_json(
            filename,
            compression='bz2',
            orient='records',
            lines=True,
        )
        return df


if __name__ == '__main__':
    pass
