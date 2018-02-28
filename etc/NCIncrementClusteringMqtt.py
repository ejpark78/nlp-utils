#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import json
import queue
import threading

from time import time
from datetime import datetime

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

from NCIncrementClustering import NCIncrementClustering


class NCIncrementClusteringMqtt:
    """
    클러스터링 mqtt 메세지 처리 함수 모음
    """
    def __init__(self, parameter=None):
        if parameter is None:
            return

        self.parameter = parameter
        self.document_list = {}

        self.job_queue = queue.Queue()
        self.clustering = {}

        self.mutex = False

    @staticmethod
    def json_serial(obj):
        """
        날자 형식을 문자로 바꾸는 함수
        """
        from datetime import datetime

        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S.%f")

        raise TypeError("Type not serializable")

    @staticmethod
    def document_cleanning(document_list):
        """
        문서 목록에서 필요한 정보만 추출
        """
        result = {}
        for doc_id in document_list:
            document = {}
            for key in ['_id', 'date', 'title', 'pos_tagged', 'pos_tagged_title']:
                if key not in document_list[doc_id]:
                    continue

                document[key] = document_list[doc_id][key]

            if len(document) > 0:
                result[doc_id] = document

        return result

    def save_file(self, topic, payload, dir_path='payload'):
        """
        페이로드를 파일로 저장
        """
        if os.path.isdir(dir_path) is False:
            return

        if isinstance(payload, str) is not True:
            payload = json.dumps(payload, ensure_ascii=False, default=self.json_serial)

        topic = topic.replace('/', '.')
        with open('{}/{}.json'.format(dir_path, topic), 'w') as fp:
            fp.write(payload)

        return

    def save_document(self, document_list):
        """
        입력 문서 버퍼링
        """
        for doc_id in document_list:
            if doc_id in self.document_list:
                continue

            document = {}
            for key in ['_id', 'date', 'title']:
                if key not in document_list[doc_id]:
                    continue

                document[key] = document_list[doc_id][key]

            self.document_list[doc_id] = document

        return

    def publish_message(self, payload, topic, host, qos, pretty=False):
        """
        mqtt 서버에 메세지 전달
        """
        if len(payload) == 0:
            return

        if pretty is True:
            message = json.dumps(payload, ensure_ascii=False, indent=4, default=self.json_serial)
            print('payload', message)
        else:
            message = json.dumps(payload, ensure_ascii=False, default=self.json_serial)

        publish.single(topic, message, qos=qos, hostname=host)
        return

    def get_visual_message(self, topic_id, visualization_info, episode_id):
        """
        웹 시각화 메세지 반환
        """
        en2ko_team = {
            "OB": "두산",
            "SS": "삼성",
            "HT": "KIA",
            "WO": "넥센",
            "SK": "SK",
            "HH": "한화",
            "LT": "롯데",
            "LG": "LG",
            "NC": "NC",
            "KT": "KT"
        }

        result = {}
        for vis in visualization_info:
            document_id = vis['_id']
            if document_id not in self.document_list:
                continue

            vis['topic_id'] = topic_id
            document = self.document_list[document_id]

            # 새로운 클러스터나 클러스터 정보가 변경되었을 경우에만 전달
            if 'is_summarizable' not in document or 'event_id' not in document \
                    or document['is_summarizable'] != vis['is_summarizable'] \
                    or document['event_id'] != vis['event_id'] \
                    or document['episode_id'] != episode_id:
                token = episode_id.split(',')
                episode = []
                if episode_id == 'etc':
                    episode.append('기타')

                if episode_id == 'whole':
                    episode.append('전체')

                for team in token:
                    if team in en2ko_team:
                        episode.append(en2ko_team[team])

                document['episode_id'] = ' vs '.join(episode)
                document['event_id'] = vis['event_id']
                document['is_summarizable'] = vis['is_summarizable']

                result[document_id] = document

        return result

    def get_publish_message(self, diff_list, curr_time, episode_id):
        """
        클러스터링 매핑 함수
        """
        sent_clus = self.clustering[episode_id].get_string2sentclus(
            diff_list, curr_time, self.clustering[episode_id].publish_cluster)

        # 문서 정보를 버퍼링
        result = {}
        for cluster_id in sent_clus['data']:
            for document_id in sent_clus['data'][cluster_id]['docs']:
                if document_id not in self.document_list:
                    continue

                document = self.document_list[document_id]
                document['episode_id'] = episode_id
                document['event_id'] = cluster_id

                result[document_id] = document

        return result

    @staticmethod
    def split_episode(document_list):
        """
        문서 목록을 입력 받아 에피소드별로 분류된 결과 반환
        """
        result = {}
        for document_id in document_list:
            episode = NCIncrementClustering().get_episode(document_list[document_id])

            if episode not in result:
                result[episode] = {}
            result[episode][document_id] = document_list[document_id]

        return result

    def run_queue(self):
        """
        메세지 큐 실행
        """
        start_date = datetime.now()

        if self.job_queue.empty() is True:
            return

        print('queue size: {}'.format(self.job_queue.qsize()))

        if self.mutex is True:
            return

        self.mutex = True

        #  작업 큐에서 작업을 하나 가져온다.
        job = self.job_queue.get()

        topic_id = job['topic_id']
        payload = job['payload']

        document_list = json.loads(payload)

        # 문서에서 필요한 정보만 추출
        document_list = self.document_cleanning(document_list)

        # 입력 문서 버퍼링
        self.save_document(document_list)

        # 문서를 에피소드별로 분류
        episode_list = self.split_episode(document_list)

        # 에피소드별로 클러스터링 실행
        for episode_id in episode_list:
            print('episode_id: ', episode_id, ' : ', len(episode_list[episode_id]))

            if episode_id not in self.clustering:
                self.clustering[episode_id] = NCIncrementClustering()
                self.clustering[episode_id].open()

            # 클러스터링 실행
            visualization_info, diff_list, curr_time = self.clustering[episode_id].run(episode_list[episode_id])

            # 문장 클러스터링 모듈에 데이터 전달
            if diff_list:
                topic = '{}/{}'.format(self.parameter['publish_topic'], topic_id)
                payload = self.get_publish_message(diff_list, curr_time, episode_id=episode_id)

                if len(payload) > 0:
                    payload['meta'] = {'start_date': start_date, 'end_date': datetime.now()}
                    self.publish_message(topic=topic, payload=payload, host=self.parameter['host'], qos=2)

                    # 페이로드 저장
                    if self.parameter['save_payload'] is True:
                        self.save_file(topic=topic, payload=payload)

            # 웹 시각화 모듈에 데이터 전달
            topic = '{}/{}'.format(self.parameter['visualization_topic'], topic_id)
            payload = self.get_visual_message(topic_id, visualization_info, episode_id=episode_id)

            if len(payload) > 0:
                payload['meta'] = {'start_date': start_date, 'end_date': datetime.now()}
                self.publish_message(topic=topic, payload=payload, host=self.parameter['host'], qos=2)

        self.mutex = False

        # 작업 큐가 빌때까지 재실행
        self.run_queue()
        return

    @staticmethod
    def parse_argument():
        """"
        옵션 설정
        """
        import argparse

        arg_parser = argparse.ArgumentParser(description='increment clustering')

        arg_parser.add_argument('-mqtt_host', help='', default='localhost')
        arg_parser.add_argument('-mqtt_port', help='', default=1883, type=int)
        arg_parser.add_argument('-mqtt_publish_topic', help='', default='saga/incremental_clustering')
        arg_parser.add_argument('-mqtt_subscribe_topic', help='', default='saga/document_list')
        arg_parser.add_argument(
            '-mqtt_visualization_topic', help='', default='saga/visualization/incremental_clustering')

        arg_parser.add_argument('-save_payload', help='', action='store_true', default=False)

        return arg_parser.parse_args()

