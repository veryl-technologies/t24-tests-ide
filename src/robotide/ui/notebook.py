#  Copyright 2008-2012 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

try:
    from wx.lib.agw import flatnotebook as fnb
except ImportError:
    from wx.lib import flatnotebook as fnb

from robotide.publish import RideNotebookTabChanging, RideNotebookTabChanged

from robotide.widgets.images import ImageList
from robotide.widgets.images import ImageProvider

class NoteBook(fnb.FlatNotebook):

    def __init__(self, parent, app):
        self._app = app
        style = fnb.FNB_NODRAG|fnb.FNB_HIDE_ON_SINGLE_TAB|fnb.FNB_VC8
        fnb.FlatNotebook.__init__(self, parent, style=style)
        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnTabClosing)
        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGING, self.OnTabChanging)
        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.OnTabChanged)
        imageList = ImageList(16,16)
        imageList.add(ImageProvider().TEST_STEPS_LIST)# todo build good image list
        imageList.add(ImageProvider().TEST_RUN)
        self.SetImageList(imageList)

        self._tab_closing = False
        self._uncloseable = []

    def add_tab(self, tab, title, allow_closing=True):
        if not allow_closing:
            self._uncloseable.append(tab)

        if title == 'Run':
            self.add_tab_with_img(tab, title, 1, allow_closing)
        else:
            self.AddPage(tab, title.strip())

    def add_tab_with_img(self, tab, title, imageIndex, allow_closing=True):
        if not allow_closing:
            self._uncloseable.append(tab)

        self.AddPage(tab, title.strip(), False, imageIndex)
        # self.InsertPage(0,tab,title.strip(),False,imageIndex)

    def show_tab(self, tab):
        """Shows the notebook page that contains the given tab."""
        if not self.tab_is_visible(tab):
            page = self.GetPageIndex(tab)
            if page >= 0:
                self.SetSelection(page)

    def delete_tab(self, tab):
        if tab in self._uncloseable:
            self._uncloseable.remove(tab)
        page = self.GetPageIndex(tab)
        self.DeletePage(page)

    def rename_tab(self, tab, new_name):
        self.SetPageText(self.GetPageIndex(tab), new_name)

    def allow_closing(self, tab):
        if tab in self._uncloseable:
            self._uncloseable.remove(tab)

    def disallow_closing(self, tab):
        if tab not in self._uncloseable:
            self._uncloseable.append(tab)

    def tab_is_visible(self, tab):
        return tab == self.GetCurrentPage()

    @property
    def current_page_title(self):
        return self.GetPageText(self.GetSelection())

    def OnTabClosing(self, event):
        if self.GetPage(event.GetSelection()) in self._uncloseable:
            event.Veto()
            return
        self._tab_closing = True

    def OnTabChanging(self, event):
        if not self._tab_changed():
            return
        oldtitle = self.GetPageText(event.GetOldSelection())
        newindex = event.GetSelection()
        if newindex <= self.GetPageCount() - 1:
            newtitle = self.GetPageText(event.GetSelection())
            self.GetPage(event.GetSelection()).SetFocus()
        else:
            newtitle = None
        RideNotebookTabChanging(oldtab=oldtitle, newtab=newtitle).publish()

    def OnTabChanged(self, event):
        if not self._tab_changed():
            self._tab_closing = False
            return
        RideNotebookTabChanged().publish()

    def _tab_changed(self):
        """Change event is send even when no tab available or tab is closed"""
        if not self.GetPageCount() or self._tab_closing:
            return False
        return True
