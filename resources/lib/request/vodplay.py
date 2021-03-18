from .parser import _Parser

import re


class VodPlayParser(_Parser):
    def __init__(self):
        super().__init__()
        self._url = None
        self._path = None
        self._label = None
        self._buffer = []
        self._h2 = False
        self._script = False

    def start(self, tag, attrs):
        if tag == 'h2' and attrs.get('class') == 'title':
            self._h2 = True
        elif tag == 'script' and 'type' in attrs and 'src' not in attrs:
            self._script = True
        elif self._h2 and tag == 'a':
            self._path = attrs['href']

    def data(self, data):
        if self._h2 and data.strip():
            self._buffer.append(data)
        elif self._script:
            match = re.findall('"(?:url|url_next)":"([^"]+.m3u8)"', data)
            self._script = False

            if match:
                self._buffer.extend(url.replace('\\', '') for url in match)
                self._url = tuple(self._buffer)
                self._buffer.clear()

    def end(self, tag):
        if tag == 'h2':
            self._label = ''.join(self._buffer)
            self._buffer.clear()
            self._h2 = False

    def close(self):
        return self._url, self._path, self._label

    def error(self, message):
        pass
