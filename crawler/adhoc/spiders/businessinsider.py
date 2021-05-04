from logging import INFO
from urllib.parse import urlparse, parse_qs

import scrapy
from scrapy.http.response.html import HtmlResponse


class BusinessinsiderSpider(scrapy.Spider):

    name = 'businessinsider'
    allowed_domains = ['businessinsider.com']

    start_urls = [
        'https://www.businessinsider.com/latest'
    ]

    index = 'adhoc-businessinsider'

    history = set()

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse_list)

    def parse_list(self, response: HtmlResponse, global_index: int = 1):
        next_data = response.css('section#l-content ::attr(data-next)').get()

        if global_index > 1:
            latest = response.json()['latest']
            next_data = latest['links']['next']
            response = response.replace(body=latest['rendered'])

        for item in response.css('section.river-item.featured-post'):
            url = item.css('a.tout-title-link ::attr(href)').get()
            title = ''.join([x.get().strip() for x in item.css('a.tout-title-link *::text')])

            if url is None or url == '#':
                continue

            url = response.urljoin(url.strip())
            title = title.strip()

            if url in self.history:
                continue

            self.history.add(url)

            self.logger.log(level=INFO, msg={
                'url': url,
                'title': title
            })

            if title == '':
                pass

            yield scrapy.Request(
                url=url,
                callback=self.parse_article,
                cb_kwargs=dict(url=url, title=title, list_item=item.get())
            )

        q = {k: v[0] for k, v in parse_qs(urlparse(next_data).query).items()}

        global_index += 20

        next_url = 'https://www.businessinsider.com/ajax/content-api/category/latest?templateId=river'
        next_url += '&filter[format]={!static-page}'
        next_url += '&filter[vertical]={!reuters,!associated-press,!intelligence}'
        next_url += '&page[limit]=20'
        next_url += '&globalIndex=' + str(global_index)
        next_url += '&page[after]=' + q['page[after]']

        yield scrapy.Request(
            url=next_url,
            callback=self.parse_list,
            cb_kwargs=dict(global_index=global_index)
        )

    def parse_article(self, response: HtmlResponse, url: str = None, title: str = None, list_item: str = None):
        contents = [x.get().strip() for x in response.css('div.content-lock-content *::text')]

        return {
            '_index': self.index,
            '_id': url.split('?')[0].split('/')[-1],
            'url': url,
            'title': title,
            'contents': '\n'.join(contents).strip(),
            'raw': response.body.decode('utf-8'),
            'list_raw': list_item
        }
