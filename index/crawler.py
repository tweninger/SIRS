from scrapy.crawler import CrawlerProcess
from scrapy import Spider, Request
from scrapy.http import HtmlResponse
from urllib.parse import urlparse, quote
from definitions import ROOT_DIR
import tarfile
import os


class NDCrawler(Spider):
    name = "NDCrawler"
    tmp = os.path.join(ROOT_DIR, 'data')
    data = os.path.join(ROOT_DIR, 'data')

    custom_settings = {
        'DEPTH_LIMIT': 3,
    }

    def start_requests(self):
        urls = [
            'http://cse.nd.edu',
        ]

        for url in urls:
            yield Request(url=url, callback=self.parse)

    def parse(self, response):
        if isinstance(response, HtmlResponse):
            url = response.url
            if 'text/html' not in response.headers['Content-Type'].decode('utf-8'):
                return
            if url.startswith('http://'):
                url = url[7:]
            if url.startswith('https://'):
                url = url[8:]
            if url.endswith('/'):
                url = url[:-1]

            encoded_url = quote(url, safe='')
            encoded_url = os.path.join(NDCrawler.tmp, encoded_url)
            with open(encoded_url, 'wb+') as file:
                file.write(response.body)
            with tarfile.open(os.path.join(NDCrawler.data, NDCrawler.name) + "_result_large" + ".tar", "a") as tar:
                tar.add(encoded_url)
            os.remove(encoded_url)

            urls = response.xpath('//@href').extract()
            for url in urls:
                url = response.urljoin(url)
                parsed_url = urlparse(url)
                if parsed_url.hostname is not None and parsed_url.hostname.endswith('nd.edu'):
                    yield Request(url, callback=self.parse)
                else:
                    pass
            self.log('Saved file %s' % response.url)


process = CrawlerProcess({
    'USER_AGENT': 'netid@nd.edu'
})

process.crawl(NDCrawler)
process.start()  # the script will block here until the crawling is finished

