
*** Keywords ***


GET API Request
    [Arguments]    ${url}    ${headers}=${EMPTY}    ${params}=${EMPTY}
    Log API Request    GET    ${url}
    ${response}=    GET    ${url}    headers=${headers}    params=${params}
    Log API Response    ${response}
    RETURN    ${response}

Log API Request
    [Arguments]    ${method}    ${url}    ${payload}=${EMPTY}
    Log    --- API Request ---
    Log    Method: ${method}
    Log    URL: ${url}
    ${is_payload}=    Evaluate    bool($payload)
    Run Keyword If    ${is_payload}    Log    Payload: ${payload}
    Log    -------------------

Log API Response
    [Arguments]    ${response}
    Log    --- API Response ---
    Log    Status Code: ${response.status_code}
    Log    Response Body: ${response.text}
    Log    --------------------

POST API Request
    [Arguments]    ${url}    ${payload}    ${headers}=${EMPTY}
    Log API Request    POST    ${url}    ${payload}
    ${response}=    POST    ${url}    json=${payload}    headers=${headers}
    Log API Response    ${response}
    RETURN    ${response}
