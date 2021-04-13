#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import jwt
import sys
import json


if __name__ == '__main__':
    buf = ''
    for line in sys.stdin:
        buf += line.strip()

    print(json.dumps(jwt.decode(buf, ''), ensure_ascii=False), flush=True)
