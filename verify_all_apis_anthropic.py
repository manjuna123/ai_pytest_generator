import anthropic
import os
import re
import subprocess
import tempfile
import yaml
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# 1. Read OpenAPI spec
def read_openapi_spec(spec_path):
    logging.info(f"Reading OpenAPI spec from {spec_path}")
    with open(spec_path, 'r') as f:
        if spec_path.endswith('.yaml') or spec_path.endswith('.yml'):
            return yaml.safe_load(f)
        else:
            import json
            return json.load(f)

# 2. Build prompt for LLM
def build_prompt(openapi_spec, base_url=None):
    base_url_instruction = f"The base URL for all requests is: {base_url}\n" if base_url else ""
    prompt = f"""
Given the following OpenAPI spec, generate Python pytest test cases using the requests library to test all endpoints. The tests should be runnable as a single file.
{base_url_instruction}
OpenAPI Spec:
{openapi_spec}
"""
    logging.info("Prompt for LLM built.")
    return prompt

# 3. Call Anthropic LLM to generate test code
def generate_tests_with_llm(prompt):
    logging.info("Sending prompt to Anthropic LLM...")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-3-opus-20240229",  # Update to your preferred model
        max_tokens=4096,
        temperature=0.2,
        system="You are a helpful assistant that writes Python pytest code.",
        messages=[{"role": "user", "content": prompt}]
    )
    code = message.content[0].text if hasattr(message.content[0], 'text') else message.content[0]['text']
    logging.info("Received test code from LLM.")
    return code

def extract_python_code(llm_response):
    match = re.search(r"```python\s*([\s\S]+?)```", llm_response)
    if match:
        return match.group(1)
    return llm_response

# 4. Save test code to file
def save_test_code(test_code):
    fd, path = tempfile.mkstemp(suffix="_generated_test.py")
    with os.fdopen(fd, 'w') as f:
        f.write(test_code)
    logging.info(f"Test code saved to {path}")
    return path

# 5. Run test code and collect results
def run_tests(test_file_path):
    logging.info(f"Running tests in {test_file_path}")
    result = subprocess.run([
        "python3", "-m", "pytest", test_file_path, "--tb=short", "--maxfail=100", "--disable-warnings", "--json-report"
    ], capture_output=True, text=True)
    logging.info("Test execution completed.")
    # Try to read pytest's JSON report
    import json
    json_report_path = ".report.json"
    scenarios = []
    status = "unknown"
    if os.path.exists(json_report_path):
        with open(json_report_path) as f:
            report = json.load(f)
            for test in report.get("tests", []):
                scenarios.append({
                    "name": test.get("nodeid"),
                    "outcome": test.get("outcome")
                })
            status = report.get("exitcode", "unknown")
    return result.stdout, result.stderr, result.returncode, scenarios, status

# 6. Main function to orchestrate all steps
def verify_all_apis(spec_path, base_url=None):
    openapi_spec = read_openapi_spec(spec_path)
    prompt = build_prompt(openapi_spec, base_url)
    test_code = generate_tests_with_llm(prompt)
    logging.info("===== LLM Response (Python test code) =====")
    print("===== LLM Response (Python test code) =====")
    print(test_code)
    test_code = extract_python_code(test_code)
    test_file = save_test_code(test_code)
    stdout, stderr, exit_code, scenarios, status = run_tests(test_file)
    report = {
        "test_file": test_file,
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        "scenarios": scenarios,
        "status": status
    }
    logging.info("===== Test Report =====")
    print("Scenarios:")
    for s in scenarios:
        print(f"  - {s['name']}: {s['outcome']}")
    print(f"Overall status: {status}")
    print(stdout)
    if stderr:
        print("Errors:\n", stderr)
    return report

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python verify_all_apis.py <openapi_spec.yaml> [base_url]")
        sys.exit(1)
    spec_path = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else None
    verify_all_apis(spec_path, base_url)
