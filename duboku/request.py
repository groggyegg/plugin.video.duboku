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

from re import compile, match, search

from bs4 import BeautifulSoup, SoupStrainer
from requests import Session
from xbmcext import Log, urlparse
from xbmcext.pymaybe import maybe


class Request(object):
    session = Session()

    @classmethod
    def get(cls, path):
        url = 'https:/{}'.format(path)
        Log.info('[plugin.video.duboku] GET "{}"'.format(url))
        response = cls.session.get(url)

        if response.status_code == 200:
            return response.text

        raise Exception()

    @classmethod
    def post(cls, url, **params):
        response = cls.session.post(url, params=params)

        if response.status_code == 200:
            return

        raise Exception()

    @classmethod
    def netloc(cls, path):
        url = urlparse('https:/{}'.format(path))
        return url.netloc

    @classmethod
    def urlunsplit(cls, netloc, path):
        return path if path.startswith('https://') else 'https:/{}'.format(cls.urljoin(netloc, path))

    @classmethod
    def urljoin(cls, netloc, path):
        return '/{}{}'.format(netloc, path)

    @classmethod
    def vodshow(cls, path):
        netloc = cls.netloc(path)
        parse_only = SoupStrainer(['div', 'ul'], {'class': ['myui-panel myui-panel-bg clearfix', 'myui-page text-center clearfix']})
        doc = BeautifulSoup(cls.get(path), 'html.parser', parse_only=parse_only)
        shows = [cls.urljoin(netloc, a.attrs['href']) for a in doc.find('div', {'class': 'myui-panel_bd'}).find_all('a', {'data-original': True})]
        selected = maybe(doc.find('a', {'class': 'btn btn-warm'})).attrs['href']
        pages = [(cls.urljoin(netloc, a.attrs['href']), a.text) for a in doc.find_all('a', text=['上一页', '下一页']) if a.attrs['href'] != selected]
        return shows, pages

    @classmethod
    def voddetail(cls, path):
        netloc = cls.netloc(path)
        parse_only = SoupStrainer(['div', 'span'], {'class': ['data', 'myui-content__detail', 'myui-content__thumb', 'myui-msg__head text-center', 'myui-msg__body']})
        doc = BeautifulSoup(cls.get(path), 'html.parser', parse_only=parse_only)
        pwd = doc.find('p', {'class': 'text-red'})

        if pwd:
            pwd = match('密码：(.+)', pwd.text).group(1)
            attrs = doc.find('a', {'data-id': True, 'data-mid': True, 'data-type': True}).attrs
            cls.post(cls.urlunsplit(netloc, '/index.php/ajax/pwd.html'), id=attrs['data-id'], mid=attrs['data-mid'], pwd=pwd, type=attrs['data-type'])
            doc = BeautifulSoup(cls.get(path), 'html.parser', parse_only=parse_only)

        return {'path': path,
                'poster': cls.urlunsplit(netloc, doc.find('img').attrs['data-original']),
                'title': doc.find('h1').text,
                'plot': ' '.join(doc.find('span', {'class': 'data'}).text.replace('&nbsp;', '').split()),
                'category': cls.category(search('分类：(.+)', doc.find('p', {'class': 'data'}).text).group(1)),
                'country': cls.country(search('地区：(.+)', doc.find('p', {'class': 'data'}).text).group(1)),
                'year': int(search('年份：(.+)', doc.find('p', {'class': 'data'}).text).group(1).replace('未知', '0'))}

    @staticmethod
    def category(category):
        return {'日韩剧': 30016,
                '台泰剧': 30018,
                '陆剧': 30015,
                '港剧': 30019,
                '短剧': 30130,
                '英美剧': 30017,
                '综艺': 30004,
                '动漫': 30005,
                '连续剧': 30002,
                '剧情片': 30134,
                '恐怖片': 30135,
                '喜剧片': 30136,
                '战争片': 30137,
                '动作片': 30138,
                '爱情片': 30139,
                '科幻片': 30140,
                '电影': 30003}.get(category, 30112)

    @staticmethod
    def country(countries):
        translate = {'其他': 30112,
                     '内地': 30043,
                     '台湾': 30046,
                     '国产': 30128,
                     '巴西': 30049,
                     '日本': 30054,
                     '法国': 30053,
                     '泰国': 30051,
                     '美国': 30047,
                     '英国': 30048,
                     '荷兰': 30055,
                     '韩国': 30044,
                     '香港': 30045}
        countries = {id for country, id in translate.items() if country in countries}
        return sorted(countries) if countries else [30112]

    @classmethod
    def voddetail_playlist(cls, path):
        doc = BeautifulSoup(cls.get(path), 'html.parser', parse_only=SoupStrainer('a', {'href': compile('#playlist\\d')}))
        return [(a.attrs['href'].strip('#'), a.text) for a in doc.find_all('a')]

    @classmethod
    def voddetail_episode(cls, path, id):
        netloc = cls.netloc(path)
        doc = BeautifulSoup(cls.get(path), 'html.parser', parse_only=SoupStrainer('div', {'id': id}))
        return [(cls.urljoin(netloc, a.attrs['href']), a.text) for a in doc.find_all('a')]

    @classmethod
    def vodplay(cls, path):
        netloc = cls.netloc(path)
        doc = BeautifulSoup(cls.get(path), 'html.parser', parse_only=SoupStrainer('h2'))
        return cls.urljoin(netloc, doc.find('a').attrs['href']), ' '.join(doc.text.split())
