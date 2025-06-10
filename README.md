
# 📄 Requirement Document: Automated API Testing with LLM from OpenAPI Spec

## 1. **Objective**
Develop a Python-based system that:
- Accepts an OpenAPI specification.
- Uses an LLM to generate Python test code for API endpoints.
- Executes the generated tests.
- Captures and reports the results.

## 2. **System Components**

### 2.1 Input
- OpenAPI Specification (`.yaml` or `.json`)

### 2.2 Processing
- LLM (e.g., OpenAI GPT-4o or GPT-4.5) for generating test code.
- Python environment to parse, generate, and execute test cases.

### 2.3 Output
- Executed test results (stdout/stderr).
- Optional: structured test reports (e.g., JSON or HTML).

## 3. **Functional Requirements**

### 3.1 Read and Parse OpenAPI Spec
- Load the OpenAPI file.
- Validate it against the OpenAPI schema (optional but recommended).
- Extract `paths`, `methods`, and `operation details`.

### 3.2 Prepare LLM Prompt
- For each endpoint:
  - Build a prompt that includes the HTTP method, path, parameters, and response schema.
  - Ask the LLM to generate a Python test file using `requests` and `unittest` or `pytest`.

### 3.3 Generate Test Code via LLM
- Use the OpenAI API (or similar) to submit the prompt.
- Receive Python code as a string.
- Handle LLM response errors or malformed code gracefully.

### 3.4 Save Generated Test Code
- Save the received code into a uniquely named `.py` test file.
- Ensure the filename indicates the endpoint/method for traceability.

### 3.5 Execute Test Code
- Run the generated Python file using `subprocess` or similar.
- Capture `stdout`, `stderr`, and `exit status`.

### 3.6 Collect and Log Results
- Log test results in a readable format.
- Optionally convert results to structured format (JSON, CSV, or report).

## 4. **Non-Functional Requirements**

- **Extensibility**: Should be easy to extend to support other testing frameworks (e.g., Postman, Playwright).
- **Modularity**: Each component (parse, prompt, run, collect) must be isolated and reusable.
- **Security**: Sanitize input/output to avoid arbitrary code execution issues.
- **Rate Limiting**: Respect OpenAI API limits, possibly implement retries and backoff.

## 5. **Technologies & Tools**

| Task | Technology |
|------|------------|
| OpenAPI Parsing | `PyYAML`, `json`, `openapi-spec-validator`, `prance` |
| LLM Integration | `openai` Python SDK |
| Test Code Execution | `subprocess`, `tempfile` |
| HTTP Requests in Tests | `requests` library |
| Test Framework | `unittest` or `pytest` |
| Logging & Reporting | `logging`, `json`, `csv` (optional HTML report) |

## 6. **Step-by-Step Execution Flow**

1. **User provides OpenAPI file**.
2. **Main script parses the OpenAPI spec** and extracts endpoints.
3. **For each endpoint**:
   - Build a prompt using its details.
   - Submit the prompt to the LLM.
   - Receive and save the test code.
   - Run the test and capture the output.
   - Store or display the result.
4. **Summary report is generated** at the end.

## 7. **Error Handling Requirements**

- LLM errors (e.g., API timeout, malformed response) must be retried with backoff.
- Generated code should be validated for syntax before execution.
- OpenAPI parsing failures must be reported with line numbers if possible.
- Execution errors (e.g., `requests.exceptions`) must be caught and logged.

## 8. **Optional Enhancements (Future Scope)**

- Add a web UI or CLI to manage test runs.
- Integrate with CI/CD (e.g., GitHub Actions, GitLab CI).
- Test coverage metrics per endpoint/method.
- Authentication handling (API key, OAuth2).
- Fuzz testing and security testing.
