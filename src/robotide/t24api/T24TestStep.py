__author__ = 'Zhelev'

from robot.parsing.model import Step

class T24TestStep(object):

    # consts
    keyword_M = 'Execute T24 Menu Command'
    keyword_I = 'Create Or Amend T24 Record'
    keyword_A = 'Authorize T24 Record'
    keyword_S = 'Check T24 Record Exists'
    keyword_E = 'Execute T24 Enquiry'
    keyword_V = 'Validate T24 Record'

    # members
    _stepPreActions = None
    _stepDetails = None

    # properties
    Action = ''
    AppVersion = ''
    TransactionID = ''

    TestData = []

    IsRealTestStep=False

    def __init__( self, stepPreActions, stepDetails ):
        # todo - stepPreActions are the keywords for initialization of variables etc that belong to the entire test step
        self._stepPreActions = stepPreActions
        self._stepDetails = stepDetails
        self.IsRealTestStep = self.parseTestStep(stepDetails)

    @staticmethod
    def isT24TestStep(stepDetails):
        return T24TestStep(None, stepDetails).Action != ''

    def parseTestStep(self, stepDetails):
        self._testDataPreAction = None
        # todo-parse the text and init the object
        # todo - this is just for the demo - real parsing must be implemented
        if stepDetails.keyword == self.keyword_M:
            self.Action='M'
            self.setMenuArgs(stepDetails.args)
        elif stepDetails.keyword == self.keyword_I:
            self.Action='I'
            self.setCreateOrAmendOrValidateArgs(stepDetails.args)
        elif stepDetails.keyword == self.keyword_A:
            self.Action='A'
            self.setAuthorizeArgs(stepDetails.args)
        elif stepDetails.keyword == self.keyword_S:
            self.Action='S'
            self.setCheckRecordArgs(stepDetails.args)
        elif stepDetails.keyword == self.keyword_E:
            self.Action='E'
            self.setEnquiryArgs(stepDetails.args)
        elif stepDetails.keyword == self.keyword_V:
            self.Action='V'
            self.setCreateOrAmendOrValidateArgs(stepDetails.args)
        else:
            # todo - we need to implement other types
            return False

        return True

    def setMenuArgs(self, args):
        # Expected Format
        # Execute T24 Menu Command {menu_parent_1 \ menu_parent_2 \ ... \ menu_item}
        #
        if not args:
            return

        if args.__len__() >= 1:
            self.AppVersion=args[0]

    def setCreateOrAmendOrValidateArgs(self, args):
        # Expected Format
        # Create Or Amend T24 Record {application,version} {recordFieldValues} {overridesHandling} {errorsHandling} {postVerifications}
        # or
        # Validate T24 Record {application,version} {recordFieldValues} {overridesHandling} {errorsHandling} {postVerifications}
        #
        if not args:
            return

        if args.__len__() >= 1:
            self.AppVersion=args[0]

        if args.__len__() >= 2:
            self.setRecordFieldValues(args[1])

        """ todo
        if args.__len__() >= 3:
            setOverridesHandling(args[2])

        if args.__len__() >=4:
            setErrorsHandling(args[3])

        if args.__len__() >=5:
            setPostVerification(args[4])
        """

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

    def setEnquiryArgs(self, args):
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

        # todo rest of the arguments

    def setRecordFieldValues(self, arg):
        testDataList = self.findPreAction("Create List", arg)
        if testDataList is None:
            return

        self._testDataPreAction = testDataList
        self.TestData = self.getNameValueList(testDataList.args)

    def subSteps(self):
        ls = []
        if self._stepDetails:
            ls.append(self._stepDetails)
        if self._stepPreActions:
            for pa in self._stepPreActions:
                ls.append(pa)

        return ls

    # create default step type
    @staticmethod
    def createNew():
        stepDetails = Step('')
        stepDetails.keyword='Create Or Amend T24 Record'
        stepDetails.args=['']
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
        if not self._testDataPreAction:
            # todo - we have to create it!!!
            return

        self._testDataPreAction.args = []

        # todo - we have to identify whether the test data is changed and if not this func must result false
        # todo - then the caller function will know whether this is a real change or not!

        for td in self.TestData:
           self._testDataPreAction.args.append('{}={}'.format(td[0],td[1]))


    def findPreAction(self, keyword, assign):
        if self._stepPreActions is None:
            return None

        for pa in self._stepPreActions:
            # todo - this should be revised but currently work for:
            # @{fields1}=    Create List    NAME.1.1 = John    MNEMONIC = ${mnemonic}
            if pa.keyword == keyword and pa.assign is not None and pa.assign[0] == "{}=".format(assign):
                return pa

        return None

    def toString(self):
        # todo - this is just for the demo
        # todo - real implementation is needed
        return self.Action + ' ' + self.AppVersion

    def applyChanges(self):
        # todo - apply other changes also
        self._stepDetails.args[0] = self.AppVersion

        if self.Action == 'M':
            self._stepDetails.keyword = self.keyword_M
        elif self.Action == 'I':
            self._stepDetails.keyword = self.keyword_I
        elif self.Action == 'A':
            self._stepDetails.keyword = self.keyword_A
            self._stepDetails.args[1] = self.TransactionID
        elif self.Action == 'S':
            self._stepDetails.keyword = self.keyword_S
            self._stepDetails.args[1] = self.TransactionID
        elif self.Action == 'V':
            self._stepDetails.keyword = self.keyword_V
        elif self.Action == 'E':
            self._stepDetails.keyword = self.keyword_E
