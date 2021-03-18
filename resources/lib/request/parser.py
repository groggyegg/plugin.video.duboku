from abc import ABC, abstractmethod
from html.parser import HTMLParser


class _Parser(HTMLParser, ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def start(self, tag, attrs):
        pass

    @abstractmethod
    def data(self, data):
        pass

    @abstractmethod
    def end(self, tag):
        pass

    @abstractmethod
    def close(self):
        pass

    def handle_starttag(self, tag, attrs):
        self.start(tag, dict(attrs))

    def handle_data(self, data):
        self.data(data)

    def handle_endtag(self, tag):
        self.end(tag)
