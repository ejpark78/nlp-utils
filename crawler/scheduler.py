#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys

from time import sleep
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
            spotv_baseball_2017
            {
                "_id": "spotv_baseball_2017",
                "schedule": {
                    "group": "spotv",
                    "mode": "crawler",
                    "sleep_range": "01,02,03,04,05,06,07,08,19,20,21,22,23,24"
                },
                "docker": {
                    "command": "python3 scheduler.py",
                    "image": "crawler:1.0",
                    "working_dir": "/usr/local/app"
                },
                "parameter": {
                    "const_value": {
                        "section": "스포츠-야구"
                    },
                    "db_info": {
                        "corpus-process": {
                            "url": "https://gollum02:5004/v1.0/api/batch"
                        },
                        "elastic": {
                            "host": "http://nlpapi.ncsoft.com:9200"
                        },
                        "mongo": {
                            "collection": "2017-04",
                            "host": "frodo",
                            "name": "spotv_baseball",
                            "port": 27018,
                            "update": false
                        }
                    },
                    "delay": "15~20",
                    "document_id": "{_id}",
                    "end": "1934",
                    "max_skip": 5000,
                    "parsing_info": "spotv.sports",
                    "start": "1",
                    "url_frame": [
                        {
                            "const_value": {
                                "section": "스포츠-야구"
                            },
                            "url": "http://www.spotvnews.co.kr/?page={start}&mod=news&act=articleList&total=38674&sc_code=1384128643&view_type=S"
                        }
                    ]
                }
            }

        :return:
            True/False
        """

        while True:
            # job info 갱신
            job_info = self.get_job_info(scheduler_db_info)

            if job_info is None:
                return

            schedule = job_info['schedule']

            sleep_time = -1
            if 'mode' in schedule and schedule['mode'] == 'daemon':
                sleep_time = 60
                if 'sleep' in schedule:
                    sleep_time = int(schedule['sleep'])

                # sleep_range: 01,02,03,04,05,06
                if 'sleep_range' in schedule:
                    dt = datetime.now()

                    sleep_range = schedule['sleep_range'].split(',')
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
