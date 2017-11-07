#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys

from time import time, sleep

from pymongo import MongoClient
from datetime import datetime

from language_utils.language_utils import LanguageUtils

from crawler import NCCrawler


class NCDockerClusterScheduler:
    """
    도커 클러스터 스케줄러
    """
    def __init__(self):
        pass

    @staticmethod
    def open_db(db_name, host='gollum', port=37017):
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
        LanguageUtils().print([scheduler_db_info, cursor.count()])

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
        :return:
        """

        start_time = time()

        job_info = self.get_job_info(scheduler_db_info)
        if job_info is None:
            return

        sleep_time = -1
        if job_info['group'].find('daemon') > 0:
            sleep_time = 10
            if 'sleep' in job_info:
                sleep_time = int(job_info['sleep'])
            else:
                job_info['sleep'] = 10

        while True:
            # job info 갱신
            job_info = self.get_job_info(scheduler_db_info)

            crawler = NCCrawler()
            crawler.run(scheduler_db_info=scheduler_db_info, job_info=job_info)

            if sleep_time > 0:
                str_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print('{}, sleep {}'.format(str_now, sleep_time), flush=True)
                sleep(sleep_time * 60)
            else:
                break

        util = LanguageUtils()
        run_time = util.get_runtime(start_time=start_time)
        str_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print('DONE at {}, runtime: {}'.format(str_now, run_time), flush=True)

        return

    @staticmethod
    def parse_argument():
        """
        옵션 설정

        :return:
        """
        import argparse

        arg_parser = argparse.ArgumentParser(description='crawling web news articles')

        # 공통 옵션: 스케줄러 디비 접속 정보
        arg_parser.add_argument('-scheduler_db_host', help='db server host name', default='frodo01')
        arg_parser.add_argument('-scheduler_db_port', help='db server port', default=27018)
        arg_parser.add_argument('-scheduler_db_name', help='job db name', default='crawler')
        arg_parser.add_argument('-scheduler_db_collection', help='job collection name', default='schedule')

        arg_parser.add_argument('-document_id', help='document id', default=None)

        return arg_parser.parse_args()


def main():
    """

    :return:
    """
    nc_curl = NCDockerClusterScheduler()
    args = nc_curl.parse_argument()

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

    LanguageUtils().print({'scheduler_db_info': scheduler_db_info})
    nc_curl.run(scheduler_db_info)

    return


if __name__ == '__main__':
    main()
