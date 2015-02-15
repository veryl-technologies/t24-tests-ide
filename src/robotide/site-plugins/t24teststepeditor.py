# Copyright Zhelev 2015
#
#


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
            self._editor_component.setTestCase(None, None)
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
                self._editor.setTestCase(message.node, self.tree)
            else:
                self._editor.setTestCase(None,None)
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



""" ========================================================================= """
class T24TestStepEditorPanelBase ( wx.Panel ):

    def __init__( self, parent ):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 704,428 ), style = wx.TAB_TRAVERSAL )

        bSizer1 = wx.BoxSizer( wx.VERTICAL )

        fgSizer3 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer3.SetFlexibleDirection( wx.BOTH )
        fgSizer3.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"Test Case Name", wx.Point( -1,-1 ), wx.DefaultSize, wx.ALIGN_CENTRE )
        self.m_staticText1.Wrap( -1 )
        self.m_staticText1.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), 70, 93, 92, False, wx.EmptyString ) )
        self.m_staticText1.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_HIGHLIGHT ) )

        fgSizer3.Add( self.m_staticText1, 0, wx.ALL, 8 )

        self.m_txtTestCaseName = wx.TextCtrl( self, wx.ID_ANY, u"Customer individual", wx.DefaultPosition, wx.Size( 500,-1 ), 0 )
        self.m_txtTestCaseName.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), 70, 93, 92, False, wx.EmptyString ) )
        self.m_txtTestCaseName.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_CAPTIONTEXT ) )

        fgSizer3.Add( self.m_txtTestCaseName, 0, wx.ALL, 5 )


        bSizer1.Add( fgSizer3, 0, wx.EXPAND, 5 )

        fgSizer1 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer1.SetFlexibleDirection( wx.BOTH )
        fgSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_NONE )

        self.m_staticline1 = wx.StaticLine( self, wx.ID_ANY, wx.Point( -1,-1 ), wx.Size( 2000,-1 ), wx.LI_HORIZONTAL )
        fgSizer1.Add( self.m_staticline1, 0, wx.EXPAND |wx.ALL, 5 )


        bSizer1.Add( fgSizer1, 0, 0, 5 )

        fgSizer2 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer2.SetFlexibleDirection( wx.BOTH )
        fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        sbSizer8 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Test Steps" ), wx.VERTICAL )

        bSizer2 = wx.BoxSizer( wx.VERTICAL )

        self.m_lsTestSteps = wx.ListCtrl( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 200,280 ), wx.LC_LIST )
        bSizer2.Add( self.m_lsTestSteps, 1, wx.ALL|wx.EXPAND, 5 )


        sbSizer8.Add( bSizer2, 1, wx.EXPAND, 5 )

        bSizer3 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_hyperlinkDeleteTestStep = wx.HyperlinkCtrl( self, wx.ID_ANY, u"Delete", wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.HL_DEFAULT_STYLE )
        bSizer3.Add( self.m_hyperlinkDeleteTestStep, 0, wx.ALL, 5 )

        self.m_hyperlinkNewTestStep = wx.HyperlinkCtrl( self, wx.ID_ANY, u"New", wx.EmptyString, wx.DefaultPosition, wx.Size( -1,24 ), wx.HL_DEFAULT_STYLE )
        bSizer3.Add( self.m_hyperlinkNewTestStep, 0, wx.ALL, 5 )


        sbSizer8.Add( bSizer3, 1, wx.TOP|wx.BOTTOM, 5 )


        fgSizer2.Add( sbSizer8, 1, wx.EXPAND|wx.RIGHT, 5 )

        sbSizer3 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Test Step Details" ), wx.HORIZONTAL )

        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

        m_choiceTestStepActionChoices = [ u"M", u"E(nq)", u"I", u"A", u"S", u"V" ]
        self.m_choiceTestStepAction = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 60,-1 ), m_choiceTestStepActionChoices, 0 )
        self.m_choiceTestStepAction.SetSelection( 0 )
        bSizer4.Add( self.m_choiceTestStepAction, 0, wx.ALL, 5 )

        self.m_txtTestStepTransaction = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 380,-1 ), 0 )
        bSizer4.Add( self.m_txtTestStepTransaction, 1, wx.ALL, 5 )


        sbSizer3.Add( bSizer4, 1, 0, 5 )

        bSizer5 = wx.BoxSizer( wx.VERTICAL )

        self.m_panel1 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer5.Add( self.m_panel1, 1, wx.ALL|wx.EXPAND, 5 )


        sbSizer3.Add( bSizer5, 1, wx.EXPAND, 5 )


        fgSizer2.Add( sbSizer3, 1, wx.LEFT|wx.EXPAND, 5 )


        bSizer1.Add( fgSizer2, 1, wx.EXPAND, 5 )


        self.SetSizer( bSizer1 )
        self.Layout()

        # Connect Events
        self.m_txtTestCaseName.Bind( wx.EVT_TEXT, self.OnTestCaseNameChanged )
        self.m_lsTestSteps.Bind( wx.EVT_LIST_ITEM_SELECTED, self.OnSelectedTestStepChanged )
        self.m_hyperlinkDeleteTestStep.Bind( wx.EVT_HYPERLINK, self.OnDeleteSelectedTestStep )
        self.m_hyperlinkNewTestStep.Bind( wx.EVT_HYPERLINK, self.OnNewTestStep )
        self.m_choiceTestStepAction.Bind( wx.EVT_CHOICE, self.OnActionChanged )
        self.m_txtTestStepTransaction.Bind( wx.EVT_TEXT, self.OnTransactionChanged )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def OnTestCaseNameChanged( self, event ):
        event.Skip()

    def OnSelectedTestStepChanged( self, event ):
        event.Skip()

    def OnNewTestStep( self, event ):
        event.Skip()

    def OnDeleteSelectedTestStep( self, event ):
        event.Skip()

    def OnActionChanged( self, event ):
        event.Skip()

    def OnTransactionChanged( self, event ):
        event.Skip()

