#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import sys
import json


if __name__ == '__main__':
    for line in sys.stdin:
        line = line.strip()
        if line == '':
            continue

        if line.find("ISODate(") > 0:
            line = re.sub(r'ISODate\("(.+?)"\)', '"\g<1>"', line)
            
        data = json.loads(line)
        print(json.dumps(data, sort_keys=True, indent=4, ensure_ascii=False), flush=True)
