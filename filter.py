#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import sys
import json
import dateutil.parser


if __name__ == '__main__':
    for line in sys.stdin:
        line = line.strip()
        if line == '':
            continue

        if line.find("ISODate(") > 0:
            line = re.sub(r'ISODate\("(.+?)"\)', '"\g<1>"', line)
            
        document = json.loads(line)

        result = {}
        for k in ['title', 'title_pos_tagged', 'date', 'paragraph', 'pos_tagged', 'source', 'section']:
            if k in document:
                result[k] = document[k]

        if 'date' in result:
            if '$date' in result['date']:
                result['date'] = result['date']['$date']

            date = dateutil.parser.parse(result['date'])
            result['date'] = date.strftime('%Y-%m-%d %H:%M:%S')

        print(json.dumps(result, sort_keys=True, ensure_ascii=False), flush=True)
