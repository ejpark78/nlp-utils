#!/usr/bin/env bash

host=$1
merge_home=$2
merge_path=${merge_home}/${host}
tbl=$3

# 결과 병합
for f in $(find ${merge_path} -name '*.db'); do
    sqlite3 ${f} "SELECT raw FROM ${tbl}"
done | bzip2 > ${merge_home}/${host}.${tbl}.json.bz2
