"""
Code Review Environment — Task Registry & Grader.

6 tasks with randomized variants (14 total code snippets).
Each reset() selects a random variant, ensuring the environment
never presents the same "quiz" twice.

Tasks:
1. style_review (easy) — 3 variants
2. bug_hunt (medium) — 3 variants
3. concurrency_review (medium-hard) — 2 variants
4. security_audit (hard) — 2 variants
5. api_design_review (hard) — 2 variants
6. diff_review (medium-hard) — 2 variants
"""

import random
import re
from typing import List, Tuple

from tasks.variants.style_variants import VARIANTS as STYLE_VARIANTS
from tasks.variants.bug_variants import VARIANTS as BUG_VARIANTS
from tasks.variants.concurrency_variants import VARIANTS as CONCURRENCY_VARIANTS
from tasks.variants.security_variants import VARIANTS as SECURITY_VARIANTS
from tasks.variants.api_variants import VARIANTS as API_VARIANTS
from tasks.variants.diff_variants import VARIANTS as DIFF_VARIANTS
# from tasks.mutator import generate_buggy_code
# from tasks.variants.dynamic_variants import CLEAN_VARIANTS



# ═══════════════════════════════════════════════
# TASK DESCRIPTIONS (shared across variants)
# ═══════════════════════════════════════════════

TASK_DESCRIPTIONS = {
    "style_review": (
        "Review the following Python code for style issues, naming convention "
        "violations, missing docstrings, unused/duplicate imports, and PEP 8 "
        "violations. Note: some functions in the code are correctly written — "
        "do NOT flag code that follows best practices. "
        "Return your findings as a JSON array where each finding has: "
        '"line" (approximate line number), "issue" (short snake_case label), '
        '"severity" (low/medium/high/critical), and "suggestion" (how to fix it).'
    ),
    "bug_hunt": (
        "Review the following Python code for logical bugs that would cause "
        "incorrect results or runtime errors. Focus on off-by-one errors, missing "
        "edge cases, incorrect logic, and missing operations. "
        "Note: some functions are correctly implemented — only flag actual bugs. "
        "Return your findings as a JSON array where each finding has: "
        '"line" (approximate line number), "issue" (short snake_case label), '
        '"severity" (low/medium/high/critical), and "suggestion" (how to fix it).'
    ),
    "concurrency_review": (
        "Review the following Python threading code for concurrency bugs: race "
        "conditions, deadlocks, missing synchronization, and incorrect shared state "
        "access. Consider what happens when multiple threads call these methods "
        "simultaneously. Note: some classes are correctly synchronized — only flag "
        "actual concurrency issues. "
        "Return your findings as a JSON array where each finding has: "
        '"line" (approximate line number), "issue" (short snake_case label), '
        '"severity" (low/medium/high/critical), and "suggestion" (how to fix it).'
    ),
    "security_audit": (
        "Perform a security audit of the following web application. Identify "
        "all security vulnerabilities including but not limited to: injection attacks, "
        "insecure deserialization, path traversal, command injection, XSS, and weak "
        "cryptography. Note: some endpoints are correctly implemented with proper "
        "security practices — do NOT flag correct code. "
        "For each vulnerability, classify its severity and suggest a "
        "specific fix. Return your findings as a JSON array where each finding has: "
        '"line" (approximate line number), "issue" (short snake_case label), '
        '"severity" (low/medium/high/critical), and "suggestion" (how to fix it).'
    ),
    "api_design_review": (
        "Review the following Python service class for bugs, design flaws, and "
        "potential security issues. Consider: cache consistency, error handling, "
        "SQL safety, data format correctness, resource management, and edge cases. "
        "Note: some methods are correctly implemented — only flag actual issues. "
        "Return your findings as a JSON array where each finding has: "
        '"line" (approximate line number), "issue" (short snake_case label), '
        '"severity" (low/medium/high/critical), and "suggestion" (how to fix it).'
    ),
    "diff_review": (
        "Review the following UNIFIED DIFF of changes to a Python module. "
        "This diff shows what was changed in a pull request. Focus on security "
        "regressions (was secure code replaced with insecure code?), resource leaks, "
        "data exposure, and logic errors introduced by the changes. Lines starting "
        "with '+' are new code, lines starting with '-' are removed code. "
        "Note: some changes are legitimate improvements — only flag actual issues "
        "introduced by the diff. "
        "Return your findings as a JSON array where each finding has: "
        '"line" (approximate line number in the diff), "issue" (short snake_case label), '
        '"severity" (low/medium/high/critical), and "suggestion" (how to fix it).'
    ),
    "dynamic_bug_hunt" : ("Review this complex algorithm for logical bugs, operator mistakes, and off-by-one errors. The bugs are procedurally generated via AST mutation."),
}

