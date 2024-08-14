import re
import json
import random
import asyncio
import hashlib
import logging
import traceback
from pathlib import Path
from urllib.parse import urlparse

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from bs4 import BeautifulSoup
from tor_python_easy.tor_control_port_client import TorControlPortClient

import s3_utils


BASE_URL = None
OUTPUT_FOLDER = 'output'

LOGGER = logging.getLogger()
LOGGER.setLevel("INFO")


def hash_string(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


def parse_html(html_content: str) -> str:
    soup = BeautifulSoup(html_content, 'lxml')
    for element in soup(['script', 'style', 'img', 'canvas', 'iframe', 'form', 'noscript', 'footer', 'nav']):
        element.decompose()

    textual_content = soup.get_text()
    textual_content = re.sub(' +', ' ', textual_content)
    textual_content = re.sub('\n+', '\n', textual_content)

    return textual_content


def build_clean_link(link: str):
    parsed_link = urlparse(link)
    return parsed_link, f'{parsed_link.scheme}://{parsed_link.netloc}{parsed_link.path}'


class TorSpider(scrapy.Spider):
    name = "TorSpider"
    proxy_url = 'http://localhost:8118'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parsed_link, self.base_url = build_clean_link(BASE_URL)
        self.visited = set()
        self.output_folder = Path(OUTPUT_FOLDER)
        self.output_folder.mkdir(exist_ok=True)
        self.link_extractor = LinkExtractor(allow=rf'{self.base_url}.*')

        self.tor_control_port_client = TorControlPortClient('localhost', 9051)

    def _set_new_ip(self, probability=.1):
        if random.random() < probability:
            self.tor_control_port_client.change_connection_ip(seconds_wait=1)

    def start_requests(self):
        LOGGER.info('Starting to scrape...')
        self._set_new_ip()
        user_agent = random.choice(self.settings.get('USER_AGENT_LIST'))
        yield scrapy.Request(
            url=self.base_url, callback=self.html_response_parser, headers={'User-Agent': user_agent},
            meta={'proxy': self.proxy_url}
        )

    def html_response_parser(self, response):
        if not response.url.startswith(self.base_url):
            return
        LOGGER.info(f'Saving {response.url}...')
        text_content = parse_html(response.text)
        file_name = f'{hash_string(response.url)}_{hash_string(text_content)}.txt'
        Path(self.output_folder, file_name).write_text(text_content)
        with open(Path(self.output_folder, f'{file_name}.metadata.json'), 'w') as f:
            json.dump({"metadataAttributes": {"url": response.url}}, f, indent=4)
        self.visited.add(response.url)

        for link in self.link_extractor.extract_links(response):
            _, clean_link = build_clean_link(link.url)
            if clean_link.startswith('/'):
                clean_link = f'{self.parsed_link.scheme}://{self.parsed_link.netloc}{link}'
            if not clean_link.startswith(self.base_url) or clean_link in self.visited:
                continue
            user_agent = random.choice(self.settings.get('USER_AGENT_LIST'))
            yield response.follow(
                clean_link, callback=self.html_response_parser, headers={'User-Agent': user_agent},
                meta={'proxy': self.proxy_url}
            )


async def commit_into_s3(bucket_prefix):
    files = [f for f in Path(OUTPUT_FOLDER).glob('*')]
    if not files:
        LOGGER.warning('No url scraped. Aborting.')
        return
    LOGGER.info(f'Saving {len(files)} files into s3...')
    try:
        backup_folder = await s3_utils.make_backup(bucket_prefix)
        s3_utils.delete_folder(bucket_prefix)
        await s3_utils.upload_files(bucket_prefix, files)
        s3_utils.delete_folder(backup_folder)
    except:
        LOGGER.error(traceback.format_exc())
        LOGGER.error('Restoring backup...')
        await s3_utils.restore_backup(bucket_prefix)


def crawl(base_url):
    settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
        },
        'RETRY_TIMES': 5,
        'DOWNLOAD_DELAY': 3,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'AUTOTHROTTLE_DEBUG': False,
        'USER_AGENT_LIST': [ua for ua in Path('user_agents.txt').read_text().split('\n') if 'Mobile' not in ua],
        'LOG_LEVEL': 'INFO',
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
    }

    global BASE_URL
    BASE_URL = base_url

    process = CrawlerProcess(settings)
    process.crawl(TorSpider)
    process.start()


if __name__ == '__main__':
    import argparse

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    parser = argparse.ArgumentParser(description="Web scraping tool")
    parser.add_argument("url", help="Target url for scraping")
    parser.add_argument("bucket_prefix", help="s3 bucket's location")
    args = parser.parse_args()

    base_url = args.url
    bucket_prefix = args.bucket_prefix

    crawl(base_url)
    asyncio.run(commit_into_s3(bucket_prefix))
