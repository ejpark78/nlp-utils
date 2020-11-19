
## 영화 리뷰 크롤러 개발 

```bash
PYTHONPATH=. python3 module/movie_reviews/daum.py --use-cache --movie-reviews
PYTHONPATH=. python3 module/movie_reviews/naver.py --use-cache --movie-reviews
```

```bash

❯ ll
total 8.6G
-rw-rw-r-- 1 ejpark ejpark 515M Nov 19 14:16 daum.bak.db
-rw-r--r-- 1 ejpark ejpark 516M Nov 19 14:39 daum.db

sqlite3 ${filename} ".tables" | sed -r 's/\s+/\n/g' 


filename=naver.bak.db
sqlite3 ${filename} ".tables" \
    | sed -r 's/\s+/\n/g' \
    | xargs -I{} echo "sqlite3 ${filename} \".dump {}\" | bzip2 - > ${filename}.{}.sql.bz2" \
    | bash - 

filename=naver.bak.db
sqlite3 ${filename} ".tables" \
    | sed -r 's/\s+/\n/g' \
    | xargs -I{} echo "bzcat naver.bak.{}.sql.bz2 | sqlite3 naver.2.db \".read /dev/stdin\"" \
    | bash -

```
