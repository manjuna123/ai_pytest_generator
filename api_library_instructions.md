# API Keyword Library Documentation

## File: `api_keywords.robot`

This Robot Framework resource file provides reusable keywords for making GET and POST API requests with consistent logging. It is designed to be imported into your test suites or other resource files.

---

## How to Use

1. **Import the Library in Your Robot File**

At the top of your `.robot` test file, add:

```
Resource    api_keywords.robot
Resource    custom_keywords.robot   # (if your custom logging keywords are in a separate file)
Library     RequestsLibrary
```

2. **Call the Keywords in Your Test Cases**

Example:

```
*** Test Cases ***
Get Users Should Return 200
    ${response}=    GET API Request    ${BASE_URL}/users
    Validate Status Code    ${response}    200

Create User
    ${payload}=    Create Dictionary    name=John Doe    email=john@example.com    username=johndoe
    ${response}=    POST API Request    ${BASE_URL}/users    ${payload}
    Validate Status Code    ${response}    201
```

---

## Keyword Details

### `GET API Request`
- **Arguments:**
    - `${url}`: The endpoint URL
    - `${headers}` (optional): Dictionary of headers (default: empty)
    - `${params}` (optional): Dictionary of query parameters (default: empty)
- **Behavior:**
    - Logs the request using `Log API Request`
    - Sends a GET request using RequestsLibrary
    - Logs the response using `Log API Response`
    - Returns the response object

### `POST API Request`
- **Arguments:**
    - `${url}`: The endpoint URL
    - `${payload}`: The request body as a dictionary
    - `${headers}` (optional): Dictionary of headers (default: empty)
- **Behavior:**
    - Logs the request using `Log API Request`
    - Sends a POST request using RequestsLibrary
    - Logs the response using `Log API Response`
    - Returns the response object

---

## Prerequisites
- You must have `RequestsLibrary` imported in your test suite.
- The custom keywords `Log API Request` and `Log API Response` must be available (import from your `custom_keywords.robot` or define in the same file).

---

## Example Import Block
```
*** Settings ***
Library     RequestsLibrary
Resource    api_keywords.robot
Resource    custom_keywords.robot
```
