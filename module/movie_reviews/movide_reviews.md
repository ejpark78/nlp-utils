
## 영화 리뷰 크롤러 개발 

```bash
PYTHONPATH=. python3 module/movie_reviews/daum.py --use-cache --movie-reviews
PYTHONPATH=. python3 module/movie_reviews/naver.py --use-cache --movie-reviews
```

```bash
sqlite3 ${filename} ".tables" | sed -r 's/\s+/\n/g' 


filename=naver.bak.db
cat <<EOF | xargs -I{} echo "sqlite3 ${filename} \".dump {}\" | bzip2 - > ${filename}.{}.sql.bz2" | bash -
cache
movie_code
movie_reviews
EOF


cat <<EOF | xargs -I{} echo "bzcat ${filename}.{}.sql.bz2 | sqlite3 naver.2.db \".read /dev/stdin\"" | bash -
cache
movie_code
movie_reviews
EOF

```