TASK_DIFFICULTIES = {
    "style_review": "easy",
    "bug_hunt": "medium",
    "concurrency_review": "medium-hard",
    "security_audit": "hard",
    "api_design_review": "hard",
    "diff_review": "medium-hard",
    "dynamic_bug_hunt": "expert",
}

TASK_VARIANTS = {
    "style_review": STYLE_VARIANTS,
    "bug_hunt": BUG_VARIANTS,
    "concurrency_review": CONCURRENCY_VARIANTS,
    "security_audit": SECURITY_VARIANTS,
    "api_design_review": API_VARIANTS,
    "diff_review": DIFF_VARIANTS,
    "dynamic_bug_hunt": [{"code": "# Generated dynamically", "filename": "core_algorithm.py", "issues": []}],

}


def get_task(task_name: str, variant_index: int = None) -> dict:
    """Get a task configuration, optionally with a specific variant."""
    if task_name not in TASK_VARIANTS:
        raise ValueError(f"Unknown task: {task_name}. Available: {list(TASK_VARIANTS.keys())}")

    if task_name == "dynamic_bug_hunt":
        # import random
        from tasks.variants.dynamic_variants import CLEAN_VARIANTS
        from tasks.mutator import generate_buggy_code
        
        clean_code = random.choice(CLEAN_VARIANTS)
        buggy_code, planted_issues = generate_buggy_code(clean_code, probability=0.5)
        
        return {
            "description": TASK_DESCRIPTIONS[task_name],
            "code": buggy_code,
            "filename": "core_algorithm.py",
            "issues": planted_issues,
            "difficulty": TASK_DIFFICULTIES[task_name],
            "variant_count": "Infinite",
        }

    variants = TASK_VARIANTS[task_name]

    if variant_index is not None:
        variant = variants[variant_index % len(variants)]
    else:
        variant = random.choice(variants)

    return {
        "description": TASK_DESCRIPTIONS[task_name],
        "code": variant["code"],
        "filename": variant["filename"],
        "issues": variant["issues"],
        "difficulty": TASK_DIFFICULTIES[task_name],
        "variant_count": len(variants),
    }


# Backwards-compatible TASKS dict (uses first variant of each task)
TASKS = {}
for _name in TASK_VARIANTS:
    _v = TASK_VARIANTS[_name][0]
    TASKS[_name] = {
        "description": TASK_DESCRIPTIONS[_name],
        "code": _v["code"],
        "filename": _v["filename"],
        "issues": _v["issues"],
        "difficulty": TASK_DIFFICULTIES[_name],
    }


# ═══════════════════════════════════════════════
# GRADER
# ═══════════════════════════════════════════════

def _normalize_issue(issue_str: str) -> str:
    """Normalize an issue label for fuzzy matching."""
    return re.sub(r'[^a-z0-9]', '', issue_str.lower())


def _match_finding(finding: dict, planted: dict) -> bool:
    """
    Check if an agent finding matches a planted issue.

    Uses three strategies:
    1. Normalized label match (exact or substring)
    2. Keyword overlap between descriptions (>= 2 significant words)
    3. Line proximity (within 5 lines) + severity match
    """
    f_issue = _normalize_issue(finding.get("issue", ""))
    p_issue = _normalize_issue(planted.get("issue", ""))

    if not f_issue or not p_issue:
        return False

    # Strategy 1: label match
    if f_issue == p_issue or f_issue in p_issue or p_issue in f_issue:
        return True

    # Strategy 2: keyword overlap
    f_desc = " ".join([
        finding.get("suggestion", ""),
        finding.get("issue", ""),
        finding.get("description", ""),
    ])
    p_desc = planted.get("description", "")
    f_words = set(re.findall(r'[a-z]{4,}', f_desc.lower()))
    p_words = set(re.findall(r'[a-z]{4,}', p_desc.lower()))
    overlap = f_words & p_words
    if len(overlap) >= 2:
        return True

    # Strategy 3: line proximity + severity match
    try:
        f_line = int(finding.get("line", -1))
        p_line = int(planted.get("line", -1))
        if abs(f_line - p_line) <= 5 and \
           finding.get("severity", "").lower() == planted.get("severity", "").lower():
            return True
    except (ValueError, TypeError):
        pass

    return False


