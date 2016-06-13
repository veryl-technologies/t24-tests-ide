#  Copyright 2012 Nokia Siemens Networks Oyj
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

import re

from pygments.lexer import Lexer
from pygments.token import Token

FIELDNAME = Token.FieldName
SEPARATOR = Token.Punctuation
OPERATOR = Token.Operator
VALUECONST = Token.ConstantValue
VALUEVARIABLE = Token.Variable
VARIABLENAME = Token.VariableName
ERROR = Token.Error
FORMULA = Token.Formula

#
# Syntax:
# {FIELD.NAME} {OPERATOR} {VALUE}
#       * {VALUE} can be constant, variable or expression
#
# Input Values Example:    (only operator ':=' is applicable for field assignment)
# MNEMONIC:=$NEXT_MNEMONIC
# Short Name:=John Smith
# NAME:1:1:=John Bonn Smith
# Sector:=${Calculated Sector}
#
#
# Enquiry Constraint / Validation Rules Example:
# Name.1 matches ...Bonn...
# SHORT.NAME:EQ:=John Smith
# Sector ends with 99
#


class TipLexer(Lexer):

    _isInputValuesSyntax = False

    def __init__(self):
        Lexer.__init__(self, tabsize=2, encoding='UTF-8')

    def setInputValuesSyntax(self, isInputValuesSyntax):
        self._isInputValuesSyntax = isInputValuesSyntax

    def get_tokens_unprocessed(self, text):
        row_tokenizer = RowTokenizer()
        row_tokenizer._isInputValuesSyntax = self._isInputValuesSyntax
        index = 0
        for row in text.splitlines():
            for localIndex, token, value in row_tokenizer.tokenize(row):
                yield index, token, value
                index += len(value)
            index += 1  #Cr

