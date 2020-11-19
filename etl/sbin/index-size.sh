#!/usr/bin/env bash

curl -s -k -u elastic:nlplab "https://corpus.ncsoft.com:9200/_cat/indices?v&s=index&h=index,docs.count"
