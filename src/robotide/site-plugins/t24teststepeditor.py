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

from robotide.t24api.T24TestStep import T24TestStep


import wx
import wx.xrc
import wx.grid

try:
    from . import robotframeworklexer
except Exception as e:
    robotframeworklexer = None

# from ..editor.popupwindow import HtmlDialog



class T24EditorPlugin(Plugin, TreeAwarePluginMixin):
    title = 'Test Steps'

    def __init__(self, application):
        Plugin.__init__(self, application)
        self._editor_component = None

    @property
    def _editor(self):
        if not self._editor_component:
            self._editor_component = T24TestStepsContainer(self.notebook, self.title)
            self.add_tab(self._editor_component, self.title, allow_closing=False)
            self.show_tab(self.title)
            self._refresh_timer = wx.Timer(self._editor_component)
            self._editor_component.Bind(wx.EVT_TIMER, self._on_timer)
            self._editor_component.setTestCase(None, None)
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



###########################################################################

class T24TestStepsContainerBase ( wx.Panel ):

    def __init__( self, parent ):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.TAB_TRAVERSAL )

        bSizer8 = wx.BoxSizer( wx.VERTICAL )

        self.m_scrolledWindow2 = wx.ScrolledWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.VSCROLL )
        self.m_scrolledWindow2.SetScrollRate( 5, 5 )
        self.m_sizerTestStepsContainer = wx.BoxSizer( wx.VERTICAL )


        self.m_scrolledWindow2.SetSizer( self.m_sizerTestStepsContainer )
        self.m_scrolledWindow2.Layout()
        self.m_sizerTestStepsContainer.Fit( self.m_scrolledWindow2 )
        bSizer8.Add( self.m_scrolledWindow2, 1, wx.EXPAND |wx.ALL, 5 )


        self.SetSizer( bSizer8 )
        self.Layout()

    def __del__( self ):
        pass


class T24TestStepsContainer(T24TestStepsContainerBase):

    _testCaseTreeNode = None
    _tree = None
    _testSteps = []

    def __init__( self, parent, title ):
        T24TestStepsContainerBase.__init__(self,parent)

    def __del__( self ):
        pass

    def setTestCase(self, treeNode, tree):
        self._testCaseTreeNode = treeNode
        self._tree = tree
        # todo - self._testCaseTreeNode._data.item is the test case we should read from it and update it
        if self._testCaseTreeNode is None:
            self.Hide()
        else:
            self.Show()
            self.createTestStepsControls(self._testCaseTreeNode._data.item.steps)

    def createTestStepsControls(self, testSteps):
        if not not self.m_sizerTestStepsContainer.Children:
            self.m_sizerTestStepsContainer.DeleteWindows()

        if testSteps is not None:
            for step in testSteps:
                panel = self.createStepPanel(step)
                if not not panel:
                    self.m_sizerTestStepsContainer.Add(panel, 1, wx.EXPAND |wx.ALL, 5 )

            self.m_scrolledWindow2.SetSizer(self.m_sizerTestStepsContainer)
            self.m_scrolledWindow2.Layout()
            self.m_sizerTestStepsContainer.Fit( self.m_scrolledWindow2 )
            self.m_sizerTestStepsContainer.Layout()

            self.Layout()



    def createStepPanel(self, stepDetails):
        t24TestStep = T24TestStep(stepDetails)
        self._testSteps.append(t24TestStep)

        if t24TestStep.IsRealTestStep:
            panel = T24TestStepPanel(self.m_scrolledWindow2, t24TestStep)
            return panel

        return None

###########################################################################

