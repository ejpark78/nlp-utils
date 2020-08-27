#!/usr/bin/env bash

PYTHONPATH=. python3 module/facebook/crawler.py \
    --list \
    --reply \
    --use_head \
    --config config/facebook/베트남.json \
    --index crawler-facebook-vi \
    --reply_index crawler-facebook-vi-reply \
    --user_data ./cache/selenium/facebook-vi

PYTHONPATH=. python3 module/facebook/crawler.py \
    --reply \
    --use_head \
    --config "config/facebook/group.json,config/facebook/likes.json,config/facebook/friends.json,config/facebook/구단.json,config/facebook/친목.json,config/facebook/언론.json,config/facebook/대나무숲.json,config/facebook/커뮤니티.json,config/facebook/follows.json" \
    --index crawler-facebook-ko \
    --reply_index crawler-facebook-ko-reply \
    --user_data ./cache/selenium/facebook

PYTHONPATH=. python3 module/facebook/crawler.py \
    --list \
    --reply \
    --use_head \
    --max_page 500000 \
    --config config/facebook/태국-200819.json \
    --index crawler-facebook-th \
    --reply_index crawler-facebook-th-reply \
    --user_data ./cache/selenium/facebook-th

PYTHONPATH=. python3 module/naver/bbs.py \
  --content --max_page 10000

