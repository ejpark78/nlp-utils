#!/usr/bin/env bash

filename=$1

# sql dump
echo "sql dump ${filename} => *.sql"
sqlite3 "${filename}" ".tables" \
  | sed -r 's/\s+/\n/g' \
  | xargs -I{} echo "sqlite3 ${filename} \".dump {}\" | bzip2 - > ${filename}.{}.sql.bz2" \
  | bash -
sync

rename 's/.db././' "${filename}".*.sql.bz2
sync
