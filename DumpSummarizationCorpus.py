#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from pymongo import MongoClient


class NCDumpSummarizationCorpus:
    """
    """
    def __init__(self):
        pass

    @staticmethod
    def get_summary_info(doc_id, summary):
        result = {}

        if doc_id in summary:
            for index in summary[doc_id].keys():
                p_id, s_id = index.split('_')

                p_id = int(p_id)
                s_id = int(s_id)

                if p_id not in result:
                    result[p_id] = {}

                result[p_id][s_id] = 1

        return result

    @staticmethod
    def get_summary_flag(i, j, summary):
        flag = False
        if i in summary and j in summary[i]:
            flag = True

        return flag

    def print_result(self, summary, document_index):
        """
        """

        result = []
        first_date = None

        # 이벤트 ID, doc_id, 본문, 100자 요약, 60자 요약, 최종 요약, keywords
        for doc_id in sorted(summary['articles']):
            document = document_index[doc_id]
            str_date = document['date']

            if first_date is None or first_date > str_date:
                first_date = str_date

            summary_100 = self.get_summary_info(doc_id, summary['100'])
            summary_50 = self.get_summary_info(doc_id, summary['50'])

            flag_100 = self.get_summary_flag(-1, -1, summary_100)
            flag_50 = self.get_summary_flag(-1, -1, summary_50)

            buf_document = {'sentence': [], '100': [], '50': []}
            if flag_100 is True:
                buf_document['100'].append(document['title'])

            if flag_50 is True:
                buf_document['50'].append(document['title'])

            for i, paragraph in enumerate(document['paragraph']):
                buf = {'sentence': [], '100': [], '50': []}
                for j, sentence in enumerate(paragraph):
                    flag_100 = self.get_summary_flag(i, j, summary_100)
                    flag_50 = self.get_summary_flag(i, j, summary_50)

                    buf['sentence'].append(sentence)
                    if flag_100 is True:
                        buf['100'].append(sentence)

                    if flag_50 is True:
                        buf['50'].append(sentence)

                buf_document['sentence'].append(' '.join(buf['sentence']))
                if len(buf['100']) > 0:
                    buf_document['100'].append(' '.join(buf['100']))

                if len(buf['50']) > 0:
                    buf_document['50'].append(' '.join(buf['50']))

            str_document = '\n'.join(buf_document['sentence'])
            str_100 = '\n'.join(buf_document['100'])
            str_50 = '\n'.join(buf_document['50'])

            result.append(['{}'.format(str_date), doc_id, document['title'], str_document, str_100, str_50])

        return result, first_date

    def dump(self, collection, filename):
        """
        정답셋 생성
        """
        connect = MongoClient('mongodb://{}:{}'.format('gollum', 27017))
        db = connect['summarization']

        # get new format
        cursor = db[collection].find({}, {'title': 1, 'date': 1, 'paragraph': 1})

        document_index = {}
        for document in cursor:
            document_index[document['_id']] = document
        cursor.close()

        # summary result
        result = {}
        cursor = db['ext_{}'.format(collection)].find({})
        for document in cursor:
            summary = json.loads(document['summary'])

            for event_id in summary:
                ret, str_date = self.print_result(summary[event_id], document_index)

                edited_summary = summary[event_id]['edited_summary'].replace('\n', ' ')
                keywords = ','.join(summary[event_id]['keywords'])

                ret[0].append(edited_summary)
                ret[0].append(keywords)
                ret[0].append('{}_{}'.format(document['user_name'], event_id))

                result[str_date] = ret

        cursor.close()

        from xlsxwriter.workbook import Workbook

        workbook = Workbook(filename)
        worksheet = workbook.add_worksheet(collection)

        format_merge = workbook.add_format()

        format_merge.set_text_wrap()
        format_merge.set_align('vcenter')

        title = ['date', 'document id', 'title', 'document', '100', '50', 'edited summary', 'keywords', 'event_id']
        for i, k in enumerate(title):
            worksheet.write(0, i, k)

        width = [25, 30, 40, 50, 50, 50, 60, 40, 30]
        for i, w in enumerate(width):
            worksheet.set_column(i, i, w)

        offset = 1
        for str_date in sorted(result, reverse=False):
            offset = self.save_to_xlsx(worksheet, result[str_date], offset, format_merge)

        workbook.close()
        return

    @staticmethod
    def save_to_xlsx(worksheet, data, offset, format_merge):
        """
        """

        # 문서 출력
        for i, row in enumerate(data):
            for j, col in enumerate(row):
                worksheet.write(i + offset, j, col)

        count = len(data)
        print(offset, offset+count, count, data[0][8])

        if count > 1:
            worksheet.merge_range(offset, 6, offset + count - 1, 6, data[0][6], format_merge)
            worksheet.merge_range(offset, 7, offset + count - 1, 7, data[0][7], format_merge)
            worksheet.merge_range(offset, 8, offset + count - 1, 8, data[0][8], format_merge)

        return offset + count + 1

    @staticmethod
    def parse_argument():
        """
        파라메터 옵션 정의
        """
        import argparse

        arg_parser = argparse.ArgumentParser(description='')

        arg_parser.add_argument('-collection', help='collection name', default='300_on_base_2016_10_03')

        return arg_parser.parse_args()


