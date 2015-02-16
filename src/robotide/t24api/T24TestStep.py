__author__ = 'Zhelev'


class T24TestStep(object):
    Action = ''
    AppVersion = ''

    def __init__( self, text ):
        self.parseTestStep(text)

    def parseTestStep(self, text):
        # todo-parse the text and init the object
        # todo - this is just for the demo - real parsing must be implemented
        if text.startswith('I'):
            self.Action='I'
            self.AppVersion='CUSTOMER,IND'
        else:
            self.Action='A'
            self.AppVersion='CUSTOMER,CORP'
        pass

    def toString(self):
        # todo - this is just for the demo
        # todo - real implementation is needed
        return self.Action + ' ' + self.AppVersion
