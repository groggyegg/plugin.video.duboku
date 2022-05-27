"""
MIT License

Copyright (c) 2021 groggyegg

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from abc import abstractmethod
from os.path import join
from re import compile, search

from bs4 import BeautifulSoup
from bs4.element import SoupStrainer, NavigableString
from requests import Session
from requests.utils import requote_uri
from xbmcext import Dialog, getLocalizedString, getPath

__all__ = []


class Request(object):
    domains = 'duboku.tv', 'duboku.ru'
    session = Session()

    def get(self, path):
        for domain in self.domains:
            response = self.session.get('https://{}{}'.format(domain, path))

            if response.status_code == 200:
                return self.parse(response.text, path)

    @abstractmethod
    def parse(self, text, path):
        pass


class VodDetailRequest(Request):
    def parse(self, text, path):
        soup = BeautifulSoup(text, 'html.parser', parse_only=SoupStrainer('div', {'class': ['myui-content__thumb', 'myui-content__detail', 'col-pd text-collapse content']}))
        poster = soup.find('img').attrs['data-original']
        title = soup.find('h1').text
        setoverview, country, year = [a.text.strip() for a in soup.find_all('a', {'href': compile(r'/vodshow/\d*-[A-Z\d%]*----------\d*\.html')})]
        cast = [a.text.strip() for a in soup.find_all('a', {'href': compile(r'/vodsearch/-[A-Z\d%]+------------.html')})]
        director = [a.text.strip() for a in soup.find_all('a', {'href': compile(r'/vodsearch/-----[A-Z\d%]+--------.html')})]
        plot = soup.find('span', {'class': 'data'}).text
        return {'path': path, 'poster': requote_uri(poster), 'title': title, 'setoverview': setoverview, 'country': country,
                'year': int(year), 'cast': cast, 'director': director, 'plot': plot}


class VodSearchRequest(Request):
    def parse(self, text, path):
        soup = BeautifulSoup(text, 'html.parser', parse_only=SoupStrainer('a', {'class': ['searchkey', 'btn btn-default', 'btn  btn-warm']}))
        warm = soup.find('a', {'class': 'btn btn-warm'}).attrs['href']
        return [a.attrs['href'] for a in soup.find_all('a', {'class': 'searchkey'})], [(a.attrs['href'], a.text) for a in soup.find_all('a', {'class': 'btn btn-default'}) if a.attrs['href'] != warm]


m = VodDetailRequest().get('/voddetail/2750.html')
m = VodSearchRequest().get('/vodsearch/he----------1---.html')
pass
