"""
Task definitions for the Code Review environment.

Each task provides:
- code_snippet: The code to review
- planted_issues: Ground truth issues the agent should find
- grader: Scores the agent's findings against ground truth
"""

import json
import re
from typing import List, Dict, Any, Tuple


# ─────────────────────────────────────────────
# TASK 1: Style Review (Easy)
# ─────────────────────────────────────────────

STYLE_REVIEW_CODE = '''
def calculate_total(items,tax):
    x = 0
    for i in items:
        x = x + i["price"] * i["qty"]
    T = x * (1 + tax)
    return T

class order_processor:
    def __init__(self, db):
        self.db=db

    def Process(self, order_id):
        o = self.db.get(order_id)
        if o == None:
            return None
        t = calculate_total(o["items"], o["tax"])
        return {"id": order_id, "total": t}

import os
import sys
import json
import os
'''

STYLE_REVIEW_ISSUES = [
    {"line": 1, "issue": "missing_docstring_function", "severity": "low",
     "description": "Function 'calculate_total' has no docstring"},
    {"line": 2, "issue": "poor_variable_name", "severity": "low",
     "description": "Variable 'x' is not descriptive; use 'subtotal' or similar"},
    {"line": 1, "issue": "missing_space_after_comma", "severity": "low",
     "description": "Missing space after comma in parameters (items,tax)"},
    {"line": 5, "issue": "poor_variable_name", "severity": "low",
     "description": "Variable 'T' is not descriptive; use 'total' or similar"},
    {"line": 8, "issue": "class_naming_convention", "severity": "low",
     "description": "Class 'order_processor' should use CamelCase: 'OrderProcessor'"},
    {"line": 8, "issue": "missing_docstring_class", "severity": "low",
     "description": "Class 'order_processor' has no docstring"},
    {"line": 13, "issue": "method_naming_convention", "severity": "low",
     "description": "Method 'Process' should be lowercase: 'process'"},
    {"line": 15, "issue": "none_comparison", "severity": "medium",
     "description": "Use 'is None' instead of '== None'"},
    {"line": 19, "issue": "duplicate_import", "severity": "low",
     "description": "Duplicate import: 'os' imported twice"},
    {"line": 18, "issue": "unused_import", "severity": "low",
     "description": "Unused imports: 'sys' and 'json' are imported but not used"},
]

# ─────────────────────────────────────────────
# TASK 2: Bug Hunt (Medium)
# ─────────────────────────────────────────────

BUG_HUNT_CODE = '''
def binary_search(arr, target):
    """Search for target in sorted array. Returns index or -1."""
    left, right = 0, len(arr)
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1


def merge_sorted_lists(list1, list2):
    """Merge two sorted lists into one sorted list."""
    result = []
    i, j = 0, 0
    while i < len(list1) and j < len(list2):
        if list1[i] <= list2[j]:
            result.append(list1[i])
            i += 1
        else:
            result.append(list2[j])
            j += 1
    result.extend(list1[i:])
    return result


def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)


def flatten_dict(d, parent_key='', sep='.'):
    """Flatten a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def remove_duplicates(lst):
    """Remove duplicates while preserving order."""
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            result.append(item)
    return result
'''

BUG_HUNT_ISSUES = [
    {"line": 3, "issue": "off_by_one_error", "severity": "high",
     "description": "binary_search: 'right' should be 'len(arr) - 1', not 'len(arr)'. Current code can cause IndexError when arr[mid] accesses out-of-bounds index."},
    {"line": 27, "issue": "missing_remaining_elements", "severity": "high",
     "description": "merge_sorted_lists: Missing 'result.extend(list2[j:])' — elements remaining in list2 are dropped."},
    {"line": 33, "issue": "division_by_zero", "severity": "high",
     "description": "calculate_average: No check for empty list — will raise ZeroDivisionError when numbers is empty."},
    {"line": 52, "issue": "missing_set_add", "severity": "high",
     "description": "remove_duplicates: Never calls 'seen.add(item)' — the 'seen' set stays empty so no duplicates are actually removed."},
]

# ─────────────────────────────────────────────
# TASK 3: Security Audit (Hard)
# ─────────────────────────────────────────────

