
# 크롤러 설정 파일

# 구조

```yaml
---
jobs:
- index: raw-donga-cn-{year}
  
  article: 
    document_id: {}
      
  list: []
  
parsing:
  version: v2021-01-26

  parser: html5lib
  
  trace: []

  list: []

  article: []
```

## 저장될 인덱스 이름: jobs.index

문서(기사) 목록의 날짜에서 년도 정보를 {year}로 바꾼다.
날자가 없는 경우 -{year} 를 삭제한 인덱스를 사용한다.

```yaml
jobs:
- index: raw-donga-cn-{year}
```

## 문서 번호: jobs.article.document_id

문서 아이디 추출 정보 query, path 가 있다. 

* query 

> url: https://news.naver.com/main/read.nhn?mode=LSD&mid=shm&sid1=101&oid=421&aid=0005135218
>
> query 정보: mode=LSD&mid=shm&sid1=101&oid=421&aid=0005135218

```yaml
jobs:
- article:
    document_id:
      frame: '{oid}-{aid}'
      type: query
```

* path 

> url: https://www.donga.com/news/Economy/article/all/20210129/105175836/1
> 
> path 정보: /news/Economy/article/all/20210129/105175836/1

```yaml
jobs:
- article:
    document_id:
      replace:
      - from: /news/
        to: '/'
      - from: ^/
        to: ''
      - from: /
        to: '-'
      type: path
```

* value

```yaml
jobs:
- article:
    document_id:
      frame: '{document_id}'
      type: value
```

## 신문 기사 섹션(분류) 목록: jobs.list

* 크롤러 실행 옵션

```bash
python3 \
    -m crawler.web_news.web_news \
    --config config/naver/economy.yaml \
    --sub-category 경제/증권 \
    --date-range 2021-01-01~2021-12-31 \
    --date-step 1 \
    --page-range 1~20 \
    --page-step 1 \
    --sleep 10
```

* GET 조회 -> html 형식 응답

```yaml
jobs:
- list:
  - category: 경제/증권
    date_format: '%Y%m%d'
    url_frame: https://news.naver.com/main/list.nhn?date={date}&page={page}
```

* GET 조회 -> json 형식 응답

```yaml
jobs:
- list:
  - category: 야구/삼성
    url_frame: http://osen.mt.co.kr/api/probaseball/team_news/lions?offset={page}
    headers:
      Content-Type: application/json
```

* POST 조회 -> html 형식 응답

> TODO

* POST 조회 -> json 형식 응답

> TODO

## parsing.trace

글 목록에서 글 상자 하나의 테그 정보 

* bs4 select 함수 호촐 방식

```yaml
parsing:
  trace:
  - select: div.list_body.newsflash_body li
```

* bs4 select 함수 호촐 방식

```yaml
parsing:
  trace:
  - name: div
    attribute:
      class: list_body newsflash_body
  - name: li
    attribute:
      class: item
```

## parsing.list

```yaml
parsing:
  list:
  - key: title
    value:
    - name: div
      attribute:
        class: title
    type: text
  - key: url
    value:
    - select: a.url
    type: href
  - key: date
    value:
    - select: span#date
    type: text
    convert:
      to: date
      merge: single
```

## parsing.article

```yaml
parsing:
  article:
  - key: html
    value:
    - name: html
    remove:
    - name: script
    - name: style
    - name: comment
    - name: div
      attribue:
        role: date
    - select: div[role=date]
    type: html
  - key: title
    value:
    - select: div.article_info
    type: text
  - key: content
    value:
    - select: div#articleBodyContents
    type: text
```

## 파서 타입: parsing.parser

soup = BeautifulSoup(resp, 'html5lib')

* default

```yaml
parsing:
  parser: html5lib
```

```yaml
parsing:
  parser: lxml
```

## html 파싱 정보 버전: parsing.version

```yaml
parsing:
  version: v2021-01-26
```
