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

from robotide.tip_api.T24TestStep import T24TestStep
from robotide.tip_api.TipServerResources import TipServerResources
from robotide.tip_api.TipStyledTextCtrl import TipStyledTextCtrl

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

    def onTestStepChanged(self, testStep, oldSubSteps = None):
        pass

    def onTestStepDeleted(self, testStep):
        pass

    def onTestStepMoveUp(self, testStep):
        pass

    def onTestStepMoveDown(self, testStep):
        pass

class T24EditorPlugin(Plugin, TreeAwarePluginMixin, TestStepEventListener):
    """A plugin for editing test steps within a specialized Temenos T24-specific interface.
    This plugin shows a tab 'Test Steps' where the user can create/edit/move/delete T24 test steps."""
    title = 'Test Steps'

    # todo this should be there but causes problems with deleting of test steps
    # tabJustChanged = False

    def __init__(self, application):
        Plugin.__init__(self, application)
        self._editor_component = None

    def onTestStepCreated(self, testStep, insertBeforeTestStep):
        if insertBeforeTestStep:  # insert before
            idx = self._current_test_case.steps.index(insertBeforeTestStep.subSteps()[0])
            for subStep in testStep.subSteps():
                self._current_test_case.steps.insert(idx, subStep)
                idx += 1
        else:  # last one
            for subStep in testStep.subSteps():
                self._current_test_case.steps.append(subStep)

        self.tree.get_selected_datafile_controller().mark_dirty()

    def onTestStepChanged(self, testStep, oldSubSteps=None):
        if oldSubSteps and oldSubSteps.__len__() > 1:
            # remove old pre steps
            for oldSubStep in oldSubSteps[:oldSubSteps.__len__() - 1]:
                self._current_test_case.steps.remove(oldSubStep)

        if oldSubSteps and testStep.subSteps().__len__() > 1:
            # insert new pre steps
            idx = self._current_test_case.steps.index(testStep.subSteps()[testStep.subSteps().__len__() - 1])
            for newPreStep in testStep.subSteps()[:testStep.subSteps().__len__() - 1]:
                self._current_test_case.steps.insert(idx, newPreStep)
                idx+=1

        self.tree.get_selected_datafile_controller().mark_dirty()

    def onTestStepDeleted(self, testStep):
        if self._current_test_case:
            for subStep in testStep.subSteps():
                self._current_test_case.steps.remove(subStep)

        self.tree.get_selected_datafile_controller().mark_dirty()

    def onTestStepMoveUp(self, testStep):
        if self._current_test_case:
            firsSubStep = testStep.subSteps()[0]
            firsSubStepIdx = self._current_test_case.steps.index(firsSubStep)
            if firsSubStepIdx > 0:
                previousStepIndex = firsSubStepIdx - 1
                while(previousStepIndex > 0 and not T24TestStep.isT24TestStep(self._current_test_case.steps[previousStepIndex - 1]) ):
                    previousStepIndex -= 1

                self.onTestStepDeleted(testStep)

                for subStep in testStep.subSteps():
                    self._current_test_case.steps.insert(previousStepIndex, subStep)
                    previousStepIndex += 1

                self.tree.get_selected_datafile_controller().mark_dirty()

                return True

        return False

    def onTestStepMoveDown(self, testStep):
        if self._current_test_case:
            lastSubStep = testStep.subSteps()[testStep.subSteps().__len__() - 1]
            lastSubStepIdx = self._current_test_case.steps.index(lastSubStep)
            if lastSubStepIdx < (self._current_test_case.steps.__len__() - 1):
                nextStepIndex = lastSubStepIdx + 1;
                while(nextStepIndex < self._current_test_case.steps.__len__() and not T24TestStep.isT24TestStep(self._current_test_case.steps[nextStepIndex]) ):
                    nextStepIndex += 1

                self.onTestStepDeleted(testStep)

                nextStepIndex -= testStep.subSteps().__len__()
                nextStepIndex += 1

                for subStep in testStep.subSteps():
                    self._current_test_case.steps.insert(nextStepIndex, subStep)
                    nextStepIndex += 1

                self.tree.get_selected_datafile_controller().mark_dirty()

                return True

        return False

    @property
    def _editor(self):
        if not self._editor_component:
            self._editor_component = T24TestStepsContainer(self.notebook, self)
            self._editor_component._eventListeners.append(self)

            self.add_tab_with_img(self._editor_component, self.title, 0, allow_closing=False)
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
            # NOTE: All of the changes must be executed by T24TestStepPanel and its testStep member
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

        self.m_scrolledWindow2 = wx.ScrolledWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL )
        self.m_scrolledWindow2.SetScrollRate( 5, 5 )
        self.m_sizerTestStepsContainer = wx.FlexGridSizer( 0, 1, 0, 0 )
        self.m_sizerTestStepsContainer.AddGrowableCol( 0 )
        self.m_sizerTestStepsContainer.SetFlexibleDirection( wx.BOTH )
        self.m_sizerTestStepsContainer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_ALL )


        self.m_scrolledWindow2.SetSizer( self.m_sizerTestStepsContainer )
        self.m_scrolledWindow2.Layout()
        self.m_sizerTestStepsContainer.Fit( self.m_scrolledWindow2 )
        bSizer8.Add( self.m_scrolledWindow2, 1, wx.ALL|wx.EXPAND, 5 )


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
        #self.SetDoubleBuffered(True)

    def __del__( self ):
        pass

    def setTestCase(self, treeNode, tree):
        # self._testCaseTreeNode._data.item is the test case - we read and update it
        self._testCaseTreeNode = treeNode
        self._tree = tree
        if self._testCaseTreeNode is None:
            self.Hide()
        else:
            self.Show()
            self.Freeze()
            self.createTestStepsControls(self._testCaseTreeNode._data.item.steps)
            self.Thaw()

    def createTestStepsControls(self, testSteps):
        #if not not self.m_sizerTestStepsContainer.Children:
        #    self.m_sizerTestStepsContainer.DeleteWindows()
        self.m_sizerTestStepsContainer.Clear(True)

        stepPreActions = []

        stepIdx = 1

        if testSteps is not None:
            for step in testSteps:
                if not T24TestStep.isT24TestStep(step):
                    stepPreActions.append(step)
                else:
                    panel = self._createStepPanel(stepPreActions, step)
                    stepPreActions = []
                    if panel:
                        panel.setIndex(stepIdx)
                        stepIdx += 1
                        self.m_sizerTestStepsContainer.Add(panel, 1, wx.EXPAND | wx.ALL, 5)

            dummyPanel = self._createEndDummyTestStepPanel()
            self.m_sizerTestStepsContainer.Add(dummyPanel, 1, wx.EXPAND | wx.ALL, 5)

            self.m_scrolledWindow2.SetSizer(self.m_sizerTestStepsContainer)
            self.m_scrolledWindow2.Layout()

            self.m_sizerTestStepsContainer.FitInside(self.m_scrolledWindow2)
            self.m_sizerTestStepsContainer.Layout()

            self.Layout()

    def _createStepPanel(self, stepPreActions, stepDetails):
        t24TestStep = T24TestStep(stepPreActions, stepDetails)
        self._testSteps.append(t24TestStep)

        return self._createTestStepPanel(t24TestStep)

    def _createTestStepPanel(self, testStep):
        if testStep.IsRealTestStep:
            panel = T24TestStepPanel(self.m_scrolledWindow2, self, testStep)
            return panel

        return None

    def _createEndDummyTestStepPanel(self):
        return T24TestStepPanel(self.m_scrolledWindow2, self, None)

    def fireOnNewTestStepBeforeEvent(self, insertBeforeTestStep, stepAction):
        testStep = T24TestStep.createNew(stepAction)

        if self._eventListeners:
            for el in self._eventListeners:
                el.onTestStepCreated(testStep, insertBeforeTestStep)

        # recreate self
        self.setTestCase(self._testCaseTreeNode, self._tree)

    def fireOnTestStepChangeEvent(self, testStep, oldSubSteps = None):
        if not not self._eventListeners:
            for el in self._eventListeners:
                el.onTestStepChanged(testStep, oldSubSteps)

        if oldSubSteps:
            self.m_scrolledWindow2.Layout()
            #self.m_sizerTestStepsContainer.Fit( self.m_scrolledWindow2 )
            self.m_sizerTestStepsContainer.FitInside(self.m_scrolledWindow2)
            self.m_sizerTestStepsContainer.Layout()
            self.Layout()

    def fireOnTestStepDeleteEvent(self, testStep):
        if not not self._eventListeners:
            for el in self._eventListeners:
                el.onTestStepDeleted(testStep)

    def fireOnTestStepMoveUpEvent(self, testStep):
        moved = False
        if self._eventListeners:
            for el in self._eventListeners:
                if el.onTestStepMoveUp(testStep):
                    moved = True

        if moved:
            # recreate self
            self.setTestCase(self._testCaseTreeNode, self._tree)

    def fireOnTestStepMoveDownEvent(self, testStep):
        moved = False
        if self._eventListeners:
            for el in self._eventListeners:
                if el.onTestStepMoveDown(testStep):
                    moved = True

        if moved:
            # recreate self
            self.setTestCase(self._testCaseTreeNode, self._tree)

