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

from robotide.action.actioninfo import ActionInfo

from robotide.t24api.T24TestStep import T24TestStep


import wx
import wx.xrc
import wx.grid

try:
    from . import robotframeworklexer
except Exception as e:
    robotframeworklexer = None

# from ..editor.popupwindow import HtmlDialog


class TestStepEventListener:

    def __init__(self):
        pass

    def onTestStepCreated(self, testStep, insertBeforeTestStep):
        pass

    def onTestStepChanged(self, testStep):
        pass

    def onTestStepDeleted(self, testStep):
        pass

class T24EditorPlugin(Plugin, TreeAwarePluginMixin, TestStepEventListener):
    title = 'Test Steps'

    def __init__(self, application):
        Plugin.__init__(self, application)
        self._editor_component = None

    def onTestStepCreated(self, testStep, insertBeforeTestStep):
        if insertBeforeTestStep: # insert before
            idx = self._current_test_case.steps.index(insertBeforeTestStep.subSteps()[0])
            for subStep in testStep.subSteps():
                self._current_test_case.steps.insert(idx, subStep)
                idx+=1
        else: # last one
            for subStep in testStep.subSteps():
                self._current_test_case.steps.append(subStep)

        self.tree.get_selected_datafile_controller().mark_dirty()

    def onTestStepChanged(self, testStep):
        self.tree.get_selected_datafile_controller().mark_dirty()

    def onTestStepDeleted(self, testStep):
        if self._current_test_case:
            for subStep in testStep.subSteps():
                self._current_test_case.steps.remove(subStep)

        self.tree.get_selected_datafile_controller().mark_dirty()

    @property
    def _editor(self):
        if not self._editor_component:
            self._editor_component = T24TestStepsContainer(self.notebook, self)
            self._editor_component._eventListeners.append(self)

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
        self.show_tab(self._editor)

    def disable(self):
        self.remove_self_from_tree_aware_plugins()
        self.unsubscribe_all()
        self.unregister_actions()
        self.delete_tab(self._editor)
        self._editor_component = None

    def OnOpen(self, event):
        #self.show_tab(self._editor)
        pass

    def OnSaving(self, message):
        pass
        #if self.is_focused():
            # self._editor.save()
            # NOTE: All of the changes must be executed by T24TestStepPanel and its _testStep memner
            #controller = self.tree.get_selected_datafile_controller()
            #bub = self._current_test_case
            #controller.datafile.testcase_table.test
            #bui = controller

    def OnDataChanged(self, message):
        pass
        """
        if self._should_process_data_changed_message(message):
            if isinstance(message, RideOpenSuite):
                self._editor.reset()
            if self._editor.dirty:
                self._apply_txt_changes_to_model()
            self._refresh_timer.Start(500, True) # For performance reasons only run after all the data changes
        """

    def _on_timer(self, event):
        # self._open_tree_selection_in_editor()
        event.Skip()

    def _should_process_data_changed_message(self, message):
        return isinstance(message, RideDataChanged) and \
               not isinstance(message, RideDataChangedToDirty)

    def OnTreeSelection(self, message):
        # self._editor.store_position()
        self._last_tree_selection_message = message;
        if message.node._data.item.__class__.__name__ is 'TestCase':
            self._current_test_case = message.node._data.item
        else:
            self._current_test_case = None

        if self.is_focused() or self.tabJustChanged:
            self.tabJustChanged = False
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

    def OnTabChange(self, message):
        if message.newtab == self.title:
            self.tabJustChanged=True
            self.OnTreeSelection(self._last_tree_selection_message)

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

    _eventListeners = []

    _testCaseTreeNode = None
    _tree = None
    _testSteps = []

    _plugin = None

    def __init__( self, parent, parentPlugin ):
        T24TestStepsContainerBase.__init__(self, parent)
        self._plugin = parentPlugin

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

        stepPreActions = []

        stepIdx = 1

        if testSteps is not None:
            for step in testSteps:
                if not T24TestStep.isT24TestStep(step):
                    stepPreActions.append(step)
                else:
                    panel = self.createStepPanel(stepPreActions, step)
                    stepPreActions = []
                    if panel:
                        panel.setIndex(stepIdx)
                        stepIdx+=1
                        self.m_sizerTestStepsContainer.Add(panel, 1, wx.EXPAND |wx.ALL, 5 )

            self.m_scrolledWindow2.SetSizer(self.m_sizerTestStepsContainer)
            self.m_scrolledWindow2.Layout()
            self.m_sizerTestStepsContainer.Fit( self.m_scrolledWindow2 )
            self.m_sizerTestStepsContainer.Layout()

            self.Layout()

    def createStepPanel(self, stepPreActions, stepDetails):
        t24TestStep = T24TestStep(stepPreActions, stepDetails)
        self._testSteps.append(t24TestStep)

        return self.createTestStepPanel(t24TestStep)

    def createTestStepPanel(self, testStep):
        if testStep.IsRealTestStep:
            panel = T24TestStepPanel(self.m_scrolledWindow2, self, testStep)
            return panel

        return None

    def fireOnNewTestStepBeforeEvent(self, insertBeforeTestStep):
        testStep = T24TestStep.createNew()

        if self._eventListeners:
            for el in self._eventListeners:
                el.onTestStepCreated(testStep, insertBeforeTestStep)

        # recreate self
        self.setTestCase(self._testCaseTreeNode, self._tree)

    def fireOnTestStepChangeEvent(self, testStep):
        if not not self._eventListeners:
            for el in self._eventListeners:
                el.onTestStepChanged(testStep)

    def fireOnTestStepDeleteEvent(self, testStep):
        if not not self._eventListeners:
            for el in self._eventListeners:
                el.onTestStepDeleted(testStep)

