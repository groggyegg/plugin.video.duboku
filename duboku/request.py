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

from re import compile, split, match

from bs4 import BeautifulSoup, SoupStrainer
from requests import Session
from xbmcext import urlparse


def get(path):
    response = session.get('https:/{}'.format(path))

    if response.status_code == 200:
        return response.text

    raise Exception()


def post(path, **params):
    response = session.post('https:/{}'.format(path), params=params)

    if response.status_code == 200:
        return

    raise Exception()


def vodshow(path):
    _, netloc, _, _, _, _ = urlparse('https:/{}'.format(path))
    strainer = SoupStrainer(['div', 'ul'], {'class': ['myui-panel myui-panel-bg clearfix', 'myui-page text-center clearfix']})
    soup = BeautifulSoup(get(path), 'html.parser', parse_only=strainer)
    return ['/{}{}'.format(netloc, a.attrs['href']) for a in soup.find('div', {'class': 'myui-panel_bd'}).find_all('a', {'class': 'myui-vodlist__thumb'})]


def voddetail(path):
    _, netloc, _, _, _, _ = urlparse('https:/{}'.format(path))
    attrs = {'class': ['data', 'myui-content__detail', 'myui-content__thumb', 'myui-msg__head text-center', 'myui-msg__body']}
    strainer = SoupStrainer(['div', 'span'], attrs)
    soup = BeautifulSoup(get(path), 'html.parser', parse_only=strainer)
    pwd = soup.find('p', {'class': 'text-red'})

    if pwd:
        pwd = match('密码：(.+)', pwd.text).group(1)
        attrs = soup.find('a', {'data-id': True, 'data-mid': True, 'data-type': True}).attrs
        post('https://{}/index.php/ajax/pwd.html'.format(netloc), id=attrs['data-id'], mid=attrs['data-mid'], pwd=pwd, type=attrs['data-type'])
        soup = BeautifulSoup(get(path), 'html.parser', parse_only=strainer)

    poster = soup.find('img').attrs['data-original']

    return {'path': path,
            'poster': poster if poster.startswith('https://') else 'https://{}{}'.format(netloc, poster),
            'title': {'zh': soup.find('h1').text},
            'plot': {'zh': soup.find('span', {'class': 'data'}).text.replace('　', '')},
            'category': {'zh': soup.find('span', text='分类：').next_sibling.text},
            'country': {'zh': sorted(filter(None, map(str.strip, split(',|/|\u3001', soup.find('span', text='地区：').next_sibling.text))))},
            'cast': {'zh': sorted(filter(None, split(',|\xa0', soup.find('span', text='主演：').parent.text.lstrip('主演：'))))},
            'director': {'zh': sorted(filter(None, split(',|\xa0', soup.find('span', text='导演：').parent.text.lstrip('导演：'))))},
            'year': int(soup.find('span', text='年份：').next_sibling.text.replace('未知', '0'))}


def vodplaylist(path):
    soup = BeautifulSoup(get(path), 'html.parser', parse_only=SoupStrainer('a', {'href': compile('#playlist\\d')}))
    return [(a.text, a.attrs['href'].strip('#')) for a in soup.find_all('a')]


def vodepisode(path, id):
    _, netloc, _, _, _, _ = urlparse('https:/{}'.format(path))
    soup = BeautifulSoup(get(path), 'html.parser', parse_only=SoupStrainer('div', {'id': id}))
    return [('/{}{}'.format(netloc, a.attrs['href']), {'zh': a.text}) for a in soup.find_all('a')]


def vodvideo(path):
    _, netloc, _, _, _, _ = urlparse('https:/{}'.format(path))
    soup = BeautifulSoup(get(path), 'html.parser', parse_only=SoupStrainer('h2'))
    return '/{}{}'.format(netloc, soup.find('a').attrs['href']), {'zh': soup.text.replace('\n', ' ').strip()}


session = Session()
