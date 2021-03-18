from .parser import _Parser


class InfoParser(_Parser):
    def __init__(self):
        super().__init__()
        self._buffer = []
        self._data = []
        self._title = False
        self._country = False
        self._year = False
        self._cast = False
        self._director = False
        self._p = False
        self._plot = False

    def start(self, tag, attrs):
        if tag == 'img' and 'data-original' in attrs:
            self._data.append(attrs['data-original'])
        elif tag == 'h1':
            self._title = True
        elif tag == 'p' and attrs.get('class') == 'data':
            self._p = True
        elif tag == 'span' and attrs.get('class') == 'data':
            self._plot = True

    def data(self, data):
        if self._title:
            self._data.append(data)
            self._title = False
        elif self._plot:
            self._data.append(data)
            self._plot = False

        if self._p:
            if self._country:
                self._data.append(data)
                self._country = False
            elif self._year:
                self._data.append(int(data) if data.isdigit() else None)
                self._year = False
            elif self._cast and data.strip():
                self._buffer.append(data)
            elif self._director and data.strip():
                self._buffer.append(data)
            elif data == '地区：':
                self._country = True
            elif data == '年份：':
                self._year = True
            elif data == '主演：':
                self._cast = True
            elif data == '导演：':
                self._director = True

    def end(self, tag):
        if tag == 'p':
            self._p = False

            if self._cast:
                self._data.append(tuple(self._buffer))
                self._buffer.clear()
                self._cast = False
            elif self._director:
                self._data.append(tuple(self._buffer))
                self._buffer.clear()
                self._director = False

    def close(self):
        return self._data

    def error(self, message):
        pass


class EpisodeParser(_Parser):
    def __init__(self):
        super().__init__()
        self._buffer = []
        self._data = []
        self._a = False
        self._div = False

    def start(self, tag, attrs):
        if tag == 'div' and attrs.get('id') == 'playlist1':
            self._div = True
        elif self._div and tag == 'a':
            self._buffer.append(attrs['href'])
            self._a = True

    def data(self, data):
        if self._a:
            self._buffer.append(data)
            self._data.append(tuple(self._buffer))
            self._buffer.clear()
            self._a = False

    def end(self, tag):
        if self._div and tag == 'div':
            self._div = False

    def close(self):
        return self._data

    def error(self, message):
        pass


class CaptchaParser(_Parser):
    def __init__(self):
        super().__init__()
        self._data = {}
        self._p = False

    def start(self, tag, attrs):
        if tag == 'p' and attrs.get('class') == 'text-red':
            self._p = True
        elif tag == 'a' and 'data-id' in attrs:
            self._data['id'] = attrs['data-id']
            self._data['mid'] = attrs['data-mid']
            self._data['type'] = attrs['data-type']

    def data(self, data):
        if self._p:
            self._data['pwd'] = data[3:]
            self._p = False

    def end(self, tag):
        pass

    def close(self):
        return self._data

    def error(self, message):
        pass
