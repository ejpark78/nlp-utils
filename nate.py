#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from utils import open_config, build_dag

build_dag(config=open_config(filename='config/nate.yaml'))