###########################################################################

class T24TestStepPanelBase ( wx.Panel ):

    def __init__( self, parent ):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 683,295 ), style = wx.TAB_TRAVERSAL )

        bSizer1 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer10 = wx.BoxSizer( wx.VERTICAL )

        bSizer111 = wx.BoxSizer( wx.VERTICAL )

        self.m_btnNewBefore = wx.Button( self, wx.ID_ANY, u"+", wx.DefaultPosition, wx.Size( 22,22 ), 0 )
        self.m_btnNewBefore.SetFont( wx.Font( 10, 74, 90, 92, False, "Arial Black" ) )
        self.m_btnNewBefore.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_HIGHLIGHTTEXT ) )
        self.m_btnNewBefore.SetBackgroundColour( wx.Colour( 0, 128, 0 ) )
        self.m_btnNewBefore.SetToolTipString( u"Create and insert new test step before current one" )

        bSizer111.Add( self.m_btnNewBefore, 0, wx.TOP|wx.BOTTOM|wx.LEFT, 5 )


        bSizer10.Add( bSizer111, 1, 0, 5 )

        bSizer12 = wx.BoxSizer( wx.VERTICAL )

        self.m_btnUp = wx.Button( self, wx.ID_ANY, u"/\\", wx.DefaultPosition, wx.Size( 22,22 ), wx.BU_BOTTOM|wx.NO_BORDER )
        self.m_btnUp.SetFont( wx.Font( 9, 74, 90, 92, False, "Arial Black" ) )
        self.m_btnUp.SetToolTipString( u"Move test step up" )

        bSizer12.Add( self.m_btnUp, 0, wx.TOP|wx.BOTTOM|wx.LEFT, 5 )

        self.m_btnDown = wx.Button( self, wx.ID_ANY, u"\\/", wx.DefaultPosition, wx.Size( 22,22 ), wx.BU_TOP|wx.NO_BORDER )
        self.m_btnDown.SetFont( wx.Font( 9, 74, 90, 92, False, "Arial Black" ) )
        self.m_btnDown.SetToolTipString( u"Move test step down" )

        bSizer12.Add( self.m_btnDown, 0, wx.BOTTOM|wx.LEFT, 5 )

        self.m_dummySpacer1 = wx.StaticText( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_dummySpacer1.Wrap( -1 )
        bSizer12.Add( self.m_dummySpacer1, 0, wx.TOP|wx.BOTTOM|wx.RIGHT, 5 )

        self.m_btnNewAfter = wx.Button( self, wx.ID_ANY, u"+", wx.DefaultPosition, wx.Size( 22,22 ), 0 )
        self.m_btnNewAfter.SetFont( wx.Font( 10, 74, 90, 92, False, "Arial Black" ) )
        self.m_btnNewAfter.SetForegroundColour( wx.Colour( 0, 128, 0 ) )
        self.m_btnNewAfter.Hide()
        self.m_btnNewAfter.SetToolTipString( u"Create and insert new test step before current one" )

        bSizer12.Add( self.m_btnNewAfter, 0, wx.ALL, 5 )


        bSizer10.Add( bSizer12, 0, wx.ALIGN_BOTTOM, 5 )


        bSizer1.Add( bSizer10, 0, wx.EXPAND, 5 )

        self.m_panel3 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SIMPLE_BORDER|wx.TAB_TRAVERSAL )
        bSizer11 = wx.BoxSizer( wx.VERTICAL )

        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer91 = wx.BoxSizer( wx.HORIZONTAL )

        self.lblTestStepIndex = wx.StaticText( self.m_panel3, wx.ID_ANY, u"4", wx.Point( -1,-1 ), wx.DefaultSize, wx.ALIGN_CENTRE )
        self.lblTestStepIndex.Wrap( -1 )
        self.lblTestStepIndex.SetFont( wx.Font( 12, 74, 93, 92, False, "Arial" ) )
        self.lblTestStepIndex.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_HIGHLIGHT ) )

        bSizer91.Add( self.lblTestStepIndex, 0, wx.ALL, 8 )

        m_choiceTestStepActionChoices = [ u"M", u"E(nq)", u"I", u"A", u"S", u"V" ]
        self.m_choiceTestStepAction = wx.Choice( self.m_panel3, wx.ID_ANY, wx.DefaultPosition, wx.Size( 60,-1 ), m_choiceTestStepActionChoices, 0 )
        self.m_choiceTestStepAction.SetSelection( 0 )
        bSizer91.Add( self.m_choiceTestStepAction, 0, wx.ALL, 5 )

        self.m_txtTestStepTransaction = wx.TextCtrl( self.m_panel3, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 514,-1 ), 0 )
        bSizer91.Add( self.m_txtTestStepTransaction, 0, wx.ALIGN_LEFT|wx.ALIGN_RIGHT|wx.ALL, 5 )


        bSizer4.Add( bSizer91, 1, wx.EXPAND, 5 )

        bSizer9 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_btnDelete = wx.Button( self.m_panel3, wx.ID_ANY, u"X", wx.Point( -1,-1 ), wx.Size( 22,22 ), 0 )
        self.m_btnDelete.SetFont( wx.Font( 9, 74, 90, 92, False, "Arial Black" ) )
        self.m_btnDelete.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_HIGHLIGHTTEXT ) )
        self.m_btnDelete.SetBackgroundColour( wx.Colour( 236, 77, 0 ) )
        self.m_btnDelete.SetToolTipString( u"Delete the test step" )

        bSizer9.Add( self.m_btnDelete, 0, wx.BOTTOM|wx.LEFT, 5 )


        bSizer4.Add( bSizer9, 0, wx.ALIGN_RIGHT, 5 )


        bSizer11.Add( bSizer4, 0, wx.ALIGN_LEFT|wx.EXPAND, 5 )

        fgSizer4 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer4.SetFlexibleDirection( wx.BOTH )
        fgSizer4.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticline2 = wx.StaticLine( self.m_panel3, wx.ID_ANY, wx.DefaultPosition, wx.Size( 664,-1 ), wx.LI_HORIZONTAL )
        fgSizer4.Add( self.m_staticline2, 0, wx.EXPAND |wx.ALL, 5 )


        bSizer11.Add( fgSizer4, 0, wx.ALIGN_LEFT, 5 )

        self.m_sizerTransactionID = wx.BoxSizer( wx.HORIZONTAL )

        self.m_lblTransID = wx.StaticText( self.m_panel3, wx.ID_ANY, u"@ID", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_lblTransID.Wrap( -1 )
        self.m_sizerTransactionID.Add( self.m_lblTransID, 0, wx.ALL, 8 )

        self.m_txtTransactionID = wx.TextCtrl( self.m_panel3, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 320,-1 ), 0 )
        self.m_sizerTransactionID.Add( self.m_txtTransactionID, 0, wx.ALL, 5 )


        bSizer11.Add( self.m_sizerTransactionID, 0, wx.EXPAND, 5 )

        self.m_sizerTestData = wx.BoxSizer( wx.HORIZONTAL )

        self.m_sizerTestDataCtrlHolder = wx.StaticBoxSizer( wx.StaticBox( self.m_panel3, wx.ID_ANY, u"Test Data" ), wx.VERTICAL )

        # WARNING: wxPython code generation isn't supported for this widget yet.
        self.m_editTestData = self.createTestDataEditCtrl() #wx.Window( self.m_panel3 )
        self.m_sizerTestDataCtrlHolder.Add( self.m_editTestData, 1, wx.EXPAND |wx.ALL, 5 )


        self.m_sizerTestData.Add( self.m_sizerTestDataCtrlHolder, 1, wx.LEFT, 5 )

        bSizer13 = wx.BoxSizer( wx.VERTICAL )

        sbSizer2 = wx.StaticBoxSizer( wx.StaticBox( self.m_panel3, wx.ID_ANY, u"How to Handle Overrides" ), wx.HORIZONTAL )

        m_choiceHowToHandleOverridesChoices = [ u"Accept All", u"Fail", wx.EmptyString, wx.EmptyString ]
        self.m_choiceHowToHandleOverrides = wx.Choice( self.m_panel3, wx.ID_ANY, wx.DefaultPosition, wx.Size( 200,-1 ), m_choiceHowToHandleOverridesChoices, 0 )
        self.m_choiceHowToHandleOverrides.SetSelection( 0 )
        sbSizer2.Add( self.m_choiceHowToHandleOverrides, 0, wx.ALIGN_RIGHT, 5 )


        bSizer13.Add( sbSizer2, 0, wx.ALIGN_RIGHT, 5 )

        sbSizer21 = wx.StaticBoxSizer( wx.StaticBox( self.m_panel3, wx.ID_ANY, u"How to Handle Errors" ), wx.VERTICAL )

        m_choiceHowToHandleErrorsChoices = [ u"Fail", u"Expect Any Error", u"Expect Error Containing" ]
        self.m_choiceHowToHandleErrors = wx.Choice( self.m_panel3, wx.ID_ANY, wx.DefaultPosition, wx.Size( 200,-1 ), m_choiceHowToHandleErrorsChoices, 0 )
        self.m_choiceHowToHandleErrors.SetSelection( 0 )
        sbSizer21.Add( self.m_choiceHowToHandleErrors, 0, wx.ALIGN_RIGHT, 5 )

        self.m_txtExpectErrorContaining = wx.TextCtrl( self.m_panel3, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 200,-1 ), 0 )
        sbSizer21.Add( self.m_txtExpectErrorContaining, 0, wx.ALIGN_RIGHT|wx.TOP, 5 )


        bSizer13.Add( sbSizer21, 1, wx.EXPAND|wx.TOP, 5 )


        self.m_sizerTestData.Add( bSizer13, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.LEFT, 5 )


        bSizer11.Add( self.m_sizerTestData, 0, wx.EXPAND, 5 )


        self.m_panel3.SetSizer( bSizer11 )
        self.m_panel3.Layout()
        bSizer11.Fit( self.m_panel3 )
        bSizer1.Add( self.m_panel3, 1, wx.EXPAND |wx.ALL, 5 )


        self.SetSizer( bSizer1 )
        self.Layout()

        # Connect Events
        self.m_btnNewBefore.Bind( wx.EVT_BUTTON, self.onNewTestStepBefore )
        self.m_btnUp.Bind( wx.EVT_BUTTON, self.onBtnMoveUp )
        self.m_btnDown.Bind( wx.EVT_BUTTON, self.onBtnMoveDown )
        self.m_btnNewAfter.Bind( wx.EVT_BUTTON, self.onNewTestStepBefore )
        self.m_choiceTestStepAction.Bind( wx.EVT_CHOICE, self.onActionChanged )
        self.m_txtTestStepTransaction.Bind( wx.EVT_TEXT, self.onTransactionChanged )
        self.m_btnDelete.Bind( wx.EVT_BUTTON, self.onBtnDelete )
        self.m_txtTransactionID.Bind( wx.EVT_TEXT, self.onTransactionIDChanged )
        self.m_editTestData.Bind( wx.EVT_KEY_UP, self.onEditTestDataKeyUp )

    def __del__( self ):
        pass

    # Virtual event handlers, overide them in your derived class
    def onNewTestStepBefore( self, event ):
        event.Skip()

    def onBtnMoveUp( self, event ):
        event.Skip()

    def onBtnMoveDown( self, event ):
        event.Skip()


    def onActionChanged( self, event ):
        event.Skip()

    def onTransactionChanged( self, event ):
        event.Skip()

    def onBtnDelete( self, event ):
        event.Skip()

    def onTransactionIDChanged( self, event ):
        event.Skip()

    def onEditTestDataKeyUp( self, event ):
		event.Skip()

    def createTestDataEditCtrl(self):
        ctrl = wx.stc.StyledTextCtrl(self.m_panel3, wx.ID_ANY)

        # todo - add stryles etc to the control
        # todo - create simple syntax highlighter. For ex:
        # MNEMONIC:=SUPER001
        # SHORT.NAME:=Super Duper
        # Name.1:=Bab Jaga
        # City|ADDRESS:1:1=London

        self._register_shortcuts(ctrl)
        return ctrl

    def _register_shortcuts(self, editor):

        accels = []

        accels.append(self._createAccelerator(wx.ACCEL_CTRL, ord('X'),(lambda e: self.m_editTestData.Cut())))
        accels.append(self._createAccelerator(wx.ACCEL_CTRL, ord('C'),(lambda e: self.m_editTestData.Copy())))

        if IS_MAC: # Mac needs this key binding
            accels.append(self._createAccelerator(wx.ACCEL_CTRL, ord('A'),(lambda e: self.m_editTestData.SelectAll())))

        if IS_WINDOWS or IS_MAC: # Linux does not need this key binding
            accels.append(self._createAccelerator(wx.ACCEL_CTRL, ord('V'),(lambda e: self.m_editTestData.Paste())))

        accels.append(self._createAccelerator(wx.ACCEL_CTRL, ord('Z'),(lambda e: self.m_editTestData.Undo())))
        accels.append(self._createAccelerator(wx.ACCEL_CTRL, ord('Y'),(lambda e: self.m_editTestData.Redo())))
        accels.append(self._createAccelerator(wx.ACCEL_NORMAL, wx.WXK_DELETE,(lambda e: self.m_editTestData.DeleteBack())))#todo how to delete the selection?
        #accels.append(self._createAccelerator(wx.ACCEL_CTRL, ord('G'),(lambda e: self.m_editTestData.FindText())))

        self.SetAcceleratorTable(wx.AcceleratorTable(accels))

    def _createAccelerator(self, modifierKey, key, func):
        cutId = wx.NewId()
        self.Bind(wx.EVT_MENU, func, id=cutId)
        return (modifierKey, key, cutId )

