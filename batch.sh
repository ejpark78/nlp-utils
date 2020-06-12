#!/usr/bin/env bash

PYTHONPATH=. python3 module/facebook.py \
    --use_head \
    --list --reply \
    --config config/facebook/커뮤니티.json \
    --max_page 1000000 \
    --index crawler-facebook-ko \
    --reply_index crawler-facebook-ko-reply \
    --user_data ./cache/selenium/facebook


PYTHONPATH=. python3 module/facebook.py \
    --use_head \
    --list --reply \
    --config config/facebook/인도네시아.json \
    --max_page 10000 \
    --index crawler-facebook-id \
    --reply_index crawler-facebook-id-reply \
    --user_data ./cache/selenium/facebook-id


PYTHONPATH=. python3 module/facebook.py \
    --use_head \
    --list --reply \
    --config config/facebook/베트남.json \
    --max_page 10000 \
    --index crawler-facebook-vi \
    --reply_index crawler-facebook-vi-reply \
    --user_data ./cache/selenium/facebook-vi
