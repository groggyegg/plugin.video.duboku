from functools import reduce
from json import dumps
from operator import or_

from resolveurl import resolve
from xbmcext import Dialog, Keyboard, ListItem, Plugin, executebuiltin, SortMethod

from database import ExternalDatabase, InternalDatabase, Drama, RecentDrama, RecentFilter
from request import vodplaylist, vodvideo, vodepisode

plugin = Plugin()


@plugin.route('/')
def home():
    plugin.addDirectoryItems([
        (plugin.getUrlFor('/search'), ListItem('搜索(Search)', iconImage='DefaultAddonsSearch.png'), True),
        (plugin.getUrlFor('/recently-viewed'), ListItem('最近看过(Recently Watched)', iconImage='DefaultTags.png'), True),
        (plugin.getUrlFor('/recently-filtered'), ListItem('(Recently Filtered)', iconImage='DefaultTags.png'), True),
        (plugin.getUrlFor('/vodfilter'), ListItem('连续剧(TV Series)', iconImage='DefaultTVShows.png'), True)
    ])
    plugin.endOfDirectory()


@plugin.route('/search')
def search():
    keyboard = Keyboard()
    keyboard.doModal()

    if keyboard.isConfirmed():
        plugin.redirect('/search', keyword='*{}*'.format(keyboard.getText()))


@plugin.route('/search')
def search_keyword(keyword):
    items = []

    for item in Drama.select().where((Drama.title % keyword) | (Drama.plot % keyword)):
        items.append((plugin.getUrlFor(item.path), item, True))

    plugin.setContent('tvshows')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/recently-viewed')
def recently_viewed():
    items = []

    for recent_drama in RecentDrama.select(RecentDrama.path).order_by(RecentDrama.timestamp.desc()):
        item = Drama.get(Drama.path.contains(recent_drama.path))
        item.addContextMenuItems([
            ('移除', 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-viewed', delete=recent_drama.path))),
            ('清除', 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-viewed', delete='%')))
        ])
        items.append((plugin.getUrlFor(recent_drama.path), item, True))

    plugin.setContent('tvshows')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/recently-filtered')
def recently_filtered():
    items = []

    for recent_filter in RecentFilter.select(RecentFilter.path, RecentFilter.title).order_by(RecentFilter.timestamp.desc()):
        recent_filter.addContextMenuItems([
            ('移除', 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-filtered', delete=recent_filter.path))),
            ('清除', 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-filtered', delete='%')))
        ])
        items.append((plugin.getUrlFor(recent_filter.path), recent_filter, True))

    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/recently-viewed')
def delete_recently_viewed(delete):
    RecentDrama.delete().where(RecentDrama.path ** delete).execute()
    executebuiltin('Container.Refresh')


@plugin.route('/recently-filtered')
def delete_recently_filtered(delete):
    RecentFilter.delete().where(RecentFilter.path ** delete).execute()
    executebuiltin('Container.Refresh')


@plugin.route('/vodfilter')
def filter_vod():
    items = Dialog().multiselecttab('Filter', {
        'Source': ['duboku.ru', 'duboku.tv'],
        'Category': sorted(drama.category['zh'] for drama in Drama.select(Drama.category).distinct()),
        'Country': sorted({country for drama in Drama.select(Drama.country).distinct() for country in drama.country['zh']}),
        'Year': [str(drama.year) for drama in Drama.select(Drama.year).order_by(Drama.year.desc()).distinct()]
    })

    if items:
        items = {key: dumps(sorted(value), ensure_ascii=False) for key, value in items.items()}
        plugin.redirect('/vodshow/{Source}/{Category}/{Country}/{Year}'.format(**items))


@plugin.route('/vodshow/{sources:json}/{categories:json}/{countries:json}/{years:json}')
def show_vod(sources, categories, countries, years):
    expression = Drama.path % '*'

    if sources:
        expression &= reduce(or_, [(Drama.path % '*{}*'.format(source)) for source in sources])

    if categories:
        expression &= Drama.category % ('*{}*'.format('*'.join('"{}"'.format(category) for category in categories)))

    if countries:
        expression &= Drama.country % ('*{}*'.format('*'.join('"{}"'.format(country) for country in countries)))

    if years:
        expression &= Drama.year << years

    title = 'Source: [{}] Category: [{}] Country: [{}] Year: [{}]'.format(', '.join(sources), ', '.join(categories), ', '.join(countries), ', '.join(years))
    RecentFilter.create(path=plugin.path, title=title)
    items = []

    for item in Drama.select().where(expression):
        items.append((plugin.getUrlFor(item.path), item, True))

    plugin.setContent('tvshows')
    plugin.addSortMethods(SortMethod.TITLE, SortMethod.VIDEO_YEAR)
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/www.duboku.tv/voddetail/{}')
@plugin.route('/duboku.ru/voddetail/{}')
def playlist():
    items = []

    for label, playlist_id in vodplaylist(plugin.path):
        item = ListItem(label)
        items.append((plugin.getSerializedUrlFor(plugin.path, playlist_id=playlist_id), item, True))

    plugin.setContent('tvshows')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/www.duboku.tv/voddetail/{}')
@plugin.route('/duboku.ru/voddetail/{}')
def episode(playlist_id):
    items = []

    for path, title in vodepisode(plugin.path, playlist_id):
        item = Drama(title=title)
        item.setProperty('IsPlayable', 'true')
        items.append((plugin.getUrlFor(path), item, False))

    plugin.setContent('episodes')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory(cacheToDisc=False)


@plugin.route('/duboku.ru/video/{}')
@plugin.route('/www.duboku.tv/vodplay/{}')
def play():
    path, title = vodvideo(plugin.path)
    item = Drama(title=title)
    url = resolve('https:/{}'.format(plugin.path))

    if url:
        RecentDrama.create(path=path)
        item.setPath(url)
    else:
        Dialog().notification('找不到视频', '')

    plugin.setResolvedUrl(bool(url), item)


if __name__ == '__main__':
    try:
        ExternalDatabase.connect()
        ExternalDatabase.create()
        InternalDatabase.connect()
        plugin()
    finally:
        ExternalDatabase.close()
        InternalDatabase.close()
