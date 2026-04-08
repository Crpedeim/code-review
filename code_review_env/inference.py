"""
Inference script for the Code Review environment.

Runs an LLM agent against all 3 tasks and emits structured stdout logs
in the [START]/[STEP]/[END] format required by the hackathon.
"""

import json
import os
import sys
import traceback

from openai import OpenAI

# ── Required environment variables ──────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
HF_TOKEN = os.getenv("HF_TOKEN")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

# ── Import environment components ───────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models import ReviewAction
from server.code_review_environment import CodeReviewEnvironment
from tasks import TASKS

ENV_NAME = "code-review-env"
MAX_STEPS = 3  # safety cap per task


def build_prompt(task_description: str, code_snippet: str, filename: str) -> str:
    """Build the review prompt for the LLM."""
    return f"""You are an expert code reviewer. Your job is to review the following Python code and identify all issues.

TASK: {task_description}

FILE: {filename}
```python
{code_snippet}
```

IMPORTANT: Respond with ONLY a JSON array. No markdown, no explanation, no backticks.
Each element must be an object with these exact keys:
- "line": integer (approximate line number)
- "issue": string (short snake_case label like "sql_injection" or "off_by_one_error")
- "severity": string (one of: "low", "medium", "high", "critical")
- "suggestion": string (brief description of the fix)

Example format:
[{{"line": 5, "issue": "missing_null_check", "severity": "high", "suggestion": "Add a check for None before accessing .value"}}]
"""


def run_task(task_name: str) -> float:
    """Run a single task and return the score."""
    env = CodeReviewEnvironment(task_name=task_name)
    obs = env.reset(task_name=task_name)

    print(f"[START] task={task_name} env={ENV_NAME} model={MODEL_NAME}")

    all_rewards = []
    step_num = 0
    final_score = 0.0
    success = False

    try:
        for step_num in range(1, MAX_STEPS + 1):
            # Build prompt and call LLM
            prompt = build_prompt(obs.task_description, obs.code_snippet, obs.filename)

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=4096,
            )

            review_text = response.choices[0].message.content or ""

            # Submit review to environment
            action = ReviewAction(review=review_text)
            obs = env.step(action)

            reward = obs.reward
            done = obs.done
            error = obs.last_action_error

            all_rewards.append(reward)

            error_str = error if error else "null"
            print(
                f"[STEP] step={step_num} "
                f"action=submit_review reward={reward:.2f} "
                f"done={'true' if done else 'false'} "
                f"error={error_str}"
            )

            if done:
                final_score = obs.score
                success = final_score > 0.0
                break

    except Exception as e:
        all_rewards.append(0.0)
        print(
            f"[STEP] step={step_num} "
            f"action=error reward=0.00 done=true "
            f"error={str(e)[:200]}"
        )
        traceback.print_exc(file=sys.stderr)

    rewards_str = ",".join(f"{r:.2f}" for r in all_rewards)
    print(
        f"[END] success={'true' if success else 'false'} "
        f"steps={step_num} score={final_score:.2f} "
        f"rewards={rewards_str}"
    )

    return final_score


def main():
    """Run all tasks."""
    task_names = ["style_review", "bug_hunt", "security_audit"]
    scores = {}

    for task_name in task_names:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Running task: {task_name}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        scores[task_name] = run_task(task_name)

    print("\n--- Summary ---", file=sys.stderr)
    for task, score in scores.items():
        print(f"  {task}: {score:.2f}", file=sys.stderr)
    avg = sum(scores.values()) / len(scores)
    print(f"  Average: {avg:.2f}", file=sys.stderr)


if __name__ == "__main__":
    main()