###########################################################################

class T24TestStepPanelBase ( wx.Panel ):

    def __init__( self, parent ):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL )
        # wx.Size(683,375)
        bSizer1 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer10 = wx.BoxSizer( wx.VERTICAL )

        bSizer111 = wx.BoxSizer( wx.VERTICAL )

        self.m_btnNewBefore = wx.Button( self, wx.ID_ANY, u"+", wx.DefaultPosition, wx.Size( 22,22 ), 0 )
        self.m_btnNewBefore.SetFont( wx.Font( 10, 74, 90, 92, False, "Arial Black" ) )
        self.m_btnNewBefore.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_HIGHLIGHTTEXT ) )
        self.m_btnNewBefore.SetBackgroundColour( wx.Colour( 0, 163, 255 ) )
        self.m_btnNewBefore.SetToolTipString( u"Create and insert new test step before current one" )

        self.m_menuNewTestStepBefore = wx.Menu()
        self.m_menuItemNewLoginStepBefore = wx.MenuItem( self.m_menuNewTestStepBefore, wx.ID_ANY, u"&L - Login in T24", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menuNewTestStepBefore.AppendItem( self.m_menuItemNewLoginStepBefore )

        self.m_menuItemNewMenuStepBefore = wx.MenuItem( self.m_menuNewTestStepBefore, wx.ID_ANY, u"&M - Go to a T24 Menu", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menuNewTestStepBefore.AppendItem( self.m_menuItemNewMenuStepBefore )

        self.m_menuItemNewInputStepBefore = wx.MenuItem( self.m_menuNewTestStepBefore, wx.ID_ANY, u"&I - Input T24 Record", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menuNewTestStepBefore.AppendItem( self.m_menuItemNewInputStepBefore )

        self.m_menuItemNewAuthorizeStepBefore = wx.MenuItem( self.m_menuNewTestStepBefore, wx.ID_ANY, u"&A - Authorize T24 Record", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menuNewTestStepBefore.AppendItem( self.m_menuItemNewAuthorizeStepBefore )

        self.m_menuItemNewSeeStepBefore = wx.MenuItem( self.m_menuNewTestStepBefore, wx.ID_ANY, u"&S - See and Verify T24 Record", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menuNewTestStepBefore.AppendItem( self.m_menuItemNewSeeStepBefore )

        self.m_menuItemNewEnquiryStepBefore = wx.MenuItem( self.m_menuNewTestStepBefore, wx.ID_ANY, u"&E - Run and Verify T24 &Enquiry", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menuNewTestStepBefore.AppendItem( self.m_menuItemNewEnquiryStepBefore )

        self.m_menuItemNewValidateStepBefore = wx.MenuItem( self.m_menuNewTestStepBefore, wx.ID_ANY, u"&V - Validate T24 Record", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menuNewTestStepBefore.AppendItem( self.m_menuItemNewValidateStepBefore )

        self.m_btnNewBefore.Bind( wx.EVT_RIGHT_DOWN, self.m_btnNewBeforeOnContextMenu )

        bSizer111.Add( self.m_btnNewBefore, 0, wx.TOP|wx.BOTTOM|wx.LEFT, 5 )


        bSizer10.Add( bSizer111, 1, 0, 5 )

        self.m_sizerTestStepUpDown = wx.BoxSizer( wx.VERTICAL )

        self.m_btnUp = wx.Button( self, wx.ID_ANY, u"/\\", wx.DefaultPosition, wx.Size( 22,22 ), wx.BU_BOTTOM|wx.NO_BORDER )
        self.m_btnUp.SetFont( wx.Font( 9, 74, 90, 92, False, "Arial Black" ) )
        self.m_btnUp.SetToolTipString( u"Move test step up" )

        self.m_sizerTestStepUpDown.Add( self.m_btnUp, 0, wx.TOP|wx.BOTTOM|wx.LEFT, 5 )

        self.m_btnDown = wx.Button( self, wx.ID_ANY, u"\\/", wx.DefaultPosition, wx.Size( 22,22 ), wx.BU_TOP|wx.NO_BORDER )
        self.m_btnDown.SetFont( wx.Font( 9, 74, 90, 92, False, "Arial Black" ) )
        self.m_btnDown.SetToolTipString( u"Move test step down" )

        self.m_sizerTestStepUpDown.Add( self.m_btnDown, 0, wx.BOTTOM|wx.LEFT, 5 )

        self.m_dummySpacer1 = wx.StaticText( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_dummySpacer1.Wrap( -1 )
        self.m_sizerTestStepUpDown.Add( self.m_dummySpacer1, 0, wx.TOP|wx.BOTTOM|wx.RIGHT, 5 )


        bSizer10.Add( self.m_sizerTestStepUpDown, 0, wx.ALIGN_BOTTOM, 5 )


        bSizer1.Add( bSizer10, 0, wx.EXPAND, 5 )

        self.m_panelTestStepContents = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SIMPLE_BORDER|wx.TAB_TRAVERSAL )
        self.m_sizerTestStepContents = wx.BoxSizer( wx.VERTICAL )

        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer91 = wx.BoxSizer( wx.HORIZONTAL )

        self.lblTestStepIndex = wx.StaticText( self.m_panelTestStepContents, wx.ID_ANY, u"4", wx.Point( -1,-1 ), wx.DefaultSize, wx.ALIGN_CENTRE )
        self.lblTestStepIndex.Wrap( -1 )
        self.lblTestStepIndex.SetFont( wx.Font( 12, 74, 93, 92, False, "Arial" ) )
        self.lblTestStepIndex.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_HIGHLIGHT ) )

        bSizer91.Add( self.lblTestStepIndex, 0, wx.ALL, 8 )

        m_choiceTestStepActionChoices = [ u"Login", u"M", u"E", u"I", u"A", u"S", u"V" ]
        self.m_choiceTestStepAction = wx.Choice( self.m_panelTestStepContents, wx.ID_ANY, wx.DefaultPosition, wx.Size( 60,-1 ), m_choiceTestStepActionChoices, 0 )
        self.m_choiceTestStepAction.SetSelection( 0 )
        self.m_choiceTestStepAction.SetFont( wx.Font( 9, 74, 90, 92, False, "Arial Black" ) )

        bSizer91.Add( self.m_choiceTestStepAction, 0, wx.ALL, 5 )

        self.m_lblLoginUsingUserOfGroup = wx.StaticText( self.m_panelTestStepContents, wx.ID_ANY, u"using user of group", wx.Point( -1,-1 ), wx.DefaultSize, wx.ALIGN_CENTRE )
        self.m_lblLoginUsingUserOfGroup.Wrap( -1 )
        self.m_lblLoginUsingUserOfGroup.SetFont( wx.Font( 10, 74, 93, 92, False, "Arial" ) )
        self.m_lblLoginUsingUserOfGroup.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNTEXT ) )

        bSizer91.Add( self.m_lblLoginUsingUserOfGroup, 0, wx.TOP|wx.BOTTOM, 9 )

        m_choiceLoginUsingUserOfGroupChoices = []
        self.m_choiceLoginUsingUserOfGroup = wx.Choice( self.m_panelTestStepContents, wx.ID_ANY, wx.DefaultPosition, wx.Size( 200,-1 ), m_choiceLoginUsingUserOfGroupChoices, 0 )
        self.m_choiceLoginUsingUserOfGroup.SetSelection( 0 )
        bSizer91.Add( self.m_choiceLoginUsingUserOfGroup, 0, wx.ALL, 5 )

        self.m_txtTestStepTransaction = wx.TextCtrl( self.m_panelTestStepContents, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 514,-1 ), 0 )
        bSizer91.Add( self.m_txtTestStepTransaction, 0, wx.ALIGN_LEFT|wx.ALIGN_RIGHT|wx.ALL, 5 )


        bSizer4.Add( bSizer91, 1, wx.EXPAND, 5 )

        bSizer9 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_btnDelete = wx.Button( self.m_panelTestStepContents, wx.ID_ANY, u"X", wx.Point( -1,-1 ), wx.Size( 22,22 ), 0 )
        self.m_btnDelete.SetFont( wx.Font( 9, 74, 90, 92, False, "Arial Black" ) )
        self.m_btnDelete.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_HIGHLIGHTTEXT ) )
        self.m_btnDelete.SetBackgroundColour( wx.Colour( 236, 77, 0 ) )
        self.m_btnDelete.SetToolTipString( u"Delete the test step" )

        bSizer9.Add( self.m_btnDelete, 0, wx.BOTTOM|wx.LEFT, 5 )


        bSizer4.Add( bSizer9, 0, wx.ALIGN_RIGHT, 5 )


        self.m_sizerTestStepContents.Add( bSizer4, 0, wx.ALIGN_LEFT|wx.EXPAND, 5 )

        fgSizer4 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer4.SetFlexibleDirection( wx.BOTH )
        fgSizer4.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticline2 = wx.StaticLine( self.m_panelTestStepContents, wx.ID_ANY, wx.DefaultPosition, wx.Size( 664,-1 ), wx.LI_HORIZONTAL )
        fgSizer4.Add( self.m_staticline2, 0, wx.EXPAND |wx.ALL, 5 )


        self.m_sizerTestStepContents.Add( fgSizer4, 0, wx.ALIGN_LEFT, 5 )

        self.m_sizerTransactionID = wx.BoxSizer( wx.HORIZONTAL )

        self.m_lblTransID = wx.StaticText( self.m_panelTestStepContents, wx.ID_ANY, u"@ID", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_lblTransID.Wrap( -1 )
        self.m_sizerTransactionID.Add( self.m_lblTransID, 0, wx.ALL, 8 )

        self.m_txtTransactionID = wx.TextCtrl( self.m_panelTestStepContents, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 320,-1 ), 0 )
        self.m_sizerTransactionID.Add( self.m_txtTransactionID, 0, wx.ALL, 5 )


        self.m_sizerTestStepContents.Add( self.m_sizerTransactionID, 0, wx.EXPAND, 5 )

        self.m_sizerTestData = wx.BoxSizer( wx.HORIZONTAL )

        bSizer14 = wx.BoxSizer( wx.VERTICAL )

        self.m_sizerTestDataCtrlHolder = wx.StaticBoxSizer( wx.StaticBox( self.m_panelTestStepContents, wx.ID_ANY, u"Test Data" ), wx.VERTICAL )


        # WARNING: wxPython code generation isn't supported for this widget yet.
        self.m_editTestData = self.createTestDataEditCtrl() #wx.Window( self.m_panelTestStepContents )
        self.m_sizerTestDataCtrlHolder.Add( self.m_editTestData, 1, wx.EXPAND |wx.ALL, 5 )


        bSizer14.Add( self.m_sizerTestDataCtrlHolder, 1, wx.LEFT|wx.EXPAND, 5 )

        self.m_sizerValidationHolder = wx.StaticBoxSizer( wx.StaticBox( self.m_panelTestStepContents, wx.ID_ANY, u"Validation Rules" ), wx.VERTICAL )

        # WARNING: wxPython code generation isn't supported for this widget yet.
        self.m_editValidationRules = self.createTestDataEditCtrl() # wx.Window( self.m_panelTestStepContents )
        self.m_sizerValidationHolder.Add( self.m_editValidationRules, 1, wx.EXPAND |wx.ALL, 5 )


        bSizer14.Add( self.m_sizerValidationHolder, 1, wx.EXPAND|wx.LEFT, 5 )


        self.m_sizerTestData.Add( bSizer14, 1, wx.LEFT, 5 )

        bSizer13 = wx.BoxSizer( wx.VERTICAL )

        self.m_sizerHandleOverrides = wx.StaticBoxSizer( wx.StaticBox( self.m_panelTestStepContents, wx.ID_ANY, u"How to Handle Overrides" ), wx.HORIZONTAL )

        m_choiceHowToHandleOverridesChoices = [ u"Accept All", u"Fail" ]
        self.m_choiceHowToHandleOverrides = wx.Choice( self.m_panelTestStepContents, wx.ID_ANY, wx.DefaultPosition, wx.Size( 200,-1 ), m_choiceHowToHandleOverridesChoices, 0 )
        self.m_choiceHowToHandleOverrides.SetSelection( 0 )
        self.m_sizerHandleOverrides.Add( self.m_choiceHowToHandleOverrides, 0, wx.ALIGN_RIGHT, 5 )


        bSizer13.Add( self.m_sizerHandleOverrides, 0, wx.ALIGN_RIGHT, 5 )

        self.m_sizerHandleErrors = wx.StaticBoxSizer( wx.StaticBox( self.m_panelTestStepContents, wx.ID_ANY, u"How to Handle Errors" ), wx.VERTICAL )

        m_choiceHowToHandleErrorsChoices = [ u"Fail", u"Expect Any Error", u"Expect Error Containing" ]
        self.m_choiceHowToHandleErrors = wx.Choice( self.m_panelTestStepContents, wx.ID_ANY, wx.DefaultPosition, wx.Size( 200,-1 ), m_choiceHowToHandleErrorsChoices, 0 )
        self.m_choiceHowToHandleErrors.SetSelection( 0 )
        self.m_sizerHandleErrors.Add( self.m_choiceHowToHandleErrors, 0, wx.ALIGN_RIGHT, 5 )

        self.m_txtExpectErrorContaining = wx.TextCtrl( self.m_panelTestStepContents, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 200,-1 ), 0 )
        self.m_sizerHandleErrors.Add( self.m_txtExpectErrorContaining, 0, wx.ALIGN_RIGHT|wx.TOP, 5 )


        bSizer13.Add( self.m_sizerHandleErrors, 1, wx.EXPAND|wx.TOP, 5 )

        self.m_sizerEnquiryType = wx.StaticBoxSizer( wx.StaticBox( self.m_panelTestStepContents, wx.ID_ANY, u"Enquiry Step type" ), wx.VERTICAL )

        m_choiceEnquiryStepTypeChoices = [ u"Check Result", u"Read Data", u"Action" ]
        self.m_choiceEnquiryStepType = wx.Choice( self.m_panelTestStepContents, wx.ID_ANY, wx.DefaultPosition, wx.Size( 200,-1 ), m_choiceEnquiryStepTypeChoices, 0 )
        self.m_choiceEnquiryStepType.SetSelection( 0 )
        self.m_sizerEnquiryType.Add( self.m_choiceEnquiryStepType, 0, wx.ALIGN_RIGHT, 5 )

        self.m_txtEnquiryActionCommand = wx.TextCtrl( self.m_panelTestStepContents, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 200,-1 ), 0 )
        self.m_sizerEnquiryType.Add( self.m_txtEnquiryActionCommand, 0, wx.ALIGN_RIGHT|wx.TOP, 5 )


        bSizer13.Add( self.m_sizerEnquiryType, 1, wx.EXPAND, 5 )


        self.m_sizerTestData.Add( bSizer13, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.LEFT, 5 )


        self.m_sizerTestStepContents.Add( self.m_sizerTestData, 0, wx.EXPAND, 5 )


        self.m_panelTestStepContents.SetSizer( self.m_sizerTestStepContents )
        self.m_panelTestStepContents.Layout()
        self.m_sizerTestStepContents.Fit( self.m_panelTestStepContents )
        bSizer1.Add( self.m_panelTestStepContents, 1, wx.EXPAND |wx.ALL, 5 )


        self.SetSizer( bSizer1 )
        self.Layout()

        # Connect Events
        self.m_btnNewBefore.Bind( wx.EVT_LEFT_UP, self.onNewTestStepBefore )
        self.Bind( wx.EVT_MENU, self.onInsertLoginStep, id = self.m_menuItemNewLoginStepBefore.GetId() )
        self.Bind( wx.EVT_MENU, self.onInsertMenuStep, id = self.m_menuItemNewMenuStepBefore.GetId() )
        self.Bind( wx.EVT_MENU, self.onInsertInputStep, id = self.m_menuItemNewInputStepBefore.GetId() )
        self.Bind( wx.EVT_MENU, self.onInsertAuthorizeStep, id = self.m_menuItemNewAuthorizeStepBefore.GetId() )
        self.Bind( wx.EVT_MENU, self.onInsertSeeStep, id = self.m_menuItemNewSeeStepBefore.GetId() )
        self.Bind( wx.EVT_MENU, self.onInsertEnquiryStep, id = self.m_menuItemNewEnquiryStepBefore.GetId() )
        self.Bind( wx.EVT_MENU, self.onInsertValidateStep, id = self.m_menuItemNewValidateStepBefore.GetId() )
        self.m_btnUp.Bind( wx.EVT_BUTTON, self.onBtnMoveUp )
        self.m_btnDown.Bind( wx.EVT_BUTTON, self.onBtnMoveDown )
        self.m_choiceTestStepAction.Bind( wx.EVT_CHOICE, self.onActionChanged )
        self.m_choiceLoginUsingUserOfGroup.Bind( wx.EVT_CHOICE, self.onLoginUsingUserOfGroupChanged )
        self.m_txtTestStepTransaction.Bind( wx.EVT_TEXT, self.onTransactionChanged )
        self.m_btnDelete.Bind( wx.EVT_BUTTON, self.onBtnDelete )
        self.m_txtTransactionID.Bind( wx.EVT_TEXT, self.onTransactionIDChanged )
        self.m_editTestData.Bind( wx.stc.EVT_STC_CHANGE, self.onEditTestDataChanged )
        self.m_editValidationRules.Bind( wx.stc.EVT_STC_CHANGE, self.onValidationRulesChanged )
        self.m_choiceHowToHandleOverrides.Bind( wx.EVT_CHOICE, self.onHowToHandleOverridesChanged )
        self.m_choiceHowToHandleErrors.Bind( wx.EVT_CHOICE, self.onHowToHandleErrorsChanged )
        self.m_txtExpectErrorContaining.Bind( wx.EVT_TEXT, self.onExpectedErrorContainingTextChanged )
        self.m_choiceEnquiryStepType.Bind( wx.EVT_CHOICE, self.onEnquiryStepTypeChanged )
        self.m_txtEnquiryActionCommand.Bind( wx.EVT_TEXT, self.onEnquiryActionCommandChanged )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def onNewTestStepBefore(self, event):
        event.Skip()

    def onInsertLoginStep(self, event):
        event.Skip()

    def onInsertMenuStep(self, event):
        event.Skip()

    def onInsertInputStep(self, event):
        event.Skip()

    def onInsertAuthorizeStep(self, event):
        event.Skip()

    def onInsertSeeStep(self, event):
        event.Skip()

    def onInsertEnquiryStep(self, event):
        event.Skip()

    def onInsertValidateStep(self, event):
        event.Skip()

    def onBtnMoveUp(self, event):
        event.Skip()

    def onBtnMoveDown(self, event):
        event.Skip()

    def onActionChanged(self, event):
        event.Skip()

    def onLoginUsingUserOfGroupChanged(self, event):
        event.Skip()

    def onTransactionChanged(self, event):
        event.Skip()

    def onBtnDelete(self, event):
        event.Skip()

    def onTransactionIDChanged(self, event):
        event.Skip()

    def onEditTestDataChanged(self, event):
        event.Skip()

    def onValidationRulesChanged(self, event):
        event.Skip()

    def onHowToHandleOverridesChanged(self, event):
        event.Skip()

    def onHowToHandleErrorsChanged(self, event):
        event.Skip()

    def onExpectedErrorContainingTextChanged(self, event):
        event.Skip()

    def onEnquiryStepTypeChanged(self, event):
        event.Skip()

    def onEnquiryActionCommandChanged(self, event):
        event.Skip()

    def m_btnNewBeforeOnContextMenu(self, event):
        self.m_btnNewBefore.PopupMenu( self.m_menuNewTestStepBefore, event.GetPosition() )

    # PASTE UI TILL HERE

    def createTestDataEditCtrl(self):
        ctrl = TipStyledTextCtrl(self.m_panelTestStepContents)
        return ctrl