###########################################################################
class T24TestStepPanel (T24TestStepPanelBase):



    _testStep = None
    _testStepsContainer = None;

    def __init__(self, parent, testStepContainer, testStep):
        T24TestStepPanelBase.__init__ ( self, parent )
        self._testStep = testStep
        self.setTestStepDetails()
        self.updateUI()

        # leave it last not to fire change events during initialization
        self._testStepsContainer = testStepContainer

    def __del__( self ):
        pass


    def setIndex(self, idx):
        self.lblTestStepIndex.SetLabel('{}'.format(idx))

    def onActionChanged( self, event ):
        if self._testStep:
            self._testStep.Action = self.m_choiceTestStepAction.GetStringSelection()
            self._testStep.applyChanges()
            self.updateUI()
            self.Layout()
            self._testStepsContainer.fireOnTestStepChangeEvent(self._testStep)

    def onTransactionChanged( self, event ):
        if self._testStep:
            self._testStep.AppVersion = self.m_txtTestStepTransaction.GetValue()
            self._testStep.applyChanges()
            self._testStepsContainer.fireOnTestStepChangeEvent(self._testStep)

    def onTransactionIDChanged(self, event):
        if self._testStep:
            self._testStep.TransactionID = self.m_txtTransactionID.GetValue()
            self._testStep.applyChanges()
            self._testStepsContainer.fireOnTestStepChangeEvent(self._testStep)

    def onEditTestDataKeyUp( self, event ):
        if self._testStep:
            self._testStep.TestData = self.getTestDataFromUI()
            self._testStep.applyTestDataChanges()
            self._testStepsContainer.fireOnTestStepChangeEvent(self._testStep)

    def setTestStepDetails(self):
        self.m_choiceTestStepAction.SetSelection(self.m_choiceTestStepAction.FindString(self._testStep.Action))
        self.m_txtTestStepTransaction.SetValue(self._testStep.AppVersion)
        self.m_txtTransactionID.SetValue(self._testStep.TransactionID)

    def updateUI(self):
        if self._testStep is None:
            # hide all
            self.m_sizerTransactionID.ShowItems(False)
            self.m_sizerTestData.ShowItems(False)
        elif self._testStep.Action == 'I':
            self.m_sizerTransactionID.ShowItems(False)
            self.m_sizerTestData.ShowItems(True)
            self.setTestData(self._testStep.TestData)
        elif self._testStep.Action == 'A':
            self.m_sizerTransactionID.ShowItems(True)
            self.m_sizerTestData.ShowItems(False)
        elif self._testStep.Action == 'S':
            self.m_sizerTransactionID.ShowItems(True)
            self.m_sizerTestData.ShowItems(False)

        # todo - rest of cases
        else:
            # self.m_lblTransID.SetLabel('TODO Not Implemented')
            self.m_sizerTransactionID.ShowItems(False)
            self.m_sizerTestData.ShowItems(False)


        self.Update()
        self.Layout()

    def setTestData(self, testData):

        self.m_editTestData.Clear()

        if testData is None:
            return

        for attr in testData:
            self.m_editTestData.AppendText(attr[0])
            self.m_editTestData.AppendText(' := ')
            self.m_editTestData.AppendText(attr[1])
            self.m_editTestData.AppendText('\r\n')

        ""
        """
        self.m_gridTestData.DeleteRows(0, self.m_gridTestData.GetNumberRows(), True)

        if testData is None:
            return

        self.m_gridTestData.AppendRows(testData.__len__())

        row = 0
        for attr in testData:
            self.m_gridTestData.SetCellValue(row,0,attr[0])
            self.m_gridTestData.SetCellValue(row,2,attr[1])

            row+=1
        """
    def getTestDataFromUI(self):

        res = []

        for line in self.m_editTestData.GetText().split('\n'):
            nameValue = T24TestStepPanel.splitNameValue(line)
            if nameValue:
                res.append(nameValue)

        return res

    @staticmethod
    def splitNameValue(nameValue):

        if not nameValue or len(nameValue)==0:
            return None

        pos = nameValue.find(':=')
        if pos <= 0:
            return None

        name = nameValue[:pos].strip()
        value = nameValue[pos+2:].strip()

        if name and len(name)>0:
            return (name,value)

        return None


    @staticmethod
    def Warn(parent, message, caption = 'Warning!'):
        dlg = wx.MessageDialog(parent, message, caption, wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()

    @staticmethod
    def YesNo(parent, question, caption = 'Yes or no?', icon = wx.ICON_QUESTION):
        dlg = wx.MessageDialog(parent, question, caption, wx.YES_NO | icon)
        result = dlg.ShowModal() == wx.ID_YES
        dlg.Destroy()
        return result

    @staticmethod
    def confirmTestStepDeletion(parent, testStepName):
        return T24TestStepPanel.YesNo(parent, "Do you really want to delete test step: '{}'?".format(testStepName), "Confirm Deletion", wx.ICON_WARNING)

    def onBtnDelete( self, event ):
        if T24TestStepPanel.confirmTestStepDeletion(self, self._testStep.toString()):
            parent = self.Parent
            container = self._testStepsContainer
            testStep = self._testStep
            self.Destroy()
            parent.Layout()
            container.fireOnTestStepDeleteEvent(testStep)

    def onNewTestStepBefore( self, event ):
        self._testStepsContainer.fireOnNewTestStepBeforeEvent(self._testStep)

    def onBtnMoveUp( self, event ):
        T24TestStepPanel.Warn(self, "TODO: Not implemented")
        self._testStepsContainer.fireOnTestStepChangeEvent(self._testStep)

    def onBtnMoveDown( self, event ):
        T24TestStepPanel.Warn(self, "TODO: Not implemented")
        self._testStepsContainer.fireOnTestStepChangeEvent(self._testStep)
