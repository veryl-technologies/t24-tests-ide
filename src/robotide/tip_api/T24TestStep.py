__author__ = 'Zhelev'

from robot.parsing.model import Step
from robotide.tip_api.tiplexer import RowUtils


# todo - need to build test steps inheritance
class T24TestStep(object):
    # consts
    keyword_L = 'T24 Login'
    keyword_M = 'Execute T24 Menu Command'
    keyword_I = 'Create Or Amend T24 Record'
    keyword_A = 'Authorize T24 Record'
    keyword_S = 'Check T24 Record Exists'
    keyword_E = 'Execute T24 Enquiry'
    keyword_V = 'Validate T24 Record'

    # members
    _stepDetails = None

    # properties
    _Action = ''   # the step type
    AppVersion = ''   # the T24 application and version
    TransactionID = ''   # the T24 record ID

    TestData = []
    EnquiryConstraints = []
    ValidationRules = []

    # I, V specific properties
    HowToHandleErrors = None
    ExpectErrorContaining = None
    HowToHandleOverrides = None

    EnquiryAction = None

    IsRealTestStep = False

    def __init__(self, stepPreActions, stepDetails):
        # stepPreActions are the keywords for initialization of variables etc that belong to the entire test step
        self._stepDetails = stepDetails
        self.IsRealTestStep = self.parseTestStep(stepDetails, stepPreActions)

    @staticmethod
    def isT24TestStep(stepDetails):
        return T24TestStep(None, stepDetails)._Action != ''

    def __str__(self):
        return self._Action

    def __repr__(self):
        return self.__str__()

    def parseTestStep(self, stepDetails, stepPreActions=None):
        self._testDataPreAction = None
        self._enquiryConstraintsPreAction = None
        self._validationRulesPreAction = None

        if stepDetails.keyword == self.keyword_L:
            self._Action = 'Login'
            self.setLoginArgs(stepDetails.args)
        elif stepDetails.keyword == self.keyword_M:
            self._Action = 'M'
            self.setMenuArgs(stepDetails.args)
        elif stepDetails.keyword == self.keyword_I:
            self._Action = 'I'
            self.setCreateOrAmendOrValidateArgs(stepDetails.args, stepPreActions)
            if self._testDataPreAction is None:
                self.SetStepType(self._Action)  # this will create new _testDataPreAction
        elif stepDetails.keyword == self.keyword_A:
            self._Action = 'A'
            self.setAuthorizeArgs(stepDetails.args)
        elif stepDetails.keyword == self.keyword_S:
            self._Action = 'S'
            if self._validationRulesPreAction is None:
                self.SetStepType(self._Action)
            self.setCheckRecordArgs(stepDetails.args, stepPreActions)
        elif stepDetails.keyword == self.keyword_E:
            self._Action = 'E'
            self.setEnquiryArgs(stepDetails.args, stepPreActions)
            if self._enquiryConstraintsPreAction is None:
                self.SetStepType(self._Action)  # this will create new _enquiryConstraintsPreAction
            if self._validationRulesPreAction is None:
                self.SetStepType(self._Action)
        elif stepDetails.keyword == self.keyword_V:
            self._Action = 'V'
            self.setCreateOrAmendOrValidateArgs(stepDetails.args, stepPreActions)
            if self._testDataPreAction is None:
                self.SetStepType(self._Action)  # this will create new _testDataPreAction
        else:
            # Other types goes here
            return False

        return True

    def GetStepType(self):
        return self._Action

    def SetStepType(self, action):
        self._Action = action

        if self._Action == 'I' or self._Action == 'V':
            self._enquiryConstraintsPreAction = None
            self._validationRulesPreAction = None
            if self._testDataPreAction is None:
                testDataVarName = '@{testDataFields}'
                self._testDataPreAction = Step('')
                self._testDataPreAction.keyword = 'Create List'
                self._testDataPreAction.assign = [testDataVarName + '=']
                self._testDataPreAction.args = []
                self._setArg(1, testDataVarName)

        elif self._Action == 'E':
            self._testDataPreAction = None
            if self._enquiryConstraintsPreAction is None:
                enqVarName = '@{enquiryConstraints}'
                self._enquiryConstraintsPreAction = Step('')
                self._enquiryConstraintsPreAction.keyword = 'Create List'
                self._enquiryConstraintsPreAction.assign = [enqVarName + '=']
                self._enquiryConstraintsPreAction.args = []
                self._setArg(1, enqVarName)

            if self._validationRulesPreAction is None:
                varName = '@{validationRules}'
                self._validationRulesPreAction = Step('')
                self._validationRulesPreAction.keyword = 'Create List'
                self._validationRulesPreAction.assign = [varName + '=']
                self._validationRulesPreAction.args = []
                self._setArg(3, varName)

        elif self._Action == 'S':
            self._testDataPreAction = None
            self._enquiryConstraintsPreAction = None

            if self._validationRulesPreAction is None:
                varName = '@{validationRules}'
                self._validationRulesPreAction = Step('')
                self._validationRulesPreAction.keyword = 'Create List'
                self._validationRulesPreAction.assign = [varName + '=']
                self._validationRulesPreAction.args = []
                self._setArg(2, varName)

    def setLoginArgs(self, args):
        # Expected Format
        # Execute T24 Login {user_group}
        #
        # the {user_group} can be INPUTTER, AUTHORISER, AUTHORISER.2...
        #

        if not args:
            return

        if args.__len__() >= 1:
            self.AppVersion = args[0]

    def setMenuArgs(self, args):
        # Expected Format
        # Execute T24 Menu Command {menu_parent_1 \ menu_parent_2 \ ... \ menu_item}
        #
        if not args:
            return

        if args.__len__() >= 1:
            self.AppVersion = args[0]

    def setCreateOrAmendOrValidateArgs(self, args, stepPreActions):
        # Expected Format
        # Create Or Amend T24 Record {application,version} {recordFieldValues} {overridesHandling} {errorsHandling}
        # or
        # Validate T24 Record {application,version} {recordFieldValues} {overridesHandling} {errorsHandling}
        #
        #
        # if {errorsHandling} contains ':' we have 2 parts - contains text for ex: 'Expect Error Containing:Unknown'
        #
        if not args:
            return

        if args.__len__() >= 1:
            self.AppVersion = args[0]

        if args.__len__() >= 2:
            self.setRecordFieldValues(args[1], stepPreActions)

        if args.__len__() >= 3:
            self.HowToHandleOverrides = args[2]

        if args.__len__() >= 4:
            self._setHowToHandleErrors(args[3])

    def setAuthorizeArgs(self, args):
        # Expected Format
        # Authorize T24 Record {application,version} {recordID}
        if not args:
            return

        if args.__len__() >= 1:
            self.AppVersion = args[0]

        if args.__len__() >= 2:
            self.TransactionID = args[1]

    def setCheckRecordArgs(self, args, stepPreActions):
        # Expected Format
        # Check T24 Record Exists {application,version} {recordID} {validation rules}
        if not args:
            return

        if args.__len__() >= 1:
            self.AppVersion = args[0]

        if args.__len__() >= 2:
            self.TransactionID = args[1]

        if args.__len__() >= 3:
            self.setValidationRules(args[2], stepPreActions)

    def setEnquiryArgs(self, args, stepPreActions):
        # Expected Format
        # Execute T24 Enquiry {Enquiry Name} {constraints - post & pre} {action} {validation rules}
        #
        # {action} can be real enquiry action or 'Check Values'
        #
        #
        if not args:
            return

        if args.__len__() >= 1:
            self.AppVersion = args[0]

        if args.__len__() >= 2:
            self.setEnquiryConstraints(args[1], stepPreActions)

        if args.__len__() >= 3:
            self.EnquiryAction = args[2]

        if args.__len__() >= 4:
            self.setValidationRules(args[3], stepPreActions)

    def setRecordFieldValues(self, arg, stepPreActions):
        testDataList = self.findPreAction(stepPreActions, "Create List", arg)
        if testDataList is None:
            return

        self._testDataPreAction = testDataList
        self.TestData = self._getNameValueList(testDataList.args)

    def setEnquiryConstraints(self, arg, stepPreActions):
        enqConstraintsList = self.findPreAction(stepPreActions, "Create List", arg)
        if enqConstraintsList is None:
            return

        self._enquiryConstraintsPreAction = enqConstraintsList
        self.EnquiryConstraints = self._getEnqConstraintList(enqConstraintsList.args)

    def setValidationRules(self, arg, stepPreActions):
        validationRulesList = self.findPreAction(stepPreActions, "Create List", arg)
        if validationRulesList is None:
            return

        self._validationRulesPreAction = validationRulesList
        self.ValidationRules = self._getValidationRulesList(validationRulesList.args)

    def subSteps(self):
        ls = []
        for pa in self._getPreActions():
            ls.append(pa)
        if self._stepDetails:
            ls.append(self._stepDetails)

        return ls

    def _getPreActions(self):
        if self._Action == 'I' or self._Action == 'V':
            return [self._testDataPreAction]
        elif self._Action == 'E':
            return [self._enquiryConstraintsPreAction, self._validationRulesPreAction]
        elif self._Action == 'S':
            return [self._validationRulesPreAction]

        return []

    # create default step type
    @staticmethod
    def createNew(action):
        stepDetails = Step('')
        stepDetails.keyword = T24TestStep.getKeywordFromAction(action)
        stepDetails.args = []

        return T24TestStep([], stepDetails)

    @staticmethod
    def getKeywordFromAction(action):
        if action == 'Login':
            return 'T24 Login'
        elif action == 'M':
            return 'Execute T24 Menu Command'
        elif action == 'I':
            return 'Create Or Amend T24 Record'
        elif action == 'A':
            return 'Authorize T24 Record'
        elif action == 'S':
            return 'Check T24 Record Exists'
        elif action == 'E':
            return 'Execute T24 Enquiry'
        elif action == 'V':
            return 'Validate T24 Record'
        else:  # todo - we have to have generic test step as a new test step type
            return 'T24 Login'

    def _getNameValueList(self, list):
        if list is None:
            return None

        res = []

        for item in list:
            eqIdx = item.find('=')
            if eqIdx < 0:
                return None  # todo - maybe report an error?

            name = item[:eqIdx].strip()
            value = item[eqIdx + 1:].strip()
            res.append((name, value))

        return res;

    def _getEnqConstraintList(self, listConstraints):
        # Expected format
        #     Short Name:EQ:=Baba    MNEMONIC:LK:=...01...
        if listConstraints is None:
            return None

        res = []
        for item in listConstraints:
            name, oper, value = RowUtils.ParseEnquiryRow(item)
            res.append((name, oper, value))

        return res

    def _getValidationRulesList(self, list):
        # so far both are with same syntax
        return self._getEnqConstraintList(list)

    def applyTestDataOrEnqConstraintChanges(self):
        if self._Action == 'I' or self._Action == 'V':
            self._testDataPreAction.args = []
            for td in self.TestData:
                self._testDataPreAction.args.append(u'{}={}'.format(td[0], td[1]))

        elif self._Action == 'E':
            self._enquiryConstraintsPreAction.args = []
            for enc in self.EnquiryConstraints:
                self._enquiryConstraintsPreAction.args.append(u'{} {} {}'.format(enc[0], enc[1], enc[2]))

    def applyValidationRulesChanges(self):
        if self._Action == 'E' or self._Action == 'S':
            self._validationRulesPreAction.args = []
            for vr in self.ValidationRules:
                self._validationRulesPreAction.args.append(u'{} {} {}'.format(vr[0], vr[1], vr[2]))

    def findPreAction(self, stepPreActions, keyword, assign):
        if stepPreActions is None:
            return None

        for pa in stepPreActions:
            if pa.keyword == keyword and pa.assign is not None and pa.assign[0] == "{}=".format(assign):
                return pa

        return None

    def applyChanges(self):
        self._setArg(0, self.AppVersion)

        if self._Action == 'Login':
            self._stepDetails.keyword = self.keyword_L
        elif self._Action == 'M':
            self._stepDetails.keyword = self.keyword_M
        elif self._Action == 'I':
            self._stepDetails.keyword = self.keyword_I
            self._setArg(2, self.HowToHandleOverrides)
            self._setArg(3, self._getHowToHandleErrors())
        elif self._Action == 'A':
            self._stepDetails.keyword = self.keyword_A
            self._setArg(1, self.TransactionID)
        elif self._Action == 'S':
            self._stepDetails.keyword = self.keyword_S
            self._setArg(1, self.TransactionID)
        elif self._Action == 'V':
            self._stepDetails.keyword = self.keyword_V
            self._setArg(2, self.HowToHandleOverrides)
            self._setArg(3, self._getHowToHandleErrors())
        elif self._Action == 'E':
            self._stepDetails.keyword = self.keyword_E
            self._setArg(2, self.EnquiryAction)

    def _setArg(self, index, value):
        while self._stepDetails.args.__len__() <= index:
            self._stepDetails.args.append('')

        if value:
            self._stepDetails.args[index] = value

    def _setHowToHandleErrors(self, arg):
        pos = arg.find(':')
        if pos < 0:
            self.HowToHandleErrors = arg
        else:
            self.HowToHandleErrors = arg[:pos].strip()
            self.ExpectErrorContaining = arg[(pos + 1):].strip()

    def _getHowToHandleErrors(self):
        result = ''
        if self.HowToHandleErrors:
            result = result + self.HowToHandleErrors
        if self.ExpectErrorContaining and len(self.ExpectErrorContaining) > 0:
            result = result + ':' + self.ExpectErrorContaining
        return result
