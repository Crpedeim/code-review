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

An OpenEnv environment that evaluates LLM agents on Python code review across **6 tasks, 14 randomized code variants, and 117 planted issues**. Supports multi-step interaction with progressive hints. Replicates the technical core of [CodeRabbit](https://coderabbit.ai).

## Environment Overview & Motivation

Code review is the highest-volume daily engineering task — every pull request at every company goes through it. AI-powered code review is a rapidly growing product category (CodeRabbit, Codium, Greptile), but there is no standardized benchmark for evaluating how well LLM agents perform this task.

This environment fills that gap with:

- **14 randomized code variants** — each `reset()` selects a random variant, so the agent never sees the same code twice. This prevents memorization and ensures genuine evaluation.
- **6 tasks** spanning easy to hard across style, logic, concurrency, security, API design, and diff-based review
- **117 planted issues** with ground truth across all variants
- **Multi-step interaction** — agents submit partial reviews, get feedback with severity hints and line-number clues, and refine
- **Red herrings** — correctly-written code mixed in to test false-positive discipline
- **Diff-based PR review** — the closest task to how CodeRabbit actually operates in production

## Action Space

```python
class ReviewAction(Action):
    review: str  # JSON array of findings, or "DONE" to finalize
```

Each finding: `{"line": int, "issue": "snake_case_label", "severity": "low|medium|high|critical", "suggestion": "specific fix"}`

Multi-step flow: `reset() → step(findings) → feedback + hints → step(more) → step("DONE")`

## Observation Space

```python
class ReviewObservation(Observation):
    task_name: str            # Current task
    task_description: str     # What to look for
    code_snippet: str         # Code or diff to review (randomized variant)
    filename: str             # Simulated filename
    feedback: str             # Grader feedback with progressive hints
    score: float              # 0.01-0.99
    done: bool                # Episode complete?
    reward: float             # Reward signal
```

## Tasks, Variants & Difficulty

| Task | Difficulty | Variants | Issues per Variant | Domain |
|------|-----------|----------|-------------------|--------|
| `style_review` | Easy | 3 | 15-17 | Order processing, data pipeline, API client |
| `bug_hunt` | Medium | 3 | 4 | Algorithms, data structures, text processing |
| `concurrency_review` | Med-Hard | 2 | 6-7 | Bank/cache/workers, connection pool/event bus |
| `security_audit` | Hard | 2 | 8 | Flask REST API, file upload service |
| `api_design_review` | Hard | 2 | 8 | User service, payment service |
| `diff_review` | Med-Hard | 2 | 6-7 | Session manager PR, database migration PR |

### Variant Details

**style_review** — V1: order processing module with shipping calculator. V2: data pipeline with ETL processing. V3: API client with HTTP requests. Each has different naming violations, import issues, and missing docstrings. Red herrings: correctly-written utility functions.

**bug_hunt** — V1: classic algorithms (binary search off-by-one, merge missing remainder). V2: data structures (MinStack incorrect pop, LRU cache missing order update). V3: text processing (CSV parser missing last field, wrap text off-by-one). Red herrings: correct flatten_dict, chunk_list, CircularBuffer.

**concurrency_review** — V1: bank account races, deadlock in transfer, unsynchronized cache. V2: connection pool without locking, event bus callback blocking, batch processor race conditions. Red herrings: correctly-implemented RateLimiter, SafeCounter.

**security_audit** — V1: Flask app with SQL injection, XSS, pickle deserialization, command injection. V2: file service with YAML deserialization, SSTI, eval(), arbitrary file deletion, timing attack. Red herrings: correct HMAC webhook verification, secure file serving.

**api_design_review** — V1: user service with cache invalidation bugs, SQL injection in search, CSV injection. V2: payment service with float money, missing status checks, double-charge vulnerability. Red herrings: correctly parameterized queries, proper activity tracking.

**diff_review** — V1: session manager PR replacing secrets.token_urlsafe with predictable MD5, logging tokens. V2: migration helper PR adding shell command injection, removing rollback-on-error. Red herrings: legitimate remember-me feature, schema table extension.

## Reward Design

**Severity weights:** low=1, medium=2, high=3, critical=4

**Suggestion quality bonus:** +0.05 to +0.25 per finding for specific fix suggestions

**False positive penalty:** -0.5 per unmatched finding

**Progressive hints:** Feedback reveals missed severity categories and approximate line locations

**Score:** `max(0.01, min(0.99, (earned + bonus - penalties) / total_possible))`

## Setup & Usage

### Docker
```bash
docker build -t code-review-env .
docker run -p 7860:7860 code-review-env
```

### Inference
```bash
export HF_TOKEN=your_api_key
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4.1-mini
python inference.py
```

### API Endpoints
`/` health check | `/reset` POST | `/step` POST | `/state` GET | `/ws` WebSocket

## Baseline Performance

With `gpt-4.1-mini` (multi-step, 3 iterations):

| Task | Score Range | Notes |
|------|-----------|-------|
| `style_review` | 0.35-0.65 | Many issues; sometimes flags red herrings |
| `bug_hunt` | 0.45-0.75 | V2 (data structures) harder than V1 |
| `concurrency_review` | 0.35-0.60 | Deadlock detection inconsistent |
| `security_audit` | 0.50-0.80 | V2 (SSTI, eval) harder than V1 |
| `api_design_review` | 0.40-0.65 | Float-for-money and double-charge often missed |
| `diff_review` | 0.40-0.70 | Regression detection varies |

## Project Structure

```
code-review-env/
├── inference.py                          # Multi-step inference (6 tasks)
├── models.py                             # Pydantic models
├── openenv.yaml                          # OpenEnv metadata
├── Dockerfile / pyproject.toml / uv.lock
├── server/
│   ├── app.py                            # FastAPI entry point
│   └── code_review_environment.py        # Multi-step engine + random variants
└── tasks/
    ├── __init__.py                       # Registry + grader
    └── variants/
        ├── style_variants.py             # 3 variants (47 issues)
        ├── bug_variants.py               # 3 variants (12 issues)
        ├── concurrency_variants.py       # 2 variants (13 issues)
        ├── security_variants.py          # 2 variants (16 issues)
        ├── api_variants.py               # 2 variants (16 issues)
        └── diff_variants.py              # 2 variants (13 issues)
```
