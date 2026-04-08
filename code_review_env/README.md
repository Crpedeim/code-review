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

An OpenEnv environment that evaluates LLM agents on their ability to review Python code — replicating the technical core of AI code review tools like [CodeRabbit](https://coderabbit.ai).

## Motivation

Code review is one of the most common, time-consuming tasks in software engineering. AI-powered code review (as pioneered by CodeRabbit, Codium, and others) is a rapidly growing category. This environment provides a standardized benchmark for evaluating how well LLM agents can:

- Detect style violations and naming issues
- Find logical bugs that cause incorrect behavior
- Identify security vulnerabilities in web applications

## Action Space

The agent submits a **single action** per episode: a JSON array of findings.

```python
ReviewAction(review: str)  # JSON string
```

Each finding is a JSON object:
```json
{
  "line": 5,
  "issue": "sql_injection",
  "severity": "critical",
  "suggestion": "Use parameterized queries instead of f-strings"
}
```

## Observation Space

```python
ReviewObservation(
    task_name: str,          # Current task
    task_description: str,   # What to look for
    code_snippet: str,       # The code to review
    filename: str,           # Simulated filename
    language: str,           # Always "python"
    feedback: str,           # Grader feedback after submission
    score: float,            # 0.0-1.0
    done: bool,              # Episode complete?
    reward: float,           # Same as score
)
```

## Tasks

| Task | Difficulty | Issues | Description |
|------|-----------|--------|-------------|
| `style_review` | Easy | 10 | PEP 8, naming conventions, missing docstrings, unused imports |
| `bug_hunt` | Medium | 4 | Off-by-one errors, missing operations, unhandled edge cases |
| `security_audit` | Hard | 8 | SQL injection, XSS, command injection, path traversal, insecure deserialization |

## Reward Design

- Each planted issue has a **severity weight**: low=1, medium=2, high=3, critical=4
- Finding an issue earns its weight in points
- **False positives** incur a -0.5 penalty each
- Final score = (earned - penalties) / total_possible, clamped to [0.0, 1.0]
- Partial credit: finding 3 of 4 bugs still scores well

## Setup

### Local
```bash
pip install -e .
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Docker
```bash
docker build -t code-review-env .
docker run -p 7860:7860 code-review-env
```

### Run Inference
```bash
export HF_TOKEN=your_token
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4.1-mini
python inference.py
```

## Baseline Scores

| Task | GPT-4.1-mini | Notes |
|------|------------|-------|
| style_review | ~0.60-0.80 | Catches most obvious issues |
| bug_hunt | ~0.50-0.75 | Usually finds off-by-one and division errors |
| security_audit | ~0.55-0.85 | Finds SQL injection and XSS reliably |

## Project Structure

```
code-review-env/
├── inference.py          # Baseline inference script
├── openenv.yaml          # OpenEnv metadata
├── Dockerfile            # Container config
├── pyproject.toml        # Python dependencies
├── models.py             # Pydantic/dataclass models
├── server/
│   ├── app.py            # FastAPI entry point
│   └── code_review_environment.py  # Environment logic
├── tasks/
│   └── __init__.py       # Task definitions + grader
└── README.md
```
