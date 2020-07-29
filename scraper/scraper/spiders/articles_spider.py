import scrapy
from bs4 import BeautifulSoup
import re

class ArticlesSpider(scrapy.Spider):
    name = "articles"

    start_urls = [
        'https://medium.com/topics'
    ]

    def parse(self, response):
        #fetches the pages for each medium topic
        links = response.css('a')
        for i in range(20, 205, 2):
            soup = BeautifulSoup(links[i].extract(), 'html.parser')
            link = soup.a.get('href')
            yield response.follow(link, callback=self.parseTopics)

    def parseTopics(self, response):
        articles = response.css('h3.ap.q').xpath('./a/@href')
        for i in range(len(articles)):
            # the fourth entry currently is a writer feature card which doesn't match
            # the further scraping routine
            if i != 4:
                fullLink = articles[i].extract()
                yield response.follow(fullLink, callback=self.parseArticles)

    def postprocess(self, original):
        #post processing
        text = original.replace('( ', '(')
        text = text.replace('\u201c', '"')
        text = text.replace('\u201d', '"')
        parentheticals = re.findall('\([^()]*\)', text)
        quotes = re.findall('"[^"]*"', text)
        for paren in parentheticals:
            words = paren.split(' ')
            if len(words) > 3:
                text = text.replace(paren, paren[1:len(paren) - 1])
        for quote in quotes:
            words = quote.split(' ')
            if len(words) > 3:
                text = text.replace(quote, quote[1:len(quote) - 1])

        text = re.sub('Sources.*', '', text, flags=re.DOTALL)
        text = re.sub('Written by.*', '', text, flags=re.DOTALL)
        text = re.sub('Written By.*', '', text, flags=re.DOTALL)
        text = re.sub('written by.*', '', text, flags=re.DOTALL)
        text = re.sub('References.*', '', text, flags=re.DOTALL)
        text = re.sub('Further Reading.*', '', text, flags=re.DOTALL)
        text = re.sub(' .*@.*', '', text, flags=re.DOTALL)
        text = re.sub('http.*', '', text)
        text = re.sub('www.*', '', text)
        text = re.sub('Credit:.*', '', text)
        text = re.sub('Copyright.*', '', text)
        text = re.sub('\u00A9.*', '', text)
        text = re.sub('\u00Ae.*', '', text)
        text = re.sub('Trademark.*', '', text)
        text = re.sub('Illustration:.*', '', text)
        text = re.sub('Illustrations:.*', '', text)
        text = re.sub('Photo:.*', '', text)
        text = re.sub('Photo by.*', '', text)
        text = re.sub('\[\d\]', '', text)
        text = re.sub('\(\d\)', '', text)
        text = re.sub('#\d', '', text)
        text = text.strip()
        text = re.sub(' +', ' ', text)

        return text

    def parseArticles(self, response):
        # extract the text from each article
        scrapedFile = ''
        for paragraph in response.css('p'):
            soup = BeautifulSoup(paragraph.extract(), 'html.parser')
            text = soup.get_text()
            text = self.postprocess(text)

            scrapedFile += '<p>' + text + '</p>'

        yield {'text': scrapedFile}

