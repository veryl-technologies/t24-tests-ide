from robotide.context.platform import IS_WINDOWS, IS_MAC

import wx
from wx import stc

import tiplexer
from tiplexer import TipLexer
from tiplexer import RowUtils

class TipStyledTextCtrl(stc.StyledTextCtrl):
    _isInputValues = False

    def __init__(self, parent):
        stc.StyledTextCtrl.__init__(self, parent, wx.ID_ANY)
        # Sample content
        # MNEMONIC:=SUPER001
        # SHORT.NAME:=Super Duper
        # Name.1:=Bab Jaga
        # City|ADDRESS:1:1=London

        font = self._create_font()
        face = font.GetFaceName()
        size = font.GetPointSize()
        self.SetFont(font)
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,"face:%s,size:%d" % (face, size))
        self.StyleSetSpec(2, "fore:#b22222")  # firebrick
        self.SetScrollWidth(100)

        #ctrl.SetLexer(stc.STC_LEX_PASCAL)
        #ctrl.StyleSetSpec(stc.STC_P_OPERATOR, "fore:#0000ff" )

        self.SetLexer(stc.STC_LEX_CONTAINER)
        self.Bind(stc.EVT_STC_STYLENEEDED, self.OnStyle)
        self.Bind(stc.EVT_STC_CHARADDED, self.OnCharAdded)  # we can use also stc.EVT_STC_MODIFIED
        self.stylizer = TypStylizer(self, font)

        # We don't need all wx.stc.EVT_STC_CHANGE events -> just those notify for actual changes in the text
        self.SetModEventMask(wx.stc.STC_MOD_INSERTTEXT |
                    wx.stc.STC_MOD_DELETETEXT |
                    wx.stc.STC_PERFORMED_UNDO |
                    wx.stc.STC_PERFORMED_REDO)

        self._register_shortcuts()

    def _create_font(self):
        font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FIXED_FONT)
        if not font.IsFixedWidth():
            # fixed width fonts are typically a little bigger than their variable width
            # peers so subtract one from the point size.
            font = wx.Font(font.GetPointSize()-1, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        return font

    def setInputValuesSyntax(self, isInputValuesMode):
        self._isInputValues = isInputValuesMode
        self.stylizer.setInputValuesSyntax(isInputValuesMode)

    def setInputValues(self, inputValues):
        self.setInputValuesSyntax(True)
        self.set_text('')

        if inputValues is None:
            return

        text = ''
        for attr in inputValues:
            text += '{} := {}\r\n'.format(attr[0], attr[1])

        self.set_text(text)

    def setEnquiryConstraints(self, enquiryConstraints):
        self.setInputValuesSyntax(False)
        self.set_text('')

        if enquiryConstraints is None:
            return

        text = ''
        for attr in enquiryConstraints:
            if attr[1] or attr[1].strip():
                text += '{} {} {}\r\n'.format(attr[0], attr[1], attr[2])
            else:
                text += attr[0] + '\r\n'

        self.set_text(text)

    def setValidationRules(self, validationRules):
        self.set_text('')

        if validationRules is None:
            return

        text = ''
        for attr in validationRules:
            if attr[1] or attr[1].strip():
                text += '{} {} {}\r\n'.format(attr[0], attr[1], attr[2])
            else:
                text += attr[0] + '\r\n'

        self.set_text(text)

    def getTestDataFromUI(self):
        res = []

        for line in self.GetText().split('\n'):
            line = line.strip()
            if line:
                nameValue = RowUtils.ParseTestDataRow(line)
                if nameValue:
                    res.append(nameValue)

        return res

    def getEnqConstraintsFromUI(self):
        res = []

        for line in self.GetText().split('\n'):
            line = line.strip()
            if line:
                nameOperValue = RowUtils.ParseEnquiryRow(line)
                if nameOperValue:
                    res.append(nameOperValue)

        return res

    def getValidationRulesFromUI(self):
        # Currently enquiry constraints syntax must be OK for validation rules also
        res = []

        for line in self.GetText().split('\n'):
            line = line.strip()
            if line:
                nameOperValue = RowUtils.ParseEnquiryRow(line)
                if nameOperValue:
                    res.append(nameOperValue)

        return res

    def set_enabled(self, enabled):
        if enabled:
            self.StyleResetDefault()
            self.SetReadOnly(False)
        else:
            self.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, (240, 240, 240))
            self.ClearAll()
            self.SetReadOnly(True)

    def set_text(self, text):
        self.set_enabled(True)
        self.SetText(text)
        self.stylizer.stylize()
        self.EmptyUndoBuffer()

    def append_text(self, text):
        self.AppendText(text)

    def OnStyle(self, event):
        self.stylizer.stylize()

        #start = self.GetEndStyled()    # this is the first character that needs styling
        #end = event.GetPosition()          # this is the last character that needs styling
        #self.StartStyling(start, 31)   # in this example, only style the text style bits
        #for pos in range(start, end):  # in this example, simply loop over it..
        #    self.SetStyling(1, self.tokens[tiplexer.OPERATOR])
        #self.GetText().split lines....

    def OnCharAdded(self, event):
        self._try_show_autocomplete()

    def _handle_delete(self):
        if self.GetSelectionStart() == self.GetSelectionEnd():
            self.CharRight()
            self.DeleteBack()
        else:
            self.DeleteBack()

    def _try_show_autocomplete(self):
        line = self.GetLine(self.GetCurrentLine()).rstrip('\n')  # TODO instead get the text until the caret pos

        # demand a space before showing the autocomplete (just after the first token)
        if not line.endswith(" "):
            return

        # check if there is a single valid token (which should be a field name or an enquiry row number)
        line = line.strip()
        if not line or ' ' in line:
            return

        # depending on the context, show the corresponding operators
        operators = [":="] if self._isInputValues else [
             '>>',
             ':EQ:=',
             ':LK:=',
             ':UL:=',
             ':NE:=',
             ':GT:=',
             ':GE:=',
             ':LT:=',
             ':LE:=',
             ':CT:=',
             ':NC:=',
             ':BW:=',
             ':EW:=',
         ]

        self.AutoCompSetSeparator(ord(','))
        self.AutoCompShow(0, " ,".join(operators))

    def _register_shortcuts(self):
        accels = []

        accels.append(self._createAccelerator(wx.ACCEL_CTRL, ord('X'),(lambda e: self.Cut())))
        accels.append(self._createAccelerator(wx.ACCEL_CTRL, ord('C'),(lambda e: self.Copy())))

        if IS_MAC: # Mac needs this key binding
            accels.append(self._createAccelerator(wx.ACCEL_CTRL, ord('A'),(lambda e: self.SelectAll())))

        if IS_WINDOWS or IS_MAC: # Linux does not need this key binding
            accels.append(self._createAccelerator(wx.ACCEL_CTRL, ord('V'),(lambda e: self.Paste())))

        accels.append(self._createAccelerator(wx.ACCEL_CTRL, ord('Z'),(lambda e: self.Undo())))
        accels.append(self._createAccelerator(wx.ACCEL_CTRL, ord('Y'),(lambda e: self.Redo())))
        accels.append(self._createAccelerator(wx.ACCEL_NORMAL, wx.WXK_DELETE, (lambda e: self._handle_delete())))
        accels.append(self._createAccelerator(wx.ACCEL_CTRL, ord(' '), (lambda e: self._try_show_autocomplete())))
        #accels.append(self._createAccelerator(wx.ACCEL_CTRL, ord('G'),(lambda e: self.FindText())))
        self.SetAcceleratorTable(wx.AcceleratorTable(accels))

    def _createAccelerator(self, modifierKey, key, func):
        cutId = wx.NewId()
        self.Bind(wx.EVT_MENU, func, id=cutId)
        return (modifierKey, key, cutId)

