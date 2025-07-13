# Project Design Document: AI-Driven Robot Framework API Test Generation

## 1. Overview
This project automates the generation and execution of API tests from an OpenAPI specification using a Large Language Model (LLM). All tests are written in Robot Framework and leverage a custom keyword library for HTTP requests and logging, ensuring maintainability, extensibility, and robust reporting.

---

## 2. Architecture

### 2.1. Inputs
- **OpenAPI Specification** (`api_spec.yaml`): Defines API endpoints, methods, parameters, and response schemas.

### 2.2. Core Components
- **Custom Keyword Library** (`api_keywords.robot`):
  - Implements reusable keywords for GET/POST API requests and detailed logging.
  - Ensures all generated tests use a consistent interface for HTTP calls and logging.
- **LLM Orchestration Script** (`verify_all_apis_anthropic.py`):
  - Reads the OpenAPI spec.
  - Builds a prompt instructing the LLM to generate Robot Framework test cases using only the custom keywords.
  - Submits the prompt to the LLM (Anthropic Claude).
  - Saves the generated `.robot` test file and copies the keyword library to the test directory.
  - Executes the generated tests using Robot Framework.
  - Parses and logs the results.
- **Test Suites and Results**:
  - Generated test files are stored in `generated_tests/`.
  - Test execution results are saved in `latest_test_results/` (including `report.html`, `output.xml`).
- **Documentation** (`api_library_instructions.md`):
  - Documents the usage and arguments for each custom keyword.
  - Provides examples for importing and using the keywords in test cases.
- **Requirements** (`requirements.txt`):
  - Lists all Python dependencies for orchestration and LLM integration.

### 2.3. Outputs
- **Robot Framework Test Suites**: Generated `.robot` files for each API endpoint.
- **Execution Reports**: HTML/XML reports and logs for test results.

---

## 3. Workflow

1. **Input**: Place your OpenAPI spec in `api_spec.yaml`.
2. **Test Generation**: Run `verify_all_apis_anthropic.py` to:
   - Parse the OpenAPI spec.
   - Build a prompt for the LLM, instructing it to use only the custom keywords.
   - Generate a Robot Framework test suite.
   - Save the test file and copy the keyword library.
3. **Test Execution**: The script runs the generated tests using Robot Framework.
4. **Result Collection**: Results are saved in `latest_test_results/` and logs are available for review.

---

## 4. Design Principles

- **Separation of Concerns**: Parsing, prompt building, test generation, execution, and result parsing are modularized.
- **Extensibility**: New HTTP methods or logging enhancements can be added by updating `api_keywords.robot` and the LLM prompt.
- **Maintainability**: All HTTP requests and logging are routed through custom keywords, making updates and debugging straightforward.
- **Robustness**: The LLM prompt enforces the use of only the custom keywords, preventing direct use of RequestsLibrary in test cases.
- **Traceability**: Test files and results are named and organized for easy mapping to API endpoints and debugging.

---

## 5. Custom Keyword Library (`api_keywords.robot`)

### 5.1. Purpose
- Provides a consistent, maintainable interface for all HTTP requests and logging in generated tests.

### 5.2. Key Keywords
- `GET API Request`: Handles GET requests with logging.
- `POST API Request`: Handles POST requests with logging.
- `Log API Request`: Logs method, URL, and payload.
- `Log API Response`: Logs status code and response body.

### 5.3. Usage Example
```robot
Resource    api_keywords.robot
Library     RequestsLibrary

*** Test Cases ***
Get Users Should Return 200
    ${response}=    GET API Request    ${BASE_URL}/users
    Validate Status Code    ${response}    200
```

---

## 6. LLM Prompt Design
- The prompt instructs the LLM to:
  - Generate only Robot Framework `.robot` files.
  - Use only the custom keywords for all HTTP requests.
  - Validate response status codes and data structure.
  - Include setup/teardown and detailed logging.
  - Avoid Python/pytest code entirely.

---

## 7. Example Generated Test (Excerpt)
```
*** Test Cases ***
Get Users
    [Documentation]    Test getting a list of users
    [Tags]    api    smoke    users
    [Setup]    Log Test Start    Get Users
    [Teardown]    Log Test End    Get Users
    ${response}=    GET API Request    ${BASE_URL}/users
    Status Should Be    200
    ${json}=    Set Variable    ${response.json()}
    Should Be True    len(${json}) > 0
    FOR    ${user}    IN    @{json}
        Dictionary Should Contain Key    ${user}    id
        Dictionary Should Contain Key    ${user}    name
    END
```

---

## 8. Directory Structure
- `api_keywords.robot`: Custom keyword implementations.
- `api_library_instructions.md`: Keyword documentation.
- `verify_all_apis_anthropic.py`: Orchestration script.
- `api_spec.yaml`: OpenAPI specification input.
- `generated_tests/`: Generated Robot test files.
- `latest_test_results/`: Test execution results.
- `requirements.txt`: Python dependencies.
- `README.md`: Project overview and requirements.

---

## 9. Extending the System
- **New HTTP Methods**: Add new keywords (e.g., `PATCH API Request`) in `api_keywords.robot` and update the LLM prompt.
- **Enhanced Logging/Validation**: Update keyword implementations and documentation.
- **Prompt Tuning**: Refine the prompt in `verify_all_apis_anthropic.py` for new requirements.

---

## 10. Best Practices
- Always use the custom keywords for HTTP requests and logging.
- Do not use RequestsLibrary keywords directly in test cases.
- Update documentation and keyword library as the API evolves.
- Review test results in `latest_test_results/` for debugging and validation.

---

## 11. References
- `api_library_instructions.md` for keyword usage.
- `README.md` for project requirements and overview.

---

This design ensures robust, maintainable, and extensible AI-driven API test automation using Robot Framework and LLMs.
