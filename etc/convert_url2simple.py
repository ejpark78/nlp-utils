#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import re
import sys
import json


def get_query(url):
    """
    url 에서 쿼리문을 반환
    """
    from urllib.parse import urlparse, parse_qs

    url_info = urlparse(url)
    result = parse_qs(url_info.query)
    for key in result:
        result[key] = result[key][0]

    return result, '{}://{}{}'.format(url_info.scheme, url_info.netloc, url_info.path)


def merge_section():
    """
    """
    new_id = '{oid}-{aid}'
    simple_query = 'oid={oid}&aid={aid}'

    section = {}
    filename = 'section.json'
    if os.path.exists(filename) is True:
        with open(filename, 'r') as fp:
            section = json.loads(''.join(fp.readlines()))

    for line in sys.stdin:
        line = line.strip()
        if line == '':
            continue

        if line.find('ISODate(') > 0:
            line = re.sub(r'ISODate\("(.+?)"\)', '"\g<1>"', line)

        document = json.loads(line)

        if '$date' in document['date']:
            document['date'] = document['date']['$date']

        query, url = get_query(document['url'])
        str_query = simple_query.format(**query)

        document['full_url'] = document['url']
        document['url'] = '{}?{}'.format(url, str_query)

        document['_id'] = new_id.format(**query)

        oid = query['oid']
        aid = query['aid']

        document['oid'] = oid
        document['aid'] = aid

        if oid in section and aid in section[oid]:
            document['section'] = section[oid][aid]
        else:
            pass

        msg = json.dumps(document, sort_keys=True, ensure_ascii=False)
        print(msg, flush=True)


if __name__ == '__main__':
    from urllib.parse import urlparse, parse_qs

    with open('data/sample.json', 'rt') as fp:
        for line in fp.readlines():
            line = line.strip()
            if line == '':
                continue

            document = json.loads(line)

            url = document['url']['full']

            if url.find('lineagem') >= 0 or url.find('lineagem') >= 0:
                url_info = urlparse(url)

                document_id = url

                document_id = document_id.replace('{}://{}'.format(url_info.scheme, url_info.hostname), '')
                document_id = document_id.replace('/board/free/article/', '')
                document_id = document_id.replace('.json', '')

                document['_id'] = document_id

                print(document_id)

            # document['_id'] = url
            print(document)


