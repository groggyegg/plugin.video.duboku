from .parser import _Parser

import xbmcaddon
import xbmcgui

_addon = xbmcaddon.Addon()
_localized_header = {
    '类型': 30013,
    '剧情': 30020,
    '地区': 30042,
    '年份': 30057,
    '语言': 30058,
    '字母': 30071,
    '排序': 30072,
}
_localized_data = {
    '全部': 30014,
    '陆剧': 30015,
    '日韩剧': 30016,
    '英美剧': 30017,
    '台泰剧': 30018,
    '港剧': 30019,
    '悬疑': 30021,
    '武侠': 30022,
    '科幻': 30023,
    '都市': 30024,
    '爱情': 30025,
    '古装': 30026,
    '战争': 30027,
    '青春': 30028,
    '偶像': 30029,
    '喜剧': 30030,
    '家庭': 30031,
    '犯罪': 30032,
    '奇幻': 30033,
    '乡村': 30034,
    '年代': 30035,
    '警匪': 30036,
    '谍战': 30037,
    '冒险': 30038,
    '罪案': 30039,
    '宫廷': 30040,
    '魔幻': 30041,
    '内地': 30043,
    '韩国': 30044,
    '香港': 30045,
    '台湾': 30046,
    '美国': 30047,
    '英国': 30048,
    '巴西': 30049,
    '西班牙': 30050,
    '泰国': 30051,
    '德国': 30052,
    '法国': 30053,
    '日本': 30054,
    '荷兰': 30055,
    '丹麦': 30056,
    '国语': 30059,
    '英语': 30060,
    '粤语': 30061,
    '韩语': 30062,
    '西班牙语': 30063,
    '葡萄牙语': 30064,
    '泰语': 30065,
    '德语': 30066,
    '法语': 30067,
    '日语': 30068,
    '荷兰语': 30069,
    '挪威语': 30070,
    '时间': 30073,
    '人气': 30074,
    '评分': 30075,
    '剧情': 30076,
    '恐怖': 30077,
    '动作': 30078,
    '动画': 30079,
    '枪战': 30080,
    '惊悚': 30081,
    '文艺': 30082,
    '纪录片': 30083,
    '歌舞': 30084,
    '大陆': 30085,
    '印度': 30086,
    '加拿大': 30087,
    '意大利': 30088,
    '澳大利亚': 30089,
    '俄罗斯': 30090,
    '印地语': 30091,
    '意大利语': 30092,
    '阿拉伯语': 30093,
    '俄语': 30094,
    '真人秀': 30095,
    '选秀': 30096,
    '竞演': 30097,
    '情感': 30098,
    '访谈': 30099,
    '播报': 30100,
    '旅游': 30101,
    '音乐': 30102,
    '美食': 30103,
    '纪实': 30104,
    '曲艺': 30105,
    '生活': 30106,
    '游戏互动': 30107,
    '港台': 30108,
    '日韩': 30109,
    '欧美': 30110,
    '闽南语': 30111,
    '其它': 30112,
    '玄幻': 30113,
    '热血': 30114,
    '推理': 30115,
    '搞笑': 30116,
    '萝莉': 30117,
    '校园': 30118,
    '机战': 30119,
    '运动': 30120,
    '少年': 30121,
    '少女': 30122,
    '社会': 30123,
    '亲子': 30124,
    '益智': 30125,
    '励志': 30126,
    '其他': 30127,
    '国产': 30128
}


class VodShowParser(_Parser):
    def __init__(self):
        super().__init__()
        self._parserlist = [_VodListParser(), _PaginationParser()]

    def start(self, tag, attrs):
        for parser in self._parserlist:
            parser.start(tag, attrs)

    def data(self, data):
        for parser in self._parserlist:
            parser.data(data)

    def end(self, tag):
        for parser in self._parserlist:
            parser.end(tag)

    def close(self):
        return [parser.close() for parser in self._parserlist]

    def error(self, message):
        pass


class _VodListParser:
    def __init__(self):
        self._buffer = []
        self._data = []
        self._ul = False
        self._span = False

    def start(self, tag, attrs):
        if tag == 'ul' and attrs.get('class') == 'myui-vodlist clearfix':
            self._ul = True
        elif self._ul:
            if tag == 'a' and 'data-original' in attrs:
                self._buffer.append(attrs['href'])
            elif tag == 'span' and attrs.get('class') == 'tag':
                self._span = True

    def data(self, data):
        if self._span:
            self._buffer.append(float(data[:-1]))
            self._data.append(tuple(self._buffer))
            self._buffer.clear()
            self._span = False

    def end(self, tag):
        if self._ul and tag == 'ul':
            self._ul = False

    def close(self):
        return self._data


class _PaginationParser:
    def __init__(self):
        self._buffer = []
        self._data = []
        self._a = False
        self._href = None
        self._ul = False

    def start(self, tag, attrs):
        if tag == 'ul' and attrs.get('class') == 'myui-page text-center clearfix':
            self._ul = True
        elif self._ul and tag == 'a' and 'href' in attrs:
            if attrs.get('class') == 'btn  btn-warm':
                self._href = attrs['href']
            else:
                self._buffer.append(attrs['href'])
                self._a = True

    def data(self, data):
        if self._a:
            if data == '首页':
                self._buffer.append(_addon.getLocalizedString(30006))
            elif data == '上一页':
                self._buffer.append(_addon.getLocalizedString(30007))
            elif data == '下一页':
                self._buffer.append(_addon.getLocalizedString(30008))
            elif data == '尾页':
                self._buffer.append(_addon.getLocalizedString(30009))
            else:
                self._buffer.append(data)

            self._data.append(tuple(self._buffer))
            self._buffer.clear()
            self._a = False

    def end(self, tag):
        if self._ul and tag == 'ul':
            self._ul = False

    def close(self):
        return [(path, f'[COLOR FFFFA07A]{label}[/COLOR]') for path, label in self._data if path != self._href]


class FilterParser(_Parser):
    def __init__(self):
        super().__init__()
        self._buffer = []
        self._data = {}
        self._a = False
        self._href = None
        self._ul = False
        self._warm = False

    def start(self, tag, attrs):
        if tag == 'ul' and 'data-align' in attrs:
            self._ul = True
        elif self._ul and tag == 'a':
            self._href = attrs.get('href')
            self._warm = 'btn-warm' in attrs['class']
            self._a = True

    def data(self, data):
        if self._a:
            if self._buffer:
                if data in _localized_data:
                    data = _addon.getLocalizedString(_localized_data[data])
            else:
                if data in _localized_header:
                    data = _addon.getLocalizedString(_localized_header[data])

            self._buffer.append(xbmcgui.ListItem(label=f'[COLOR orange]{data}[/COLOR]' if self._warm else data, path=self._href))
            self._a = False

    def end(self, tag):
        if self._ul and tag == 'ul':
            self._data[self._buffer[0].getLabel()] = self._buffer[1:]
            self._buffer.clear()
            self._ul = False

    def close(self):
        return self._data

    def error(self, message):
        pass
