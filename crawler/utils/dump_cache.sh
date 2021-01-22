#!/usr/bin/env bash

cache=$1

youtube_scripts="module/youtube/youtube.py"
facebook_scripts="module/facebook/facebook.py"

case ${cache} in
  daum)
    filename="data/movie_reviews/daum.db"
    meta_filename="data/movie_reviews/daum-meta.json"
    export_scripts="module/movie_reviews/daum.py"
    ;;
  naver)
    filename="data/movie_reviews/naver.db"
    meta_filename="data/movie_reviews/naver-meta.json"
    export_scripts="module/movie_reviews/naver.py"
    ;;
  youtube-bns)
    filename="data/youtube/bns.db"
    meta_filename="data/youtube/bns-meta.json"
    export_scripts="${youtube_scripts}"
    ;;
  youtube-mtd)
    filename="data/youtube/mtd.db"
    meta_filename="data/youtube/mtd-meta.json"
    export_scripts="${youtube_scripts}"
    ;;
  youtube-news)
    filename="data/youtube/news.db"
    meta_filename="data/youtube/news-meta.json"
    export_scripts="${youtube_scripts}"
    ;;
  kbsec)
    filename="data/kbsec/kbsec.db"
    meta_filename="data/kbsec/kbsec-meta.json"
    export_scripts="module/kbsec/kbsec.py"
    ;;
  facebook)
    filename="data/facebook/facebook.db"
    meta_filename="data/facebook/facebook-meta.json"
    export_scripts="${facebook_scripts}"
    ;;
  facebook-stock)
    filename="data/facebook/stock.db"
    meta_filename="data/facebook/stock-meta.json"
    export_scripts="${facebook_scripts}"
    ;;
  *)
    echo "which cache ?"
    exit
    ;;
esac

src_path="$(dirname "${filename}")"
dump_path="${src_path}/$(date "+%Y-%m-%d")"
dump_meta="${dump_path}/$(basename "${meta_filename}")"
dump_filename="${dump_path}/$(basename "${filename}")"

echo "파일 복사: ${filename} to ${dump_filename}"
mkdir -p "${dump_path}"

cp "${filename}" "${dump_filename}"
sync

echo "데이터 덤프: ${dump_filename} => json,xlsx"
PYTHONPATH=src python3 "src/${export_scripts}" \
  --export \
  --cache "${dump_filename}"
sync

echo "데이터셋 업로드"
cp "${meta_filename}" "${dump_meta}"
sync

PYTHONPATH=src python3 "src/${export_scripts}" \
  --upload \
  --meta "${dump_meta}"
sync

echo "sql 덤프"
src/utils/sql_dump.sh "${dump_filename}"
sync

#rm "${dump_filename}"
