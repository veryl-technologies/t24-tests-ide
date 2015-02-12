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

from time import time
from robotide.context.platform import IS_WINDOWS, IS_MAC
import wx
from wx import stc
from StringIO import StringIO
import string

from robot.parsing.model import TestDataDirectory
from robot.parsing.populators import FromFilePopulator
from robot.parsing.txtreader import TxtReader

from robotide.controller.commands import SetDataFile
from robotide.controller.dataloader import TestDataDirectoryWithExcludes
from robotide.publish.messages import RideMessage
from robotide.widgets import VerticalSizer, HorizontalSizer, ButtonWithHandler
from robotide.pluginapi import (Plugin, RideSaving, TreeAwarePluginMixin,
        RideTreeSelection, RideNotebookTabChanging, RideDataChanged,
        RideOpenSuite, RideDataChangedToDirty)
from robotide.widgets.text import TextField
from robotide.widgets.label import Label


import wx
import wx.xrc
import wx.grid


try:
    from . import robotframeworklexer
except Exception as e:
    robotframeworklexer = None

# from ..editor.popupwindow import HtmlDialog

class T24EditorPlugin(Plugin, TreeAwarePluginMixin):
    title = 'T24 Text Edit'

    def __init__(self, application):
        Plugin.__init__(self, application)
        self._editor_component = None

    @property
    def _editor(self):
        if not self._editor_component:
            self._editor_component = T24TestStepEditorPanel(self.notebook, self.title)
            self.add_tab(self._editor_component, self. title, allow_closing=False)
            self._refresh_timer = wx.Timer(self._editor_component)
            self._editor_component.Bind(wx.EVT_TIMER, self._on_timer)
        return self._editor_component

    def enable(self):
        self.add_self_as_tree_aware_plugin()
        self.subscribe(self.OnSaving, RideSaving)
        self.subscribe(self.OnTreeSelection, RideTreeSelection)
        self.subscribe(self.OnDataChanged, RideMessage)
        self.subscribe(self.OnTabChange, RideNotebookTabChanging)
        self._register_shortcuts()
        self._open()

    def _register_shortcuts(self):
        def focused(func):
            def f(event):
                if self.is_focused() and self._editor.is_focused():
                    func(event)
            return f
        self.register_shortcut('CtrlCmd-X', focused(lambda e: self._editor.cut()))
        self.register_shortcut('CtrlCmd-C', focused(lambda e: self._editor.copy()))
        if IS_MAC: # Mac needs this key binding
            self.register_shortcut('CtrlCmd-A', focused(lambda e: self._editor.select_all()))
        if IS_WINDOWS or IS_MAC: # Linux does not need this key binding
            self.register_shortcut('CtrlCmd-V', focused(lambda e: self._editor.paste()))
        self.register_shortcut('CtrlCmd-Z', focused(lambda e: self._editor.undo()))
        self.register_shortcut('CtrlCmd-Y', focused(lambda e: self._editor.redo()))
        self.register_shortcut('Del', focused(lambda e: self._editor.delete()))
        self.register_shortcut('CtrlCmd-F', lambda e: self._editor._search_field.SetFocus())
        self.register_shortcut('CtrlCmd-G', lambda e: self._editor.OnFind(e))
        self.register_shortcut('CtrlCmd-Shift-G', lambda e: self._editor.OnFindBackwards(e))

    def disable(self):
        self.remove_self_from_tree_aware_plugins()
        self.unsubscribe_all()
        self.unregister_actions()
        self.delete_tab(self._editor)
        self._editor_component = None

    def OnOpen(self, event):
        self._open()

    def _open(self):
        datafile_controller = self.tree.get_selected_datafile_controller()
        if datafile_controller:
            self._open_data_for_controller(datafile_controller)
        self.show_tab(self._editor)

    def OnSaving(self, message):
        if self.is_focused():
            self._editor.save()

    def OnDataChanged(self, message):
        if self._should_process_data_changed_message(message):
            if isinstance(message, RideOpenSuite):
                self._editor.reset()
            if self._editor.dirty:
                self._apply_txt_changes_to_model()
            self._refresh_timer.Start(500, True) # For performance reasons only run after all the data changes

    def _on_timer(self, event):
        self._open_tree_selection_in_editor()
        event.Skip()

    def _should_process_data_changed_message(self, message):
        return isinstance(message, RideDataChanged) and \
               not isinstance(message, RideDataChangedToDirty)

    def OnTreeSelection(self, message):
        # self._editor.store_position()
        if self.is_focused():
            if message.node._data.item.__class__.__name__ is 'TestCase':
                self._editor.setTestCase(message.node)
            else:
                self._editor.hide()
            #next_datafile_controller = message.item and message.item.datafile_controller
            #if self._editor.dirty:
            #    if not self._apply_txt_changes_to_model():
            #        if self._editor.datafile_controller != next_datafile_controller:
            #            self.tree.select_controller_node(self._editor.datafile_controller)
            #        return
            #if next_datafile_controller:
            #    self._open_data_for_controller(next_datafile_controller)
            #    self._editor.set_editor_caret_position()


    def _open_tree_selection_in_editor(self):
        datafile_controller = self.tree.get_selected_datafile_controller()
        if datafile_controller:
            self._editor.open(DataFileWrapper(datafile_controller,
                                              self.global_settings))

    def _open_data_for_controller(self, datafile_controller):
        self._editor.selected(DataFileWrapper(datafile_controller,
                                              self.global_settings))

    def OnTabChange(self, message):
        if message.newtab == self.title:
            self._open()
            self._editor.set_editor_caret_position()
        elif message.oldtab == self.title:
            self._editor.remove_and_store_state()


    def _apply_txt_changes_to_model(self):
        if not self._editor.save():
            return False
        self._editor.reset()
        return True

    def is_focused(self):
        return self.notebook.current_page_title == self.title






