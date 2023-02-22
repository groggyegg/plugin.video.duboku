from functools import reduce
from re import match

from xbmcext import Dialog, Keyboard, ListItem, Plugin, executebuiltin

from database import ExternalDatabase, InternalDatabase, Drama, RecentDrama
from request import DubokuTv

plugin = Plugin()


@plugin.route('/')
def home():
    plugin.addDirectoryItems([(plugin.getUrlFor('/vodsearch'), ListItem('搜索', iconImage='DefaultAddonsSearch.png'), True),
                              (plugin.getUrlFor('/recently-watched'), ListItem('最近看过', iconImage='DefaultTags.png'), True),
                              (plugin.getUrlFor('/vodtype'), ListItem('连续剧', iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/vodtype/3.html'), ListItem('综艺', iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/vodtype/4.html'), ListItem('动漫', iconImage='DefaultTVShows.png'), True)])
    plugin.endOfDirectory()


@plugin.route('/vodsearch')
def search():
    keyboard = Keyboard()
    keyboard.doModal()

    if keyboard.isConfirmed():
        plugin.redirect('{}/-------------.html'.format(plugin.path), wd={keyboard.getText()})


@plugin.route('/vodsearch/{}')
def vodsearch():
    search, paging = DubokuTv.vodsearch(plugin.getFullPath())
    items = []

    for path in search:
        item = Drama.get_or_none(Drama.url == path)
        items.append((plugin.getUrlFor(path), item if item else Drama.create(**DubokuTv.voddetail(path)), True))

    for path, label, active in paging:
        item = ListItem(label, iconImage='DefaultFolderBack.png')
        item.setProperty('SpecialSort', 'bottom')
        items.append((plugin.getSerializedUrlFor(path), item, True))

    plugin.setContent('tvshows')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/recently-watched')
def recently_watched():
    items = []

    for drama in RecentDrama.select(RecentDrama.path).order_by(RecentDrama.timestamp.desc()):
        item = Drama.get_or_none(Drama.url == drama.url)
        item = item if item else Drama.create(**DubokuTv.voddetail(drama.url))
        item.addContextMenuItems([('移除', 'RunPlugin({})'.format(plugin.getSerializedUrlFor(plugin.path, delete=item.url))),
                                  ('清除', 'RunPlugin({})'.format(plugin.getSerializedUrlFor(plugin.path, delete='%')))])
        items.append((plugin.getUrlFor(item.url), item, True))

    plugin.setContent('tvshows')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/recently-watched')
def delete_recently_watched(delete):
    RecentDrama.delete().where(RecentDrama.path ** delete).execute()
    executebuiltin('Container.Refresh')


@plugin.route('/vodtype')
def vodtype():
    plugin.addDirectoryItems([(plugin.getUrlFor('/vodtype/2.html'), ListItem('全部', iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/vodtype/13.html'), ListItem('陆剧', iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/vodtype/15.html'), ListItem('日韩剧', iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/vodtype/21.html'), ListItem('短剧', iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/vodtype/14.html'), ListItem('台泰剧', iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/vodtype/20.html'), ListItem('港剧', iconImage='DefaultTVShows.png'), True)])
    plugin.endOfDirectory()


@plugin.route(r'/vodtype/{}')
def showtype():
    filter, preselect = DubokuTv.vodfilter(plugin.path)
    selected = Dialog().selecttab('筛选', filter, preselect)

    if selected:
        def join(accumulator, value):
            return [val if val else acc for acc, val in zip(accumulator, value)]

        pattern = '/vodshow/(.*?)-(.*?)-(.*?)-(.*?)-(.*?)-(.*?)-(.*?)-(.*?)-(.*?)-(.*?)-(.*?)-(.*?).html'
        values = reduce(join, [list(match(pattern, filter[key][value]).groups()) for key, value in selected.items()])
        plugin.redirect('/vodshow/{}-{}-{}-{}-{}-{}-{}-{}-{}-{}-{}-{}.html'.format(*values))


@plugin.route('/vodshow/{}')
def vodshow():
    show, paging = DubokuTv.vodshow(plugin.path)
    items = []

    for path in show:
        item = Drama.select().where(Drama.url == path).get_or_none()
        items.append((plugin.getSerializedUrlFor(path), item if item else Drama.create(**voddetail(path)), True))

    for path, title in paging:
        item = ListItem(title)
        item.setProperty('SpecialSort', 'bottom')
        items.append((plugin.getSerializedUrlFor(path), item, True))

    plugin.setContent('tvshows')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/voddetail/{}')
def voddetail():
    items = []

    for path, label in DubokuTv.voddetail(plugin.path):
        item = ListItem(label)
        item.setProperty('IsPlayable', 'true')
        items.append((plugin.getSerializedUrlFor(path), item, False))

    plugin.setContent('episodes')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory(cacheToDisc=False)


@plugin.route('/vodplay/{}')
def vodplay():
    path, url, label = DubokuTv.vodplay(plugin.path)

    if url:
        RecentDrama.create(path=path)
        plugin.setResolvedUrl(True, ListItem(label, path=url))
    else:
        Dialog().notification('找不到视频', '')


if __name__ == '__main__':
    try:
        ExternalDatabase.connect()
        ExternalDatabase.create()
        InternalDatabase.connect()
        plugin()
    finally:
        ExternalDatabase.close()
        InternalDatabase.close()