""" ========================================================================= """
class T24TestStepEditorPanel(T24TestStepEditorPanelBase):

    _testCaseTreeNode = None
    _tree = None

    def __init__(self, parent, title):
        T24TestStepEditorPanelBase.__init__(self, parent)
        #self._parent.add_tab(self, title, allow_closing=False)
        self.m_lsTestSteps.InsertColumn(0, 'Name', wx.LIST_FORMAT_LEFT, 200)

    def setTestCase(self, treeNode, tree):
        self._testCaseTreeNode = treeNode
        self._tree = tree
        # todo - self._testCaseTreeNode._data.item is the test case we should read from it and update it
        if self._testCaseTreeNode is None:
            self.Hide()
        else:
            self.Show()
            self.m_txtTestCaseName.SetValue(self._testCaseTreeNode.GetText())
            self.fillTestStepsList(self._testCaseTreeNode._data.item.steps)

    def fillTestStepsList(self, steps):
        self.m_lsTestSteps.DeleteAllItems()
        idx=0
        if steps is not None:
            for step in steps:
                item = wx.ListItem()
                item.SetText(step.keyword + ' ' + ', '.join(step.args))
                item.SetId(idx)
                self.m_lsTestSteps.InsertItem(item)
                idx+=1




    def getTestStepName(self):
        return '(' + self.m_choice1.GetString(self.m_choice1.GetSelection()) + ') ' + self.m_textCtrl1.GetValue()

    # T24TestStepEditorPanelBase event handler overrides
    def OnTestCaseNameChanged( self, event ):
        if self._testCaseTreeNode is not None:
            self._testCaseTreeNode.SetText(self.m_txtTestCaseName.GetValue())
            self._tree.Refresh()
            # self.testCaseTreeNode.Update() ???
            # todo - set the new name to the data (testCaseTreeNode.data....)

    def OnActionChanged( self, event ):
        if self.treeNode is not None:
            text = self.getTestStepName()
            self.treeNode.SetFocus()
            self.treeNode.SetItemText(text)
            self.m_choice1.SetFocus()



    def OnTransactionChanged( self, event ):
        if self.treeNode is not None:
            self.treeNode._text=self.getTestStepName()




