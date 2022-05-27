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

from sys import version_info

from xbmc import Keyboard

from request import VodSearchRequest
from xbmcext import ListItem, Plugin

if version_info.major == 2:
    from urllib import quote
else:
    from urllib.parse import quote

plugin = Plugin()


@plugin.route('/')
def home():
    plugin.setDirectoryItems([(plugin.getUrlFor('/vodsearch'), ListItem(33000, iconImage='DefaultAddonsSearch.png'), True),
                              (plugin.getUrlFor('/recently-watched'), ListItem(33001, iconImage='DefaultTags.png'), True),
                              (plugin.getUrlFor('/label/new.html'), ListItem(33002, iconImage='DefaultRecentlyAddedEpisodes.png'), True),
                              (plugin.getUrlFor('/vodshow/2--------1---.html'), ListItem(33002, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/vodshow/1--------1---.html'), ListItem(33003, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/vodshow/3--------1---.html'), ListItem(33004, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/vodshow/4--------1---.html'), ListItem(33005, iconImage='DefaultTVShows.png'), True)])


@plugin.route('/vodsearch')
def vodsearch():
    keyboard = Keyboard()
    keyboard.doModal()

    if keyboard.isConfirmed():
        plugin.redirect(plugin.path + '/' + quote(keyboard.getText()) + '----------1---.html')


@plugin.route('/vodsearch/{wd}')
def vodsearch(wd):
    vods, pagination = VodSearchRequest().get(plugin.getFullPath())
    items = []

    for path in vods:
        poster, label, info = db.fetchone_vod(path)
        item = ListItem(label, poster=poster, info=info, rating=rating)
        items.append((plugin.url_for(path), item, True))


@plugin.route('/vodsearch/.+')
def _():
    (vodlist, paginationlist) = VodSearchRequest().get(plugin.full_path, VodSearchParser())
    items = []
    db.connect()

    for path, rating in vodlist:
        poster, label, info = db.fetchone_vod(path)
        item = ListItem(label, poster=poster, info=info, rating=rating)
        items.append((plugin.url_for(path), item, True))

    for path, label in paginationlist:
        item = ListItem(label, properties={'SpecialSort': 'bottom'})
        items.append((plugin.url_for(path), item, True))

    db.close()
    xbmcplugin.setContent(plugin.handle, 'tvshows')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


if __name__ == '__main__':
    plugin()
