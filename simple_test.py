#!/usr/bin/env python3
import requests
import json

BASE_URL = "https://feature-test-suite-1.preview.emergentagent.com"

try:
    response = requests.get(f"{BASE_URL}/api/health", timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")