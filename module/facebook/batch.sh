#!/usr/bin/env bash

PYTHONPATH=. python3 module/facebook/crawler.py \
    --use_head \
    --list --reply \
    --config "config/facebook/group.json,config/facebook/likes.json,config/facebook/friends.json,config/facebook/구단.json,config/facebook/친목.json,config/facebook/언론.json,config/facebook/대나무숲.json,config/facebook/커뮤니티.json,config/facebook/follows.json" \
    --max_page 1000000 \
    --index crawler-facebook-ko \
    --reply_index crawler-facebook-ko-reply \
    --user_data ./cache/selenium/facebook


PYTHONPATH=. python3 module/facebook/crawler.py \
    --use_head \
    --reply \
    --config config/facebook/인도네시아.json \
    --max_page 10000 \
    --index crawler-facebook-id \
    --reply_index crawler-facebook-id-reply \
    --user_data ./cache/selenium/facebook-id


PYTHONPATH=. python3 module/facebook/crawler.py \
    --use_head \
    --reply \
    --config config/facebook/베트남.json \
    --max_page 10000 \
    --index crawler-facebook-vi \
    --reply_index crawler-facebook-vi-reply \
    --user_data ./cache/selenium/facebook-vi


PYTHONPATH=. python3 module/facebook/crawler.py \
    --use_head \
    --list --reply \
    --config config/facebook/news-zh.json \
    --max_page 10000 \
    --index crawler-facebook-zh \
    --reply_index crawler-facebook-zh-reply \
    --user_data ./cache/selenium/facebook-zh

# split_lang
PYTHONPATH=. python3 module/facebook/split_lang.py \
    --from_index crawler-facebook-ko \
    --to_index crawler-facebook-ko-new


PYTHONPATH=. python3 module/facebook/split_lang.py \
    --from_index crawler-facebook-en \
    --to_index crawler-facebook-en-new


PYTHONPATH=. python3 module/facebook/split_lang.py \
    --from_index crawler-facebook-vi \
    --to_index crawler-facebook-vi-new


PYTHONPATH=. python3 module/facebook/split_lang.py \
    --from_index crawler-facebook-id \
    --to_index crawler-facebook-id-new
