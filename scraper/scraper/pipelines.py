# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import boto3

class ScraperPipeline:

    def __init__(self, sqs_url):
        self.sqs_url = sqs_url

    @classmethod
    def from_crawler(cls, crawler):
        return cls(sqs_url=crawler.settings.get('SQS_URL'))

    def open_spider(self, spider):
        sqs = boto3.resource('sqs')
        self.queue = sqs.Queue(self.sqs_url)

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        self.queue.send_message(MessageBody=item['text'])
        return item