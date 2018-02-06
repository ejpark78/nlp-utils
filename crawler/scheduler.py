#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys

from time import time, sleep
from pymongo import MongoClient
from datetime import datetime

try:
    from crawler.crawler import Crawler
except ImportError:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

    from .crawler import Crawler


class Scheduler:
    """
    크롤러 스케줄러
    """
    def __init__(self):
        pass

    @staticmethod
    def open_db(db_name, host='frodo', port=27018):
        """
        몽고 디비 핸들 오픈

        :param db_name:
        :param host:
        :param port:
        :return:
        """
        connect = MongoClient('mongodb://{}:{}'.format(host, port))
        db = connect[db_name]

        return connect, db

    def get_job_info(self, scheduler_db_info):
        """
        디비에서 작업을 찾아 반환

        :param scheduler_db_info:
        :return:
        """
        connect, db = self.open_db(
            scheduler_db_info['scheduler_db_name'],
            scheduler_db_info['scheduler_db_host'],
            scheduler_db_info['scheduler_db_port'])

        if 'document_id' in scheduler_db_info:
            cursor = db[scheduler_db_info['scheduler_db_collection']].find({
                '_id': scheduler_db_info['document_id']
            })
        else:
            return None

        cursor = cursor[:]
        print([scheduler_db_info, cursor.count()])

        job_info = None
        for document in cursor:
            if document['state']['state'] == 'done':
                continue

            job_info = document
            break

        connect.close()

        return job_info

    def run(self, scheduler_db_info):
        """
        작업 목록에서 컨테이너 이름이 같은 것을 가져와서 실행

        :param scheduler_db_info:
            {
                "_id" : "crawler_daum_economy_2017",
                "sleep_range": "01,02,03,04,05,06",
                "parameter" : {
                    "start_date" : "2017-01-01",
                    "end_date" : "2017-12-31",
                    "delay" : "6~9",
                    "max_skip" : 5000,
                    "document_id" : "{_id}",
                    "parsing_info" : "daum.news",
                    "url_frame" : [
                        {
                            "const_value" : {
                                "section" : "경제-부동산"
                            },
                            "url" : "http://media.daum.net/breakingnews/economic/estate?regDate={date}"
                        },
                        (...)
                        {
                            "const_value" : {
                                "section" : "경제"
                            },
                            "url" : "http://media.daum.net/breakingnews/economic?regDate={date}"
                        }
                    ],
                    "db_info" : {
                        (...)
                        "mongo" : {
                            "name" : "daum_economy",
                            "port" : 27018,
                            "host" : "frodo01",
                            "upsert" : false
                        }
                    }
                },
                "state" : {
                    "running" : "2017-02-01",
                    "state" : "running",
                    "progress" : "8.5"
                },
                "group" : "daum_daemon",
                "docker" : {
                    "image" : "crawler:dev",
                    "volume" : "/data/nlp_home/docker/crawler:/data/nlp_home/docker/crawler:ro",
                    "working_dir" : "/data/nlp_home/docker/crawler",
                    "command" : "./venv/bin/python3 scheduler.py"
                }
            }

        :return:
            True/False
        """

        start_time = time()

        while True:
            # job info 갱신
            job_info = self.get_job_info(scheduler_db_info)

            if job_info is None:
                return

            sleep_time = -1
            if job_info['group'].find('daemon') > 0:
                sleep_time = 60
                if 'sleep' in job_info:
                    sleep_time = int(job_info['sleep'])

                # sleep_range: 01,02,03,04,05,06
                if 'sleep_range' in job_info:
                    dt = datetime.now()

                    sleep_range = job_info['sleep_range'].split(',')
                    if dt.strftime('%H') in sleep_range:
                        wait = 60 - dt.minute
                        print('{}, sleep {} minutes'.format(dt.strftime('%Y-%m-%d %H:%M:%S'), wait), flush=True)
                        sleep(wait * 60)
                        continue

            crawler = Crawler()
            crawler.run(scheduler_db_info=scheduler_db_info, job_info=job_info)

            if sleep_time > 0:
                str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print('{}, sleep {} minutes'.format(str_now, sleep_time), flush=True)
                sleep(sleep_time * 60)
            else:
                break

        str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print('DONE at {}'.format(str_now), flush=True)

        return


def init_arguments():
    """
    옵션 설정
    :return:
    """
    import argparse

    parser = argparse.ArgumentParser(description='crawling web news articles')

    # 공통 옵션: 스케줄러 디비 접속 정보
    parser.add_argument('-scheduler_db_host', help='db server host name', default='frodo')
    parser.add_argument('-scheduler_db_port', help='db server port', default=27018)
    parser.add_argument('-scheduler_db_name', help='job db name', default='crawler')
    parser.add_argument('-scheduler_db_collection', help='job collection name', default='schedule')

    parser.add_argument('-document_id', help='document id', default=None)

    return parser.parse_args()


def main():
    """
    :return:
    """
    nc_curl = Scheduler()
    args = init_arguments()

    if args.document_id is None:
        print('error: document_id required!')
        sys.exit(1)

    scheduler_db_info = {
        'document_id': args.document_id,
        'scheduler_db_host': args.scheduler_db_host,
        'scheduler_db_port': args.scheduler_db_port,
        'scheduler_db_name': args.scheduler_db_name,
        'scheduler_db_collection': args.scheduler_db_collection
    }

    print({'scheduler_db_info': scheduler_db_info})
    nc_curl.run(scheduler_db_info)

    return


if __name__ == '__main__':
    main()
