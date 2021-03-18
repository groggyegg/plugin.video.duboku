from .parser import _Parser
from .vodshow import _PaginationParser


class VodSearchParser(_Parser):
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
        return tuple(parser.close() for parser in self._parserlist)

    def error(self, message):
        pass


class _VodListParser:
    def __init__(self):
        self._buffer = []
        self._data = []
        self._a = False
        self._span = False
        self._ul = False

    def start(self, tag, attrs):
        if tag == 'ul' and attrs.get('id') == 'searchList':
            self._ul = True
        elif self._ul and tag == 'a' and attrs.get('class') == 'searchkey':
            self._buffer.append(attrs['href'])
            self._a = True
        elif self._a and tag == 'span' and attrs.get('class') == 'tag':
            self._span = True

    def data(self, data):
        if self._span:
            self._buffer.append(float(data[:-1]))
            self._data.append(tuple(self._buffer))
            self._buffer.clear()
            self._a = False
            self._span = False

    def end(self, tag):
        if self._ul and tag == 'ul':
            self._ul = False

    def close(self):
        return self._data