class T24TestStepPanelBase ( wx.Panel ):

    def __init__( self, parent ):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 683,400 ), style = wx.SIMPLE_BORDER|wx.TAB_TRAVERSAL )

        bSizer1 = wx.BoxSizer( wx.VERTICAL )

        fgSizer1 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer1.SetFlexibleDirection( wx.HORIZONTAL )
        fgSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_NONE )

        fgSizer41 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer41.SetFlexibleDirection( wx.BOTH )
        fgSizer41.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticline1 = wx.StaticLine( self, wx.ID_ANY, wx.Point( -1,-1 ), wx.Size( 570,4 ), wx.LI_HORIZONTAL )
        self.m_staticline1.SetFont( wx.Font( 9, 74, 90, 90, False, "Arial" ) )
        self.m_staticline1.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_HIGHLIGHT ) )
        self.m_staticline1.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_HIGHLIGHT ) )

        fgSizer41.Add( self.m_staticline1, 0, wx.EXPAND |wx.ALL, 8 )


        fgSizer1.Add( fgSizer41, 1, wx.EXPAND, 5 )

        bSizer8 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_btnUp = wx.Button( self, wx.ID_ANY, u"/\\", wx.DefaultPosition, wx.Size( 22,22 ), wx.BU_BOTTOM|wx.NO_BORDER )
        self.m_btnUp.SetFont( wx.Font( 9, 74, 90, 92, False, "Arial Black" ) )

        bSizer8.Add( self.m_btnUp, 0, wx.BOTTOM|wx.LEFT, 5 )

        self.m_btnDown = wx.Button( self, wx.ID_ANY, u"\\/", wx.DefaultPosition, wx.Size( 22,22 ), wx.BU_TOP|wx.NO_BORDER )
        self.m_btnDown.SetFont( wx.Font( 9, 74, 90, 92, False, "Arial Black" ) )

        bSizer8.Add( self.m_btnDown, 0, wx.BOTTOM|wx.RIGHT, 5 )

        self.m_btnDelete = wx.Button( self, wx.ID_ANY, u"X", wx.DefaultPosition, wx.Size( 22,22 ), 0 )
        self.m_btnDelete.SetFont( wx.Font( 10, 74, 90, 92, False, "Arial" ) )
        self.m_btnDelete.SetForegroundColour( wx.Colour( 236, 77, 0 ) )

        bSizer8.Add( self.m_btnDelete, 0, wx.BOTTOM|wx.RIGHT|wx.LEFT, 5 )


        fgSizer1.Add( bSizer8, 1, wx.EXPAND, 5 )


        bSizer1.Add( fgSizer1, 0, 0, 5 )

        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

        self.lblTestStep = wx.StaticText( self, wx.ID_ANY, u"Test Step", wx.Point( -1,-1 ), wx.DefaultSize, wx.ALIGN_CENTRE )
        self.lblTestStep.Wrap( -1 )
        self.lblTestStep.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), 70, 93, 92, False, wx.EmptyString ) )
        self.lblTestStep.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_HIGHLIGHT ) )

        bSizer4.Add( self.lblTestStep, 0, wx.ALL, 8 )

        m_choiceTestStepActionChoices = [ u"M", u"E(nq)", u"I", u"A", u"S", u"V" ]
        self.m_choiceTestStepAction = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 60,-1 ), m_choiceTestStepActionChoices, 0 )
        self.m_choiceTestStepAction.SetSelection( 0 )
        bSizer4.Add( self.m_choiceTestStepAction, 0, wx.ALL, 5 )

        self.m_txtTestStepTransaction = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 514,-1 ), 0 )
        bSizer4.Add( self.m_txtTestStepTransaction, 1, wx.ALL, 5 )

        bSizer14 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText3.Wrap( -1 )
        bSizer14.Add( self.m_staticText3, 0, wx.ALL, 5 )


        bSizer4.Add( bSizer14, 0, wx.EXPAND, 5 )


        bSizer1.Add( bSizer4, 0, 0, 5 )

        fgSizer4 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer4.SetFlexibleDirection( wx.BOTH )
        fgSizer4.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticline2 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 664,-1 ), wx.LI_HORIZONTAL )
        fgSizer4.Add( self.m_staticline2, 0, wx.EXPAND |wx.ALL, 5 )


        bSizer1.Add( fgSizer4, 0, 0, 5 )

        self.m_sizerTransactionID = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText2 = wx.StaticText( self, wx.ID_ANY, u"@ID", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText2.Wrap( -1 )
        self.m_sizerTransactionID.Add( self.m_staticText2, 0, wx.ALL, 8 )

        self.m_txtTransactionID = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 320,-1 ), 0 )
        self.m_sizerTransactionID.Add( self.m_txtTransactionID, 0, wx.ALL, 5 )


        bSizer1.Add( self.m_sizerTransactionID, 0, wx.EXPAND, 5 )

        self.m_sizerTestData = wx.BoxSizer( wx.VERTICAL )

        sbSizer3 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Test Data" ), wx.VERTICAL )

        self.m_grid1 = wx.grid.Grid( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )

        # Grid
        self.m_grid1.CreateGrid( 3, 5 )
        self.m_grid1.EnableEditing( True )
        self.m_grid1.EnableGridLines( True )
        self.m_grid1.EnableDragGridSize( False )
        self.m_grid1.SetMargins( 0, 0 )

        # Columns
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
        sbSizer3.Add( self.m_grid1, 0, wx.ALL, 5 )


        self.m_sizerTestData.Add( sbSizer3, 0, wx.EXPAND, 5 )


        bSizer1.Add( self.m_sizerTestData, 0, wx.EXPAND, 5 )


        self.SetSizer( bSizer1 )
        self.Layout()

        # Connect Events
        self.m_choiceTestStepAction.Bind( wx.EVT_CHOICE, self.OnActionChanged )
        self.m_txtTestStepTransaction.Bind( wx.EVT_TEXT, self.OnTransactionChanged )
        self.m_txtTransactionID.Bind( wx.EVT_TEXT, self.onTransactionIDChanged )

    def __del__( self ):
        pass

    # Virtual event handlers, overide them in your derived class
    def OnActionChanged( self, event ):
        event.Skip()

    def OnTransactionChanged( self, event ):
        event.Skip()

    def onTransactionIDChanged( self, event ):
        event.Skip()

###########################################################################

class T24TestStepPanel (T24TestStepPanelBase):

    _testStep = None

    def __init__( self, parent, testStep ):
        T24TestStepPanelBase.__init__ ( self, parent )
        self._testStep = testStep
        self.setTestStepDetails()
        self.updateUI()

    def __del__( self ):
        pass

    def OnActionChanged( self, event ):
        if self._testStep is not None:
            self._testStep.Action = self.m_choiceTestStepAction.GetStringSelection()
            self.updateUI()

    def setTestStepDetails(self):
        self.m_choiceTestStepAction.SetSelection(self.m_choiceTestStepAction.FindString(self._testStep.Action))
        self.m_txtTestStepTransaction.SetValue(self._testStep.AppVersion)

    def updateUI(self):
        if self._testStep is None:
            # hide all
            self.m_sizerTransactionID.ShowItems(False)
            self.m_sizerTestData.ShowItems(False)
        elif self._testStep.Action == 'I':
            self.m_sizerTransactionID.ShowItems(False)
            self.m_sizerTestData.ShowItems(True)
        elif self._testStep.Action == 'A':
            self.m_sizerTransactionID.ShowItems(True)
            self.m_sizerTestData.ShowItems(False)
        # todo - rest of cases

        self.Layout()
