#!/usr/bin/env bash

curl -s -k -u elastic:nlplab "https://nlp.ncsoft.com:9200/_cat/indices?v&s=index&h=index,docs.count" \
    | grep " 0$" | cut -f1 -d' ' \
    | xargs -I{} echo 'curl -XDELETE -s -k -u elastic:nlplab "https://nlp.ncsoft.com:9200/{}"'

