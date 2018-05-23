# coding: utf-8
from scrapy import Spider
import json, time
from bs4 import BeautifulSoup
from scrapy.http import Request
from selenium import webdriver
import datetime
from scrapy.utils.response import get_base_url


class QaSpider(Spider):
    name = 'qa'
    allowed_domains = ['sd-n-tax.gov.cn']
    start_urls = ['http://www.sd-n-tax.gov.cn/col/col43805/index.html']

    def parse(self, response):
        file = open('qa.json', 'w', encoding='utf-8')
        file.truncate()
        file.close()
        url = 'http://www.sd-n-tax.gov.cn/col/col43805/index.html'
        driver = webdriver.Chrome()
        driver.get(url)
        line = ''
        try:
            f = open('date.json', 'r', encoding='utf-8')
            line = f.readline()
            f.close()
        except:
            line = ''
        i = 0
        print(u'更新到的知识库时间：', line)
        while driver.page_source.find('default_pgNextDisabled') == -1:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            node_list = soup.select('div.title_list.font15_wryh')[0].select('a')
            # if i == 0:
            # 	file = open('date.json', 'w',encoding='utf-8')
            # 	file.write(self.twrap('art/', '/art_', node_list[0]['href']).replace('/', '-'))
            # 	file.close()
            for node in node_list:
                timestr = self.twrap('art/', '/art_', node['href']).replace('/', '-')
                date_time = datetime.datetime.strptime(timestr, '%Y-%m-%d')
                if line.strip() != u'' and date_time <= datetime.datetime.strptime(line.strip(), '%Y-%m-%d'):
                    driver.close()
                    return
                href = 'http://www.sd-n-tax.gov.cn' + node['href']
                print(href)
                yield Request(url=href, callback=self.find_parse)

            for i in range(20):
                try:
                    driver.find_element_by_class_name('default_pgNext').click()
                    break
                except:
                    print(u'重新连接...')
                    time.sleep(1)

            if driver.page_source.find('default_pgNextDisabled') != -1:
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                node_list = soup.select('div.title_list.font15_wryh')[0].select('a')
                for node in node_list:
                    timestr = self.twrap('art/', '/art_', node['href']).replace('/', '-')
                    date_time = datetime.datetime.strptime(timestr, '%Y-%m-%d')
                    if line.strip() != u'' and date_time <= datetime.datetime.strptime(line.strip(), '%Y-%m-%d'):
                        return
                    href = 'http://www.sd-n-tax.gov.cn' + node['href']
                    print(href)
                    yield Request(url=href, callback=self.find_parse)
            i = i + 1

    def find_parse(self, response):
        node_list = response.xpath('//div[@id="contentText"]/p')
        base_url = get_base_url(response)
        timestr = self.twrap('art/', '/art_', base_url).replace('/', '-')
        content = ''
        flag = 0
        for node in node_list:
            li = node.xpath('string(.)').extract()[0].split('\r\n')
            for l in li:
                if flag == 0 and (l.endswith('?') or l.endswith('？')):
                    flag = 1
                if flag == 1 and l.strip() != '':
                    q = {'qa': '', 'title': ''}
                    q['qa'] = l
                    q['title'] = datetime.datetime.strptime(timestr, '%Y-%m-%d').strftime('%Y-%m-%d')
                    content = content + json.dumps(q, ensure_ascii=False) + ',\n'
        file = open('qa.json', 'a', encoding='utf-8')
        file.write(content)
        file.close()

    def twrap(self, start_str, end, html):
        start = html.find(start_str)
        if start >= 0:
            start += len(start_str)
            end = html.find(end, start)
            if end >= 0:
                return html[start:end].strip()
