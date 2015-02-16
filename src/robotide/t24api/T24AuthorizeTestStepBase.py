# -*- coding: utf-8 -*- 

###########################################################################
## Python code generated with wxFormBuilder (version Jun  5 2014)
## http://www.wxformbuilder.org/
##
## PLEASE DO "NOT" EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class T24AuthorizeTestStepBase
###########################################################################

class T24AuthorizeTestStepBase ( wx.Panel ):
	
	def __init__( self, parent ):
		wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 612,273 ), style = wx.TAB_TRAVERSAL )
		
		bSizer8 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText2 = wx.StaticText( self, wx.ID_ANY, u"@ID", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText2.Wrap( -1 )
		bSizer8.Add( self.m_staticText2, 0, wx.ALL, 8 )
		
		self.m_txtTransactionID = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 320,-1 ), 0 )
		bSizer8.Add( self.m_txtTransactionID, 0, wx.ALL, 5 )
		
		
		self.SetSizer( bSizer8 )
		self.Layout()
		
		# Connect Events
		self.m_txtTransactionID.Bind( wx.EVT_TEXT, self.onTransactionIDChanged )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def onTransactionIDChanged( self, event ):
		event.Skip()
	

