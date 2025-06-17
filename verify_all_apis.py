import os
import subprocess
import openai  # You may need to change this to anthropic's SDK if using Anthropic
import tempfile
import yaml

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# 1. Read OpenAPI spec
def read_openapi_spec(spec_path):
    with open(spec_path, 'r') as f:
        if spec_path.endswith('.yaml') or spec_path.endswith('.yml'):
            return yaml.safe_load(f)
        else:
            import json
            return json.load(f)

# 2. Build prompt for LLM
def build_prompt(openapi_spec, base_url=None):
    base_url_instruction = f"The base URL for all requests is: {base_url}\n" if base_url else ""
    return f"""
Given the following OpenAPI spec, generate Python pytest test cases using the requests library to test all endpoints. The tests should be runnable as a single file.
{base_url_instruction}
OpenAPI Spec:
{openapi_spec}
"""

# 3. Call LLM to generate test code
def generate_tests_with_llm(prompt):
    # Replace with Anthropic's API call if needed
    response = openai.ChatCompletion.create(
        model="gpt-4o",  # or Anthropic equivalent
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
        temperature=0.2,
    )
    return response['choices'][0]['message']['content']

# 4. Save test code to file
def save_test_code(test_code):
    fd, path = tempfile.mkstemp(suffix="_generated_test.py")
    with os.fdopen(fd, 'w') as f:
        f.write(test_code)
    return path

# 5. Run test code and collect results
def run_tests(test_file_path):
    result = subprocess.run([
        "python3", "-m", "pytest", test_file_path
    ], capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

# 6. Main function to orchestrate all steps
def verify_all_apis(spec_path, base_url=None):
    openapi_spec = read_openapi_spec(spec_path)
    prompt = build_prompt(openapi_spec, base_url)
    test_code = generate_tests_with_llm(prompt)
    test_file = save_test_code(test_code)
    stdout, stderr, exit_code = run_tests(test_file)
    report = {
        "test_file": test_file,
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code
    }
    print("===== Test Report =====")
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
