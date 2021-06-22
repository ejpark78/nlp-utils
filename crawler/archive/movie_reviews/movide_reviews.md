
## 영화 리뷰 크롤러 개발 

```bash
python3 -m crawler.movie_reviews.daum.daum --use-cache --movie-reviews

python3 -m crawler.movie_reviews.naver.naver --use-cache --movie-reviews

```

## 테이블 목록 조회

```bash
filename=news.db
sqlite3 ${filename} ".tables" | sed -r 's/\s+/\n/g' 
```

## 백업

```bash
filename=naver.db
cat <<EOF | xargs -I{} echo "sqlite3 ${filename} \".dump {}\" | bzip2 - > ${filename}.{}.sql.bz2" | bash -
cache
movie_code
movie_reviews
EOF
```

## 복구

```bash
cat <<EOF | xargs -I{} echo "bzcat ${filename}.{}.sql.bz2 | sqlite3 naver.2.db \".read /dev/stdin\"" | bash -
cache
movie_code
movie_reviews
EOF

```

```bash
❯ tmux new -s daum-movie
```

## sql 구문 변환

```bash

## daum

bzcat daum.db.cache.sql.bz2 \
    | perl -ple 's/VALUES/(url, content) VALUES/' \
    | bzip2 - > daum.2.db.cache.sql.bz2


bzcat daum.db.movie_code.sql.bz2 \
    | perl -ple 's/VALUES/(url, code, title, review_count, total) VALUES/' \
    | bzip2 - > daum.2.db.movie_code.sql.bz2


bzcat daum.db.movie_reviews.sql.bz2 \
    | perl -ple 's/VALUES/(no, title, code, review) VALUES/' \
    | bzip2 - > daum.2.db.movie_reviews.sql.bz2

## naver

bzcat naver.db.cache.sql.bz2 \
    | perl -ple 's/VALUES/(url, content) VALUES/' \
    | bzip2 - > naver.2.db.cache.sql.bz2

bzcat naver.db.movie_code.sql.bz2 \
    | perl -ple 's/VALUES/(url, code, title, review_count, total) VALUES/' \
    | bzip2 - > naver.2.db.movie_code.sql.bz2

bzcat naver.db.movie_reviews.sql.bz2 \
    | perl -ple 's/VALUES/(no, title, code, review) VALUES/' \
    | bzip2 - > naver.2.db.movie_reviews.sql.bz2

```

## export 

```bash
PYTHONPATH=. python3 module/movie_reviews/daum.py \
    --export \
    --filename data/movie_reviews/daum.bak.db

PYTHONPATH=. python3 module/movie_reviews/naver.py \
    --export \
    --filename data/movie_reviews/naver.bak.db
```
