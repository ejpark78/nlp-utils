# crawler

```bash
python3 -m crawler.web_news.web_news \
    --overwrite \
    --config config/naver/economy.yaml \
    --sub-category 경제/증권 \
    --date-range 2020-12-31~2020-12-31 \
    --sleep 10
```

## crawler.web_news.web_news

1. batch()
   
2. trace_category(self, job: dict)
   > config
   ```yaml
   jobs:
   - list:
     - category: 경제/증권
       date_format: '%Y%m%d'
       url_frame: https://news.naver.com/main/list.nhn?date={date}&page={page}
   ```
3. trace_page(self, url_info: dict, job: dict, dt: datetime = None)
4. **trace_news(self, html: str, url_info: dict, job: dict, date: datetime, es: ElasticSearchUtils)**
5. trace_next_page(html: str, url_info: dict, job: dict, date: datetime, es: ElasticSearchUtils)


### trace_news(self, html: str, url_info: dict, job: dict, date: datetime, es: ElasticSearchUtils)

```python
 def trace_news(self, html: str, url_info: dict, job: dict, date: datetime, es: ElasticSearchUtils) -> bool:
        """개별 뉴스를 따라간다."""
        trace_list = self.get_trace_list(html=html, url_info=url_info)
        # CHECK: parsing.trace
        if trace_list is None:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': 'trace_list 가 없음: 조기 종료',
                'url': url_info['url'] if 'url' in url_info else '',
                **job,
            })
            return True

        # (...)

        # 개별 뉴스를 따라간다.
        for trace in trace_list:
            item = self.parse_tag(
                resp=trace,
                url_info=url_info,
                base_url=base_url,
                parsing_info=self.config['parsing']['list'],
            )
            # CHECK: parsing.list
            if item is None or 'url' not in item:
                continue

            # (...)

            doc_id = self.get_doc_id(url=item['url'], job=job, item=item)
            # CHECK: jobs.article.document_id
            if doc_id is None:
                continue

            # (...)

            # 기사 본문 조회
            article_html = self.get_article_page(item=item, offline=False)

            # 문서 저장
            article = self.parse_tag(
                resp=article_html,
                url_info=item,
                base_url=item['url'],
                parsing_info=self.config['parsing']['article'],
            )
            # CHECK: parsing.article
            if article is None or len(article) == 0:
                continue

            # 댓글 post process 처리
            self.post_request(article=article, job=job, item=item)

            # 기사 저장
            self.save_article(
                job=job,
                doc=item,
                html=article_html,
                article=article,
                es=es,
            )

            # (...)
            sleep(self.params.sleep)

        # (...)

        # 다음 페이지 정보가 있는 경우
        self.trace_next_page(html=html, url_info=url_info, job=job, date=date, es=es)

        return False

```
