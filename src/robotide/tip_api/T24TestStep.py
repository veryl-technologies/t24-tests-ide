__author__ = 'Zhelev'

from robot.parsing.model import Step
from robot.parsing.comments import Comment
from tiplexer import RowUtils


# todo - need to build test steps inheritance
class T24TestStep(object):
    # consts
    keyword_L = 'T24 Login'
    keyword_M = 'Execute T24 Menu Command'
    keyword_I = 'Create Or Amend T24 Record'
    keyword_A = 'Authorize T24 Record'
    keyword_S = 'Check T24 Record'
    keyword_E = 'Execute T24 Enquiry'
    keyword_V = 'Validate T24 Record'
    keyword_Manual_Step = 'Manual Step'
    keyword_Manual_Pause = 'Pause Step'

    # members
    _stepDetails = None

    # properties
    _Action = ''   # the step type
    AppVersion = ''   # the main command (usually T24 application and version)
    Description = ''    # the description of the test step
    TransactionID = ''   # the T24 record ID

    InputValues = []  # input values
    EnquiryConstraints = []
    ValidationRules = []  # validations and assignments

    # I, V specific properties
    HowToHandleErrors = None
    ExpectErrorContaining = None
    HowToHandleOverrides = None

    EnquiryAction = None

    ManualActionPrompt = ''

    CanDisplayTestStepInDesigner = False

    def __init__(self, stepPreActions, stepDetails):
        # stepPreActions are the keywords for initialization of variables etc that belong to the entire test step
        self._stepDetails = stepDetails
        self.CanDisplayTestStepInDesigner = self.parseTestStep(stepDetails, stepPreActions)

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
        if stepDetails.comment and len(stepDetails.comment.as_list()) > 0:
            desc = stepDetails.comment.as_list()[0]
            if desc.startswith("#"):
                desc = desc[1:]
            self.Description = desc.strip()

        if stepDetails.keyword == self.keyword_L:
            self._Action = 'Login'
            self.setLoginArgs(stepDetails.args)
        elif stepDetails.keyword == self.keyword_M:
            self._Action = 'Menu'
            self.setMenuArgs(stepDetails.args)
        elif stepDetails.keyword == self.keyword_I:
            self._Action = 'Input'
            self.setCreateOrAmendOrValidateArgs(stepDetails.args, stepPreActions)
            if self._testDataPreAction is None:
                self.SetStepType(self._Action)  # this will create new _testDataPreAction
        elif stepDetails.keyword == self.keyword_A:
            self._Action = 'Authorize'
            self.setAuthorizeArgs(stepDetails.args)
        elif stepDetails.keyword == self.keyword_S:
            self._Action = 'See'
            if self._validationRulesPreAction is None:
                self.SetStepType(self._Action)
            self.setCheckRecordArgs(stepDetails.args, stepPreActions)
        elif stepDetails.keyword == self.keyword_E:
            self._Action = 'Enquiry'
            self.setEnquiryArgs(stepDetails.args, stepPreActions)
            if self._enquiryConstraintsPreAction is None:
                self.SetStepType(self._Action)  # this will create new _enquiryConstraintsPreAction
            if self._validationRulesPreAction is None:
                self.SetStepType(self._Action)
        elif stepDetails.keyword == self.keyword_V:
            self._Action = 'Validate'
            self.setCreateOrAmendOrValidateArgs(stepDetails.args, stepPreActions)
            if self._testDataPreAction is None:
                self.SetStepType(self._Action)  # this will create new _testDataPreAction
        elif stepDetails.keyword == self.keyword_Manual_Step:
            self._Action = self.keyword_Manual_Step
            self.setManualAction(stepDetails.args)
        elif stepDetails.keyword == self.keyword_Manual_Pause:
            self._Action = self.keyword_Manual_Pause
            self.setManualAction(stepDetails.args)
        else:
            # Other types goes here
            return False

        return True

    def GetStepType(self):
        return self._Action

    def SetStepType(self, action):
        self._Action = action

        if self._Action == 'Input' or self._Action == 'Validate':
            self._enquiryConstraintsPreAction = None
            self._validationRulesPreAction = None
            if self._testDataPreAction is None:
                testDataVarName = '@{testDataFields}'
                self._testDataPreAction = Step('')
                self._testDataPreAction.keyword = 'Create List'
                self._testDataPreAction.assign = [testDataVarName + '=']
                self._testDataPreAction.args = []
                self._setArg(2, testDataVarName.replace("@", "$"))

        elif self._Action == 'Enquiry':
            self._testDataPreAction = None
            if self._enquiryConstraintsPreAction is None:
                enqVarName = '@{enquiryConstraints}'
                self._enquiryConstraintsPreAction = Step('')
                self._enquiryConstraintsPreAction.keyword = 'Create List'
                self._enquiryConstraintsPreAction.assign = [enqVarName + '=']
                self._enquiryConstraintsPreAction.args = []
                self._setArg(1, enqVarName.replace("@", "$"))

            if self._validationRulesPreAction is None:
                varName = '@{validationRules}'
                self._validationRulesPreAction = Step('')
                self._validationRulesPreAction.keyword = 'Create List'
                self._validationRulesPreAction.assign = [varName + '=']
                self._validationRulesPreAction.args = []
                self._setArg(3, varName.replace("@", "$"))

        elif self._Action == 'See':
            self._testDataPreAction = None
            self._enquiryConstraintsPreAction = None

            if self._validationRulesPreAction is None:
                varName = '@{validationRules}'
                self._validationRulesPreAction = Step('')
                self._validationRulesPreAction.keyword = 'Create List'
                self._validationRulesPreAction.assign = [varName + '=']
                self._validationRulesPreAction.args = []
                self._setArg(2, varName.replace("@", "$"))

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

    def setManualAction(self, args):
        # Expected Format:
        # Manual Step {text}
        # or
        # Manual Pause {text}
        if not args:
            return

        if args.__len__() >= 1:
            self.ManualActionPrompt = args[0]

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
            self.TransactionID = args[1]

        if args.__len__() >= 3:
            self.setRecordFieldValues(args[2], stepPreActions)

        if args.__len__() >= 4:
            self.HowToHandleOverrides = args[3]

        if args.__len__() >= 5:
            self._setHowToHandleErrors(args[4])

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
        # Check T24 Record {application,version} {recordID} {validation rules}
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
        # {action} can be real enquiry action or 'Check Result'
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
        self.InputValues = self._getNameValueList(testDataList.args)

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
        if self._Action == 'Input' or self._Action == 'Validate':
            return [self._testDataPreAction]
        elif self._Action == 'Enquiry':
            return [self._enquiryConstraintsPreAction, self._validationRulesPreAction]
        elif self._Action == 'See':
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
        elif action == 'Menu':
            return 'Execute T24 Menu Command'
        elif action == 'Input':
            return 'Create Or Amend T24 Record'
        elif action == 'Authorize':
            return 'Authorize T24 Record'
        elif action == 'See':
            return 'Check T24 Record'
        elif action == 'Enquiry':
            return 'Execute T24 Enquiry'
        elif action == 'Validate':
            return 'Validate T24 Record'
        elif action == T24TestStep.keyword_Manual_Step:
            return T24TestStep.keyword_Manual_Step
        elif action == T24TestStep.keyword_Manual_Pause:
            return T24TestStep.keyword_Manual_Pause
        else:  # todo - we have to have generic test step as a new test step type
            return 'Other'

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
            if item.strip():
                name, oper, value = RowUtils.ParseEnquiryRow(item)
                res.append((name, oper, value))

        return res

    def _getValidationRulesList(self, list):
        # so far both are with same syntax
        return self._getEnqConstraintList(list)

    def applyInputValuesOrEnquiryConstraintsChanges(self):
        if self._Action == 'Input' or self._Action == 'Validate':
            self._testDataPreAction.args = []
            for td in self.InputValues:
                self._testDataPreAction.args.append(u'{}={}'.format(td[0], td[1]))

        elif self._Action == 'Enquiry':
            self._enquiryConstraintsPreAction.args = []
            for enc in self.EnquiryConstraints:
                if enc[1] or enc[1].strip():
                    self._enquiryConstraintsPreAction.args.append(u'{} {} {}'.format(enc[0], enc[1], enc[2]))
                else:
                    self._enquiryConstraintsPreAction.args.append(u'{}'.format(enc[0]))

    def applyValidationRulesChanges(self):
        if self._Action == 'Enquiry' or self._Action == 'See':
            self._validationRulesPreAction.args = []
            for vr in self.ValidationRules:
                if vr[1] and vr[1].strip():
                    self._validationRulesPreAction.args.append(u'{} {} {}'.format(vr[0], vr[1], vr[2]))
                else:
                    self._validationRulesPreAction.args.append(u'{}'.format(vr[0]))

    def findPreAction(self, stepPreActions, keyword, variable):
        if stepPreActions is None:
            return None

        for pa in stepPreActions:
            if pa.keyword == keyword and pa.assign is not None and pa.assign[0] == "{}=".format(variable.replace("$", "@", 1)):
                return pa

        return None

    def applyChanges(self):
        self._setArg(0, self.AppVersion)
        # self._stepDetails.comment._comment = []
        if self.Description and len(self.Description):
            desc = self.Description.strip()
            desc = "# " + self.Description
            self._stepDetails.comment = Comment(desc)

        if self._Action == 'Login':
            self._stepDetails.keyword = self.keyword_L
        elif self._Action == 'Menu':
            self._stepDetails.keyword = self.keyword_M
        elif self._Action == 'Input':
            self._stepDetails.keyword = self.keyword_I
            self._setArg(1, self.TransactionID)
            self._setArg(3, self.HowToHandleOverrides)
            self._setArg(4, self._getHowToHandleErrors())
        elif self._Action == 'Authorize':
            self._stepDetails.keyword = self.keyword_A
            self._setArg(1, self.TransactionID)
        elif self._Action == 'See':
            self._stepDetails.keyword = self.keyword_S
            self._setArg(1, self.TransactionID)
        elif self._Action == 'Validate':
            self._stepDetails.keyword = self.keyword_V
            self._setArg(3, self.HowToHandleOverrides)
            self._setArg(4, self._getHowToHandleErrors())
        elif self._Action == 'Enquiry':
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
