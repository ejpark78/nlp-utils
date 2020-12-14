#!/usr/bin/env bash

cache=$1

kbsec_scripts=module/kbsec/kbsec.py
review_scripts=module/movie_reviews/daum.py
youtube_scripts=module/youtube/youtube.py
facebook_scripts=module/facebook/facebook.py

case ${cache} in
  daum)
    filename=data/movie_reviews/daum.db
    meta_filename=data/movie_reviews/daum-meta.json
    export_scripts=${review_scripts}
    ;;
  naver)
    filename=data/movie_reviews/naver.db
    meta_filename=data/movie_reviews/naver-meta.json
    export_scripts=${review_scripts}
    ;;
  youtube-mtd)
    filename=data/youtube/mtd.db
    meta_filename=data/youtube/mtd-meta.json
    export_scripts=${youtube_scripts}
    ;;
  youtube-news)
    filename=data/youtube/news.db
    meta_filename=data/youtube/news-meta.json
    export_scripts=${youtube_scripts}
    ;;
  kbsec)
    filename=data/kbsec/kbsec.db
    meta_filename=data/kbsec/kbsec-meta.json
    export_scripts=${kbsec_scripts}
    ;;
  facebook)
    filename=data/facebook/facebook.db
    meta_filename=data/facebook/facebook-meta.json
    export_scripts=${facebook_scripts}
    ;;
  facebook-stock)
    filename=data/facebook/stock.db
    meta_filename=data/facebook/stock-meta.json
    export_scripts=${facebook_scripts}
    ;;
  *)
    echo "which cache ?"
    exit
    ;;
esac

src_path="$(dirname "${filename}")"
dump_path="${src_path}/$(date "+%Y-%m-%d")"

echo "파일 복사: ${filename}"
dump_filename="${dump_path}/$(basename "${filename}")"
mkdir -p "${dump_path}"

cp "${filename}" "${dump_filename}"
sync

echo "데이터 덤프: ${dump_filename} => *.xlsx"
PYTHONPATH=. python3 "${export_scripts}" \
  --export \
  --cache "${dump_filename}"
sync

echo "데이터셋 업로드"
cp "${meta_filename}" "${dump_path}/meta.json"
sync

PYTHONPATH=. python3 "${export_scripts}" \
  --upload \
  --meta "${dump_path}/meta.json"
sync

echo "sql 덤프"
utils/sql_dump.sh "${dump_filename}"
