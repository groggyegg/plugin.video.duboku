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
from xbmcext import Dialog, Keyboard, ListItem, Plugin, SortMethod, executebuiltin, getLocalizedString, urljoin

from database import Drama, ExternalDatabase, InternalDatabase, RecentDrama, RecentFilter
from request import Request

plugin = Plugin()


@plugin.route('/')
def home():
    plugin.addDirectoryItems([
        (plugin.getUrlFor('/vodsearch'), ListItem(getLocalizedString(30000), iconImage='DefaultAddonsSearch.png'), True),
        (plugin.getUrlFor('/recently-watched'), ListItem(getLocalizedString(30001), iconImage='DefaultTags.png'), True),
        (plugin.getUrlFor('/recently-searched'), ListItem(getLocalizedString(30131), iconImage='DefaultTags.png'), True),
        (plugin.getUrlFor('/www.duboku.tv'), ListItem('www.duboku.tv', iconImage='DefaultTVShows.png'), True)])
    plugin.endOfDirectory()


@plugin.route('/recently-watched')
def recently_watched():
    items = []

    for recent_drama in RecentDrama.select(RecentDrama.path).order_by(RecentDrama.timestamp.desc()):
        item = Drama.get(Drama.path.contains(recent_drama.path))
        item.addContextMenuItems([
            (getLocalizedString(30010), 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-watched', delete=recent_drama.path))),
            (getLocalizedString(30011), 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-watched', delete='%')))])
        items.append((plugin.getUrlFor(recent_drama.path), item, True))

    plugin.setContent('tvshows')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/recently-watched')
def recently_watched_delete(delete):
    RecentDrama.delete().where(RecentDrama.path ** delete).execute()
    executebuiltin('Container.Refresh')


@plugin.route('/recently-searched')
def recently_searched():
    items = []

    for recent_filter in RecentFilter.select(RecentFilter.path, RecentFilter.title).order_by(RecentFilter.timestamp.desc()):
        recent_filter.addContextMenuItems([
            (getLocalizedString(30132), 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-searched', rename=recent_filter.title))),
            (getLocalizedString(30010), 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-searched', delete=recent_filter.title))),
            (getLocalizedString(30011), 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-searched', delete='%')))])
        items.append((plugin.getUrlFor(recent_filter.path), recent_filter, True))

    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/recently-searched')
def recently_searched_rename(rename):
    keyboard = Keyboard()
    keyboard.doModal()

    if keyboard.isConfirmed() and keyboard.getText():
        RecentFilter.update(title=keyboard.getText()).where(RecentFilter.title == rename).execute()
        executebuiltin('Container.Refresh')


@plugin.route('/recently-searched')
def recently_searched_delete(delete):
    RecentFilter.delete().where(RecentFilter.title ** delete).execute()
    executebuiltin('Container.Refresh')


@plugin.route('/vodsearch')
def vodsearch_keyboard():
    keyword, items = Dialog().multiselecttabsearch(getLocalizedString(30000), {
        (getLocalizedString(30013), '类型'): sorted((getLocalizedString(drama.category), drama.category) for drama in Drama.select(Drama.category).distinct()),
        (getLocalizedString(30042), '地区'): sorted({(getLocalizedString(country), country) for drama in Drama.select(Drama.country).distinct() for country in drama.country}),
        (getLocalizedString(30057), '年份'): sorted((str(drama.year) for drama in Drama.select(Drama.year).distinct()), reverse=True)})

    if keyword is not None:
        items = {key: dumps(sorted(value), ensure_ascii=False) for key, value in items.items()}
        plugin.redirect('/vodsearch/{}/{}/{}'.format(items['类型'], items['地区'], items['年份']), keyword='*{}*'.format(keyword))


@plugin.route('/vodsearch/{categories:json}/{countries:json}/{years:json}')
def vodsearch(categories, countries, years, keyword):
    expression = ((Drama.path % keyword) | (Drama.title % keyword) | (Drama.plot % keyword))

    if categories:
        expression &= Drama.category << categories

    if countries:
        expression &= Drama.country % ('*{}*'.format('*'.join(str(country) for country in countries)))

    if years:
        expression &= Drama.year << years

    RecentFilter.create(path=plugin.getSerializedFullPath(), title=getLocalizedString(30133))
    plugin.setContent('tvshows')
    plugin.addSortMethods(SortMethod.TITLE, SortMethod.VIDEO_YEAR)
    plugin.addDirectoryItems([(plugin.getUrlFor(item.path), item, True) for item in Drama.select().where(expression)])
    plugin.endOfDirectory()


@plugin.route('/duboku.ru')
def dubokuru():
    plugin.addDirectoryItems(
        [(plugin.getSerializedUrlFor('/duboku.ru/vod/2-----------.html', id=2), ListItem(getLocalizedString(30002), iconImage='DefaultTVShows.png'), True),
         (plugin.getSerializedUrlFor('/duboku.ru/vod/1-----------.html', id=1), ListItem(getLocalizedString(30003), iconImage='DefaultTVShows.png'), True),
         (plugin.getSerializedUrlFor('/duboku.ru/vod/3-----------.html', id=3), ListItem(getLocalizedString(30004), iconImage='DefaultTVShows.png'), True),
         (plugin.getSerializedUrlFor('/duboku.ru/vod/4-----------.html', id=4), ListItem(getLocalizedString(30005), iconImage='DefaultTVShows.png'), True),
         (plugin.getSerializedUrlFor('/duboku.ru/vod/20-----------.html', id=20), ListItem(getLocalizedString(30019), iconImage='DefaultTVShows.png'), True)])
    plugin.endOfDirectory()


@plugin.route('/www.duboku.tv')
def wwwdubokutv():
    plugin.addDirectoryItems(
        [(plugin.getSerializedUrlFor('/www.duboku.tv/vodshow/2-----------.html', id=2), ListItem(getLocalizedString(30002), iconImage='DefaultTVShows.png'), True),
         (plugin.getSerializedUrlFor('/www.duboku.tv/vodshow/1-----------.html', id=1), ListItem(getLocalizedString(30003), iconImage='DefaultTVShows.png'), True),
         (plugin.getSerializedUrlFor('/www.duboku.tv/vodshow/3-----------.html', id=3), ListItem(getLocalizedString(30004), iconImage='DefaultTVShows.png'), True),
         (plugin.getSerializedUrlFor('/www.duboku.tv/vodshow/4-----------.html', id=4), ListItem(getLocalizedString(30005), iconImage='DefaultTVShows.png'), True),
         (plugin.getSerializedUrlFor('/www.duboku.tv/vodshow/20-----------.html', id=20), ListItem(getLocalizedString(30019), iconImage='DefaultTVShows.png'), True)])
    plugin.endOfDirectory()


@plugin.route('/www.duboku.tv/vodshow/{}')
@plugin.route('/duboku.ru/vod/{}')
def vodshow_filter(id):
    items = Dialog().selecttab(
        getLocalizedString(30129),
        {(getLocalizedString(30020), '剧情'): [
            (getLocalizedString(30014), ''),
            (getLocalizedString(30021), '悬疑'),
            (getLocalizedString(30022), '武侠'),
            (getLocalizedString(30023), '科幻'),
            (getLocalizedString(30024), '都市'),
            (getLocalizedString(30025), '爱情'),
            (getLocalizedString(30026), '古装'),
            (getLocalizedString(30027), '战争'),
            (getLocalizedString(30028), '青春'),
            (getLocalizedString(30029), '偶像'),
            (getLocalizedString(30030), '喜剧'),
            (getLocalizedString(30031), '家庭'),
            (getLocalizedString(30032), '犯罪'),
            (getLocalizedString(30033), '奇幻'),
            (getLocalizedString(30020), '剧情'),
            (getLocalizedString(30034), '乡村'),
            (getLocalizedString(30035), '年代'),
            (getLocalizedString(30036), '警匪'),
            (getLocalizedString(30037), '谍战'),
            (getLocalizedString(30038), '冒险'),
            (getLocalizedString(30039), '罪案'),
            (getLocalizedString(30040), '宫廷'),
            'BL',
            (getLocalizedString(30095), '真人秀'),
            (getLocalizedString(30096), '选秀'),
            (getLocalizedString(30097), '竞演'),
            (getLocalizedString(30098), '情感'),
            (getLocalizedString(30099), '访谈'),
            (getLocalizedString(30100), '播报'),
            (getLocalizedString(30101), '旅游'),
            (getLocalizedString(30102), '音乐'),
            (getLocalizedString(30103), '美食'),
            (getLocalizedString(30104), '纪实'),
            (getLocalizedString(30105), '曲艺'),
            (getLocalizedString(30106), '生活'),
            (getLocalizedString(30107), '游戏互动'),
            (getLocalizedString(30113), '玄幻'),
            (getLocalizedString(30114), '热血'),
            (getLocalizedString(30115), '推理'),
            (getLocalizedString(30116), '搞笑'),
            (getLocalizedString(30117), '萝莉'),
            (getLocalizedString(30118), '校园'),
            (getLocalizedString(30078), '动作'),
            (getLocalizedString(30119), '机战'),
            (getLocalizedString(30120), '运动'),
            (getLocalizedString(30121), '少年'),
            (getLocalizedString(30122), '少女'),
            (getLocalizedString(30123), '社会'),
            (getLocalizedString(30124), '亲子'),
            (getLocalizedString(30125), '益智'),
            (getLocalizedString(30126), '励志'),
            (getLocalizedString(30112), '其他')],
            (getLocalizedString(30042), '地区'): [
                (getLocalizedString(30014), ''),
                (getLocalizedString(30043), '内地'),
                (getLocalizedString(30044), '韩国'),
                (getLocalizedString(30045), '香港'),
                (getLocalizedString(30046), '台湾'),
                (getLocalizedString(30047), '美国'),
                (getLocalizedString(30048), '英国'),
                (getLocalizedString(30049), '巴西'),
                (getLocalizedString(30051), '泰国'),
                (getLocalizedString(30053), '法国'),
                (getLocalizedString(30054), '日本'),
                (getLocalizedString(30055), '荷兰'),
                (getLocalizedString(30128), '国产'),
                (getLocalizedString(30112), '其他')],
            (getLocalizedString(30057), '年份'): [
                (getLocalizedString(30014), ''), '2023', '2022', '2021', '2020', '2019', '2018', '2017'],
            (getLocalizedString(30058), '语言'): [
                (getLocalizedString(30014), ''),
                (getLocalizedString(30059), '国语'),
                (getLocalizedString(30060), '英语'),
                (getLocalizedString(30061), '粤语'),
                (getLocalizedString(30062), '韩语'),
                (getLocalizedString(30065), '泰语'),
                (getLocalizedString(30067), '法语'),
                (getLocalizedString(30068), '日语'),
                (getLocalizedString(30111), '闽南语'),
                (getLocalizedString(30112), '其它')],
            (getLocalizedString(30071), '字母'): [
                (getLocalizedString(30014), ''),
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
            (getLocalizedString(30072), '排序'): [
                (getLocalizedString(30073), 'time'),
                (getLocalizedString(30074), 'hits'),
                (getLocalizedString(30075), 'score')]},
        {getLocalizedString(30020): getLocalizedString(30014),
         getLocalizedString(30042): getLocalizedString(30014),
         getLocalizedString(30057): getLocalizedString(30014),
         getLocalizedString(30058): getLocalizedString(30014),
         getLocalizedString(30071): getLocalizedString(30014),
         getLocalizedString(30072): getLocalizedString(30073)})

    if items:
        path = urljoin(plugin.path, '{}-{}-{}-{}-{}-{}------{}.html'.format(id, items['地区'], items['排序'], items['剧情'], items['语言'], items['字母'], items['年份']))
        RecentFilter.create(path=path, title=getLocalizedString(30133))
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
        item = ListItem(getLocalizedString(30007), iconImage='DefaultFolderBack.png') if label == '上一页' else ListItem(getLocalizedString(30008))
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
        Dialog().notification(getLocalizedString(30012), '')

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
