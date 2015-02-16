__author__ = 'Zhelev'

from T24InputTestStepPanelBase import T24InputTestStepPanelBase
import wx

class T24InputTestStep(T24InputTestStepPanelBase):
    
    def __init__(self, parent):
        T24InputTestStepPanelBase.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)

    def __del__( self ):
        pass
