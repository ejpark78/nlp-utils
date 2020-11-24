
## 유튜브 크롤러 개발 

```sql
DELETE FROM channels WHERE id != '삼프로tv';

DELETE FROM videos WHERE tags LIKE '%삼프로tv%';
```

## 크롤링 

```bash
PYTHONPATH=. python3 module/youtube/youtube.py \
    --videos \
    --reply \
    --filename data/youtube/mtd.db \
    --channel-list config/youtube/mtd.json

PYTHONPATH=. python3 module/youtube/youtube.py \
    --videos \
    --reply \
    --filename data/youtube/news.db \
    --channel-list config/youtube/news.json 
```

## sql 구문 변환

```bash
bzcat news.db.channels.sql.bz2 \
    | perl -ple 's/VALUES/(id, title, video_count, data) VALUES/' \
    | bzip2 - > news.2.db.channels.sql.bz2

bzcat news.db.videos.sql.bz2 \
    | perl -ple 's/VALUES/(id, title, reply_count, tags, data, total) VALUES/' \
    | bzip2 - > news.2.db.videos.sql.bz2

bzcat news.db.reply.sql.bz2 \
    | perl -ple 's/VALUES/(no, id, video_id, video_title, data) VALUES/' \
    | bzip2 - > news.2.db.reply.sql.bz2

```

## export 

```bash
PYTHONPATH=. python3 module/youtube/youtube.py \
    --export \
    --filename data/youtube/mtd.bak.db

PYTHONPATH=. python3 module/youtube/youtube.py \
    --export \
    --filename data/youtube/news.bak.db 
```