if __name__ == "__main__":
    corpus = NCDumpSummarizationCorpus()

    args = corpus.parse_argument()
    corpus.dump(args.collection, '{}.xlsx'.format(args.collection))


# ./DumpSummarizationCorpus.py -collection 300_on_base_2016_10_03
# ./DumpSummarizationCorpus.py -collection thames_drunk_driving_2016
# ./DumpSummarizationCorpus.py -collection playoff_2016_10_21
# ./DumpSummarizationCorpus.py -collection korea_2016_10_29



# class NCDumpSummarizationCorpus:
#     """
#     몽고 디비에서 summarization 태깅 말뭉치를 덤프 받는 도구
#     """
#
#     def __init__(self):
#         self.connect = None
#         self.mongo_db = None
#         self.collection = None
#
#     def open(self, db_name='summarization', collection_name='regular_season_2014', host_name='gollum', port=27017):
#         """
#         몽고 디비 오픈
#         """
#         self.connect = MongoClient('mongodb://{}:{}'.format(host_name, port))
#         self.mongo_db = self.connect[db_name]
#         self.collection = self.mongo_db[collection_name]
#
#         return
#
#     @staticmethod
#     def print(data, pretty=True):
#         """
#         딕셔너리 데이터 형을 JSON 표준 형식으로 출력
#         """
#
#         if pretty is True:
#             print(json.dumps(data, sort_keys=True, indent=4, ensure_ascii=False))
#         else:
#             print(json.dumps(data, sort_keys=True, ensure_ascii=False))
#
#         return
#
#     def dump(self, print_type='json'):
#         """
#         문서 요약 말뭉치 추출
#         """
#
#         # 전체 문서 덤프
#         # cursor = self.collection.find({'summarization': {'$exists': 1}})
#
#         # {'summarization': {'$exists': 1}}
#         #   검색 조건: 태깅 완료된 문서만 검색
#         # {"summarization": 1, "title": 1, "date": 1}
#         #   summarization 태깅 정보, 제목, 날짜만 덤프
#         # cursor = self.collection.find({'summarization': {'$exists': 1}},
#         #                               {'summarization': 1, 'title': 1, 'date': 1, 'url': 1, 'evaluation': 1}).sort('date', 1)
#
#         cursor = self.collection.find({'summarization': {'$exists': 1}}).sort('date', 1)
#
#         document_list = cursor[:]
#
#         workbook = None
#         worksheet = None
#         title = ['_id', 'date', 'title', 'url', 'episode', 'event', 'subevent', 'username', 'evaluation']
#         if print_type == 'tab':
#             print('\t'.join(title))
#         elif print_type == 'xlsx':
#             filename = 'result.xlsx'
#
#             from xlsxwriter.workbook import Workbook
#
#             workbook = Workbook(filename)
#             worksheet = workbook.add_worksheet()
#
#             for i, k in enumerate(title):
#                 worksheet.write(0, i, k)
#
#         # 문서 출력
#         for i, document in enumerate(document_list):
#             if 'date' in document:
#                 # date 형식일 경우 문자열로 변환
#                 document['date'] = document['date'].strftime("%Y-%m-%d %H:%M:%S")
#
#             if print_type == 'tab':
#                 doc2 = self.serialize(document)
#
#                 token = []
#                 for k in title:
#                     if k in doc2:
#                         token.append(doc2[k])
#                     else:
#                         token.append('')
#
#                 print('\t'.join(token))
#             elif print_type == 'xlsx' and worksheet is not None:
#                 doc2 = self.serialize(document)
#
#                 for j, k in enumerate(title):
#                     if k in doc2:
#                         worksheet.write(i + 1, j, doc2[k])
#                     else:
#                         worksheet.write(i + 1, j, '')
#             else:
#                 self.print(document, pretty=True)
#                 # self.print(document, pretty=False)
#
#         if workbook is not None:
#             workbook.close()
#         # print(document_list.count())
#
#         return
#
#     @staticmethod
#     def serialize(data):
#         result = {}
#
#         for k in data:
#             if isinstance(data[k], dict) is True:
#                 for sub_k in data[k]:
#                     result[sub_k] = data[k][sub_k]
#
#                     if result[sub_k] is None:
#                         result[sub_k] = ""
#
#                     if sub_k == 'evaluation':
#                         result[sub_k] = json.dumps(result[sub_k], sort_keys=True, ensure_ascii=False)
#
#             result[k] = data[k]
#
#         return result
#
#     @staticmethod
#     def parse_argument():
#         """
#         파라메터 옵션 정의
#         """
#         import argparse
#
#         arg_parser = argparse.ArgumentParser(description='')
#
#         arg_parser.add_argument('-host_name', help='host name', default='gollum')
#         arg_parser.add_argument('-port', help='port', default=27017)
#
#         arg_parser.add_argument('-db_name', help='db name', default='summarization')
#         arg_parser.add_argument('-collection', help='collection name', default='regular_season_2014')
#
#         arg_parser.add_argument('-format', help='format', default='json')
#
#         return arg_parser.parse_args()
#
#
# if __name__ == "__main__":
#     corpus = NCDumpSummarizationCorpus()
#
#     args = corpus.parse_argument()
#     corpus.open(db_name=args.db_name, collection_name=args.collection,
#                 host_name=args.host_name, port=args.port)
#
#     corpus.dump(args.format)
