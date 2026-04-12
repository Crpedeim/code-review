# filepath: code_review_env/tests/test_grader.py
import pytest
from tasks import grade_review

@pytest.fixture
def sample_planted_issues():
    return [
        {"line": 10, "issue": "sql_injection", "severity": "critical", "description": "SQLi here"},
        {"line": 20, "issue": "unused_import", "severity": "low", "description": "Unused os"},
    ]

def test_grader_minimum_bound_is_strictly_greater_than_zero(sample_planted_issues):
    """Proves the grader never returns 0.0, passing OpenEnv validation."""
    # Agent finds nothing
    agent_findings = []
    score, feedback = grade_review(agent_findings, sample_planted_issues)
    assert score == 0.01, f"Expected 0.01 minimum bound, got {score}"

def test_grader_maximum_bound_is_strictly_less_than_one(sample_planted_issues):
    """Proves the grader never returns 1.0, passing OpenEnv validation."""
    # Agent finds exactly the issues
    agent_findings = sample_planted_issues 
    score, feedback = grade_review(agent_findings, sample_planted_issues)
    assert score == 0.99, f"Expected 0.99 maximum bound, got {score}"

def test_false_positive_penalty(sample_planted_issues):
    """Ensures agents are penalized for hallucinating issues."""
    agent_findings = [
        {"line": 10, "issue": "sql_injection", "severity": "critical"}, # Correct
        {"line": 99, "issue": "hallucinated_bug", "severity": "high"}   # False positive
    ]
    # Critical weight = 4.0. False positive penalty = -0.5. Total possible = 5.0
    # Score = (4.0 - 0.5) / 5.0 = 0.7
    score, feedback = grade_review(agent_findings, sample_planted_issues)
    assert score < 0.8, "Score should reflect false positive penalty"
    assert "False positives: 1" in feedback

def test_adaptive_hints_easy_mode(sample_planted_issues):
    """Ensures struggling agents get explicit hints at later steps."""
    score, feedback = grade_review([], sample_planted_issues, step_number=3, max_steps=5)
    # 0% found at step 3 should trigger verbosity level 3 (explicit category hints)
    assert "Look specifically for these types of bugs" in feedback

def test_adaptive_hints_hard_mode(sample_planted_issues):
    """Ensures high-performing agents don't get hand-holding."""
    agent_findings = [{"line": 10, "issue": "sql_injection", "severity": "critical"}]
    # Found 1/2 (50% of issues, but 80% of weight, let's assume count-based check)
    # The agent found 50% so it's in medium mode
    score, feedback = grade_review(agent_findings, sample_planted_issues, step_number=2)
    assert "missing" in feedback.lower()