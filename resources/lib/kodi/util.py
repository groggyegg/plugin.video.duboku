import xbmcgui


class ListItem(xbmcgui.ListItem):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args)

    def __init__(self, label, path=None, icon=None, poster=None, info=None, rating=None, properties=None):
        if path:
            self.setPath(path)

        if icon:
            self.setArt({'icon': icon})

        if poster:
            self.setArt({'poster': poster})

        if rating:
            info['rating'] = rating

        if properties:
            self.setProperties(properties)

        self.setInfo('video', info)
