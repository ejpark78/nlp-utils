#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import sys
import json


if __name__ == '__main__':
    section = {}

    for line in sys.stdin:
        line = line.strip()
        if line == '':
            continue

        if line.find("ISODate(") > 0:
            line = re.sub(r'ISODate\("(.+?)"\)', '"\g<1>"', line)

        data = json.loads(line)
        token = data['_id'].split('-')

        oid = token[0]
        aid = token[1]

        if oid not in section:
            section[oid] = {}

        section[oid][aid] = data['section']

    print(json.dumps(section, sort_keys=True, indent=4, ensure_ascii=False), flush=True)