class RowTokenizer(object):

    _isInputValuesSyntax = False

    _input_field_assignment_operator = ':='

    _operators = [ \
                     ':EQ:=', 'EQUALS', \
                     ':LK:=', 'MATCHES', \
                     ':UL:=', 'NOT MATCHES', \
                     ':NE:=', 'NOT EQUAL TO', \
                     ':GT:=', 'GREATER THAN', \
                     ':GE:=', 'GREATER THAN OR EQUALS', \
                     ':LT:=', 'LESS THAN', \
                     ':LE:=', 'LESS THAN OR EQUALS', \
                     ':RG:=', 'BETWEEN', \
                     ':NR:=', 'NOT BETWEEN', \
                     ':CT:=', 'CONTAINS', \
                     ':NC:=', 'NOT CONTAINING', \
                     ':BW:=', 'BEGINS WITH', \
                     ':EW:=', 'ENDS WITH', \
                     ':DNBW:=', 'DOES NOT BEGIN WITH', \
                     ':DNEW:=', 'DOES NOT END WITH', \
                     ':SAID:=', 'SOUNDS LIKE', \
                     '>>' \
                     ]

    def __init__(self):
        pass

    def tokenize(self, row):
        hasFieldName = False
        hasOper = False
        isOperAssignToVariable = False

        hasFormulaStarted = False
        hasConstantStarted = False
        hasVariableStarted = False


        for index, value in self._next_word(row):
            if self._isOperator(value):
                if not hasFieldName:
                    yield index, ERROR, unicode(value)  # have operator prior field name
                elif hasOper:
                    yield index, ERROR, unicode(value)  # second operator
                else:
                    yield index, OPERATOR, unicode(value)
                    hasOper = True
                    isOperAssignToVariable = (value == ">>")
            elif value.startswith(' ') or value.startswith('\t'):
                yield index, SEPARATOR, unicode(value)  # separator
            elif hasOper is False:
                yield index, FIELDNAME, unicode(value)
                hasFieldName = True
            else:   # we already have field name and operator, now handle the right-side
                if not hasFormulaStarted and not hasVariableStarted and not hasConstantStarted:
                    if unicode(value).startswith("#"):
                        hasFormulaStarted = True
                        yield index, FORMULA, unicode(value)
                    elif unicode(value).startswith("$"):  # TODO maybe also @%
                        hasVariableStarted = True
                        yield index, VALUEVARIABLE, unicode(value)
                    else:
                        hasConstantStarted = True
                        yield index, VALUECONST if not isOperAssignToVariable else VARIABLENAME, unicode(value)
                else:
                    # TODO we don't handle currently a variable within a formula
                    yield index, \
                          FORMULA if hasFormulaStarted else (VALUEVARIABLE if hasVariableStarted else VALUECONST),\
                          unicode(value)

    def _next_word(self, row):
        buff = []
        for index, value in self._next(row):
            buff.append((index, value))

            while not self._canBeMultiWordOperator(buff) and buff.__len__() > 0:
                yield buff[0]
                buff = buff[1:]

            if buff.__len__() > 0:
                operIndex, oper, residual = self._getOperator(buff)
                if oper:
                    yield operIndex, oper
                    buff = residual

        # return all buffered
        for index, value in buff:
            yield index, value

    def _next(self, row):
        word = ''
        sepa = ''
        startIdx=0
        for i, c in enumerate(row):
            if c == '=' and len(word) > 0 and word.endswith(':'):
                if len(word) >= 4 and self._isOperator(word[-4:]+'='):
                    if len(word) > 4:
                        yield startIdx, word[:-4]
                    yield (startIdx + len(word) - 4), (word[-4:] + '=')
                else:
                    if len(word) > 1:
                        yield startIdx, word[:-1]
                    yield (startIdx + len(word) - 1), (word[-1:] + '=')
                word = ''
                startIdx = i
                continue

            if c == ' ' or c == '\t':
                if len(word) > 0:
                    yield startIdx, word
                    word = ''
                if len(sepa) == 0:
                    startIdx = i
                sepa += c
            else:
                if len(sepa) > 0:
                    yield  startIdx, sepa
                    sepa = ''
                if len(word) == 0:
                    startIdx = i
                word += c
        if len(word) > 0:
            yield startIdx, word
        elif len(sepa) > 0:
            yield startIdx, sepa

    def _isOperator(self, text):
        if self._isInputValuesSyntax:
            return text == self._input_field_assignment_operator

        return text.upper() in self._operators

    _multiWordOperators = None

    def _getMultiWordOperators(self):
        if self._isInputValuesSyntax:
            return {}

        if self._multiWordOperators is None:
            self._multiWordOperators= {}
            for op in self._operators:
                arr = op.split(' ')
                if arr.__len__() > 1:
                    self._pushMultiWordOperator(self._multiWordOperators, arr)

        return self._multiWordOperators

    def _pushMultiWordOperator(self, dictOperators, arr):
        if dictOperators.get(arr[0]) is None:
            dictOperators[arr[0]] = {}

        if arr.__len__() == 1: # last one
            return

        # add space and move forward
        if dictOperators[arr[0]].get(' ') is None:
            dictOperators[arr[0]][' '] = {}

        self._pushMultiWordOperator(dictOperators[arr[0]][' '], arr[1:])

    def _canBeMultiWordOperator(self, buff):
        dictMVOperators = self._getMultiWordOperators()

        for index, value in buff:
            val = value.upper()
            if dictMVOperators.get(val) is None:
                return False
            dictMVOperators = dictMVOperators[val]

        return True

    def _getOperator(self, buff):
        dictMVOperators = self._getMultiWordOperators()

        operIndex = -1
        oper = ''
        hasOper = False
        residual = []

        for index, value in buff:
            if hasOper:
                residual.append((index, value))
                continue

            if operIndex == -1:
                operIndex = index
            oper += value

            valueU = value.upper()

            if dictMVOperators[valueU] is None:
                break
            dictMVOperators = dictMVOperators[valueU]
            if len(dictMVOperators) == 0: # found!
                hasOper = True

        if hasOper:
            return operIndex, oper, residual
        else:
            return -1, None, buff

class RowUtils(object):

    def __init__(self):
        pass

    @staticmethod
    def ParseTestDataRow(row):
        name, oper, value = RowUtils._parseRow(row, True)
        return name, value

    @staticmethod
    def ParseEnquiryRow(row):
        return RowUtils._parseRow(row, False)

    @staticmethod
    def _parseRow(row, isInputValuesSyntax):
        res_name = ''
        res_oper = ''
        res_value = ''
        hasOper = False

        tokenizer = RowTokenizer()
        tokenizer._isInputValuesSyntax = isInputValuesSyntax

        for index, token, value in tokenizer.tokenize(row):
            if token == OPERATOR:
                hasOper = True
                res_oper = value
            elif hasOper is False:
                res_name += value
            else:
                res_value += value

        return res_name.strip(), res_oper, res_value.strip()
