import scrapy
from scrapy.http.response.html import HtmlResponse
from scrapy.selector import Selector
from logging import INFO
from dateutil.parser import parse as parse_date


class MarketwatchSpider(scrapy.Spider):

    name = 'marketwatch'
    allowed_domains = ['marketwatch.com']

    start_urls = [
        'https://www.marketwatch.com/latest-news'
    ]

    index = 'adhoc-marketwatch'

    history = set()

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse_list)

    def parse_list(self, response: HtmlResponse):
        msg_id = None
        position = response.css('div.column.column--primary ::attr(data-layout-position)').get()
        channel_id = response.css('div.column.column--primary ::attr(data-channel-id)').get()

        for item in response.css('div.element.element--article'):
            url = item.css('.article__headline a.link ::attr(href)').get()
            title = ''.join([x.get().strip() for x in item.css('.article__headline *::text')])

            m_id = item.css('::attr(data-msgid)').get()
            if m_id:
                msg_id = m_id

            if url is None or url == '#':
                continue

            url = url.strip()
            title = title.strip()

            if url in self.history:
                continue

            self.history.add(url)

            self.logger.log(level=INFO, msg={
                'url': url,
                'title': title
            })

            yield scrapy.Request(
                url=url,
                callback=self.parse_article,
                cb_kwargs=dict(url=url, title=title, list_item=item.get())
            )

        if msg_id and position and channel_id:
            next_url = f'https://www.marketwatch.com/latest-news?messageNumber={msg_id}&channelId={channel_id}&position={position}&partial=true'
            yield scrapy.Request(url=next_url, callback=self.parse_list)

    def parse_article(self, response: HtmlResponse, url: str = None, title: str = None, list_item: str = None):
        date = response.css('time.timestamp ::text').get()
        if date:
            date = date.split(':', maxsplit=1)[-1].strip()
            date = parse_date(date, tzinfos={"ET": -4*3600})

        contents = [x.get().strip() for x in response.css('div[itemprop=articleBody] *::text')]

        return {
            '_index': self.index,
            '_id': url.split('?')[0].split('/')[-1],
            'url': url,
            'title': title,
            'date': date,
            'contents': '\n'.join(contents).strip(),
            'raw': response.body.decode('utf-8'),
            'list_raw': list_item
        }

# https://www.scrapingbee.com/blog/scrapy-javascript/