# NCIncrementClusteringMqtt 클래스 끝


def on_connect(client, userdata, rc):
    """
    MQTT 서버에 연결되었을 때
    """
    print('Connected with result code {}'.format(rc))
    client.subscribe('{}/+'.format(client.util.parameter['subscribe_topic']))


def on_message(client, userdata, msg):
    """
    MQTT 서버에서 메세지를 받았을 때
    """
    topic, topic_id = msg.topic.rsplit('/', maxsplit=1)
    print('topic', topic, 'topic_id', topic_id)

    if topic != client.util.parameter['subscribe_topic']:
        return

    payload = msg.payload.decode('utf-8')

    # 스래드로 작업 시작
    if client.util.job_queue.empty() is True:
        # queue 목록에 작업 저장
        client.util.job_queue.put({'topic_id': topic_id, 'payload': payload})

        # 스래드 시작
        thread = threading.Thread(target=client.util.run_queue)
        thread.start()
    else:
        client.util.job_queue.put({'topic_id': topic_id, 'payload': payload})

    # 페이로드 저장
    if client.util.parameter['save_payload'] is True:
        client.util.save_file(topic=msg.topic, payload=payload)

    return


def start_mqtt_client(parameter):
    """
    Increment Clustering MQTT 클라이언트 실행
    """
    client = mqtt.Client(client_id="Increment Clustering")

    client.util = NCIncrementClusteringMqtt(parameter)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(host=parameter['host'], port=parameter['port'], keepalive=60)

    client.loop_forever()
    return


if __name__ == "__main__":
    args = NCIncrementClusteringMqtt().parse_argument()

    param = {
        'host': args.mqtt_host,
        'port': int(args.mqtt_port),
        'publish_topic': args.mqtt_publish_topic,
        'subscribe_topic': args.mqtt_subscribe_topic,
        'visualization_topic': args.mqtt_visualization_topic,
        'save_payload': args.save_payload
    }

    print(param)
    start_mqtt_client(parameter=param)
