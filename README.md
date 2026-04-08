---
title: Code Review Env
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: docker
app_file: server/app.py
pinned: false
tags:
  - openenv
---

# Code Review Environment (OpenEnv)

An OpenEnv environment that evaluates LLM agents on their ability to review Python code for real-world issues — style violations, logical bugs, and security vulnerabilities. This replicates the technical core of AI-powered code review tools like [CodeRabbit](https://coderabbit.ai), [Codium](https://www.codium.ai/), and [Greptile](https://www.greptile.com/).

## Environment Overview & Motivation

Code review is one of the highest-volume, highest-stakes daily tasks in software engineering. Every pull request at every company goes through it. Studies consistently show that code review catches 60–90% of defects before they reach production, yet it remains a manual bottleneck — senior engineers spend 5–10 hours per week on reviews.

AI-powered code review is now a rapidly growing product category. Tools like CodeRabbit process millions of PRs per month by having LLMs analyze diffs and surface issues automatically. But there is **no standardized benchmark** for evaluating how well an LLM agent actually performs this task.

This environment fills that gap. It presents an agent with Python code containing **known, planted issues** across three difficulty levels, and grades the agent's ability to identify them — with partial credit, severity weighting, and false-positive penalties. This creates a rich reward signal suitable for RL training and agent evaluation.

**Why this matters for the RL/agent community:**
- Code review is a real task with measurable ground truth (planted issues with known locations and types)
- The grading function provides dense reward signal, not just binary pass/fail
- Difficulty scales naturally from style linting to security auditing
- Directly evaluates a capability that production AI tools need

## Action Space

The agent submits a single `ReviewAction` per episode containing a JSON-encoded array of findings.

```python
class ReviewAction(Action):
    review: str  # JSON string containing array of findings
```

Each finding in the JSON array must have these fields:

| Field | Type | Description |
|-------|------|-------------|
| `line` | int | Approximate line number of the issue |
| `issue` | str | Short snake_case label (e.g., `sql_injection`, `off_by_one_error`) |
| `severity` | str | One of: `low`, `medium`, `high`, `critical` |
| `suggestion` | str | Brief description of how to fix the issue |

Example action payload:
```json
[
  {"line": 23, "issue": "sql_injection", "severity": "critical", "suggestion": "Use parameterized queries instead of f-strings"},
  {"line": 45, "issue": "path_traversal", "severity": "critical", "suggestion": "Validate and sanitize the filename, use os.path.realpath to resolve symlinks"}
]
```

## Observation Space

On `reset()`, the agent receives the code to review along with task instructions. After `step()`, the agent receives grading feedback.

```python
class ReviewObservation(Observation):
    task_name: str            # Current task identifier
    task_description: str     # Instructions: what to look for
    code_snippet: str         # The Python code to review
    filename: str             # Simulated filename for context
    language: str             # Always "python"
    feedback: str             # Grader feedback after submission
    score: float              # Final score 0.0–1.0
    done: bool                # Whether the episode is complete
    reward: float             # Reward signal (same as score)
    last_action_error: str    # Parse errors if JSON was malformed, null otherwise
```

## Tasks & Difficulty Levels

### Task 1: `style_review` (Easy)

The agent reviews a Python module (`order_utils.py`) containing 10 planted style issues including PEP 8 violations, poor variable naming, missing docstrings, incorrect naming conventions, `== None` comparisons, duplicate imports, and unused imports.

**What makes it easy:** Issues are surface-level and follow well-known Python conventions. Any model familiar with PEP 8 should catch most of them.

| Property | Value |
|----------|-------|
| Planted issues | 10 |
| Severity breakdown | 9 low, 1 medium |
| Max possible score | 1.0 |

### Task 2: `bug_hunt` (Medium)

The agent reviews an algorithms module (`algorithms.py`) containing 4 planted logical bugs across functions for binary search, list merging, averaging, and deduplication. Bugs include off-by-one errors, missing operations, and unhandled edge cases.

**What makes it medium:** Bugs require understanding program logic and reasoning about edge cases (empty lists, boundary indices). The agent must trace execution mentally to find them.

| Property | Value |
|----------|-------|
| Planted issues | 4 |
| Severity breakdown | 4 high |
| Max possible score | 1.0 |

### Task 3: `security_audit` (Hard)

The agent audits a Flask web application (`app.py`) containing 8 planted security vulnerabilities: SQL injection (2 instances), insecure deserialization, path traversal, command injection, XSS, open redirect, and weak password hashing.

**What makes it hard:** Requires knowledge of web security patterns (OWASP Top 10), understanding how user input flows through the application, and recognizing that seemingly innocuous code patterns can be exploitable. The agent must also correctly classify severity levels.

| Property | Value |
|----------|-------|
| Planted issues | 8 |
| Severity breakdown | 2 medium, 1 high, 5 critical |
| Max possible score | 1.0 |

## Reward Design

The reward function provides meaningful signal across the full trajectory:

**Severity-weighted scoring:** Each issue has a weight based on severity — low (1 point), medium (2), high (3), critical (4). Finding a critical SQL injection is worth 4× more than catching a missing docstring.

**Fuzzy matching:** The grader uses three matching strategies to avoid penalizing valid findings that use different terminology than the ground truth: (1) normalized issue label matching, (2) keyword overlap in descriptions, and (3) line proximity combined with severity match.

**False positive penalty:** Each finding that doesn't match any planted issue incurs a −0.5 point penalty. This prevents agents from gaming the system by submitting every possible issue type.

**Final score:** `max(0.0, min(1.0, (earned − penalties) / total_possible))`

This design ensures that partial progress is always rewarded — finding 3 out of 4 bugs gives a strong score, while spamming false positives is penalized.

## Setup & Usage

### Prerequisites
- Python 3.10+
- Docker (for containerized deployment)

### Local Development
```bash
git clone https://huggingface.co/spaces/Crpedeim/code_review_env
cd code_review_env
pip install openenv-core fastapi uvicorn pydantic openai
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Docker
```bash
docker build -t code-review-env .
docker run -p 7860:7860 code-review-env
```

### Running Inference
```bash
export HF_TOKEN=your_api_key
export API_BASE_URL=https://api.openai.com/v1   # or any OpenAI-compatible endpoint
export MODEL_NAME=gpt-4.1-mini
python inference.py
```

The inference script runs all 3 tasks sequentially and emits structured logs in the required `[START]`/`[STEP]`/`[END]` format.

### API Endpoints

Once running, the server exposes the standard OpenEnv interface:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/reset` | POST | Reset environment, returns initial observation |
| `/step` | POST | Submit a review action, returns graded observation |
| `/state` | GET | Returns current internal state |
| `/health` | GET | Server health status |
| `/ws` | WebSocket | OpenEnv WebSocket protocol |

## Baseline Performance Scores

Scores from running the baseline inference script with `gpt-4.1-mini`:

| Task | Score | Notes |
|------|-------|-------|
| `style_review` | 0.60–0.80 | Reliably catches naming issues and missing docstrings; sometimes misses duplicate/unused imports |
| `bug_hunt` | 0.50–0.75 | Finds off-by-one and division-by-zero consistently; the missing `seen.add()` is harder |
| `security_audit` | 0.55–0.85 | SQL injection and XSS found reliably; insecure deserialization and open redirect are sometimes missed |

**Average baseline score: ~0.60**

Frontier models (GPT-4o, Claude Sonnet) score higher, particularly on `security_audit`. The hard task is designed to genuinely challenge even frontier models.

## Project Structure

```
code-review-env/
├── inference.py                        # Baseline inference script (required)
├── openenv.yaml                        # OpenEnv metadata
├── Dockerfile                          # Container configuration
├── pyproject.toml                      # Python project & dependencies
├── models.py                           # Pydantic models (Action, Observation, State)
├── README.md                           # This file
├── server/
│   ├── __init__.py
│   ├── app.py                          # FastAPI entry point
│   └── code_review_environment.py      # Core environment (reset/step/state)
└── tasks/
    └── __init__.py                     # Task definitions, planted issues & grader
```