def _score_suggestion_quality(finding: dict, planted: dict) -> float:
    """
    Bonus score for quality of fix suggestion.
    Returns 0.0-0.25 bonus based on keyword overlap with ground truth.
    """
    suggestion = finding.get("suggestion", "")
    if not suggestion:
        return 0.0

    description = planted.get("description", "")
    fix_keywords = set(re.findall(r'[a-z]{4,}', description.lower()))
    sugg_keywords = set(re.findall(r'[a-z]{4,}', suggestion.lower()))
    overlap = fix_keywords & sugg_keywords

    if len(overlap) >= 4:
        return 0.25
    elif len(overlap) >= 2:
        return 0.15
    elif len(overlap) >= 1:
        return 0.05
    return 0.0


def grade_review(
    agent_findings: List[dict],
    planted_issues: List[dict],
    step_number: int = 1,
    max_steps: int = 5,
) -> Tuple[float, str]:
    """
    Grade the agent's review against planted issues.

    Returns (score, feedback) where score is in (0.01, 0.99).

    Scoring:
    - Each planted issue found = severity weight (low=1, med=2, high=3, critical=4)
    - Bonus for quality suggestions (0-0.25 per finding)
    - False positives = -0.5 penalty each
    - Score clamped to (0.01, 0.99)
    """
    severity_weights = {"low": 1.0, "medium": 2.0, "high": 3.0, "critical": 4.0}

    total_possible = sum(
        severity_weights.get(issue.get("severity", "low"), 1.0)
        for issue in planted_issues
    )

    if total_possible == 0:
        return 0.50, "No issues to find."

    matched_planted = set()
    matched_findings = set()
    earned = 0.0
    suggestion_bonus = 0.0

    for i, finding in enumerate(agent_findings):
        for j, planted in enumerate(planted_issues):
            if j in matched_planted:
                continue
            if _match_finding(finding, planted):
                weight = severity_weights.get(planted.get("severity", "low"), 1.0)
                earned += weight
                suggestion_bonus += _score_suggestion_quality(finding, planted)
                matched_planted.add(j)
                matched_findings.add(i)
                break

    # False positive penalty
    false_positives = len(agent_findings) - len(matched_findings)
    penalty = false_positives * 0.5

    raw_score = (earned + suggestion_bonus - penalty) / total_possible

    # STRICT (0, 1) range
    score = max(0.01, min(0.99, raw_score))

    # Build feedback
    found_count = len(matched_planted)
    total_count = len(planted_issues)
    missed = [planted_issues[j] for j in range(len(planted_issues)) if j not in matched_planted]

    feedback_parts = [
        f"Found {found_count}/{total_count} issues.",
        f"False positives: {false_positives}.",
        f"Score: {score:.2f}.",
    ]



    if suggestion_bonus > 0:
        feedback_parts.append(f"Suggestion quality bonus: +{suggestion_bonus:.2f}.")

    # =================================================================
    # ADAPTIVE DIFFICULTY SCALING (Dynamic Hints)
    # =================================================================
    percent_found = found_count / total_count if total_count > 0 else 1.0

    # Determine Hint Verbosity (0 = none, 1 = vague, 2 = targeted, 3 = explicit)
    if percent_found >= 0.8:
        # Hard mode: Agent is doing well, no hand-holding
        verbosity = 0
    elif percent_found >= 0.4:
        # Medium mode: Give general area/severity hints
        verbosity = 1
    else:
        # Easy mode: Agent is struggling. Increase help as steps progress.
        verbosity = min(3, step_number)

    if not missed:
        feedback_parts.append("Excellent — all issues identified!")
    elif step_number < max_steps:
        missed_severities = [m.get("severity", "unknown") for m in missed]

        if verbosity == 0:
            feedback_parts.append("HINT: You are very close. Review the code carefully for subtle edge cases.")

        elif verbosity == 1:
            if "critical" in missed_severities or "high" in missed_severities:
                feedback_parts.append("HINT: You are missing high/critical severity issues.")
            else:
                feedback_parts.append("HINT: You are missing medium/low severity issues.")

        elif verbosity >= 2:
            # Provide specific line numbers
            lines = sorted(set(m.get("line", 0) for m in missed[:verbosity]))
            if "critical" in missed_severities:
                feedback_parts.append("HINT: Critical issues remain.")
            feedback_parts.append(f"HINT: Focus your review around lines {', '.join(str(l) for l in lines)}.")

        if verbosity == 3 and step_number >= 3:
            # Maximum help: Reveal the exact category/issue type if they are failing late in the episode
            missed_labels = list(set([m.get("issue", "unknown") for m in missed[:2]]))
            feedback_parts.append(f"HINT: Look specifically for these types of bugs: {', '.join(missed_labels)}")
    else:
        # Final step: Reveal what they missed
        missed_labels = [m.get("issue", "unknown") for m in missed[:3]]
        feedback_parts.append(f"Episode finished. Missed issues: {', '.join(missed_labels)}")

    return score, " ".join(feedback_parts)
