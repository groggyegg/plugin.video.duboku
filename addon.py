# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from cloudscraper import CloudScraper
from collections import OrderedDict
from routing import Plugin
from xbmc import Keyboard
from xbmcaddon import Addon
from xbmcgui import Dialog, ListItem

import json
import os
import pickle
import re
import xbmc
import xbmcplugin


class Duboku:
    profile = xbmc.translatePath(Addon().getAddonInfo('profile'))
    cache = profile + 'cache'

    def __init__(self):
        self._document = None
        self._domain = 'https://www.duboku.co'

        if os.path.exists(Duboku.cache):
            with open(Duboku.cache, 'rb') as i:
                self._session = pickle.load(i)
        else:
            os.makedirs(Duboku.profile)
            self._session = CloudScraper()

            with open(Duboku.cache, 'wb') as o:
                pickle.dump(self._session, o, pickle.HIGHEST_PROTOCOL)

    def pwd(self):
        params = {}
        element = self._document.find('div', {'class': 'myui-msg__head text-center'})
        params['pwd'] = element.find('p', {'class': 'text-red'}).text[-1]
        element = element.find_next_sibling('form').find('a', {'href': 'javascript:;'})
        params['id'] = element.attrs['data-id']
        params['mid'] = element.attrs['data-mid']
        params['type'] = element.attrs['data-type']
        response = self._session.post(self._domain + '/index.php/ajax/pwd.html', params=params)
        return json.loads(response.text)['code'] == 1

    def voddetail(self, path):
        response = self._session.get(self._domain + path)
        self._document = BeautifulSoup(response.text, 'html.parser')
        root = self._document.find('div', {'class': 'myui-panel myui-panel-bg clearfix'})
        element = root.find('div', {'class': 'myui-content__thumb'})
        poster = element.find('img').attrs['data-original']
        element = element.find_next_sibling('div', {'class': 'myui-content__detail'}).find('h1')
        title = element.text
        element = element.find_next_sibling('div', {'class': 'score'})
        rating = float(element.find('span', {'class': 'branch'}).text)
        element = element.find_next_sibling('p', {'class': 'data'})
        (genre, country, year) = [a.text for a in element.find_all('a')]
        element = element.find_next_sibling('p', {'class': 'data'}).find_next_sibling('p', {'class': 'data'})
        cast = [a.text for a in element.find_all('a')]
        element = element.find_next_sibling('p', {'class': 'data'})
        director = element.find('a').text
        root = root.find_next_sibling('div', {'id': 'desc'})
        plot = root.find('span', {'class': 'data'}).text
        root = root.find_next_sibling('div', {'class': 'myui-panel myui-panel-bg clearfix'}).find('div', {'id': 'playlist1'})
        xbmcplugin.setPluginCategory(plugin.handle, title)
        xbmcplugin.setContent(plugin.handle, 'videos')
        items = []

        for episode, element in enumerate(root.find_all('a')):
            item = ListItem(element.text)
            item.setArt({'poster': poster})
            item.setInfo('video', {'genre': genre,
                                   'country': country,
                                   'year': int(year),
                                   'episode': episode + 1,
                                   'rating': rating,
                                   'cast': cast,
                                   'director': director,
                                   'plot': plot,
                                   'title': title + ' ' + element.text})
            item.setProperty('IsPlayable', 'true')
            items.append((plugin.url_for_path(element.attrs['href']), item, False))

        xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
        xbmcplugin.endOfDirectory(plugin.handle)

    def vodplay(self, path):
        response = self._session.get(self._domain + path)
        url = re.search('"url":"([^"]+.m3u8)"', response.text).group(1).replace('\\', '')
        xbmcplugin.setResolvedUrl(plugin.handle, True, ListItem(path=url))

    def vodsearch(self, path):
        response = self._session.get(self._domain + path)
        self._document = BeautifulSoup(response.text, 'html.parser')
        root = self._document.find('div', {'class': 'myui-panel myui-panel-bg clearfix'})
        title = re.sub('[\n\r\t]| {2}', '', root.find('div', {'class': 'myui-panel_hd'}).text)
        xbmcplugin.setPluginCategory(plugin.handle, title)
        xbmcplugin.setContent(plugin.handle, 'videos')
        items = []

        for element in root.find_all('li', {'class': 'clearfix'}):
            element = element.find('div', {'class': 'thumb'})
            poster = element.find('a').attrs['data-original']
            element = element.find_next_sibling('div').find('h4')
            title = element.text
            href = element.find('a').attrs['href']
            element = element.find_next_sibling('p')
            director = element.find('span').next_sibling
            element = element.find_next_sibling('p')
            cast = element.find('span').next_sibling.split(',')
            element = element.find_next_sibling('p')
            (genre, country, year) = [span.next_sibling for span in element.find_all('span', {'class': 'text-muted'})]
            element = element.find_next_sibling('p')
            plot = element.find('span').next_sibling
            item = ListItem(title)
            item.setArt({'poster': poster})
            item.setInfo('video', {'genre': genre,
                                   'country': country,
                                   'year': int(year),
                                   'cast': cast,
                                   'director': director,
                                   'plot': plot,
                                   'title': title + ' ' + element.text})
            items.append((plugin.url_for_path(href), item, True))

        root = root.find_next_sibling('ul', {'class': 'myui-page text-center clearfix'})

        if root is not None:
            for element in root.find_all('li', {'class': ''})[1:-1]:
                element = element.find('a')
                href = element.attrs['href']

                if href != path:
                    item = ListItem('[COLOR orange]' + element.text + '[/COLOR]')
                    items.append((plugin.url_for_path(href), item, True))

        xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
        xbmcplugin.endOfDirectory(plugin.handle)

    def vodshow(self, path):
        response = self._session.get(self._domain + path)
        self._document = BeautifulSoup(response.text, 'html.parser')
        root = self._document.find('div', {'class': 'myui-panel myui-panel-bg clearfix'})
        items = []

        for element in root.find_all('li', {'class': 'col-lg-8 col-md-6 col-sm-4 col-xs-3'}):
            element = element.find('a')
            title = element.attrs['title']
            href = element.attrs['href']
            poster = element.attrs['data-original']
            element = element.find_next_sibling('div')
            plot = element.find('p', {'class': 'text text-overflow text-muted hidden-xs'}).text
            item = ListItem(title)
            item.setArt({'poster': poster})
            item.setInfo('video', {'plot': plot, 'title': title})
            items.append((plugin.url_for_path(href), item, True))

        root = root.find_next_sibling('ul')

        if root is not None:
            for element in root.find_all('li', {'class': ''})[1:-1]:
                element = element.find('a')
                href = element.attrs['href']

                if href != path:
                    item = ListItem('[COLOR orange]' + element.text + '[/COLOR]')
                    items.append((plugin.url_for_path(href), item, True))

        xbmcplugin.setPluginCategory(plugin.handle, self._document.find('title').text)
        xbmcplugin.setContent(plugin.handle, 'videos')
        xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
        xbmcplugin.endOfDirectory(plugin.handle)

    def vodshow_filtering(self, path):
        while True:
            response = self._session.get(self._domain + path)
            self._document = BeautifulSoup(response.text, 'html.parser')
            root = self._document.find('div', {'class': 'slideDown-box'})
            headers = OrderedDict()
            items = []

            for element in root.find_all('ul', {'class': 'myui-screen__list nav-slide clearfix'}):
                header = element.find('a').text
                headers[header] = element.find_all('a', href=True)
                item = '[COLOR gray]' + element.find('a').text + '[/COLOR] |'

                for a in headers[header]:
                    item += ' [COLOR orange]' + a.text + '[/COLOR]' if 'btn-warm' in a.attrs['class'] else ' ' + a.text

                items.append(item)

            position = Dialog().select('過濾', items)

            if position != -1:
                (header, items) = list(headers.items())[position]
                position = Dialog().select(header, ['[COLOR orange]' + a.text + '[/COLOR]' if 'btn-warm' in a.attrs['class'] else a.text for a in items])

                if position != -1:
                    path = items[position].attrs['href']
            else:
                break

        self.vodshow(path)


