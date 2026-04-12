# filepath: code_review_env/tests/test_environment.py
import pytest
from server.code_review_environment import CodeReviewEnvironment
from models import ReviewAction

@pytest.fixture
def env():
    return CodeReviewEnvironment(task_name="style_review")

def test_env_reset_returns_safe_bounds(env):
    """Proves that environment reset state complies with (0, 1) OpenEnv bounds."""
    obs = env.reset("style_review")
    
    assert obs.score > 0.0, f"Initial score must be > 0.0, got {obs.score}"
    assert obs.score < 1.0, f"Initial score must be < 1.0, got {obs.score}"
    assert obs.reward > 0.0, f"Initial reward must be > 0.0, got {obs.reward}"
    
    state = env.state()
    assert state.current_score > 0.0, "Internal state score must be bounded"

def test_env_step_processes_valid_json(env):
    """Tests if the environment successfully parses JSON and updates step count."""
    env.reset("style_review")
    
    # Send a valid JSON action mimicking the LLM
    action = ReviewAction(review='[{"line": 4, "issue": "duplicate_import", "severity": "low", "suggestion": "remove"}]')
    obs = env.step(action)
    
    state = env.state()
    assert state.step_count == 1
    assert not obs.done
    assert "PARSE ERROR" not in obs.feedback

def test_env_handles_invalid_json_gracefully(env):
    """Ensures the LLM output parser doesn't crash on bad formatting."""
    env.reset("style_review")
    
    # Send garbage text instead of JSON
    action = ReviewAction(review="I think the bug is on line 4.")
    obs = env.step(action)
    
    assert "PARSE ERROR" in obs.feedback
    assert obs.last_action_error is not None

def test_env_done_command(env):
    """Tests early termination using the DONE keyword."""
    env.reset("style_review")
    
    action = ReviewAction(review="DONE")
    obs = env.step(action)
    
    assert obs.done is True