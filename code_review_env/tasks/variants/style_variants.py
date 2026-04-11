"""Style review task variants — 3 different code domains."""

VARIANT_1 = {
    "filename": "order_utils.py",
    "code": '''
import os
import sys
import json
import os
import re
from typing import List, Dict, Optional
from datetime import datetime


def calculate_total(items,tax):
    x = 0
    for i in items:
        x = x + i["price"] * i["qty"]
    T = x * (1 + tax)
    return T


def apply_Discount(price, discount_percent):
    d = price * discount_percent / 100
    Final = price - d
    return Final


class order_processor:
    def __init__(self, db):
        self.db=db
        self.Logger = None

    def Process(self, order_id):
        o = self.db.get(order_id)
        if o == None:
            return None
        t = calculate_total(o["items"], o["tax"])
        return {"id": order_id, "total": t}

    def processRefund(self, order_id, reason):
        o = self.db.get(order_id)
        if o == None:
            return False
        o["status"] = "refunded"
        self.db.save(o)
        return True


class ShippingCalculator:
    """Calculate shipping costs based on weight and destination."""

    RATE_PER_KG = 5.0
    EXPRESS_MULTIPLIER = 2.5

    def __init__(self, base_rate: float = 3.0):
        self.base_rate = base_rate

    def calculate(self, weight_kg: float, express: bool = False) -> float:
        """Calculate total shipping cost.

        Args:
            weight_kg: Package weight in kilograms.
            express: Whether to use express shipping.

        Returns:
            Total shipping cost as a float.
        """
        cost = self.base_rate + (weight_kg * self.RATE_PER_KG)
        if express:
            cost *= self.EXPRESS_MULTIPLIER
        return round(cost, 2)
''',
    "issues": [
        {"line": 4, "issue": "duplicate_import", "severity": "low",
         "description": "Duplicate import: 'os' imported twice"},
        {"line": 3, "issue": "unused_import", "severity": "low",
         "description": "Unused imports: 'sys' and 'json' are imported but not used"},
        {"line": 14, "issue": "missing_docstring_function", "severity": "low",
         "description": "Function 'calculate_total' has no docstring"},
        {"line": 15, "issue": "poor_variable_name", "severity": "low",
         "description": "Variable 'x' is not descriptive; use 'subtotal' or similar"},
        {"line": 14, "issue": "missing_space_after_comma", "severity": "low",
         "description": "Missing space after comma in parameters (items,tax)"},
        {"line": 18, "issue": "poor_variable_name", "severity": "low",
         "description": "Variable 'T' is not descriptive; use 'total' or similar"},
        {"line": 22, "issue": "function_naming_convention", "severity": "low",
         "description": "Function 'apply_Discount' should be lowercase snake_case: 'apply_discount'"},
        {"line": 22, "issue": "missing_docstring_function", "severity": "low",
         "description": "Function 'apply_Discount' has no docstring"},
        {"line": 24, "issue": "poor_variable_name", "severity": "low",
         "description": "Variables 'd' and 'Final' are not descriptive; 'Final' violates snake_case"},
        {"line": 28, "issue": "class_naming_convention", "severity": "low",
         "description": "Class 'order_processor' should use CamelCase: 'OrderProcessor'"},
        {"line": 28, "issue": "missing_docstring_class", "severity": "low",
         "description": "Class 'order_processor' has no docstring"},
        {"line": 31, "issue": "attribute_naming_convention", "severity": "low",
         "description": "Attribute 'self.Logger' should be lowercase: 'self.logger'"},
        {"line": 33, "issue": "method_naming_convention", "severity": "low",
         "description": "Method 'Process' should be lowercase: 'process'"},
        {"line": 35, "issue": "none_comparison", "severity": "medium",
         "description": "Use 'is None' instead of '== None'"},
        {"line": 40, "issue": "method_naming_convention", "severity": "low",
         "description": "Method 'processRefund' should be snake_case: 'process_refund'"},
        {"line": 40, "issue": "missing_docstring_method", "severity": "low",
         "description": "Method 'processRefund' has no docstring"},
        {"line": 42, "issue": "none_comparison", "severity": "medium",
         "description": "Second instance of '== None'; use 'is None'"},
    ],
}

