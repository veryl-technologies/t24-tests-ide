*** Variables ***
${LastT24TransactionID}    <CalculatedRuntime>    # The ID of the last created/ammended record

*** Keywords ***
Login to T24
    [Arguments]    ${user}    ${password}
    Comment    Not Implemented

Enter T24 Command
    [Arguments]    ${commandText}
    Comment    Not Implemented

Open T24 Record for Viewing
    [Arguments]    ${applicationName}    ${recordID}
    Comment    Not Implemented

Open T24 Record for Ammendment
    [Arguments]    ${application}    ${version}=${EMPTY}    ${recordID}=${EMPTY}
    Comment    Not Implemented

Open T24 Enquiry
    [Arguments]    ${enquiryName}
    Comment    Not Implemented

Navigate and Click T24 Main Menu Item
    [Arguments]    ${menuPath}
    Comment    Not Implemented

Expand T24 Main Menu Item
    [Arguments]    ${menuItemName}
    Comment    Not Implemented

Click T24 Main Menu Item
    [Arguments]    ${menuItemName}
    Comment    Not Implemented

Log Off T24 User
    Comment    Not Implemented

Enter T24 Text Field Value
    [Arguments]    ${fieldName}    ${fieldValue}
    Comment    Not Implemented

Select T24 Dropdown Field Value
    [Arguments]    ${fieldName}    ${fieldValue}
    Comment    Not Implemented

Select T24 Radiobutton Field Value
    [Arguments]    ${fieldName}    ${fieldValue}
    Comment    Not Implemented

Set T24 Field Value
    [Arguments]    ${fieldName}    ${fieldLabel}    ${fieldType}    ${fieldValue}
    Comment    Not Implemented

Click T24 Commit Button
    Comment    Not Implemented

Get Result of Attempt to Complete T24 Transaction
    Comment    Not Implemented

Get Overrides Text after T24 Action
    Comment    Not Implemented

Get Error Text after T24 Action
    Comment    Not Implemented

Get T24 Record ID from Completed Transaction
    Comment    Not Implemented

Accept Overrides after T24 Action
    Comment    Not Implemented

Click T24 Validate Button
    Comment    Not Implemented

Click T24 Authorize Button
    Comment    Not Implemented

Close T24 Record Ammendment Page
    Comment    Not Implemented

Get T24 Record Value By Field Label
    [Arguments]    ${labelText}
    Comment    Not Implemented

Get T24 Record Value By Field Name
    [Arguments]    ${fieldName}
    Comment    Not Implemented

Close T24 Record View Page
    Comment    Not Implemented
