*** Keywords ***
Create Or Amend T24 Record
    [Arguments]    ${application}    ${version}    ${recordID}    ${recordFieldValues}    ${overridesHandling}=${EMPTY}    ${errorsHandling}=${EMPTY}
    ...    ${postVerifications}=${EMPTY}
    Comment    ${recordFieldValues}

Authorize T24 Record
    [Arguments]    ${application}    ${recordID}    ${numberOfAutorizationsRequired}=1
