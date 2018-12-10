#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import sys
from time import sleep

from pymongo import MongoClient

from crawler import Crawler

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)


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

        :param db_name: 디비명
        :param host: 디비 서버 주소
        :param port: 접속 포트
        :return:
        """
        connect = MongoClient('mongodb://{}:{}'.format(host, port))
        db = connect[db_name]

        return connect, db

    def get_job_info(self, scheduler_db_info):
        """
        디비에서 작업을 찾아 반환

        :param scheduler_db_info: 스케쥴 디비 정보
        :return: 스케쥴
        """
        from datetime import datetime

        if scheduler_db_info['file_db'] is True:
            file_name = 'schedule/list/{}.json'.format(scheduler_db_info['document_id'])
            with open(file_name, 'r') as fp:
                body = ''.join(fp.readlines())
                job_info = json.loads(body)
        else:
            connect, db = self.open_db(scheduler_db_info['name'],
                                       scheduler_db_info['host'],
                                       scheduler_db_info['port'])

            if 'document_id' in scheduler_db_info:
                collection = db.get_collection(scheduler_db_info['collection'])
                job_info = collection.find_one({
                    '_id': scheduler_db_info['document_id']
                })

                for k in job_info:
                    if isinstance(job_info[k], datetime):
                        job_info[k] = str(job_info[k])
            else:
                return None

            connect.close()

        logging.info(msg=json.dumps(job_info, ensure_ascii=False))

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
                            "url": "http://www.spotvnews.co.kr/?page={start}&mod=news
                            &act=articleList&total=38674&sc_code=1384128643&view_type=S"
                        }
                    ]
                }
            }

        :return:
            True/False
        """
        import os
        from datetime import datetime

        debug_mode = False
        debug = os.getenv('DEBUG', 'False')
        if debug == 'true' or debug == 'True' or debug == '1':
            debug_mode = True

        while True:
            # job info 갱신
            job_info = self.get_job_info(scheduler_db_info)

            if job_info is None:
                logging.error(msg='error: 스케쥴 정보가 없습니다.')
                logging.error(msg=json.dumps(scheduler_db_info, ensure_ascii=False))
                return

            schedule = job_info['schedule']

            sleep_time = -1
            if 'mode' in schedule and schedule['mode'] == 'daemon':
                sleep_time = 60
                if 'sleep' in schedule:
                    sleep_time = int(schedule['sleep'])

                # sleep_range: 01,02,03,04,05,06
                if debug_mode is False and 'sleep_range' in schedule:
                    dt = datetime.now()

                    sleep_range = schedule['sleep_range'].split(',')
                    if dt.strftime('%H') in sleep_range:
                        wait = 60 - dt.minute

                        logging.info(msg='sleep range {} minutes'.format(wait))
                        sleep(wait * 60)
                        continue

            crawler = Crawler()
            crawler.run(scheduler_db_info=scheduler_db_info, job_info=job_info)

            if sleep_time > 0:
                logging.error(msg='sleep {} minutes'.format(sleep_time))
                sleep(sleep_time * 60)
            else:
                break

        logging.info(msg='DONE')

        return


def init_arguments():
    """
    옵션 설정
    :return:
    """
    import argparse

    parser = argparse.ArgumentParser(description='crawling web news articles')

    parser.add_argument('-file_db', help='', action='store_true', default=False)

    # 스케쥴러 아이디
    parser.add_argument('-document_id', help='document id', default=None)

    # 스케줄러 디비 사용시: 디비 접속 정보
    parser.add_argument('-host', help='db server host name', default='frodo')
    parser.add_argument('-port', help='db server port', default=27018)
    parser.add_argument('-name', help='job db name', default='crawler')
    parser.add_argument('-collection', help='job collection name', default='schedule_list')

    return parser.parse_args()


def main():
    """
    :return:
    """
    nc_curl = Scheduler()
    args = init_arguments()

    if args.document_id is None:
        logging.error(msg='error: document_id required!')
        sys.exit(1)

    scheduler_db_info = {
        'file_db': args.file_db,
        'document_id': args.document_id,
        'host': args.host,
        'port': args.port,
        'name': args.name,
        'collection': args.collection
    }

    nc_curl.run(scheduler_db_info)

    return


if __name__ == '__main__':
    main()