SECURITY_AUDIT_CODE = '''
import os
import sqlite3
import pickle
import subprocess
import hashlib
from flask import Flask, request, send_file, redirect

app = Flask(__name__)
DB_PATH = "app.db"


def get_db():
    return sqlite3.connect(DB_PATH)


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    hashed = hashlib.md5(password.encode()).hexdigest()
    db = get_db()
    query = f"SELECT * FROM users WHERE username='{username}' AND password_hash='{hashed}'"
    user = db.execute(query).fetchone()
    if user:
        return {"status": "ok", "user_id": user[0]}
    return {"status": "error"}, 401


@app.route("/profile/<user_id>")
def profile(user_id):
    db = get_db()
    user = db.execute(f"SELECT * FROM users WHERE id={user_id}").fetchone()
    return {"username": user[1], "email": user[2]}


@app.route("/export", methods=["POST"])
def export_data():
    data = request.get_data()
    obj = pickle.loads(data)
    return {"result": str(obj)}


@app.route("/download")
def download():
    filename = request.args.get("file")
    filepath = os.path.join("/app/uploads", filename)
    return send_file(filepath)


@app.route("/run-report")
def run_report():
    report_name = request.args.get("name")
    result = subprocess.run(
        f"python reports/{report_name}.py",
        shell=True, capture_output=True, text=True
    )
    return {"output": result.stdout}


@app.route("/redirect")
def open_redirect():
    url = request.args.get("url")
    return redirect(url)


@app.route("/search")
def search():
    q = request.args.get("q", "")
    return f"<h1>Results for: {q}</h1>"
'''

SECURITY_AUDIT_ISSUES = [
    {"line": 21, "issue": "weak_hashing", "severity": "medium",
     "description": "Using MD5 for password hashing — MD5 is cryptographically broken. Use bcrypt or argon2."},
    {"line": 23, "issue": "sql_injection", "severity": "critical",
     "description": "SQL injection via f-string query construction with unsanitized username input. Use parameterized queries."},
    {"line": 33, "issue": "sql_injection", "severity": "critical",
     "description": "SQL injection in profile endpoint — user_id is interpolated directly into query."},
    {"line": 39, "issue": "insecure_deserialization", "severity": "critical",
     "description": "pickle.loads on untrusted user data allows arbitrary code execution."},
    {"line": 45, "issue": "path_traversal", "severity": "critical",
     "description": "Path traversal in download — attacker can use '../' in filename to read arbitrary files."},
    {"line": 51, "issue": "command_injection", "severity": "critical",
     "description": "Command injection via shell=True with user-controlled report_name. Attacker can inject arbitrary shell commands."},
    {"line": 59, "issue": "open_redirect", "severity": "medium",
     "description": "Open redirect — user-controlled URL passed directly to redirect() enables phishing."},
    {"line": 64, "issue": "xss", "severity": "high",
     "description": "Reflected XSS — user input 'q' rendered directly in HTML without escaping."},
]


# ─────────────────────────────────────────────
# TASK REGISTRY
# ─────────────────────────────────────────────

TASKS = {
    "style_review": {
        "description": (
            "Review the following Python code for style issues, naming convention "
            "violations, missing docstrings, unused/duplicate imports, and PEP 8 "
            "violations. Return your findings as a JSON array where each finding has: "
            '"line" (approximate line number), "issue" (short snake_case label), '
            '"severity" (low/medium/high/critical), and "suggestion" (how to fix it).'
        ),
        "code": STYLE_REVIEW_CODE,
        "filename": "order_utils.py",
        "issues": STYLE_REVIEW_ISSUES,
        "difficulty": "easy",
    },
    "bug_hunt": {
        "description": (
            "Review the following Python code for logical bugs that would cause "
            "incorrect results or runtime errors. Focus on off-by-one errors, missing "
            "edge cases, incorrect logic, and missing operations. Return your findings "
            "as a JSON array where each finding has: "
            '"line" (approximate line number), "issue" (short snake_case label), '
            '"severity" (low/medium/high/critical), and "suggestion" (how to fix it).'
        ),
        "code": BUG_HUNT_CODE,
        "filename": "algorithms.py",
        "issues": BUG_HUNT_ISSUES,
        "difficulty": "medium",
    },
    "security_audit": {
        "description": (
            "Perform a security audit of the following Flask web application. Identify "
            "all security vulnerabilities including but not limited to: injection attacks, "
            "insecure deserialization, path traversal, command injection, XSS, and weak "
            "cryptography. For each vulnerability, classify its severity and suggest a "
            "specific fix. Return your findings as a JSON array where each finding has: "
            '"line" (approximate line number), "issue" (short snake_case label), '
            '"severity" (low/medium/high/critical), and "suggestion" (how to fix it).'
        ),
        "code": SECURITY_AUDIT_CODE,
        "filename": "app.py",
        "issues": SECURITY_AUDIT_ISSUES,
        "difficulty": "hard",
    },
}


