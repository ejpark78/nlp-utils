#!/usr/bin/env bash

work_dir="data/nate"
result_dir="data/kbo"

zcat ${work_dir}/2010.??.text_pre_processed.clean.gz | python3 NCCorpus.py -get_korean_baseball | gzip - > ${result_dir}/nate_baseball.2010.gz
zcat ${work_dir}/2011.??.text_pre_processed.clean.gz | python3 NCCorpus.py -get_korean_baseball | gzip - > ${result_dir}/nate_baseball.2011.gz
zcat ${work_dir}/2012.??.text_pre_processed.clean.gz | python3 NCCorpus.py -get_korean_baseball | gzip - > ${result_dir}/nate_baseball.2012.gz
zcat ${work_dir}/2013.??.text_pre_processed.clean.gz | python3 NCCorpus.py -get_korean_baseball | gzip - > ${result_dir}/nate_baseball.2013.gz



