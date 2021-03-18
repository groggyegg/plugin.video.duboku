from request import *

import sqlite3
import xbmcaddon
import xbmcvfs

_addon = xbmcaddon.Addon()
_addonpath = xbmcvfs.translatePath(_addon.getAddonInfo('path'))
_addonprofile = xbmcvfs.translatePath(_addon.getAddonInfo('profile'))
_connections = []
_databases = (_addonprofile + 'duboku.db', _addonpath + 'resources/data/duboku.db')
_session = WebSession()

if not os.path.exists(_addonprofile):
    os.makedirs(_addonprofile)


def connect():
    if not _connections:
        for database in _databases:
            _connections.append(sqlite3.connect(database))

        create()


def close():
    if _connections:
        for connection in _connections:
            connection.commit()
            connection.close()

        _connections.clear()


def create():
    _connections[0].execute('CREATE TABLE IF NOT EXISTS recently_watched ('
                            'path TEXT PRIMARY KEY ON CONFLICT REPLACE, '
                            'last_watched DATETIME DEFAULT CURRENT_TIMESTAMP)')

    _connections[1].execute('CREATE TABLE IF NOT EXISTS vod ('
                            'path TEXT PRIMARY KEY ON CONFLICT IGNORE, '
                            'poster TEXT, '
                            'title TEXT, '
                            'plot TEXT, '
                            'country TEXT, '
                            'cast TEXT, '
                            'director TEXT, '
                            'year INT)')


def add_recently_watched(path):
    _connections[0].execute('INSERT INTO recently_watched (path) VALUES (?)', (path,))


def add_vod(path):
    poster, title, country, year, cast, director, plot = _session.get(path, InfoParser())
    _connections[1].execute('INSERT INTO vod VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (path, poster, title, plot, country, '\n'.join(cast), '\n'.join(director), year))
    return poster, title, {'title': title, 'plot': plot, 'country': country, 'cast': cast, 'director': director, 'year': year}


def fetchall_recently_watched():
    cursor = _connections[0].execute('SELECT path FROM recently_watched ORDER BY last_watched DESC')
    return [path for (path,) in cursor.fetchall()]


def fetchone_vod(path):
    cursor = _connections[1].execute('SELECT poster, title, plot, country, "cast", director, year FROM vod WHERE path = ?', (path,))
    result = cursor.fetchone()

    if result is None:
        return add_vod(path)
    else:
        (poster, title, plot, country, cast, director, year) = result
        return poster, title, {'title': title, 'plot': plot, 'country': country, 'cast': cast.split(), 'director': director.split(), 'year': year}


def remove_recently_watched(path):
    _connections[0].execute('DELETE FROM recently_watched WHERE path LIKE ?', (path,))
