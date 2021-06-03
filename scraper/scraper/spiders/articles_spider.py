import scrapy
from bs4 import BeautifulSoup

class ArticlesSpider(scrapy.Spider):
    name = "articles"

    start_urls = [
        'https://medium.com/topics'
    ]

    def parse(self, response):
        # fetches the pages for each medium topic
        links = response.css('a')
        for i in range(20, 205, 2):
            soup = BeautifulSoup(links[i].extract(), 'html.parser')
            link = soup.a.get('href')
            topic = link.split('/')[-1]
            yield response.follow(link, callback=self.parse_topics, cb_kwargs=dict(topic=topic))

    def parse_topics(self, response, topic):
        articles = response.css('h3.bh.fx').xpath('./a/@href')
        for i in range(len(articles)):
            link = articles[i].extract()
            if link[0] == '/':
                link = 'https://medium.com' + link
            yield response.follow(link, callback=self.parse_articles, cb_kwargs=dict(topic=topic, link=link))

    def parse_articles(self, response, topic, link):
        # extract the text from each article
        content = BeautifulSoup(response.css('article').extract()[0], 'html.parser').get_text(separator=' ')

        # remove metadata: author, post date, etc
        idx = content.find('·')
        content = content[idx + 2:]
        words = content.split(' ')
        if words[2] == 'read':
            words = words[3:]
        else:
            words = words[2:]

        # cut off the query string from the url when storing it
        link = link[:link.find('?')]

        yield {'topic': topic, 'url': link, 'text': ' '.join(words)}