VARIANT_2 = {
    "filename": "data_pipeline.py",
    "code": '''
import csv
import os
import json
import csv
from datetime import datetime


def loadData(filepath):
    f = open(filepath, "r")
    d = json.load(f)
    return d


class data_cleaner:
    def __init__(self,config):
        self.Config = config
        self.errCount = 0

    def cleanRow(self, row):
        r = {}
        for k in row:
            v = row[k]
            if v == None:
                continue
            if type(v) == str:
                v = v.strip()
            r[k] = v
        return r

    def ProcessBatch(self, rows):
        Results = []
        for row in rows:
            cleaned = self.cleanRow(row)
            Results.append(cleaned)
        return Results


def write_output(data, path, fmt="json"):
    """Write processed data to file in specified format.

    Args:
        data: List of dictionaries to write.
        path: Output file path.
        fmt: Output format, either 'json' or 'csv'.
    """
    if fmt == "json":
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    elif fmt == "csv":
        if not data:
            return
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)


def validate_schema(row: dict, required_fields: list) -> bool:
    """Check that all required fields exist and are non-empty."""
    for field in required_fields:
        if field not in row or not row[field]:
            return False
    return True
''',
    "issues": [
        {"line": 4, "issue": "duplicate_import", "severity": "low",
         "description": "Duplicate import: 'csv' imported twice"},
        {"line": 9, "issue": "function_naming_convention", "severity": "low",
         "description": "Function 'loadData' should be snake_case: 'load_data'"},
        {"line": 9, "issue": "missing_docstring_function", "severity": "low",
         "description": "Function 'loadData' has no docstring"},
        {"line": 10, "issue": "resource_leak", "severity": "medium",
         "description": "File opened with open() but never closed. Use 'with' statement"},
        {"line": 11, "issue": "poor_variable_name", "severity": "low",
         "description": "Variables 'f' and 'd' are not descriptive"},
        {"line": 15, "issue": "class_naming_convention", "severity": "low",
         "description": "Class 'data_cleaner' should use CamelCase: 'DataCleaner'"},
        {"line": 15, "issue": "missing_docstring_class", "severity": "low",
         "description": "Class 'data_cleaner' has no docstring"},
        {"line": 16, "issue": "missing_space_after_comma", "severity": "low",
         "description": "Missing space after comma in __init__(self,config)"},
        {"line": 17, "issue": "attribute_naming_convention", "severity": "low",
         "description": "Attribute 'self.Config' should be lowercase: 'self.config'"},
        {"line": 20, "issue": "method_naming_convention", "severity": "low",
         "description": "Method 'cleanRow' should be snake_case: 'clean_row'"},
        {"line": 20, "issue": "missing_docstring_method", "severity": "low",
         "description": "Method 'cleanRow' has no docstring"},
        {"line": 25, "issue": "none_comparison", "severity": "medium",
         "description": "Use 'is None' instead of '== None'"},
        {"line": 26, "issue": "type_comparison", "severity": "medium",
         "description": "Use isinstance(v, str) instead of type(v) == str"},
        {"line": 31, "issue": "method_naming_convention", "severity": "low",
         "description": "Method 'ProcessBatch' should be snake_case: 'process_batch'"},
        {"line": 32, "issue": "poor_variable_name", "severity": "low",
         "description": "Variable 'Results' should be lowercase: 'results'"},
    ],
}

VARIANT_3 = {
    "filename": "api_client.py",
    "code": '''
import requests
import time
import json
import logging
import requests


def makeRequest(url, Method="GET", data=None, Headers={}):
    r = requests.request(Method, url, json=data, headers=Headers)
    return r.json()


class apiClient:
    BASE = "https://api.example.com"

    def __init__(self, apiKey):
        self.Key = apiKey
        self.session = requests.Session()

    def GetUser(self, userId):
        url = f"{self.BASE}/users/{userId}"
        r = self.session.get(url, headers={"Authorization": f"Bearer {self.Key}"})
        if r.status_code == 200:
            return r.json()
        return None

    def updateUser(self, userId, Data):
        url = f"{self.BASE}/users/{userId}"
        r = self.session.put(url, json=Data, headers={"Authorization": f"Bearer {self.Key}"})
        return r.status_code == 200


class ResponseParser:
    """Parse and validate API responses."""

    def __init__(self, strict: bool = True):
        self.strict = strict

    def parse(self, response: dict) -> dict:
        """Extract data from a standard API response envelope.

        Args:
            response: Raw API response dictionary.

        Returns:
            The 'data' field from the response, or empty dict.
        """
        if "data" in response:
            return response["data"]
        if not self.strict:
            return response
        return {}

    def is_error(self, response: dict) -> bool:
        """Check if response indicates an error."""
        return response.get("status") == "error" or "error" in response
''',
    "issues": [
        {"line": 5, "issue": "duplicate_import", "severity": "low",
         "description": "Duplicate import: 'requests' imported twice"},
        {"line": 8, "issue": "function_naming_convention", "severity": "low",
         "description": "Function 'makeRequest' should be snake_case: 'make_request'"},
        {"line": 8, "issue": "missing_docstring_function", "severity": "low",
         "description": "Function 'makeRequest' has no docstring"},
        {"line": 8, "issue": "mutable_default_argument", "severity": "high",
         "description": "Mutable default argument Headers={}. Use None and set inside function."},
        {"line": 8, "issue": "parameter_naming_convention", "severity": "low",
         "description": "Parameters 'Method' and 'Headers' should be lowercase"},
        {"line": 9, "issue": "poor_variable_name", "severity": "low",
         "description": "Variable 'r' is not descriptive; use 'response'"},
        {"line": 13, "issue": "class_naming_convention", "severity": "low",
         "description": "Class 'apiClient' should use CamelCase: 'ApiClient'"},
        {"line": 13, "issue": "missing_docstring_class", "severity": "low",
         "description": "Class 'apiClient' has no docstring"},
        {"line": 17, "issue": "parameter_naming_convention", "severity": "low",
         "description": "Parameter 'apiKey' should be snake_case: 'api_key'"},
        {"line": 18, "issue": "attribute_naming_convention", "severity": "low",
         "description": "Attribute 'self.Key' should be lowercase: 'self.key'"},
        {"line": 21, "issue": "method_naming_convention", "severity": "low",
         "description": "Method 'GetUser' should be snake_case: 'get_user'"},
        {"line": 21, "issue": "missing_docstring_method", "severity": "low",
         "description": "Method 'GetUser' has no docstring"},
        {"line": 28, "issue": "method_naming_convention", "severity": "low",
         "description": "Method 'updateUser' should be snake_case: 'update_user'"},
        {"line": 28, "issue": "missing_docstring_method", "severity": "low",
         "description": "Method 'updateUser' has no docstring"},
        {"line": 28, "issue": "parameter_naming_convention", "severity": "low",
         "description": "Parameter 'Data' should be lowercase: 'data'"},
    ],
}

VARIANTS = [VARIANT_1, VARIANT_2, VARIANT_3]
