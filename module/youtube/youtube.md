
## 유튜브 크롤러 개발 

```sql

DELETE FROM channels WHERE id != '삼프로tv';

DELETE FROM videos WHERE tags LIKE '%삼프로tv%';

```

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
