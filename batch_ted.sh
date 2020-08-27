#!/usr/bin/env bash

# find data/ted -size -2k -empty
# find data/ted -size -2k -empty -delete

PYTHONPATH=. python3 module/ted.py --list --update_talk_list --talks --language