duboku = Duboku()
plugin = Plugin()


@plugin.route('/')
def index():
    xbmcplugin.setPluginCategory(plugin.handle, '独播库')
    xbmcplugin.setContent(plugin.handle, 'videos')
    items = [(plugin.url_for_path('/vodsearch/----------1---.html'), ListItem('搜索'), True),
             (plugin.url_for_path('/vodshow_filtering/2--------1---.html'), ListItem('连续剧'), True),
             (plugin.url_for_path('/vodshow_filtering/1--------1---.html'), ListItem('电影'), True),
             (plugin.url_for_path('/vodshow_filtering/3--------1---.html'), ListItem('综艺'), True),
             (plugin.url_for_path('/vodshow_filtering/4--------1---.html'), ListItem('动漫'), True)]
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/voddetail/<id>')
def voddetail(id):
    try:
        duboku.voddetail('/voddetail/' + id)
    except:
        if duboku.pwd():
            duboku.voddetail('/voddetail/' + id)


@plugin.route('/vodplay/<id>')
def vodplay(id):
    duboku.vodplay('/vodplay/' + id)


@plugin.route('/vodsearch/<query>')
def vodsearch(query):
    if query == '----------1---.html':
        keyboard = Keyboard()
        keyboard.doModal()

        if keyboard.isConfirmed():
            wd = keyboard.getText()
            duboku.vodsearch('/vodsearch/' + wd + '----------1---.html')
        else:
            return
    else:
        duboku.vodsearch('/vodsearch/' + query)


@plugin.route('/vodshow/<filter>')
def vodshow(filter):
    duboku.vodshow('/vodshow/' + filter)


@plugin.route('/vodshow_filtering/<filter>')
def vodshow_filtering(filter):
    duboku.vodshow_filtering('/vodshow/' + filter)


if __name__ == '__main__':
    plugin.run()
