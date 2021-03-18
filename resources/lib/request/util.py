from .voddetail import CaptchaParser
from requests import Session as _Session

import os
import pickle
import xbmcaddon
import xbmcvfs


class WebSession:
    def __init__(self):
        self._base_url = 'https://www.duboku.tv'
        self._session_path = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path')) + 'resources/data/session'

        if os.path.exists(self._session_path):
            with open(self._session_path, 'rb') as file:
                self._session = pickle.load(file)
        else:
            self._session = _Session()

            with open(self._session_path, 'wb') as file:
                pickle.dump(self._session, file)

    def captcha(self, text):
        parser = CaptchaParser()
        parser.feed(text)
        self._session.post(self._base_url + '/index.php/ajax/pwd.html', params=parser.close())

    def get(self, path, parser=None):
        response = self._session.get(self._base_url + path)

        if response.status_code == 200:
            if parser:
                parser.feed(response.text)
                vod = parser.close()

                if vod:
                    return vod
                else:
                    self.captcha(response.text)
                    return self.get(path, parser)
            else:
                return response.text
