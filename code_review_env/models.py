"""Typed models for the Code Review environment."""

from typing import List, Optional

from openenv.core.env_server import Action, Observation, State


class ReviewAction(Action):
    """Agent submits a code review."""
    review: str = ""


class ReviewObservation(Observation):
    """What the agent sees."""
    task_name: str = ""
    task_description: str = ""
    code_snippet: str = ""
    filename: str = ""
    language: str = "python"
    feedback: str = ""
    score: float = 0.0
    last_action_error: Optional[str] = None


class ReviewState(State):
    """Internal environment state."""
    task_name: str = ""
    code_snippet: str = ""
    planted_issues: list = []
    agent_findings: list = []
    current_score: float = 0.0
    is_done: bool = False
    max_steps: int = 3
