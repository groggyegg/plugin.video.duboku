from request import *

import plugin
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

ACTION_NONE = 0
ACTION_MOVE_LEFT = 1
ACTION_PREVIOUS_MENU = 10
ACTION_STOP = 13
ACTION_NAV_BACK = 92
ACTION_MOUSE_MOVE = 107
ACTION_OK = 1104
NAVIGATION_LIST = 1100
CONTENT_LIST = 1101


class VodShowFilterDialog(xbmcgui.WindowXMLDialog):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, 'VodShowFilter.xml', xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path')), defaultRes='1080i')

    def __init__(self):
        self._items = None
        self._selectedHeading = None
        self._content = None
        self._navigation = None
        self._path = None

    def onInit(self):
        self._content = self.getControl(CONTENT_LIST)
        self._navigation = self.getControl(NAVIGATION_LIST)
        self._navigation.addItems(list(self._items.keys()))
        self.setFocusId(NAVIGATION_LIST)

    def onAction(self, action):
        if action.getId() in (ACTION_PREVIOUS_MENU, ACTION_STOP, ACTION_NAV_BACK):
            self._path = None
            self.close()

    def onClick(self, controlId):
        if controlId == CONTENT_LIST:
            xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
            self._path = self._content.getSelectedItem().getPath()
            self._items = WebSession().get(self._path, FilterParser())
            selectedPosition = self._content.getSelectedPosition()
            self._content.reset()
            self._content.addItems(self._items[self._selectedHeading])
            self._content.selectItem(selectedPosition)
            xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
        elif controlId == ACTION_OK:
            self.close()

    def onFocus(self, controlId):
        if controlId == NAVIGATION_LIST:
            selectedHeading = self._navigation.getSelectedItem().getLabel()

            if self._selectedHeading != selectedHeading:
                self._selectedHeading = selectedHeading
                self._content.reset()
                self._content.addItems(self._items[selectedHeading])

    def doModal(self):
        self._path = plugin.path
        self._items = WebSession().get(self._path, FilterParser())
        super().doModal()
        return self._path