# ─────────────────────────────────────────────
# GRADER
# ─────────────────────────────────────────────

def _normalize_issue(issue_str: str) -> str:
    """Normalize an issue label for fuzzy matching."""
    return re.sub(r'[^a-z0-9]', '', issue_str.lower())


def _match_finding(finding: dict, planted: dict) -> bool:
    """Check if an agent finding matches a planted issue."""
    # Match by issue label (fuzzy)
    f_issue = _normalize_issue(finding.get("issue", ""))
    p_issue = _normalize_issue(planted.get("issue", ""))

    if not f_issue or not p_issue:
        return False

    # Direct match or substring match
    if f_issue == p_issue or f_issue in p_issue or p_issue in f_issue:
        return True

    # Check description overlap — at least 2 key words match
    f_desc = finding.get("suggestion", "") + " " + finding.get("issue", "")
    p_desc = planted.get("description", "")
    f_words = set(re.findall(r'[a-z]{4,}', f_desc.lower()))
    p_words = set(re.findall(r'[a-z]{4,}', p_desc.lower()))
    overlap = f_words & p_words
    if len(overlap) >= 2:
        return True

    # Line proximity + severity match
    try:
        f_line = int(finding.get("line", -1))
        p_line = int(planted.get("line", -1))
        if abs(f_line - p_line) <= 3 and finding.get("severity", "").lower() == planted.get("severity", "").lower():
            return True
    except (ValueError, TypeError):
        pass

    return False


def grade_review(agent_findings: List[dict], planted_issues: List[dict]) -> Tuple[float, str]:
    """
    Grade the agent's review against planted issues.

    Returns (score, feedback) where score is 0.0-1.0.

    Scoring:
    - Each planted issue found = points (weighted by severity)
    - False positives (findings that don't match any planted issue) = penalty
    - Score clamped to [0.0, 1.0]
    """
    severity_weights = {"low": 1.0, "medium": 2.0, "high": 3.0, "critical": 4.0}

    total_possible = sum(
        severity_weights.get(issue.get("severity", "low"), 1.0)
        for issue in planted_issues
    )

    if total_possible == 0:
        return 1.0, "No issues to find."

    matched_planted = set()
    matched_findings = set()
    earned = 0.0

    for i, finding in enumerate(agent_findings):
        for j, planted in enumerate(planted_issues):
            if j in matched_planted:
                continue
            if _match_finding(finding, planted):
                weight = severity_weights.get(planted.get("severity", "low"), 1.0)
                earned += weight
                matched_planted.add(j)
                matched_findings.add(i)
                break

    # False positive penalty: -0.5 points per unmatched finding, but don't go below 0
    false_positives = len(agent_findings) - len(matched_findings)
    penalty = false_positives * 0.5

    raw_score = (earned - penalty) / total_possible
    score = max(0.0, min(1.0, raw_score))

    # Build feedback
    found_count = len(matched_planted)
    total_count = len(planted_issues)
    missed = [planted_issues[j] for j in range(len(planted_issues)) if j not in matched_planted]

    feedback_parts = [
        f"Found {found_count}/{total_count} issues.",
        f"False positives: {false_positives}.",
        f"Score: {score:.2f}",
    ]
    if missed:
        missed_labels = [m.get("issue", "unknown") for m in missed[:3]]
        feedback_parts.append(f"Missed issues include: {', '.join(missed_labels)}")

    return score, " ".join(feedback_parts)
