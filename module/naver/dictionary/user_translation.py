#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import re
import sys
from math import ceil
from time import sleep
from uuid import uuid4

import requests
import urllib3
from bs4 import BeautifulSoup
from tqdm.autonotebook import tqdm

from module.dictionary_utils import DictionaryUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class UserTranslationExampleCrawler(DictionaryUtils):
    """네이버 사전 수집기"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

    def get_bitext_list(self, url):
        """ """
        headers = {
            'Referer': url
        }
        headers.update(self.headers)

        resp = requests.get(url, headers=headers, timeout=60, verify=False)
        soup = BeautifulSoup(resp.content, 'html5lib')

        total = 0
        total_tag = soup.select_one('div.section_trans div.sorting p.tx span strong')
        if total_tag is None:
            return [], 0

        total = int(total_tag.get_text().replace(',', ''))

        result = []
        for exam in soup.find_all('div', {'class': 'exam'}):
            item = {}

            try:
                item['theme'] = exam.find('span', {'class': 'theme'}).get_text().strip()
                item['level'] = exam.find('span', {'class': 'level'}).get_text().strip()

                item['sentence1'] = exam.find('div', {'class': 'sentence'}).get_text()
                item['sentence2'] = exam.find('div', {'class': 'mar_top1'}).get_text()

                item['sentence1'] = item['sentence1'].replace('듣기', '')
                item['sentence2'] = item['sentence2'].replace('듣기', '')

                item['sentence1'] = re.sub(r'(\t|\n)+', '\g<1>', item['sentence1']).strip()
                item['sentence2'] = re.sub(r'(\t|\n)+', '\g<1>', item['sentence2']).strip()
            except Exception as e:
                print(e)
                continue

            if len(item) == 0:
                continue

            result.append(item)

        return result, total

    def trace_translation(self, url_frame, url_info, user_id, sleep_time, index):
        """ """
        url_info['page'] = 1
        url_info['user_id'] = user_id

        max_page = 10
        total = -1

        p_bar = None
        while url_info['page'] < max_page:
            url = url_frame.format(**url_info)

            data_list, count = self.get_bitext_list(url=url)
            if count == 0:
                break

            if total < 0:
                total = count
                max_page = ceil(total / len(data_list))
                if max_page > 100:
                    max_page = 100

                p_bar = tqdm(total=max_page, dynamic_ncols=True)

            p_bar.update(1)

            # 저장
            for doc in data_list:
                doc.update({
                    'user_id': user_id
                })

                doc['_id'] = str(uuid4())
                self.elastic.save_document(index=index, document=doc, delete=False)

            self.elastic.flush()

            url_info['page'] += 1
            if url_info['page'] > max_page:
                break

            sleep(sleep_time)

        url_info['page'] = 1
        del url_info['user_id']

        return

    def batch(self):
        """"""
        index = 'crawler-naver-dictionary-user-translation'
        self.open_db(index=index)

        url_frame = '{site}?userTrslLoc={user_id}&pageNo={page}&{extra}'

        url_info = {
            'page': 1,
            'site': 'https://endic.naver.com/userTrsl.nhn',
            'extra': 'sLn=kr&sortType=2',
        }

        user_list = [
            '019a83a88280ea0f',
            '01f56015ba8ea9d5',
            '094d5be5522d8c320f575297d165aeff',
            '14b66e405c714792',
            '14b66e405c714792',
            '17455843ebc1376a76d4cb9087331470',
            '193d4e6650756ee914d6a2e697f334b8',
            '265c776f6e19f347426e180aa20c7f67',
            '2d11dcaa29ca8d721e289404972032af',
            '2d11dcaa29ca8d721e289404972032af',
            '35c612a470ead765dec049bb66ac8f4f',
            '373f92811d72e26cd8d7b479e826dd6e',
            '37f4d5e796090f87285ddc20046361be',
            '3e3d54c9f506962e59a434467f166cfd',
            '3e3d54c9f506962e59a434467f166cfd',
            '46df0d131b862452',
            '4ce793f4650221383dedab6c999ae11e',
            '4e4e0abb7bbd32b1d4e32f5da84d80e4',
            '4e4e0abb7bbd32b1d4e32f5da84d80e4',
            '505e7b404374a56e1f6a328e61be3eec',
            '505e7b404374a56e1f6a328e61be3eec',
            '588841531b99ffc4a4f311f3461e5e5e',
            '588841531b99ffc4a4f311f3461e5e5e',
            '5a71ee0862cc7e0e',
            '5a71ee0862cc7e0e',
            '72933beb7c1089fb0215905a8286fa80',
            '72933beb7c1089fb0215905a8286fa80',
            '7e174f00c665fd3610a0cc35725e08c8',
            '7e4e41a840a5a8432c2f09c024696546',
            '8950b7ea2bf6de59ed454360483b4045',
            '8b55e22c992f5c46da73d35b8bcaca60',
            '8cb55986a95146cb11e8f1da2e42d62b',
            '8efa14630f733df4',
            '8efa14630f733df4',
            '91ad70ab0991d21622fa01a61e6841db',
            '9db4feef4e6c3f0083efb5c41a62a63c',
            '9db4feef4e6c3f0083efb5c41a62a63c',
            'a39eb51e5edec290780279f52d4c3948',
            'a79f894ca926a85f846101241e4a9d5c',
            'a79f894ca926a85f846101241e4a9d5c',
            'ad96c1fa622ceb8eb02ef135af4eb0c0',
            'af196861f96e6a4a2bead7c8998f4feb',
            'af29d5e398700b8cc1bccee8869457ea',
            'af29d5e398700b8cc1bccee8869457ea',
            'b1a8e517354ecd20',
            'b2547bfaed3af08657e8c3edd72d5be9',
            'b31edafdc28b4847a29511e56ca31871',
            'b31edafdc28b4847a29511e56ca31871',
            'ca98d5a77fb3b3ff62414b8ec326c475',
            'd16a201b5e10e52c00190860fa1b1b12',
            'd8161a9a3bf79693aab7babf4ba8ac90',
            'e416f2fee95ef1c65f05027b16accaab',
            'e8382a8e5780f78f',
            'e8382a8e5780f78f',
            'ed478b7747c36d51fd578d1d73b1d6b2',
            'eec4fe09b16384b9cfcd9ef5aaf84760',
            'f51ccb793fe0c51b931035853c34145b',
            'fd21cd5c7b8b8e69d33e95c07ccf99c9',
            #     'af29d5e398700b8cc1bccee8869457ea',
            #     '024304ae731daf383071c79344c33345',
            #     '0245b9a6b090f063e3c76896b73126ac',
            #     '094d5be5522d8c320f575297d165aeff',
            #     '0b828a0f93b7ee5bf51ff5466f5abee1',
            #     '146ce01ab848463b1381b89897877c1a',
            #     '148d0ffeefebaf13b466caf7467cdee4',
            #     '17455843ebc1376a76d4cb9087331470',
            #     '17bdd6dec5eba7f9eec7db717dbaf232',
            #     '184d7c054d3a89e3ec253873162e8909',
            #     '191c1376e37a1ea69144c80fd6a40e0e',
            #     '193d4e6650756ee914d6a2e697f334b8',
            #     '206f3d31f70da60da00c5f754c79263d',
            #     '2460a99f6d5234dfa7770a4be1e9d9ec',
            #     '255411106512a6720afb859abb70bbba',
            #     '265c776f6e19f347426e180aa20c7f67',
            #     '26e50b835a301a320276483465136dd9',
            #     '2bda10bad358878f38aeb7ffcb6057b8',
            #     '2ceae8f947e711ef0e32562faa48c4af',
            #     '2d11dcaa29ca8d721e289404972032af',
            #     '31083e534b6f8438d92a1a6f67a0b5ee',
            #     '348b45d2f0945d348d028c056ca714f1',
            #     '3546bbe845261151f04b17aead1269b2',
            #     '35c612a470ead765dec049bb66ac8f4f',
            #     '373f92811d72e26cd8d7b479e826dd6e',
            #     '37f4d5e796090f87285ddc20046361be',
            #     '3bf6f6d041855ad00a2d2e89d8920fe3',
            #     '3d498565bca1826f962dde3f270c48df',
            #     '3d71e1db17b28b904e10277e69e55427',
            #     '3e3d54c9f506962e59a434467f166cfd',
            #     '402495af191a56a9b434d54c78b2ea4d',
            #     '452f8f031256703ecba94974cb39ac9a',
            #     '4c9a3b238d390f451c5079aa373018e7',
            #     '4ce793f4650221383dedab6c999ae11e',
            #     '4e4e0abb7bbd32b1d4e32f5da84d80e4',
            #     '4f56d12565fc23adab5bc2feca201b21',
            #     '4f6aa60af84dae3abd3f20fa22c0b906',
            #     '505e7b404374a56e1f6a328e61be3eec',
            #     '51a8b252e07b0d3c9de758db1d212d09',
            #     '55098fc8769ab87fe92abf574efb5dfc',
            #     '558abdf11ee99d9a6b68ce6696e670d2',
            #     '588841531b99ffc4a4f311f3461e5e5e',
            #     '5b4bcd49c863d9a7f7e5ace7ba1570fa',
            #     '5d41043bbc27e26b6dc479d56a18c60b',
            #     '6107118563ff563ded6654c51d096f62',
            #     '66712d862e484ae161ee7d29d92b7a0c',
            #     '6ecafa64c8e77ebab48fa95428dfafb7',
            #     '6f94e8ed0910323644905409de934bc5',
            #     '72933beb7c1089fb0215905a8286fa80',
            #     '798c4412e623e1cb604c8bf062823405',
            #     '798c86b19fe93fcf1c28ae1a9766645f',
            #     '7a524a98dd029921f76b3ad282ba844e',
            #     '7dd215d9fdb27ce7f857e4e0b974761f',
            #     '7e174f00c665fd3610a0cc35725e08c8',
            #     '7e4e41a840a5a8432c2f09c024696546',
            #     '84402cdd9e4d96eb4e70adbf32bcf37f',
            #     '86cf0329ce5401f99fe7c1d153b6900e',
            #     '8910cb68b08502d17553b6f47e952ea8',
            #     '8950b7ea2bf6de59ed454360483b4045',
            #     '8a29ecb3114810fc1b4fb2b8b6c0e449',
            #     '8b55e22c992f5c46da73d35b8bcaca60',
            #     '8cb55986a95146cb11e8f1da2e42d62b',
            #     '8d75cf18186acb45307dd0f232549985',
            #     '8f5cc204a086c3efa519c8d2946096e1',
            #     '91ad70ab0991d21622fa01a61e6841db',
            #     '95cfd18bb29b153533ba0aca457f4ca6',
            #     '966ab88adbdd5f67e870339dcb9b122d',
            #     '9b3fd1aa126accc758a5d7d272f0e0e3',
            #     '9b77a267ae1682e9b085601683adbad2',
            #     '9c5c53c3a3a5d75f712d83acdeb30115',
            #     '9db4feef4e6c3f0083efb5c41a62a63c',
            #     'a39eb51e5edec290780279f52d4c3948',
            #     'a41676b2a3d1daf1dab5d0e6455e20d5',
            #     'a44b16c97a81ae83b608e2b2b87b445e',
            #     'a48567e984ecd5f53e7a3375f2ac891e',
            #     'a5ea0a7755f5993c871e4b03427b5e28',
            #     'a79f894ca926a85f846101241e4a9d5c',
            #     'a7a8e404633034dfc3ca17cd7642f00a',
            #     'a9a53d515ab5e3f0eaeb54dc3ceca3c5',
            #     'aa41b9efa87fc544c8d48826b0878fe5',
            #     'ad96c1fa622ceb8eb02ef135af4eb0c0',
            #     'adb510d39dd2fb3d1d91a1f2e36ba462',
            #     'ae3e7b85c18f0fb7aeffb10a323c1649',
            #     'af196861f96e6a4a2bead7c8998f4feb',
            #     'b2547bfaed3af08657e8c3edd72d5be9',
            #     'b31edafdc28b4847a29511e56ca31871',
            #     'b6477666cb2451081a2f40a8ebf198f7',
            #     'ba10b064bcd3608601abca048c13fbe2',
            #     'bbd1978f7ae5fd90b1694e2806e4bb5d',
            #     'bd13ace6ce05df25b085205386c2437b',
            #     'befa7b589c74bc054a2c610106a68605',
            #     'c0a6abe8567c07bc2feddecee722f492',
            #     'c0e1a3588a0b8e92cbb1d5fccd2d08c6',
            #     'ca98d5a77fb3b3ff62414b8ec326c475',
            #     'cc900994de10ed5eac3589b96a559db2',
            #     'd032261e23702b7701961df4e5f82535',
            #     'd16a201b5e10e52c00190860fa1b1b12',
            #     'd5ccd652e88926fcce0738f040995abc',
            #     'd7a29a05dab0d48b6eeffd6f3a66a828',
            #     'd8161a9a3bf79693aab7babf4ba8ac90',
            #     'da32b9187e7e6dd30233251a410cda77',
            #     'db10fcaf02f8cf4f1f4f1cae5042c9fc',
            #     'ddd3c52c93da20e8cc8d2265766b2aeb',
            #     'df6e5e01e1239c93dc406d5b3692b27e',
            #     'e06d7c194e29a3ca28ea3a64fd1c3606',
            #     'e128ebbab10ada8e0d873d8885bc7636',
            #     'e3677079597bb1c1fc814de9c98ddb30',
            #     'e416f2fee95ef1c65f05027b16accaab',
            #     'e806c564a38f0f06e0cb4d4161220f01',
            #     'e97401d6fb1b5f94f981b70e2b90f1de',
            #     'ebf1c6f4511a14bde1ab9a3d27441c54',
            #     'ec42ad9c0574203b38f619127b901f76',
            #     'ed478b7747c36d51fd578d1d73b1d6b2',
            #     'eec4fe09b16384b9cfcd9ef5aaf84760',
            #     'eef95b68f79ae8355986452b6987576f',
            #     'ef4b63428eafb6c0a6c88d136d182da9',
            #     'f05b3392c8f92476c92dcdd504e62ade',
            #     'f1351aa982878cc69c302a08c325d57e',
            #     'f23cde37876645ee4bd5e9836e53942a',
            #     'f4ad0b38247422cd446a8a1ca97fc777',
            #     'f51ccb793fe0c51b931035853c34145b',
            #     'f9304e10a5d2d9f838b61f64653dd3ae',
            #     'f933ec4f34425a513ebbb32a679b046b',
            #     'fa4807a4bf2a284bc2824933a7712830',
            #     'fc719be851e950497ed481e539552e93',
            #     'fd21cd5c7b8b8e69d33e95c07ccf99c9',
            #     'fe12a6de71e4b5ca8689c8f818c42501',
            #     'fec23b82125008667361f53f87e6fdbd',
        ]

        for user_id in tqdm(user_list):
            self.trace_translation(
                index=index,
                user_id=user_id,
                url_info=url_info,
                url_frame=url_frame,
                sleep_time=10,
            )

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        return parser.parse_args()


if __name__ == '__main__':
    UserTranslationExampleCrawler().batch()
