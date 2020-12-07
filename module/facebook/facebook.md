
```bash
PYTHONPATH=. python3 module/facebook/facebook.py \
    --use_head \
    --list --reply \
    --config "config/facebook/stock.json" \
    --max-page 1000000 \
    --index crawler-facebook-stock \
    --reply-index crawler-facebook-stock-reply \
    --user-data ./cache/selenium/facebook


PYTHONPATH=. python3 module/facebook/facebook.py \
    --use_head \
    --list --reply \
    --config "config/facebook/group.json,config/facebook/likes.json,config/facebook/friends.json,config/facebook/구단.json,config/facebook/친목.json,config/facebook/언론.json,config/facebook/대나무숲.json,config/facebook/커뮤니티.json,config/facebook/follows.json" \
    --max-page 1000000 \
    --index crawler-facebook-ko \
    --reply-index crawler-facebook-ko-reply \
    --user-data ./cache/selenium/facebook


PYTHONPATH=. python3 module/facebook/facebook.py \
    --use_head \
    --reply \
    --config config/facebook/인도네시아.json \
    --max-page 10000 \
    --index crawler-facebook-id \
    --reply-index crawler-facebook-id-reply \
    --user-data ./cache/selenium/facebook-id


PYTHONPATH=. python3 module/facebook/facebook.py \
    --use_head \
    --reply \
    --config config/facebook/베트남.json \
    --max-page 10000 \
    --index crawler-facebook-vi \
    --reply-index crawler-facebook-vi-reply \
    --user-data ./cache/selenium/facebook-vi


PYTHONPATH=. python3 module/facebook/facebook.py \
    --use_head \
    --list --reply \
    --config config/facebook/news-zh.json \
    --max-page 10000 \
    --index crawler-facebook-zh \
    --reply-index crawler-facebook-zh-reply \
    --user-data ./cache/selenium/facebook-zh

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

```

```bash
PYTHONPATH=. python3 module/facebook/facebook.py \
    --list \
    --reply \
    --use_head \
    --config config/facebook/베트남.json \
    --index crawler-facebook-vi \
    --reply-index crawler-facebook-vi-reply \
    --user-data ./cache/selenium/facebook-vi

PYTHONPATH=. python3 module/facebook/facebook.py \
    --reply \
    --use_head \
    --config "config/facebook/group.json,config/facebook/likes.json,config/facebook/friends.json,config/facebook/구단.json,config/facebook/친목.json,config/facebook/언론.json,config/facebook/대나무숲.json,config/facebook/커뮤니티.json,config/facebook/follows.json" \
    --index crawler-facebook-ko \
    --reply-index crawler-facebook-ko-reply \
    --user-data ./cache/selenium/facebook

PYTHONPATH=. python3 module/facebook/facebook.py \
    --list \
    --reply \
    --use_head \
    --max-page 500000 \
    --config config/facebook/태국-200819.json \
    --index crawler-facebook-th \
    --reply-index crawler-facebook-th-reply \
    --user-data ./cache/selenium/facebook-th
```