class TypStylizer(object):
    def __init__(self, editor, font):
        self.editor = editor
        self.lexer = TipLexer()
        self.font = font
        self._set_styles()

    def setInputValuesSyntax(self, isInputValuesMode):
        self.lexer.setInputValuesSyntax(isInputValuesMode)

    def _set_styles(self):
        # see colors http://xoomer.virgilio.it/infinity77/wxPython/Widgets/wx.ColourDatabase.html
        styles = {
            tiplexer.FIELDNAME: {
                'fore': 'firebrick'
            },
            tiplexer.OPERATOR: {
                'fore': 'blue',
                'bold': 'true'
            },
            tiplexer.VALUECONST: {
                'fore': 'MEDIUM SEA GREEN'
            },
            tiplexer.VALUEVARIABLE: {
                'fore': 'purple'
            },
            tiplexer.VARIABLENAME: {
                'fore': 'purple',
                'bold': 'true'
            },
            tiplexer.ERROR: {
                'fore': 'red',
                'bold': 'true'
            },
            tiplexer.SEPARATOR: {
                'fore': 'black'
            },
            tiplexer.FORMULA: {
                'fore': 'Dark Slate Blue'
            },
        }
        self.tokens = {}
        for index, token in enumerate(styles):
            self.tokens[token] = index
            self.editor.StyleSetSpec(index, self._get_style_string(**styles[token]))

    def _get_word_and_length(self, current_position):
        word = self.editor.GetTextRange(current_position, self.editor.WordEndPosition(current_position, False))
        return word, len(word)

    def _get_style_string(self, back='#FFFFFF', face='Courier', fore='#000000', bold='', underline=''):
        settings = locals()
        settings.update(size=self.font.GetPointSize())
        return ','.join('%s:%s' % (name, value) for name, value in settings.items() if value)

    def stylize(self):
        if not self.lexer:
            return

        self.editor.ConvertEOLs(2)
        shift = 0
        for position, token, value in self.lexer.get_tokens_unprocessed(self.editor.GetText()):
            self.editor.StartStyling(position+shift, 31)
            self.editor.SetStyling(len(value.encode('utf-8')), self.tokens[token])
            shift += len(value.encode('utf-8'))-len(value)
