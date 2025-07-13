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
    base_url_instruction = f"Use this base URL: {base_url}" if base_url else "Define BASE_URL variable"
    # Read api_library_instructions.md for richer keyword documentation
    instructions_path = os.path.join(os.path.dirname(__file__), 'api_library_instructions.md')
    try:
        with open(instructions_path, 'r') as f:
            api_keyword_docs = f.read()
    except Exception as e:
        api_keyword_docs = ""
        logging.warning(f"Could not read api_library_instructions.md: {e}")

    prompt = f"""
You are an expert Robot Framework test automation engineer. Generate comprehensive Robot Framework test cases based on the following OpenAPI specification.

Requirements:
1. Create Robot Framework .robot file syntax with proper sections
2. Use RequestsLibrary for HTTP requests
3. Import and use the custom keyword library from 'api_keywords.robot' (Resource    api_keywords.robot) in the *** Settings *** section
4. For every HTTP request, use the corresponding custom keyword from api_keywords.robot (e.g., GET API Request, POST API Request, PUT API Request, DELETE API Request, etc.) matching the HTTP method. Do not use RequestsLibrary keywords directly in test cases.
5. Validate response status codes and response data structure
6. Use descriptive test case names and documentation
7. Include proper error handling and assertions
8. Use Robot Framework best practices and conventions
9. Add extensive logging for better visibility and debugging
10. {base_url_instruction}

Refer to the documentation in api_keywords.robot for keyword usage. If a new HTTP method is present, use the corresponding <METHOD> API Request keyword (e.g., PATCH API Request for PATCH).

IMPORTANT:
- Only generate Robot Framework .robot file content. Do NOT generate Python or pytest code.
- The output must start with *** Settings *** and use Robot Framework syntax throughout.
- Do not include any Python code blocks or explanations for pytest.

---
Below is the documentation for the available custom keywords and usage examples:
{api_keyword_docs}
---

OpenAPI Specification:
{openapi_spec}

Generate a complete Robot Framework test file that:
- Imports 'api_keywords.robot' as a resource
- Uses the custom API keywords for all HTTP requests
- Tests all available endpoints from the OpenAPI spec
- Validates HTTP response codes (200, 201, 404, etc.)
- Checks response data structure and required fields
- Uses proper Robot Framework syntax
- Includes setup and teardown with detailed logging
- Uses variables for reusable data
- Has clear test documentation
- Includes detailed logging statements for each step
- Logs request and response details
- Uses Log To Console for important information

Example structure with enhanced logging:
*** Settings ***
Library    RequestsLibrary
Library    Collections
Library    BuiltIn
Resource   api_keywords.robot
Suite Setup    Test Suite Setup
Suite Teardown    Test Suite Teardown

*** Variables ***
${{BASE_URL}}    {base_url if base_url else 'https://your-api-url.com'}

*** Test Cases ***
Test Endpoint Name
    [Documentation]    Description of what this test does
    [Tags]    api    smoke
    [Setup]    Log Test Start    Test Endpoint Name
    [Teardown]    Log Test End    Test Endpoint Name
    Log    🚀 Starting endpoint test for /endpoint
    Log To Console    🚀 Testing endpoint: /endpoint
    # Make request with logging using custom keyword
    Log    📤 Sending request to: ${{BASE_URL}}/endpoint
    ${{response}}=    <METHOD> API Request    ${{BASE_URL}}/endpoint    # Use the correct keyword for the HTTP method
    Log    📥 Response status: ${{response.status_code}}
    Log    📄 Response body: ${{response.text}}
    Log To Console    📊 Status: ${{response.status_code}}
    # Validate response
    Status Should Be    200
    Log    ✅ Status code validation passed
    Log To Console    ✅ Test completed successfully

*** Keywords ***
Test Suite Setup
    Log    📋 Setting up AI Generated API Test Suite
    Log To Console    📋 AI Generated API Tests - Starting Test Suite
    Create Session    api    ${{BASE_URL}}    verify=False
    Log    🌐 Base URL configured: ${{BASE_URL}}
    Log To Console    🌐 Base URL: ${{BASE_URL}}

Test Suite Teardown
    Log    🏁 Tearing down AI Generated API Test Suite
    Log To Console    🏁 AI Generated API Tests - Test Suite Completed
    Delete All Sessions
    Log    🧹 All sessions cleaned up

Log Test Start
    [Arguments]    ${{test_name}}
    Log    🧪 Starting test case: ${{test_name}}
    Log To Console    🧪 Starting: ${{test_name}}

Log Test End
    [Arguments]    ${{test_name}}
    Log    ✅ Completed test case: ${{test_name}}
    Log To Console    ✅ Completed: ${{test_name}}

Please generate the complete .robot file content with extensive logging and proper error handling, always using the custom API keywords from 'api_keywords.robot' for all HTTP requests, and always matching the HTTP method to the correct keyword. Do NOT generate Python or pytest code.
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
        system="You are a helpful assistant that writes Robot Framework test code using proper .robot file syntax.",
        messages=[{"role": "user", "content": prompt}]
    )
    code = message.content[0].text if hasattr(message.content[0], 'text') else message.content[0]['text']
    logging.info("Received Robot Framework test code from LLM.")
    return code

def extract_python_code(llm_response):
    # Look for Robot Framework code blocks first
    robot_patterns = [
        r"```robot\s*([\s\S]+?)```",
        r"```robotframework\s*([\s\S]+?)```",
    ]
    
    for pattern in robot_patterns:
        match = re.search(pattern, llm_response)
        if match:
            return match.group(1).strip()
    
    # Look for Robot Framework content by finding *** Settings *** section
    if "*** Settings ***" in llm_response:
        # Extract everything from *** Settings *** to the end of Robot Framework content
        start_pos = llm_response.find("*** Settings ***")
        
        # Find where Robot Framework content ends (look for explanatory text)
        end_markers = [
            "\n\nThis Robot Framework test file includes:",
            "\n\nThe above Robot Framework",
            "\n\nThis test file contains:",
            "\n\nLet me know if",
            "\n\nThis file includes:"
        ]
        
        end_pos = len(llm_response)
        for marker in end_markers:
            marker_pos = llm_response.find(marker, start_pos)
            if marker_pos != -1 and marker_pos < end_pos:
                end_pos = marker_pos
        
        robot_content = llm_response[start_pos:end_pos].strip()
        return robot_content
    
    # Fallback to python code blocks
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
        # Look for Robot Framework test execution lines
        if '::' in line and ('PASS' in line or 'FAIL' in line or 'SKIP' in line):
            parts = line.split(' ')
            if len(parts) >= 2:
                test_name = parts[0]
                status = None
                for part in parts:
                    if part in ['PASS', 'FAIL', 'SKIP', 'ERROR']:
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
        
        # Also look for Robot Framework format: TestName | PASS |
        elif ' | PASS |' in line or ' | FAIL |' in line:
            parts = line.split(' | ')
            if len(parts) >= 2:
                test_name = parts[0].strip()
                status = parts[1].strip()
                test_results.append({
                    'name': test_name,
                    'description': test_name,
                    'status': status,
                    'full_line': line.strip()
                })
    
    return test_results

# 4. Save test code to file
def save_test_code(test_code):
    # Create generated_tests directory if it doesn't exist
    os.makedirs("generated_tests", exist_ok=True)
    
    # Create timestamped filename
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"generated_tests/ai_generated_api_tests_{timestamp}.robot"
    
    with open(filename, 'w') as f:
        f.write(test_code)
    
    logging.info(f"Robot Framework test code saved to {filename}")
    print(f"💾 AI-generated Robot Framework test saved to: {filename}")
    
    # Print the AI-generated Robot file content for verification
    print("\n" + "="*80)
    print("🤖 AI-GENERATED ROBOT FRAMEWORK TEST FILE CONTENT:")
    print("="*80)
    print(test_code)
    print("="*80)
    print(f"📁 File saved to: {filename}")
    print("="*80)
    
    return filename
    print(f"📁 File saved as: {filename}")
    print("="*80 + "\n")
    
    return filename

# 5. Run test code and collect results
def run_tests(test_file_path):
    logging.info(f"Running Robot Framework tests in {test_file_path}")
    
    # Create latest_test_results directory (remove existing if present)
    output_dir = "latest_test_results"
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    result = subprocess.run([
        "robot", 
        "--outputdir", output_dir,
        "--output", "output.xml",
        "--log", "log.html", 
        "--report", "report.html",
        "--loglevel", "INFO",
        "--consolecolors", "on",
        "--console", "verbose",
        test_file_path
    ], capture_output=True, text=True)
    
    logging.info("Robot Framework test execution completed.")
    
    # Print detailed information about generated reports
    abs_output_dir = os.path.abspath(output_dir)
    abs_test_file = os.path.abspath(test_file_path)
    
    print(f"\n🎯 ROBOT FRAMEWORK TEST EXECUTION COMPLETED")
    print(f"📊 Test reports and logs generated in: {abs_output_dir}")
    print(f"📄 Available files:")
    print(f"   📋 HTML Report: {abs_output_dir}/report.html")
    print(f"   📝 Detailed Log: {abs_output_dir}/log.html") 
    print(f"   📊 XML Output: {abs_output_dir}/output.xml")
    
    print(f"\n🌐 Open in browser:")
    print(f"   📋 Report: file://{abs_output_dir}/report.html")
    print(f"   📝 Log: file://{abs_output_dir}/log.html")
    
    # Parse Robot Framework output for individual test results
    test_results = parse_pytest_output(result.stdout, result.stderr)
    
    # Try to read Robot Framework's output.xml for detailed results
    import xml.etree.ElementTree as ET
    scenarios = []
    status = "unknown"
    
    output_xml_path = os.path.join(output_dir, "output.xml")
    if os.path.exists(output_xml_path):
        try:
            tree = ET.parse(output_xml_path)
            root = tree.getroot()
            
            # Parse test cases from Robot Framework XML
            for test in root.findall(".//test"):
                test_name_xml = test.get("name", "Unknown Test")
                status_elem = test.find("status")
                
                if status_elem is not None:
                    test_status = status_elem.get("status", "UNKNOWN")
                    start_time = status_elem.get("starttime", "")
                    end_time = status_elem.get("endtime", "")
                    
                    scenarios.append({
                        "name": test_name_xml,
                        "outcome": test_status.lower(),
                        "start_time": start_time,
                        "end_time": end_time,
                        "message": status_elem.text or ""
                    })
            
            # Get overall suite status
            suite_status = root.find(".//suite/status")
            if suite_status is not None:
                status = suite_status.get("status", "UNKNOWN")
                
        except Exception as e:
            logging.warning(f"Could not parse Robot Framework XML output: {e}")
    
    return result.stdout, result.stderr, result.returncode, scenarios, status, test_results, output_dir

# 6. Main function to orchestrate all steps
def verify_all_apis(spec_path, base_url=None):
    openapi_spec = read_openapi_spec(spec_path)
    prompt = build_prompt(openapi_spec, base_url)
    # Log the final prompt to a separate file prompt.log for traceability
    try:
        with open("prompt.log", "a") as logf:
            logf.write("\n" + "="*80 + "\nAnthropic LLM Prompt\n" + "="*80 + "\n" + prompt + "\n" + "="*80 + "\n")
    except Exception as e:
        logging.warning(f"Could not write LLM prompt to prompt.log: {e}")
    
    # Ensure api_keywords.robot is available in generated_tests directory
    import shutil
    keywords_src = os.path.join(os.path.dirname(__file__), 'api_keywords.robot')
    keywords_dst = os.path.join('generated_tests', 'api_keywords.robot')
    try:
        shutil.copy2(keywords_src, keywords_dst)
        logging.info(f"Copied api_keywords.robot to {keywords_dst}")
    except Exception as e:
        logging.warning(f"Could not copy api_keywords.robot: {e}")

    test_code = generate_tests_with_llm(prompt)
    logging.info("===== LLM Response (Robot Framework test code) =====")
    print("===== LLM Response (Robot Framework test code) =====")
    print(test_code)
    # Log the AI-generated test code to a file for debugging
    with open("ai_generated_test_case.log", "w") as logf:
        logf.write(test_code)
    logging.info("AI-generated Robot Framework test case written to ai_generated_test_case.log")
    test_code = extract_python_code(test_code)
    test_file = save_test_code(test_code)
    stdout, stderr, exit_code, scenarios, status, test_results, output_dir = run_tests(test_file)
    
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
                'PASS': '✅',
                'FAIL': '❌', 
                'SKIP': '⚠️',
                'ERROR': '🔴'
            }.get(test_result['status'], '❓')
            
            print(f"{status_symbol} {test_result['status']}: {test_result['description']}")
            print(f"   Test: {test_result['name']}")
            
            # Count results
            if test_result['status'] == 'PASS':
                passed_count += 1
            elif test_result['status'] == 'FAIL':
                failed_count += 1
            elif test_result['status'] == 'SKIP':
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
        "output_dir": output_dir,
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        "scenarios": scenarios,
        "status": status,
        "test_results": test_results
    }
    
    logging.info("===== Test Report =====")
    print("\n===== Detailed Robot Framework Test Report =====")
    print("Test Cases from XML report:")
    for s in scenarios:
        outcome_symbol = {
            'pass': '✅',
            'fail': '❌',
            'skip': '⚠️',
            'error': '🔴'
        }.get(s.get('outcome', '').lower(), '❓')
        
        print(f"  {outcome_symbol} {s.get('name', 'Unknown')}: {s.get('outcome', 'Unknown').upper()}")
        if s.get('message'):
            print(f"    Message: {s.get('message')}")
    
    print(f"\nOverall Exit Code: {exit_code}")
    print(f"Overall Status: {status}")
    
    # Print access information for latest_test_results
    print(f"\n🔍 HOW TO ACCESS LOGS AND REPORTS:")
    print(f" Reports Directory: {os.path.abspath(output_dir)}")
    print(f"🌐 Open in browser:")
    print(f"   📋 Report: file://{os.path.abspath(output_dir)}/report.html")
    print(f"   📝 Log:    file://{os.path.abspath(output_dir)}/log.html")
    print(f"   📊 XML:    file://{os.path.abspath(output_dir)}/output.xml")
    
    # Clean up: Delete the AI-generated Robot file after execution
    try:
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n🧹 Cleanup: AI-generated Robot file deleted: {test_file}")
            logging.info(f"Deleted temporary Robot file: {test_file}")
    except Exception as e:
        logging.warning(f"Could not delete temporary Robot file {test_file}: {e}")
    
    if stdout:
        print("\n===== Raw Robot Framework Output =====")
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
