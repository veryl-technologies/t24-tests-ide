*** Settings ***
Resource          tip-basic.robot
Resource          tip-highlevel.robot
Resource          custom.robot

*** Test Cases ***
Enter an Account
    ${mnemonic}=    Get Unique Mnemonic
    @{fields1}=    Create List    NAME.1.1=John    MNEMONIC=${mnemonic}    Short Name=Babchko
    Create Or Amend T24 Record    SUPER,DUPER    @{testDataFields1}    Fail    Expect Error Containing:Da be da
    Authorize T24 Record    CUSTOMER,IND    @{fields1}    Accept All Overrides    ${EMPTY}    ${EMPTY}
    Execute T24 Menu Command    sfsdfsfd
    Check T24 Record Exists    ACCOUNT,FR    \    @{validationRules1}    ${EMPTY}    ${EMPTY}    ${EMPTY}
    Check T24 Record Exists    ACCOUNT,FR    ZZZZ    @{validationRules1}

The Very New
    T24 Login    INPUTTER
    @{testDataFields1}=    Create List    MNEMONIC=1234    ShortName=Banan    Name=Banan1...
    Create Or Amend T24 Record    CUSTOMER    @{testDataFields1}    \    ${EMPTY}
    @{enquiryConstraints1}=    Create List    MNEMONIC:EQ:=1234
    @{validationRules1}=    Create List    ShortName:LK:=Banan    Name:LK:=Banan1...
    Execute T24 Enquiry    %CUSTOMER    @{enquiryConstraints1}    \    @{validationRules1}
    @{validationRules1}=    Create List    ShortName:LK:=Banan    Name:LK:=Banan1...    STATUS:EQ:=1
    Check T24 Record Exists    CUSTOMER    $(CUSTOMER.@ID)    @{validationRules1}

Very New Test Case
    Execute T24 Enquiry    SUPER    @{enquiryConstraints1}    rrrr    @{validationRules1}
    Check T24 Record Exists    wet    we    @{validationRules1}
    T24 Login    AUTHORISER 2    @{testDataFields1}    \    ${EMPTY}
    @{testDataFields1}=    Create List    BABA=123123    Mnogo Babab=ZZZZ
    Create Or Amend T24 Record    \    @{testDataFields1}    \    ${EMPTY}
    Authorize T24 Record    123    @{testDataFields1}    \    ${EMPTY}
    @{testDataFields1}=    Create List    V.BABA=123123    V.Mnogo Babab=ZZZZ
    Validate T24 Record    Super validation test step    @{testDataFields1}    \    ${EMPTY}
