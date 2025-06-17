*** Settings ***
Library           Process
Library           OperatingSystem

*** Variables ***
${API_SPEC_FILE}    ${CURDIR}/api_spec.yaml
${BASE_URL}         https://jsonplaceholder.typicode.com

*** Test Cases ***
Automated API Verification
    Set Base URL    ${BASE_URL}
    Load OpenAPI Spec    ${API_SPEC_FILE}
    Verify All APIs    ${API_SPEC_FILE}    ${BASE_URL}

*** Keywords ***
Set Base URL
    [Arguments]    ${url}
    Log    Setting base URL to ${url}

Load OpenAPI Spec
    [Arguments]    ${spec_file}
    Log    Loading OpenAPI spec from ${spec_file}

Verify All APIs
    [Arguments]    ${spec_file}    ${base_url}
    ${result}=    Run Process    python3    verify_all_apis_anthropic.py    ${spec_file}    ${base_url}    shell=True    stdout=PIPE    stderr=PIPE
    ${stdout}=    Set Variable    ${result.stdout}
    ${stderr}=    Set Variable    ${result.stderr}
    Log    Test Output:\n${stdout}
    Log    Test Errors:\n${stderr}
    Should Not Contain    ${stdout}    Traceback    Python script failed with error(s):\n${stderr}\n${stdout}
    Should Not Contain    ${stdout}    SyntaxError    Python script failed with error(s):\n${stderr}\n${stdout}
    Should Not Contain    ${stderr}    Traceback    Python script failed with error(s):\n${stderr}\n${stdout}
    Should Not Contain    ${stderr}    SyntaxError    Python script failed with error(s):\n${stderr}\n${stdout}
    Generate Report    ${stdout}    ${stderr}

Generate Report
    [Arguments]    ${stdout}    ${stderr}
    Log    ===== Test Report =====\n${stdout}\n${stderr}
