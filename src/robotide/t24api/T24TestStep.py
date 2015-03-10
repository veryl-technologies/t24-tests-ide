__author__ = 'Zhelev'

from robot.parsing.model import Step

# todo - need to build test steps inheritance
class T24TestStep(object):

    # consts
    keyword_M = 'Execute T24 Menu Command'
    keyword_I = 'Create Or Amend T24 Record'
    keyword_A = 'Authorize T24 Record'
    keyword_S = 'Check T24 Record Exists'
    keyword_E = 'Execute T24 Enquiry'
    keyword_V = 'Validate T24 Record'

    # members
    _stepDetails = None

    # properties
    _Action = ''
    AppVersion = ''
    TransactionID = ''

    TestData = []

    # I, V specific properties
    HowToHandleErrors = None
    ExpectErrorContaining = None
    HowToHandleOverrides = None

    IsRealTestStep = False

    def __init__( self, stepPreActions, stepDetails ):
        # stepPreActions are the keywords for initialization of variables etc that belong to the entire test step
        self._stepDetails = stepDetails
        self.IsRealTestStep = self.parseTestStep(stepDetails, stepPreActions)

    @staticmethod
    def isT24TestStep(stepDetails):
        return T24TestStep(None, stepDetails)._Action != ''

    def parseTestStep(self, stepDetails, stepPreActions = None):
        self._testDataPreAction = None
        self._enquiryConstraintsPreAction = None

        # todo-parse the text and init the object
        # todo - this is just for the demo - real parsing must be implemented
        if stepDetails.keyword == self.keyword_M:
            self._Action='M'
            self.setMenuArgs(stepDetails.args)
        elif stepDetails.keyword == self.keyword_I:
            self._Action='I'
            self.setCreateOrAmendOrValidateArgs(stepDetails.args, stepPreActions)
            if self._testDataPreAction is None:
                self.SetStepType(self._Action)  # this will create new _testDataPreAction
        elif stepDetails.keyword == self.keyword_A:
            self._Action='A'
            self.setAuthorizeArgs(stepDetails.args)
        elif stepDetails.keyword == self.keyword_S:
            self._Action='S'
            self.setCheckRecordArgs(stepDetails.args)
        elif stepDetails.keyword == self.keyword_E:
            self._Action='E'
            self.setEnquiryArgs(stepDetails.args, stepPreActions)
            if self._enquiryConstraintsPreAction is None:
                self.SetStepType(self._Action)  # this will create new _testDataPreAction
        elif stepDetails.keyword == self.keyword_V:
            self._Action='V'
            self.setCreateOrAmendOrValidateArgs(stepDetails.args, stepPreActions)
            if self._testDataPreAction is None:
                self.SetStepType(self._Action)  # this will create new _testDataPreAction
        else:
            # todo - we need to implement other types
            return False

        return True

    def GetStepType(self):
        return self._Action

    def SetStepType(self, action):
        self._Action = action

        if self._Action == 'I' or self._Action == 'V':
            self._enquiryConstraintsPreAction = None
            if self._testDataPreAction is None:
                testDataVarName = '@{testDataFields1}'  # todo - do we need to change the name or this is OK, next step will just override it
                self._testDataPreAction = Step('')
                self._testDataPreAction.keyword = 'Create List'
                self._testDataPreAction.assign =[testDataVarName + '=']
                self._testDataPreAction.args = []
                self._setArg(1, testDataVarName)

        elif self._Action == 'E':
            self._testDataPreAction = None
            if self._enquiryConstraintsPreAction is None:
                enqVarName = '@{enquiryConstraints1}'  # todo - do we need to change the name or this is OK, next step will just override it
                self._enquiryConstraintsPreAction = Step('')
                self._enquiryConstraintsPreAction.keyword = 'Create List'
                self._enquiryConstraintsPreAction.assign = [enqVarName + '=']
                self._enquiryConstraintsPreAction.args = []
                self._setArg(1, enqVarName)



    def setMenuArgs(self, args):
        # Expected Format
        # Execute T24 Menu Command {menu_parent_1 \ menu_parent_2 \ ... \ menu_item}
        #
        if not args:
            return

        if args.__len__() >= 1:
            self.AppVersion=args[0]

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
            self.AppVersion=args[0]

        if args.__len__() >= 2:
            self.TransactionID = args[1]


    def setCheckRecordArgs(self, args):
        # Expected Format
        # Check T24 Record Exists {application,version} {recordID} {recordFieldsToValidate}
        if not args:
            return

        if args.__len__() >= 1:
            self.AppVersion=args[0]

        if args.__len__() >= 2:
            self.TransactionID = args[1]

        # todo - rest of the arguments

    def setEnquiryArgs(self, args, stepPreActions):
        # Expected Format
        # Execute T24 Enquiry {Enquiry Name} {constraints} {post filtering constraints} {action} {validation criterias}
        #
        # {action} can be real enquiry action or 'Check Values'
        #
        #
        if not args:
            return

        if args.__len__() >= 1:
            self.AppVersion=args[0]

        if args.__len__() >= 2:
            self.setEnquiryConstraints(args[1], stepPreActions)

        # todo rest of the arguments

    def setRecordFieldValues(self, arg, stepPreActions):
        testDataList = self.findPreAction(stepPreActions, "Create List", arg)
        if testDataList is None:
            return

        self._testDataPreAction = testDataList
        self.TestData = self.getNameValueList(testDataList.args)

    def setEnquiryConstraints(self, arg, stepPreActions):
        enqConstraintsList = self.findPreAction(stepPreActions, "Create List", arg)
        if enqConstraintsList is None:
            return

        self._enquiryConstraintsPreAction = enqConstraintsList
        self.TestData = self.getNameValueList(enqConstraintsList.args)# todo - we have to have different syntax for enquiries

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
            return [self._enquiryConstraintsPreAction]

        return []

    # create default step type
    @staticmethod
    def createNew():
        stepDetails = Step('')
        stepDetails.keyword='Create Or Amend T24 Record' # todo - we have to have generic test step as a new test step type
        stepDetails.args=[]

        # todo - on new test step depending on the type we have to add some hints. For example for 'I' step:
        """
        // Add test data here. Format:
        // [Field Name] := [Field Value]
        // Example:
        // NAME.1 := Jhon Smith
        // Short Name := JhSmith
        """

        return T24TestStep([],stepDetails)

    def getNameValueList(self, list):
        if list is None:
            return None

        res = []

        for item in list:
            eqIdx = item.find('=')
            if eqIdx < 0:
                return None # todo - maybe report an error?

            name = item[:eqIdx].strip()
            value = item[eqIdx+1:].strip()
            res.append((name,value))

        return res;

    def applyTestDataChanges(self):
        # todo - we have to identify whether the test data is changed and if not this func must result false
        # todo - then the caller function will know whether this is a real change or not!

        if self._Action == 'I' or self._Action == 'V':
            self._testDataPreAction.args = []
            for td in self.TestData:
                self._testDataPreAction.args.append('{}={}'.format(td[0], td[1]))

        elif self._Action == 'E':
            self._enquiryConstraintsPreAction.args = []
            # todo

    def findPreAction(self, stepPreActions, keyword, assign):
        if stepPreActions is None:
            return None

        for pa in stepPreActions:
            # todo - this should be revised but currently work for:
            # @{fields1}=    Create List    NAME.1.1 = John    MNEMONIC = ${mnemonic}
            if pa.keyword == keyword and pa.assign is not None and pa.assign[0] == "{}=".format(assign):
                return pa

        return None

    def toString(self):
        # todo - this is just for the demo
        # todo - real implementation is needed
        return self._Action + ' ' + self.AppVersion

    def applyChanges(self):
        # todo - apply other changes also
        self._setArg(0, self.AppVersion)

        if self._Action == 'M':
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
            self.ExpectErrorContaining = arg[(pos+1):].strip()

    def _getHowToHandleErrors(self):
        result = ''
        if self.HowToHandleErrors:
            result = result + self.HowToHandleErrors
        if self.ExpectErrorContaining and len(self.ExpectErrorContaining) > 0:
            result = result + ':' + self.ExpectErrorContaining
        return result
