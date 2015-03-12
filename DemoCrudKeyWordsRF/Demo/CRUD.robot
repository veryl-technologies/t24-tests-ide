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
    Check T24 Record Exists    ACCOUNT,FR    \    ${EMPTY}    ${EMPTY}    ${EMPTY}    ${EMPTY}
    Check T24 Record Exists    ACCOUNT,FR    ZZZZ    Verfiy All Input Values Are Properly Saved

Enter an Account (verbose)
    ${mnemonic}=    Get Unique Mnemonic
    Open T24 Record for Ammendment    CUSTOMER
    Enter T24 Text Field Value    NAME.1.1    John
    Enter T24 Text Field Value    MNEMONIC    ${mnemonic}
    Click T24 Commit Button
    Get Result Of Attempt to Complete T24 Transaction
    Close T24 Record Ammendment Page
    Open T24 Record for Ammendment    ACCOUNT
    Enter T24 Text Field Value    CUSTOMER    ${LastT24TransactionID}
    Enter T24 Text Field Value    CATEGORY    Nostro
    Enter T24 Text Field Value    CURRENCY    USD
    Get Result Of Attempt to Complete T24 Transaction

Very New Test Case
    @{testDataFields1}=    Create List    t=2
    Create Or Amend T24 Record    SUPER    @{testDataFields1}    \    Expect Error Containing:ghfhf
    Check T24 Record Exists    SUPER    @{testDataFields1}    \    ${EMPTY}
    @{testDataFields1}=    Create List
    Create Or Amend T24 Record    \    @{testDataFields1}    \    ${EMPTY}
    Authorize T24 Record    123    @{testDataFields1}    \    ${EMPTY}
