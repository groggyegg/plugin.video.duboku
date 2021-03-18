from kodi import *
from request import *

import db
import plugin
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

_addon = xbmcaddon.Addon()


@plugin.route('/')
def _():
    items = [(plugin.url_for('/vodsearch'), ListItem(_addon.getLocalizedString(30000), icon='DefaultAddonsSearch.png'), True),
             (plugin.url_for('/recently-watched'), ListItem(_addon.getLocalizedString(30001), icon='DefaultTags.png'), True),
             (plugin.url_for('/vodshow/2--------1---.html?dialog=True'), ListItem(_addon.getLocalizedString(30002), icon='DefaultTVShows.png'), True),
             (plugin.url_for('/vodshow/1--------1---.html?dialog=True'), ListItem(_addon.getLocalizedString(30003), icon='DefaultTVShows.png'), True),
             (plugin.url_for('/vodshow/3--------1---.html?dialog=True'), ListItem(_addon.getLocalizedString(30004), icon='DefaultTVShows.png'), True),
             (plugin.url_for('/vodshow/4--------1---.html?dialog=True'), ListItem(_addon.getLocalizedString(30005), icon='DefaultTVShows.png'), True)]

    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/vodsearch')
def _():
    keyboard = xbmc.Keyboard()
    keyboard.doModal()

    if keyboard.isConfirmed():
        plugin.redirect(f'{plugin.path}/-------------.html?wd={keyboard.getText()}')


@plugin.route('/vodsearch/.+')
def _():
    (vodlist, paginationlist) = WebSession().get(plugin.full_path, VodSearchParser())
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


@plugin.route('/recently-watched', delete=False)
def _():
    items = []
    db.connect()

    for path in db.fetchall_recently_watched():
        poster, label, info = db.fetchone_vod(path)
        item = ListItem(label, poster=poster, info=info)
        item.addContextMenuItems([(_addon.getLocalizedString(30010), f'RunPlugin({plugin.url}?delete={path})'),
                                  (_addon.getLocalizedString(30011), f'RunPlugin({plugin.url}?delete=%)')])
        items.append((plugin.url_for(path), item, True))

    db.close()
    xbmcplugin.setContent(plugin.handle, 'tvshows')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/recently-watched', delete='(?P<delete>.+)')
def _(delete):
    db.connect()
    db.remove_recently_watched(delete)
    db.close()
    xbmc.executebuiltin('Container.Refresh')


@plugin.route('/vodshow/.+', dialog=True)
def _():
    path = VodShowFilterDialog().doModal()

    if path:
        plugin.redirect(path)


@plugin.route('/vodshow/.+', dialog=False)
def _():
    (vodlist, paginationlist) = WebSession().get(plugin.path, VodShowParser())
    db.connect()
    items = []

    for path, rating in vodlist:
        poster, label, info = db.fetchone_vod(path)
        item = ListItem(label, poster=poster, info=info, rating=rating)
        items.append((plugin.url_for(path), item, True))

    for path, title in paginationlist:
        item = ListItem(title, properties={'SpecialSort': 'bottom'})
        items.append((plugin.url_for(path), item, True))

    db.close()
    xbmcplugin.setContent(plugin.handle, 'tvshows')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/voddetail/.+')
def _():
    items = []

    for path, label in WebSession().get(plugin.path, EpisodeParser()):
        item = ListItem(label, info={}, properties={'IsPlayable': 'true'})
        items.append((plugin.url_for(path), item, False))

    xbmcplugin.setContent(plugin.handle, 'episodes')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/vodplay/.+')
def _():
    url, path, label = WebSession().get(plugin.path, VodPlayParser())

    if url:
        db.connect()
        db.add_recently_watched(path)
        db.close()
        xbmcplugin.setResolvedUrl(plugin.handle, True, ListItem(label, path=url[0]))
    else:
        xbmcgui.Dialog().notification(_addon.getLocalizedString(30012), '')
        xbmc.sleep(500)


if __name__ == '__main__':
    plugin.run()
