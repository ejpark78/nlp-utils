#!/usr/bin/env bash

prefix=$1
filename=$2

cat <<EOF | xargs -I{} echo "bzcat ${prefix}.{}.sql.bz2 | sqlite3 ${filename} \".read /dev/stdin\"" | bash -
cache
movie_code
movie_reviews
EOF
