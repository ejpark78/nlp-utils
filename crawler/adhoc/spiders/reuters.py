#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from logging import INFO, DEBUG

import scrapy
import urllib3
from scrapy.http.response.html import HtmlResponse

from crawler.adhoc.utils import AdhocUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'


class ReutersSpider(scrapy.Spider):
    name = 'reuters'
    allowed_domains = ['www.reuters.com']

    start_urls = [
        'https://www.reuters.com/'
    ]

    def __init__(self, max_deep: int = 1024, index: str = 'adhoc-reuters', allowed_url_query: str = 'page',
                 history_lifetime: int = 12, *args, **kwargs):
        super(ReutersSpider, self).__init__(*args, **kwargs)

        self.deep = self.max_deep = max_deep

        self.utils = AdhocUtils(
            index=index,
            logger=self.logger,
            allowed_url_query=allowed_url_query,
            allowed_domains=self.allowed_domains,
            history_lifetime=history_lifetime,
        )

    def start_requests(self):
        self.utils.open()
        self.utils.del_old_history()

        for url in self.start_urls:
            self.deep = self.max_deep

            yield scrapy.Request(url, callback=self.extract_url, cb_kwargs=dict(is_start=True))

    def extract_url(self, response: HtmlResponse, is_start: bool = False):
        self.deep -= 1
        if self.deep < 0:
            return

        doc_id = self.utils.get_doc_id(url=response.url)
        self.utils.save_document(doc_id=doc_id, doc={
            'url': response.url,
            'raw': response.body.decode('utf-8')
        })

        for link_tag in response.css('body a'):
            url = link_tag.css('::attr(href)').get()
            if url is None or url == '' or url[0] == '#' or url in {'//'}:
                continue

            if is_start is False and self.utils.is_skip(url=response.urljoin(url)):
                continue

            self.logger.log(level=DEBUG, msg=url)
            self.utils.summary['extracted url count'] += 1

            yield response.follow(url, callback=self.extract_url)

        self.logger.log(level=INFO, msg=self.utils.summary)


"""
# url 복원 
'https://www.reuters.com/video/watch/biden-says-gop-is-having-mini-revolution-id729582174?chan=6g5ka85'
'https://www.reuters.com/news/archive/instagram.com/instagram.com//instagram.com/reuters?view=page&page=2&pageSize=10'
'https://www.reuters.com/news/archive/France-news?view=page&page=7&pageSize=10'


https://docs.scrapy.org/en/latest/intro/tutorial.html
"""
