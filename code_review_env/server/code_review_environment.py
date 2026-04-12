"""Code Review Environment — OpenEnv implementation.

Multi-step code review with randomized variants.
Each reset() selects a random variant for the given task,
so the agent never sees the exact same code twice.
"""

import json
import uuid

from openenv.core.env_server import Environment

from models import ReviewAction, ReviewObservation, ReviewState
from tasks import get_task, grade_review, TASK_VARIANTS


class CodeReviewEnvironment(Environment):
    """
    An environment where an LLM agent reviews Python code for issues.

    Features:
    - 6 tasks spanning easy to hard
    - 14 randomized code variants (different code each reset)
    - Multi-step interaction with progressive hints
    - Red herrings (correct code mixed in)
    - Severity-weighted grading with suggestion quality bonus
    """

    MAX_STEPS = 5

    def __init__(self, task_name: str = "style_review"):
        super().__init__()
        self._task_name = task_name
        self._current_task = None
        self._state = ReviewState()

    def reset(self, task_name: str | None = None) -> ReviewObservation:
        if task_name:
            self._task_name = task_name

        # Random variant selection — different code each episode
        task = get_task(self._task_name)
        self._current_task = task

        self._state = ReviewState(
            episode_id=str(uuid.uuid4()),
            step_count=0,
            task_name=self._task_name,
            code_snippet=task["code"],
            planted_issues=[dict(i) for i in task["issues"]],
            agent_findings=[],
            current_score=0.01,
            is_done=False,
            max_steps=self.MAX_STEPS,
        )

        return ReviewObservation(
            task_name=self._task_name,
            task_description=task["description"],
            code_snippet=task["code"],
            filename=task["filename"],
            language="python",
            feedback=f"Submit your code review findings as a JSON array. You have up to {self.MAX_STEPS} steps to refine your review. Send DONE when finished. (Variant pool: {task['variant_count']} variants)",
            score=0.01,
            done=False,
            reward=0.01,
        )

    def _parse_findings(self, raw: str) -> tuple:
        """Parse JSON findings from agent response. Returns (findings, error)."""
        findings = []
        error_msg = None
        try:
            raw = raw.strip()
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

        return findings, error_msg

    def step(self, action: ReviewAction) -> ReviewObservation:
        self._state.step_count += 1
        task = self._current_task

        raw = action.review.strip()
        is_final = (
            raw.upper() == "DONE" or
            self._state.step_count >= self._state.max_steps
        )

        error_msg = None

        if raw.upper() != "DONE":
            findings, error_msg = self._parse_findings(raw)
            if findings:
                existing_issues = {f.get("issue", "") for f in self._state.agent_findings}
                for f in findings:
                    if f.get("issue", "") not in existing_issues:
                        self._state.agent_findings.append(f)
                        existing_issues.add(f.get("issue", ""))

        score, feedback = grade_review(
            self._state.agent_findings,
            self._state.planted_issues,
            step_number=self._state.step_count,
            max_steps=self._state.max_steps,
        )
        self._state.current_score = score

        if is_final:
            self._state.is_done = True

        if error_msg:
            feedback = f"PARSE ERROR: {error_msg}. {feedback}"

        return ReviewObservation(
            task_name=self._state.task_name,
            task_description=task["description"],
            code_snippet=self._state.code_snippet,
            filename=task["filename"],
            language="python",
            feedback=feedback,
            score=score,
            done=self._state.is_done,
            reward=score,
            last_action_error=error_msg,
        )

    def state(self) -> ReviewState:
        return self._state