class T24TestStepEditorPanelBase ( wx.Panel ):

	def __init__( self, parent ):
		wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 614,430 ), style = wx.TAB_TRAVERSAL )

        #self.parent=parent

		bSizer1 = wx.BoxSizer( wx.VERTICAL )

		sbSizer3 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Action" ), wx.HORIZONTAL )

		m_choice1Choices = [ u"M", u"E(nq)", u"I", u"A", u"S", u"V" ]
		self.m_choice1 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 60,-1 ), m_choice1Choices, 0 )
		self.m_choice1.SetSelection( 0 )
		sbSizer3.Add( self.m_choice1, 0, wx.ALL, 5 )

		self.m_textCtrl1 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 2000,-1 ), 0 )

		sbSizer3.Add( self.m_textCtrl1, 0, wx.ALL, 5 )


		bSizer1.Add( sbSizer3, 1, wx.EXPAND, 5 )

		sbSizer2 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Parameters" ), wx.HORIZONTAL )

		self.m_grid1 = wx.grid.Grid( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 2000,1000 ), 0 )

		# Grid
		self.m_grid1.CreateGrid( 20, 3 )
		self.m_grid1.EnableEditing( True )
		self.m_grid1.EnableGridLines( True )
		self.m_grid1.SetGridLineColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_ACTIVEBORDER ) )
		self.m_grid1.EnableDragGridSize( False )
		self.m_grid1.SetMargins( 0, 0 )

		# Columns
		self.m_grid1.SetColSize( 0, 116 )
		self.m_grid1.SetColSize( 1, 158 )
		self.m_grid1.SetColSize( 2, 354 )
		self.m_grid1.AutoSizeColumns()
		self.m_grid1.EnableDragColMove( False )
		self.m_grid1.EnableDragColSize( True )
		self.m_grid1.SetColLabelSize( 30 )
		self.m_grid1.SetColLabelAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )

		# Rows
		self.m_grid1.EnableDragRowSize( True )
		self.m_grid1.SetRowLabelSize( 80 )
		self.m_grid1.SetRowLabelAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )

		# Label Appearance

		# Cell Defaults
		self.m_grid1.SetDefaultCellAlignment( wx.ALIGN_LEFT, wx.ALIGN_TOP )
		sbSizer2.Add( self.m_grid1, 0, wx.ALL, 5 )


		bSizer1.Add( sbSizer2, 1, wx.EXPAND, 5 )


		self.SetSizer( bSizer1 )
		self.Layout()

		# Connect Events
		self.m_choice1.Bind( wx.EVT_CHOICE, self.OnActionChanged )
		self.m_textCtrl1.Bind( wx.EVT_TEXT, self.OnTransactionChanged )

	def __del__( self ):
		pass

	# Virtual event handlers, overide them in your derived class
	def OnActionChanged( self, event ):
		event.Skip()

	def OnTransactionChanged( self, event ):
		event.Skip()

	def setTestCase(self, treeNode):
		self.treeNode=treeNode
		action = treeNode._text
		if action.startswith('(') and action.index(') ') > 1:
			self.m_choice1.SetSelection(self.m_choice1.FindString(action[1:action.index(') ')]))

			self.m_textCtrl1.SetValue(action[action.index(') ')+2:])

class T24TestStepEditorPanel(T24TestStepEditorPanelBase):

	def __init__(self, parent, title):
		T24TestStepEditorPanelBase.__init__(self, parent)
		#self._parent.add_tab(self, title, allow_closing=False)

	def getTestStepName(self):
		return '(' + self.m_choice1.GetString(self.m_choice1.GetSelection()) + ') ' + self.m_textCtrl1.GetValue()

	# T24TestStepEditorPanelBase event handler overrides
	def OnActionChanged( self, event ):
		if self.treeNode is not None:
			text = self.getTestStepName()
			self.treeNode.SetFocus()
			self.treeNode.SetItemText(text)
			self.m_choice1.SetFocus()



	def OnTransactionChanged( self, event ):
		if self.treeNode is not None:
			self.treeNode._text=self.getTestStepName()




