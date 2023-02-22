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

from collections import defaultdict
from json import dumps, loads
from os import makedirs, path

from peewee import CharField, Model, SmallIntegerField, SQL, SqliteDatabase
from playhouse.sqlite_ext import DateTimeField
from xbmcext import ListItem, getAddonPath, getAddonProfilePath, getLanguage

if __name__ == '__main__':
    from xbmcgui import ListItem


class JSONField(CharField):
    def db_value(self, value):
        if isinstance(value, str):
            return value
        else:
            return dumps(value)

    def python_value(self, value):
        value = loads(value)
        default = value['zh']
        return defaultdict(lambda: default, value)


class ExternalDatabase(object):
    profile_path = getAddonProfilePath()
    connection = SqliteDatabase(path.join(profile_path, 'duboku.db'))

    @classmethod
    def close(cls):
        cls.connection.close()

    @classmethod
    def connect(cls):
        if not path.exists(cls.profile_path):
            makedirs(cls.profile_path)

        cls.connection.connect(True)

    @classmethod
    def create(cls):
        cls.connection.create_tables([RecentDrama, RecentFilter])
        cls.connection.commit()


class InternalDatabase(object):
    addon_path = getAddonPath()
    connection = SqliteDatabase(path.join(addon_path if addon_path else '..', 'resources/data/duboku.db'))

    @classmethod
    def close(cls):
        if cls.connection:
            cls.connection.close()

    @classmethod
    def connect(cls):
        cls.connection.connect(True)

    @classmethod
    def create(cls):
        from request import DubokuRu, DubokuTv

        cls.connection.create_tables([Drama])
        urls = {drama.url for drama in Drama.select()}

        for vodshow in [iter(DubokuTv.vodshow('/vodshow/2--------{}---.html'.format(page)) for page in range(1, 39)),
                        iter(DubokuTv.vodshow('/vodshow/3--------{}---.html'.format(page)) for page in range(1, 5)),
                        iter(DubokuTv.vodshow('/vodshow/4--------{}---.html'.format(page)) for page in range(1, 5))]:
            for show, _ in vodshow:
                for url in show:
                    if url not in urls:
                        urls.add(url)
                        while True:
                            try:
                                Drama.create(**DubokuTv.voddetail(url))
                                break
                            except AttributeError:
                                pass

        for vodshow in [iter(DubokuRu.vodshow('/vod/2--------{}---.html'.format(page)) for page in range(1, 342)),
                        iter(DubokuRu.vodshow('/vod/1--------{}---.html'.format(page)) for page in range(1, 404)),
                        iter(DubokuRu.vodshow('/vod/3--------{}---.html'.format(page)) for page in range(1, 43)),
                        iter(DubokuRu.vodshow('/vod/4--------{}---.html'.format(page)) for page in range(1, 74))]:
            for show, _ in vodshow:
                for url in show:
                    if url not in urls:
                        urls.add(url)
                        while True:
                            try:
                                Drama.create(**DubokuRu.voddetail(url))
                                break
                            except AttributeError:
                                pass

        cls.connection.commit()


class ExternalModel(Model):
    class Meta:
        database = ExternalDatabase.connection


class InternalModel(Model):
    class Meta:
        database = InternalDatabase.connection


class Drama(InternalModel, ListItem):
    url = CharField(primary_key=True, constraints=[SQL('ON CONFLICT REPLACE')])
    poster = CharField()
    title = JSONField()
    plot = JSONField()
    category = JSONField()
    country = JSONField()
    cast = JSONField()
    director = JSONField()
    year = SmallIntegerField()

    def __new__(cls, *args, **kwargs):
        return super(Drama, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        super(Drama, self).__init__(*args, **kwargs)
        self.setLabel(kwargs['title'][language])
        self.setArt({'thumb': kwargs['poster'],
                     'poster': kwargs['poster'],
                     'banner': kwargs['poster'],
                     'fanart': kwargs['poster'],
                     'clearart': kwargs['poster'],
                     'landscape': kwargs['poster'],
                     'icon': kwargs['poster']} if 'poster' in kwargs else {})
        labels = {label: kwargs[label][language] for label in ('title', 'plot', 'country', 'cast', 'director')}
        labels['year'] = kwargs['year']
        self.setInfo('video', labels)


class RecentDrama(ExternalModel):
    path = CharField(primary_key=True, constraints=[SQL('ON CONFLICT REPLACE')])
    timestamp = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])


class RecentFilter(ExternalModel, ListItem):
    path = CharField(null=False)
    title = CharField(primary_key=True, constraints=[SQL('ON CONFLICT REPLACE')])
    timestamp = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

    def __new__(cls, *args, **kwargs):
        return super(RecentFilter, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        super(RecentFilter, self).__init__(*args, **kwargs)
        self.setLabel(kwargs['title'])
        self.setArt({'icon': 'DefaultTVShows.png'})


if __name__ == '__main__':
    try:
        language = 'zh'
        InternalDatabase.connect()
        InternalDatabase.create()
    finally:
        InternalDatabase.close()
else:
    language = getLanguage()
