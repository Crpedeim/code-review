"""
Inference script for the Code Review environment.

Runs an LLM agent against all 5 tasks with multi-step review.
The agent submits findings, gets feedback with hints, and can refine.
"""

import json
import os
import sys
import traceback

from openai import OpenAI

# Required environment variables
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
HF_TOKEN = os.getenv("HF_TOKEN")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models import ReviewAction
from server.code_review_environment import CodeReviewEnvironment
from tasks import TASKS

ENV_NAME = "code-review-env"
MAX_STEPS = 3  # use fewer steps for inference speed (env allows up to 5)


def build_initial_prompt(task_description: str, code_snippet: str, filename: str) -> str:
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
- "suggestion": string (brief but specific description of the fix)

Example format:
[{{"line": 5, "issue": "missing_null_check", "severity": "high", "suggestion": "Add a check for None before accessing .value"}}]
"""


def build_refinement_prompt(
    task_description: str, code_snippet: str, filename: str,
    previous_findings: str, feedback: str
) -> str:
    return f"""You are an expert code reviewer continuing your review.

TASK: {task_description}

FILE: {filename}
```python
{code_snippet}
```

YOUR PREVIOUS FINDINGS:
{previous_findings}

GRADER FEEDBACK:
{feedback}

Based on the feedback and hints, find any issues you missed. Focus on areas you haven't covered yet.
Respond with ONLY a JSON array of NEW findings (do not repeat previously found issues).
Use the same format: [{{"line": N, "issue": "label", "severity": "level", "suggestion": "fix"}}]
If you believe you've found everything, respond with: DONE
"""


def run_task(task_name: str) -> float:
    env = CodeReviewEnvironment(task_name=task_name)
    obs = env.reset(task_name=task_name)

    print(f"[START] task={task_name} env={ENV_NAME} model={MODEL_NAME}")

    all_rewards = []
    step_num = 0
    final_score = 0.01
    success = False
    accumulated_findings = []

    try:
        for step_num in range(1, MAX_STEPS + 1):
            # Build prompt
            if step_num == 1:
                prompt = build_initial_prompt(
                    obs.task_description, obs.code_snippet, obs.filename
                )
            else:
                prompt = build_refinement_prompt(
                    obs.task_description, obs.code_snippet, obs.filename,
                    json.dumps(accumulated_findings, indent=2),
                    obs.feedback,
                )

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=4096,
            )

            review_text = response.choices[0].message.content or ""

            # Track findings for refinement prompt
            if review_text.strip().upper() != "DONE":
                try:
                    start = review_text.find("[")
                    end = review_text.rfind("]")
                    if start != -1 and end != -1:
                        new_findings = json.loads(review_text[start:end + 1])
                        if isinstance(new_findings, list):
                            accumulated_findings.extend(new_findings)
                except (json.JSONDecodeError, ValueError):
                    pass

            action = ReviewAction(review=review_text)
            obs = env.step(action)

            reward = obs.reward
            done = obs.done
            error = obs.last_action_error

            all_rewards.append(reward)

            error_str = error if error else "null"
            action_str = "submit_review" if review_text.strip().upper() != "DONE" else "finalize"
            print(
                f"[STEP] step={step_num} "
                f"action={action_str} reward={reward:.2f} "
                f"done={'true' if done else 'false'} "
                f"error={error_str}"
            )

            if done:
                final_score = obs.score
                success = final_score > 0.0
                break

    except Exception as e:
        all_rewards.append(0.01)
        print(
            f"[STEP] step={step_num} "
            f"action=error reward=0.01 done=true "
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
    task_names = ["style_review", "bug_hunt", "concurrency_review", "security_audit", "api_design_review", "diff_review",
        "dynamic_bug_hunt"]
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
