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

from json import dumps

from resolveurl import resolve
from xbmcext import Dialog, ListItem, Plugin, SortMethod, executebuiltin, urljoin

from database import ExternalDatabase, InternalDatabase, Drama, RecentDrama, RecentFilter
from request import Request

plugin = Plugin()


@plugin.route('/')
def home():
    plugin.addDirectoryItems([
        (plugin.getUrlFor('/vodsearch'), ListItem('搜索数据库', iconImage='DefaultAddonsSearch.png'), True),
        (plugin.getUrlFor('/recently-viewed'), ListItem('最近看过', iconImage='DefaultTags.png'), True),
        (plugin.getUrlFor('/recently-filtered'), ListItem('最近过滤', iconImage='DefaultTags.png'), True),
        (plugin.getUrlFor('/www.duboku.tv'), ListItem('www.duboku.tv', iconImage='DefaultTVShows.png'), True),
        (plugin.getUrlFor('/duboku.ru'), ListItem('duboku.ru', iconImage='DefaultTVShows.png'), True)])
    plugin.endOfDirectory()


@plugin.route('/recently-viewed')
def recently_viewed():
    items = []

    for recent_drama in RecentDrama.select(RecentDrama.path).order_by(RecentDrama.timestamp.desc()):
        item = Drama.get(Drama.path.contains(recent_drama.path))
        item.addContextMenuItems([
            ('移除', 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-viewed', delete=recent_drama.path))),
            ('清除', 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-viewed', delete='%')))])
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
            ('清除', 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-filtered', delete='%')))])
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


@plugin.route('/vodsearch')
def vodsearch_keyboard():
    keyword, items = Dialog().multiselecttabsearch('搜索数据库', {
        '分类': sorted(drama.category['zh'] for drama in Drama.select(Drama.category).distinct()),
        '地区': sorted({country for drama in Drama.select(Drama.country).distinct() for country in drama.country['zh']}),
        '年份': sorted((drama.year for drama in Drama.select(Drama.year).distinct()), reverse=True)})

    if keyword is not None:
        items = {key: dumps(sorted(value), ensure_ascii=False) for key, value in items.items()}
        plugin.redirect('/vodsearch/{}/{}/{}'.format(items['分类'], items['地区'], items['年份']), keyword='*{}*'.format(keyword))


@plugin.route('/vodsearch/{categories:json}/{countries:json}/{years:json}')
def vodsearch(categories, countries, years, keyword):
    expression = ((Drama.path % keyword) | (Drama.title % keyword) | (Drama.plot % keyword))

    if categories:
        expression &= Drama.category % ('*{}*'.format('*'.join('"{}"'.format(category) for category in categories)))

    if countries:
        expression &= Drama.country % ('*{}*'.format('*'.join('"{}"'.format(country) for country in countries)))

    if years:
        expression &= Drama.year << years

    RecentFilter.create(path=plugin.getSerializedFullPath(), title='无标题')
    plugin.setContent('tvshows')
    plugin.addSortMethods(SortMethod.TITLE, SortMethod.VIDEO_YEAR)
    plugin.addDirectoryItems([(plugin.getUrlFor(item.path), item, True) for item in Drama.select().where(expression)])
    plugin.endOfDirectory()


@plugin.route('/duboku.ru')
def dubokuru():
    plugin.addDirectoryItems([(plugin.getSerializedUrlFor('/duboku.ru/vod/2-----------.html', id=2), ListItem('连续剧', iconImage='DefaultTVShows.png'), True),
                              (plugin.getSerializedUrlFor('/duboku.ru/vod/1-----------.html', id=1), ListItem('电影', iconImage='DefaultTVShows.png'), True),
                              (plugin.getSerializedUrlFor('/duboku.ru/vod/3-----------.html', id=3), ListItem('综艺', iconImage='DefaultTVShows.png'), True),
                              (plugin.getSerializedUrlFor('/duboku.ru/vod/4-----------.html', id=4), ListItem('动漫', iconImage='DefaultTVShows.png'), True),
                              (plugin.getSerializedUrlFor('/duboku.ru/vod/20-----------.html', id=20), ListItem('港剧', iconImage='DefaultTVShows.png'), True)])
    plugin.endOfDirectory()


@plugin.route('/www.duboku.tv')
def wwwdubokutv():
    plugin.addDirectoryItems([(plugin.getSerializedUrlFor('/www.duboku.tv/vodshow/2-----------.html', id=2), ListItem('连续剧', iconImage='DefaultTVShows.png'), True),
                              (plugin.getSerializedUrlFor('/www.duboku.tv/vodshow/3-----------.html', id=3), ListItem('综艺', iconImage='DefaultTVShows.png'), True),
                              (plugin.getSerializedUrlFor('/www.duboku.tv/vodshow/4-----------.html', id=4), ListItem('动漫', iconImage='DefaultTVShows.png'), True),
                              (plugin.getSerializedUrlFor('/www.duboku.tv/vodshow/20-----------.html', id=20), ListItem('港剧', iconImage='DefaultTVShows.png'), True)])
    plugin.endOfDirectory()


@plugin.route('/www.duboku.tv/vodshow/{}')
@plugin.route('/duboku.ru/vod/{}')
def vodshow_filter(id):
    options = {
        '剧情': [
            '全部',
            '悬疑',
            '武侠',
            '科幻',
            '都市',
            '爱情',
            '古装',
            '战争',
            '青春',
            '偶像',
            '喜剧',
            '家庭',
            '犯罪',
            '奇幻',
            '剧情',
            '乡村',
            '年代',
            '警匪',
            '谍战',
            '冒险',
            '罪案',
            '宫廷',
            'BL',
            '真人秀',
            '选秀',
            '竞演',
            '情感',
            '访谈',
            '播报',
            '旅游',
            '音乐',
            '美食',
            '纪实',
            '曲艺',
            '生活',
            '游戏互动',
            '玄幻',
            '热血',
            '推理',
            '搞笑',
            '萝莉',
            '校园',
            '动作',
            '机战',
            '运动',
            '少年',
            '少女',
            '社会',
            '亲子',
            '益智',
            '励志',
            '其他'
        ],
        '地区': ['全部', '内地', '韩国', '香港', '台湾', '美国', '英国', '巴西', '泰国', '法国', '日本', '荷兰', '国产', '其他'],
        '年份': ['全部', '2023', '2022', '2021', '2020', '2019', '2018', '2017'],
        '语言': ['全部', '国语', '英语', '粤语', '韩语', '泰语', '法语', '日语', '闽南语', '其它'],
        '字母': [
            '全部',
            'A',
            'B',
            'C',
            'D',
            'E',
            'F',
            'G',
            'H',
            'I',
            'J',
            'K',
            'L',
            'M',
            'N',
            'O',
            'P',
            'Q',
            'R',
            'S',
            'T',
            'U',
            'V',
            'W',
            'X',
            'Y',
            'Z',
            '0-9'
        ],
        '排序': ['时间', '人气', '评分']
    }
    items = Dialog().selecttab('筛选', options, {'剧情': '全部', '地区': '全部', '年份': '全部', '语言': '全部', '字母': '全部', '排序': '时间'})

    if items:
        path = urljoin(plugin.path, '{}-{}-{}-{}-{}-{}------{}.html'.format(
            id,
            items['地区'].replace('全部', ''),
            items['排序'].replace('时间', 'time').replace('人气', 'hits').replace('评分', 'score'),
            items['剧情'].replace('全部', ''),
            items['语言'].replace('全部', ''),
            items['字母'].replace('全部', ''),
            items['年份'].replace('全部', '')))
        RecentFilter.create(path=path, title='无标题')
        plugin.redirect(path)


@plugin.route('/www.duboku.tv/vodshow/{}')
@plugin.route('/duboku.ru/vod/{}')
def vodshow():
    shows, pages = Request.vodshow(plugin.path)
    items = []

    for path in shows:
        item = Drama.get_or_none(Drama.path == path)
        item = item if item else Drama.create(**Request.voddetail(path))
        items.append((plugin.getSerializedUrlFor(item.path), item, True))

    for path, label in pages:
        item = ListItem(label, iconImage='DefaultFolderBack.png' if label == '上一页' else '')
        item.setProperty('SpecialSort', 'bottom')
        items.append((plugin.getUrlFor(path), item, True))

    plugin.setContent('tvshows')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/www.duboku.tv/voddetail/{}')
@plugin.route('/duboku.ru/voddetail/{}')
def voddetail_playlist():
    items = []

    for id, label in Request.voddetail_playlist(plugin.path):
        item = ListItem(label)
        items.append((plugin.getSerializedUrlFor(plugin.path, id=id), item, True))

    plugin.setContent('tvshows')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/www.duboku.tv/voddetail/{}')
@plugin.route('/duboku.ru/voddetail/{}')
def voddetail_episode(id):
    items = []

    for path, title in Request.voddetail_episode(plugin.path, id):
        item = Drama(title=title)
        item.setProperty('IsPlayable', 'true')
        items.append((plugin.getUrlFor(path), item, False))

    plugin.setContent('episodes')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory(cacheToDisc=False)


@plugin.route('/duboku.ru/video/{}')
@plugin.route('/www.duboku.tv/vodplay/{}')
def vodplay():
    path, title = Request.vodplay(plugin.path)
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