###########################################################################
class T24TestStepPanel (T24TestStepPanelBase):

    _testStep = None
    _testStepsContainer = None

    def __init__(self, parent, testStepContainer, testStep):
        T24TestStepPanelBase.__init__(self, parent)
        self._testStep = testStep
        self.setTestStepDetails()
        self.updateUI()

        # leave it last not to fire change events during initialization
        self._testStepsContainer = testStepContainer

    def __del__(self):
        pass

    def setIndex(self, idx):
        self.lblTestStepIndex.SetLabel('{}'.format(idx))

    def onActionChanged(self, event):
        if self._testStep and self._testStepsContainer:
            oldAction = self._testStep.GetStepType()
            newAction = self.m_choiceTestStepAction.GetStringSelection()
            oldSubSteps = self._testStep.subSteps()

            self._testStep.SetStepType(newAction)

            if (newAction == 'M' and oldAction != 'M') or (newAction != 'M' and oldAction == 'M'):
                # incompatible values for the transaction type / app version
                self._testStep.AppVersion = ''
                self.m_txtTestStepTransaction.SetValue('')

            self._testStep.applyChanges()
            self.updateUI()
            self.Layout()

            self._testStepsContainer.fireOnTestStepChangeEvent(self._testStep, oldSubSteps)

    def onTransactionChanged(self, event):
        if self._testStep and self._testStepsContainer:
            self._testStep.AppVersion = self.m_txtTestStepTransaction.GetValue()
            self._testStep.applyChanges()
            self._testStepsContainer.fireOnTestStepChangeEvent(self._testStep)

    def onTransactionIDChanged(self, event):
        if self._testStep and self._testStepsContainer:
            self._testStep.TransactionID = self.m_txtTransactionID.GetValue()
            self._testStep.applyChanges()
            self._testStepsContainer.fireOnTestStepChangeEvent(self._testStep)

    def onLoginUsingUserOfGroupChanged(self, event):
        if self._testStep and self._testStepsContainer:
            self._testStep.AppVersion = self.m_choiceLoginUsingUserOfGroup.GetStringSelection()
            self._testStep.applyChanges()
            self._testStepsContainer.fireOnTestStepChangeEvent(self._testStep)

    def onEditTestDataChanged(self, event):
        if self._testStep and self._testStepsContainer:
            if self.m_choiceTestStepAction.GetStringSelection() == 'E':
                self._testStep.EnquiryConstraints = self.getEnqConstraintsFromUI()
            else:
                self._testStep.TestData = self.getTestDataFromUI()
            self._testStep.applyTestDataOrEnqConstraintChanges()
            self._testStepsContainer.fireOnTestStepChangeEvent(self._testStep)

    def onValidationRulesChanged(self, event):
        if self._testStep and self._testStepsContainer:
            self._testStep.ValidationRules = self.getValidationRulesFromUI()
            self._testStep.applyValidationRulesChanges()
            self._testStepsContainer.fireOnTestStepChangeEvent(self._testStep)

    def onHowToHandleOverridesChanged(self, event):
        if self._testStep and self._testStepsContainer:
            self._testStep.HowToHandleOverrides = self.m_choiceHowToHandleOverrides.GetStringSelection()
            self._testStep.applyChanges()
            self._testStepsContainer.fireOnTestStepChangeEvent(self._testStep)

    def onHowToHandleErrorsChanged(self, event):
        if self._testStep and self._testStepsContainer:
            self._testStep.HowToHandleErrors = self.m_choiceHowToHandleErrors.GetStringSelection()
            self._testStep.applyChanges()
            self.updateUI()
            self._testStepsContainer.fireOnTestStepChangeEvent(self._testStep)

    def onExpectedErrorContainingTextChanged(self, event):
        if self._testStep and self._testStepsContainer:
            self._testStep.ExpectErrorContaining = self.m_txtExpectErrorContaining.GetValue()
            self._testStep.applyChanges()
            self._testStepsContainer.fireOnTestStepChangeEvent(self._testStep)

    def onEnquiryStepTypeChanged(self, event):
        if self._testStep and self._testStepsContainer:
            self._testStep.EnquiryAction = self.m_choiceEnquiryStepType.GetStringSelection()
            if self._testStep.EnquiryAction == u"Action":
                self._testStep.EnquiryAction = self.m_txtEnquiryActionCommand  # TODO maybe it's empty
                self.m_editValidationRules.set_enabled(False)
            else:
                self.m_editValidationRules.set_enabled(True)

            self._testStep.applyChanges()
            self.updateUI()
            self._testStepsContainer.fireOnTestStepChangeEvent(self._testStep)

    def onEnquiryActionCommandChanged(self, event):
        if self._testStep and self._testStepsContainer and self.m_choiceEnquiryStepType.GetStringSelection() == u"Action":
            self._testStep.EnquiryAction = self.m_txtEnquiryActionCommand.GetValue()
            self._testStep.applyChanges()
            self._testStepsContainer.fireOnTestStepChangeEvent(self._testStep)

    def setTestStepDetails(self):
        if self._testStep is None:
            return

        self.m_choiceTestStepAction.SetSelection(self.m_choiceTestStepAction.FindString(self._testStep.GetStepType()))

        if self._testStep.GetStepType() == 'Login':
            self.setLoginUsingUserOfGroupChoices()
            self.m_choiceLoginUsingUserOfGroup.SetStringSelection(self._testStep.AppVersion)
        else:
            self.m_txtTestStepTransaction.SetValue(self._testStep.AppVersion)

        self.m_txtTransactionID.SetValue(self._testStep.TransactionID)
        if self._testStep.HowToHandleErrors and len(self._testStep.HowToHandleErrors) > 0:
            self.m_choiceHowToHandleErrors.SetStringSelection(self._testStep.HowToHandleErrors)
        if self._testStep.ExpectErrorContaining and len(self._testStep.ExpectErrorContaining) > 0:
            self.m_txtExpectErrorContaining.SetValue(self._testStep.ExpectErrorContaining)
        if self._testStep.HowToHandleOverrides and len(self._testStep.HowToHandleOverrides) > 0:
            self.m_choiceHowToHandleOverrides.SetStringSelection(self._testStep.HowToHandleOverrides)

        if self._testStep.EnquiryAction and len(self._testStep.EnquiryAction) > 0:
            if self._testStep.EnquiryAction == u"Check Result":
                self.m_choiceEnquiryStepType.SetStringSelection(self._testStep.EnquiryAction)
            elif self._testStep.EnquiryAction == u"Read Data":
                self.m_choiceEnquiryStepType.SetStringSelection(self._testStep.EnquiryAction)
            else:
                self.m_choiceEnquiryStepType.SetStringSelection(u"Action")
                self.m_txtEnquiryActionCommand.SetValue(self._testStep.EnquiryAction)

    def updateUI(self):
        self.m_lblLoginUsingUserOfGroup.Hide()
        self.m_choiceLoginUsingUserOfGroup.Hide()
        self.m_txtTestStepTransaction.Show()

        if self._testStep is None:
            # hide all
            self.m_sizerTransactionID.ShowItems(False)
            self.m_sizerTestData.ShowItems(False)
            self.m_sizerTestStepUpDown.ShowItems(False)
            self.m_sizerTestStepContents.ShowItems(False)
            self.m_panelTestStepContents.Hide()
            self.m_btnNewBefore.SetToolTipString('Add new test step')
        elif self._testStep.GetStepType() == 'Login':
            self.m_lblLoginUsingUserOfGroup.Show()
            self.m_choiceLoginUsingUserOfGroup.Show()
            self.m_txtTestStepTransaction.Hide()
            self.m_sizerTransactionID.ShowItems(False)
            self.m_sizerTestData.ShowItems(False)
        elif self._testStep.GetStepType() == 'M':
            self.m_sizerTransactionID.ShowItems(False)
            self.m_sizerTestData.ShowItems(False)
        elif self._testStep.GetStepType() == 'I':
            self.m_sizerTransactionID.ShowItems(True)
            self.m_sizerTestData.ShowItems(True)
            self.m_sizerEnquiryType.ShowItems(False)
            self.m_sizerValidationHolder.ShowItems(False)
            self.m_sizerHandleErrors.ShowItems(True)
            self.m_sizerTestDataCtrlHolder.StaticBox.SetLabel('Test Data')
            self.setTestData(self._testStep.TestData)
        elif self._testStep.GetStepType() == 'A':
            self.m_sizerTransactionID.ShowItems(True)
            self.m_sizerTestData.ShowItems(False)
        elif self._testStep.GetStepType() == 'S':
            self.m_sizerTransactionID.ShowItems(True)
            self.m_sizerTestData.ShowItems(False)
            self.m_sizerValidationHolder.ShowItems(True)
            self.setValidationRules(self._testStep.ValidationRules)
        elif self._testStep.GetStepType() == 'V':
            self.m_sizerTransactionID.ShowItems(False)
            self.m_sizerTestData.ShowItems(True)
            self.m_sizerEnquiryType.ShowItems(False)
            self.m_sizerValidationHolder.ShowItems(False)
            self.m_sizerHandleErrors.ShowItems(True)
            self.m_sizerTestDataCtrlHolder.StaticBox.SetLabel('Test Data')
            self.setTestData(self._testStep.TestData)
        elif self._testStep.GetStepType() == 'E':
            self.m_sizerTransactionID.ShowItems(False)
            self.m_sizerTestData.ShowItems(True)
            self.m_sizerEnquiryType.ShowItems(True)
            self.m_sizerHandleOverrides.ShowItems(False)
            self.m_sizerValidationHolder.ShowItems(True)
            self.m_sizerHandleErrors.ShowItems(False)
            self.m_sizerTestDataCtrlHolder.StaticBox.SetLabel('Enquiry Constraints')
            self.setEnquiryConstraints(self._testStep.EnquiryConstraints)
            if self.m_choiceEnquiryStepType.IsShown() and self.m_choiceEnquiryStepType.GetStringSelection() != u"Action":
                self.setValidationRules(self._testStep.ValidationRules)

        #todo - rest of test cases. It would be good to add generic test step or sth like that
        else:
            self.m_sizerTransactionID.ShowItems(False)
            self.m_sizerTestData.ShowItems(False)

        if self.m_choiceHowToHandleErrors.IsShown() and self.m_choiceHowToHandleErrors.GetStringSelection() == u"Expect Error Containing":
            self.m_txtExpectErrorContaining.Show(True)
        else:
            self.m_txtExpectErrorContaining.Show(False)

        if self.m_choiceEnquiryStepType.IsShown() and self.m_choiceEnquiryStepType.GetStringSelection() == u"Action":
            self.m_txtEnquiryActionCommand.Show(True)
        else:
            self.m_txtEnquiryActionCommand.Show(False)

        if self.m_choiceEnquiryStepType.IsShown():
            self.updateValidationsHolderForEnquiry()

        #self.Update()
        self.m_panelTestStepContents.Layout()
        self.Layout()

    def updateValidationsHolderForEnquiry(self):
        if self.m_choiceEnquiryStepType.GetStringSelection() == u"Check Result":
            # self.m_sizerValidationHolder.ShowItems(True)
            self.m_sizerValidationHolder.StaticBox.SetLabel(u"Validation Rules for the First Row in Enquiry Result")
        elif self.m_choiceEnquiryStepType.GetStringSelection() == u"Read Data":
            # self.m_sizerValidationHolder.ShowItems(True)
            self.m_sizerValidationHolder.StaticBox.SetLabel(u"Values to Retrieve from First Row in Enquiry Result (column indexes)")
        else:
            self.m_sizerValidationHolder.StaticBox.SetLabel(u"")
            # self.m_sizerValidationHolder.ShowItems(False) # resizing is problematic

        # self.m_sizerValidationHolder.Layout()

    def setLoginUsingUserOfGroupChoices(self):
        self.m_choiceLoginUsingUserOfGroup.Clear()
        for userGroup in TipServerResources.getUserGroups():
            self.m_choiceLoginUsingUserOfGroup.Append(userGroup)

    def setTestData(self, testData):
        self.m_editTestData.setTestData(testData)

    def setEnquiryConstraints(self, enquiryConstraints):
        self.m_editTestData.setEnquiryConstraints(enquiryConstraints)

    def setValidationRules(self, validationRules):
        self.m_editValidationRules.setValidationRules(validationRules)

    def getTestDataFromUI(self):
        return self.m_editTestData.getTestDataFromUI()

    def getEnqConstraintsFromUI(self):
        return self.m_editTestData.getEnqConstraintsFromUI()

    def getValidationRulesFromUI(self):
        return self.m_editValidationRules.getValidationRulesFromUI()

    @staticmethod
    def Warn(parent, message, caption='Warning!'):
        dlg = wx.MessageDialog(parent, message, caption, wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()

    @staticmethod
    def YesNo(parent, question, caption='Yes or no?', icon=wx.ICON_QUESTION):
        dlg = wx.MessageDialog(parent, question, caption, wx.YES_NO | icon)
        result = dlg.ShowModal() == wx.ID_YES
        dlg.Destroy()
        return result

    @staticmethod
    def confirmTestStepDeletion(parent, testStepName):
        return T24TestStepPanel.YesNo(parent, "Do you really want to delete test step: '{}'?".format(testStepName), "Confirm Deletion", wx.ICON_WARNING)

    def onBtnDelete(self, event):
        if T24TestStepPanel.confirmTestStepDeletion(self, self._testStep.__str__()):
            parent = self.Parent
            container = self._testStepsContainer
            testStep = self._testStep
            self.Destroy()
            parent.Layout()
            container.fireOnTestStepDeleteEvent(testStep)
            # todo reindex the step

    def onNewTestStepBefore(self, event):
        # self._testStepsContainer.fireOnNewTestStepBeforeEvent(self._testStep)
        self.m_btnNewBeforeOnContextMenu(event)

    def onInsertLoginStep(self, event):
        self._testStepsContainer.fireOnNewTestStepBeforeEvent(self._testStep, 'Login')

    def onInsertMenuStep(self, event):
        self._testStepsContainer.fireOnNewTestStepBeforeEvent(self._testStep, 'M')

    def onInsertInputStep(self, event):
        self._testStepsContainer.fireOnNewTestStepBeforeEvent(self._testStep, 'I')

    def onInsertAuthorizeStep(self, event):
        self._testStepsContainer.fireOnNewTestStepBeforeEvent(self._testStep, 'A')

    def onInsertSeeStep(self, event):
        self._testStepsContainer.fireOnNewTestStepBeforeEvent(self._testStep, 'S')

    def onInsertEnquiryStep(self, event):
        self._testStepsContainer.fireOnNewTestStepBeforeEvent(self._testStep, 'E')

    def onInsertValidateStep(self, event):
        self._testStepsContainer.fireOnNewTestStepBeforeEvent(self._testStep, 'V')

    def onBtnMoveUp(self, event):
        self._testStepsContainer.fireOnTestStepMoveUpEvent(self._testStep)

    def onBtnMoveDown(self, event):
        self._testStepsContainer.fireOnTestStepMoveDownEvent(self._testStep)
