"""Code Review Environment — OpenEnv implementation."""

import json
import uuid

from openenv.core.env_server import Environment

from models import ReviewAction, ReviewObservation, ReviewState
from tasks import TASKS, grade_review


class CodeReviewEnvironment(Environment):
    """
    An environment where an LLM agent reviews Python code for issues.

    Tasks:
      - style_review (easy): Find style/naming/PEP8 violations
      - bug_hunt (medium): Find logical bugs
      - security_audit (hard): Find security vulnerabilities
    """

    def __init__(self, task_name: str = "style_review"):
        super().__init__()
        self._task_name = task_name
        self._state = ReviewState()

    def reset(self, task_name: str | None = None) -> ReviewObservation:
        if task_name:
            self._task_name = task_name

        task = TASKS[self._task_name]
        self._state = ReviewState(
            episode_id=str(uuid.uuid4()),
            step_count=0,
            task_name=self._task_name,
            code_snippet=task["code"],
            planted_issues=[dict(i) for i in task["issues"]],
            agent_findings=[],
            current_score=0.0,
            is_done=False,
        )

        return ReviewObservation(
            task_name=self._task_name,
            task_description=task["description"],
            code_snippet=task["code"],
            filename=task["filename"],
            language="python",
            feedback="",
            score=0.0,
            done=False,
            reward=0.0,
        )

    def step(self, action: ReviewAction) -> ReviewObservation:
        self._state.step_count += 1

        findings = []
        error_msg = None
        try:
            raw = action.review.strip()
            if "```" in raw:
                for block in raw.split("```"):
                    block = block.strip()
                    if block.startswith("json"):
                        block = block[4:].strip()
                    try:
                        findings = json.loads(block)
                        if isinstance(findings, list):
                            break
                    except (json.JSONDecodeError, ValueError):
                        continue
            else:
                start = raw.find("[")
                end = raw.rfind("]")
                if start != -1 and end != -1:
                    findings = json.loads(raw[start:end + 1])
                else:
                    findings = json.loads(raw)

            if not isinstance(findings, list):
                findings = [findings] if isinstance(findings, dict) else []

        except (json.JSONDecodeError, ValueError) as e:
            error_msg = f"Could not parse review as JSON: {str(e)[:100]}"
            findings = []

        self._state.agent_findings = findings

        score, feedback = grade_review(findings, self._state.planted_issues)
        self._state.current_score = score
        self._state.is_done = True

        if error_msg:
            feedback = f"PARSE ERROR: {error_msg}. {feedback}"

        return ReviewObservation(
            task_name=self._state.task_name,
            task_description=TASKS[self._state.task_name]["description"],
            code_snippet=self._state.code_snippet,
            filename=TASKS[self._state.task_name]["filename"],
            language="python",
            feedback=feedback,
            score=score,
            done=True,
            reward=score,
            last_action_error=error_msg,
        )

    def state(self) -> ReviewState:
        return self._state
