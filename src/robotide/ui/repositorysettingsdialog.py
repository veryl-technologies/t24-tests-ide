#__author__ = 'Hristo Bojkov'
#
# Git dialog to push/pull test cases using command line git
#

import wx
import os
import subprocess
import os.path


from robotide.widgets import Dialog, VirtualList, VerticalSizer, Label


class RepositorySettingsDialog(Dialog):
    _width = 650
    _height = 250
    __repositories = ["git", "bitbucket"]

    def __init__(self, controller):
        self._user_name = "Admin"
        self._password = ""
        self._server_list = ""
        self._repository_list = ""
        self._repository_type = self.__repositories[0]
        self._controller = controller
        title = 'Repository settings'

        Dialog.__init__(self, title, size=(self._width, self._height))
        self._sizer = VerticalSizer()
        # self._add_server_list(self, self._sizer)
        # self._add_repository_list(self, self._sizer)
        # self._sizer = wx.GridSizer(0, 2, 0, 0)
        self.m_label_user = wx.StaticText(self, wx.ID_ANY, u"User", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_label_user.Wrap(-1)
        self._sizer.Add(self.m_label_user, 0, wx.ALL, 5)

        self.m_text_user = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self._sizer.Add(self.m_text_user, 0, wx.ALL, 5)

        self.m_label_pass = wx.StaticText(self, wx.ID_ANY, u"Pass", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_label_pass.Wrap(-1)
        self._sizer.Add(self.m_label_pass, 0, wx.ALL, 5)

        self.m_text_pass = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self._sizer.Add(self.m_text_pass, 0, wx.ALL, 5)

        self.m_button_push = wx.Button(self, wx.ID_ANY, u"Push", wx.DefaultPosition, wx.DefaultSize, 0)
        self._sizer.Add(self.m_button_push, 0, wx.ALL, 5)

        self.m_button_pull = wx.Button(self, wx.ID_ANY, u"Pull", wx.DefaultPosition, wx.DefaultSize, 0)
        self._sizer.Add(self.m_button_pull, 0, wx.ALL, 5)

        self.SetSizer(self._sizer)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.m_button_push.Bind(wx.EVT_BUTTON, self.m_button_push_on_button_click)
        self.m_button_pull.Bind(wx.EVT_BUTTON, self.m_button_pull_on_button_click)

    def __del__(self):
        pass

    def _execute(self):
        pass

    # Virtual event handlers, overide them in your derived class
    def m_button_push_on_button_click(self, event):
        self._execGitCommand('git push -f')

    def m_button_pull_on_button_click(self, event):
        self._execGitCommand('git pull -f')


    # def show(self):
    #     confirmed = self.ShowModal() == wx.ID_OK
    #     return confirmed, self._checkbox.IsChecked()

    def _add_server_list(self, sizer):
        buttons = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        sizer.Add(buttons, flag=wx.ALIGN_CENTER | wx.ALL, border=5)

    def _execGitCommand(self, command):
        pr = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        msg = pr.stdout.read()
        err = pr.stderr.read()
        #HB Todo: show message and count errors