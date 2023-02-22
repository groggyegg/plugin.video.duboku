"""
MIT License

Copyright (c) 2023 groggyegg

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

from collections import defaultdict
from os.path import exists, join
from pickle import dump, load
from re import compile, search, match, split
from time import sleep

from bs4 import BeautifulSoup, SoupStrainer
from requests import Session
from xbmcext import getAddonPath


class DubokuTv(object):
    session = Session()
    session_path = join(getAddonPath(), 'resources/data/session')
    url = 'https://www.duboku.tv{}'

    @classmethod
    def dump_session(cls):
        with open(cls.session_path, 'wb') as file:
            dump(cls.session, file)

    @classmethod
    def load_session(cls):
        if exists(cls.session_path):
            with open(cls.session_path, 'rb') as file:
                cls.session = load(file)

    @classmethod
    def get(cls, url):
        response = cls.session.get(url)

        if response.status_code == 200:
            return response.text

        raise Exception()

    @classmethod
    def post(cls, path, **params):
        response = cls.session.post(cls.url.format(path), params=params)

        if response.status_code == 200:
            return

        raise Exception()

    @classmethod
    def vodfilter(cls, path):
        filter = []
        preselect = {}
        soup = BeautifulSoup(cls.get(cls.url.format(path)), 'html.parser', parse_only=SoupStrainer('div', {'class': 'myui-panel_bd'}))

        for a in soup.find('div', {'class': 'myui-panel_bd'}).find_all('a'):
            if 'text-muted' in a.attrs['class'] and '类型' not in a.text:
                filter.append((a.text, {}))
            elif filter:
                if 'btn-warm' in a.attrs['class']:
                    preselect[filter[-1][0]] = a.text

                filter[-1][-1][a.text] = a.attrs['href']

        return dict(filter), preselect

    @classmethod
    def vodsearch(cls, path):
        search = []
        paging = []
        soup = BeautifulSoup(cls.get(cls.url.format(path)), 'html.parser', parse_only=SoupStrainer('a'))

        for a in soup.find_all('a', {'class': 'searchkey'}):
            search.append(a.attrs['href'])

        for a in soup.find_all('a', {'href': compile('/vodsearch/.+----------\\d+---\\.html')}):
            paging.append((a.attrs['href'], a.text, 'btn-warm' in a.attrs['class']))

        return search, paging

    @classmethod
    def vodshow(cls, path):
        show = []
        paging = []
        strainer = SoupStrainer(['div', 'ul'], {'class': ['myui-panel myui-panel-bg clearfix', 'myui-page text-center clearfix']})
        soup = BeautifulSoup(cls.get(cls.url.format(path)), 'html.parser', parse_only=strainer)

        for a in soup.find('div', {'class': 'myui-panel_bd'}).find_all('a', {'class': 'myui-vodlist__thumb'}):
            show.append(cls.url.format(a.attrs['href']))

        for a in soup.find_all('a', {'class': 'btn', 'href': True}):
            paging.append((a.attrs['href'], a.text, 'btn-warm' in a.attrs['class']))

        return show, paging

    @classmethod
    def voddetail(cls, url):
        attrs = {'class': ['data', 'myui-content__detail', 'myui-content__thumb', 'myui-msg__head text-center', 'myui-msg__body']}
        strainer = SoupStrainer(['div', 'span'], attrs)
        soup = BeautifulSoup(cls.get(url), 'html.parser', parse_only=strainer)
        pwd = soup.find('p', {'class': 'text-red'})

        if pwd:
            pwd = match('密码：(.+)', pwd.text).group(1)
            attrs = soup.find('a', {'data-id': True, 'data-mid': True, 'data-type': True}).attrs
            cls.post('/index.php/ajax/pwd.html', id=attrs['data-id'], mid=attrs['data-mid'], pwd=pwd, type=attrs['data-type'])
            sleep(3)
            soup = BeautifulSoup(cls.get(url), 'html.parser', parse_only=strainer)

        title = soup.find('h1').text
        plot = soup.find('span', {'class': 'data'}).text.replace('　', '')
        category = soup.find('span', text='分类：').next_sibling.text
        country = soup.find('span', text='地区：').next_sibling.text
        cast = list(filter(lambda s: s, split(',|\xa0', soup.find('span', text='主演：').parent.text.lstrip('主演：'))))
        director = list(filter(lambda s: s, split(',|\xa0', soup.find('span', text='导演：').parent.text.lstrip('导演：'))))

        return {'url': url,
                'poster': soup.find('img').attrs['data-original'],
                'title': defaultdict(lambda: title, {'zh': title}),
                'plot': defaultdict(lambda: plot, {'zh': plot}),
                'category': defaultdict(lambda: category, {'zh': category}),
                'country': defaultdict(lambda: country, {'zh': country}),
                'cast': defaultdict(lambda: cast, {'zh': cast}),
                'director': defaultdict(lambda: director, {'zh': director}),
                'year': int(soup.find('span', text='年份：').next_sibling.text.replace('未知', '0'))}

    @classmethod
    def vodplaylist(cls, path):
        soup = BeautifulSoup(cls.get(cls.url.format(path)), 'html.parser', parse_only=SoupStrainer('div', {'id': 'playlist1'}))
        return [(a.attrs['href'], a.text) for a in soup.find_all('a')]

    @classmethod
    def vodplay(cls, path):
        soup = BeautifulSoup(cls.get(cls.url.format(path)), 'html.parser', parse_only=SoupStrainer('div', {'class': 'col-pd'}))
        title = soup.find('h2')
        path = title.find('a').attrs['href']
        url = search('"url":"(.+?\\.m3u8)"', soup.find('script').text).group(1).replace('\\', '')
        return path, url, title.text.replace('\n', ' ').strip()


class DubokuRu(DubokuTv):
    url = 'https://duboku.ru{}'
