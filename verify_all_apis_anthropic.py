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

# Parse pytest output for test details
def parse_pytest_output(stdout, stderr):
    """Parse pytest verbose output to extract test details"""
    test_results = []
    lines = stdout.split('\n')
    
    for line in lines:
        # Look for test execution lines with status
        if '::' in line and ('PASSED' in line or 'FAILED' in line or 'SKIPPED' in line or 'ERROR' in line):
            parts = line.split(' ')
            if len(parts) >= 2:
                test_name = parts[0]
                status = None
                for part in parts:
                    if part in ['PASSED', 'FAILED', 'SKIPPED', 'ERROR']:
                        status = part
                        break
                
                if status:
                    # Extract test description from test name
                    test_desc = test_name.split('::')[-1] if '::' in test_name else test_name
                    test_desc = test_desc.replace('_', ' ').replace('test ', '').title()
                    
                    test_results.append({
                        'name': test_name,
                        'description': test_desc,
                        'status': status,
                        'full_line': line.strip()
                    })
    
    return test_results

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
        "python3", "-m", "pytest", test_file_path, "--tb=short", "--maxfail=100", "--disable-warnings", "--json-report", "-v"
    ], capture_output=True, text=True)
    logging.info("Test execution completed.")
    
    # Parse pytest output for individual test results
    test_results = parse_pytest_output(result.stdout, result.stderr)
    
    # Try to read pytest's JSON report
    import json
    json_report_path = ".report.json"
    scenarios = []
    status = "unknown"
    if os.path.exists(json_report_path):
        with open(json_report_path) as f:
            report = json.load(f)
            for test in report.get("tests", []):
                test_info = {
                    "name": test.get("nodeid"),
                    "outcome": test.get("outcome"),
                    "duration": test.get("duration", 0),
                    "setup": test.get("setup", {}),
                    "call": test.get("call", {}),
                    "teardown": test.get("teardown", {})
                }
                scenarios.append(test_info)
            status = report.get("exitcode", "unknown")
    
    return result.stdout, result.stderr, result.returncode, scenarios, status, test_results

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
    stdout, stderr, exit_code, scenarios, status, test_results = run_tests(test_file)
    
    # Print detailed test case information
    logging.info("===== Test Execution Results =====")
    print("\n===== Test Execution Results =====")
    
    if test_results:
        print(f"\nTotal Tests Found: {len(test_results)}")
        print("-" * 60)
        
        passed_count = 0
        failed_count = 0
        skipped_count = 0
        error_count = 0
        
        for test_result in test_results:
            status_symbol = {
                'PASSED': '✅',
                'FAILED': '❌', 
                'SKIPPED': '⚠️',
                'ERROR': '🔴'
            }.get(test_result['status'], '❓')
            
            print(f"{status_symbol} {test_result['status']}: {test_result['description']}")
            print(f"   Test: {test_result['name']}")
            
            # Count results
            if test_result['status'] == 'PASSED':
                passed_count += 1
            elif test_result['status'] == 'FAILED':
                failed_count += 1
            elif test_result['status'] == 'SKIPPED':
                skipped_count += 1
            elif test_result['status'] == 'ERROR':
                error_count += 1
            
            print()
        
        # Print summary
        print("-" * 60)
        print(f"📊 Test Summary:")
        print(f"   ✅ Passed: {passed_count}")
        print(f"   ❌ Failed: {failed_count}")
        print(f"   ⚠️ Skipped: {skipped_count}")
        print(f"   🔴 Errors: {error_count}")
        print(f"   📋 Total: {len(test_results)}")
    
    report = {
        "test_file": test_file,
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        "scenarios": scenarios,
        "status": status,
        "test_results": test_results
    }
    
    logging.info("===== Test Report =====")
    print("\n===== Detailed Test Report =====")
    print("Scenarios from JSON report:")
    for s in scenarios:
        duration = s.get('duration', 0)
        outcome_symbol = {
            'passed': '✅',
            'failed': '❌',
            'skipped': '⚠️',
            'error': '🔴'
        }.get(s.get('outcome', '').lower(), '❓')
        
        print(f"  {outcome_symbol} {s.get('name', 'Unknown')}: {s.get('outcome', 'Unknown')} ({duration:.2f}s)")
    
    print(f"\nOverall Exit Code: {exit_code}")
    print(f"Overall Status: {status}")
    
    if stdout:
        print("\n===== Raw pytest Output =====")
        print(stdout)
    
    if stderr:
        print("\n===== Errors =====")
        print(stderr)
    
    return report

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python verify_all_apis.py <openapi_spec.yaml> [base_url]")
        sys.exit(1)
    spec_path = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else None
    verify_all_apis(spec_path, base_url)
