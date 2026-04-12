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

- **14 static variants + INFINITE dynamic variants** — Uses an AST mutator engine to procedurally generate subtle logic and off-by-one errors in complex algorithms (A* Pathfinding, TTL Caches).
- **7 tasks** spanning easy to expert across style, logic, concurrency, security, API design, diff-based review, and dynamic adversarial generation.
- **Adaptive Difficulty** — Grader hints scale dynamically based on the agent's real-time accuracy, forcing high-performing agents to find bugs independently while supporting struggling agents.
- **Multi-step interaction** — agents submit partial reviews, get feedback with severity hints and line-number clues, and refine.
- **Red herrings** — correctly-written code mixed in to test false-positive discipline.
- **Production-Ready Test Suite** — Comprehensive `pytest` coverage verifying mathematical bounds, state transitions, and edge-case exception handling.

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
| `dynamic_bug_hunt` | Expert | Infinite | Random | Procedurally mutated algorithms (A*, Caches) |

### Variant Details

**style_review** — V1: order processing module with shipping calculator. V2: data pipeline with ETL processing. V3: API client with HTTP requests. Each has different naming violations, import issues, and missing docstrings. Red herrings: correctly-written utility functions.

**bug_hunt** — V1: classic algorithms (binary search off-by-one, merge missing remainder). V2: data structures (MinStack incorrect pop, LRU cache missing order update). V3: text processing (CSV parser missing last field, wrap text off-by-one). Red herrings: correct flatten_dict, chunk_list, CircularBuffer.

**concurrency_review** — V1: bank account races, deadlock in transfer, unsynchronized cache. V2: connection pool without locking, event bus callback blocking, batch processor race conditions. Red herrings: correctly-implemented RateLimiter, SafeCounter.

**security_audit** — V1: Flask app with SQL injection, XSS, pickle deserialization, command injection. V2: file service with YAML deserialization, SSTI, eval(), arbitrary file deletion, timing attack. Red herrings: correct HMAC webhook verification, secure file serving.

**api_design_review** — V1: user service with cache invalidation bugs, SQL injection in search, CSV injection. V2: payment service with float money, missing status checks, double-charge vulnerability. Red herrings: correctly parameterized queries, proper activity tracking.

**diff_review** — V1: session manager PR replacing secrets.token_urlsafe with predictable MD5, logging tokens. V2: migration helper PR adding shell command injection, removing rollback-on-error. Red herrings: legitimate remember-me feature, schema table extension.

**dynamic_bug_hunt** — Uses Python's `ast.NodeTransformer` to procedurally inject bugs into complex, production-grade algorithms (A* Pathfinding, Thread-Safe TTL LRU Cache, Consistent Hashing Ring). Randomly mutates comparison operators (`<` to `<=`), None checks (`is` to `==`), and binary operations (`+` to `-`) at runtime, guaranteeing the agent never sees the same code twice.

## Reward Design

**Severity weights:** low=1, medium=2, high=3, critical=4

**Suggestion quality bonus:** +0.05 to +0.25 per finding for specific fix suggestions

**False positive penalty:** -0.5 per unmatched finding

**Adaptive Difficulty & Dynamic Hint Verbosity Matrix**
Rather than providing static hints, the environment shapes the agent's behavior by analyzing its accuracy in real-time. This prevents "lazy agent" behavior (where an LLM outputs nothing just to get line-number hints) and mimics realistic senior-to-junior code review feedback.

**Hard Mode (Verbosity 0)**: If the agent finds >80% of issues, it is doing well. The grader provides zero specific hints, forcing the agent to find the last subtle edge cases on its own.

**Medium Mode (Verbosity 1)**: If the agent finds >40% of issues, it receives general severity hints (e.g., "You are missing high/critical severity issues").

**Easy Mode (Verbosity 2-3)**: If the agent is struggling (<40%), the environment scales assistance alongside the step count. It progressively reveals approximate line numbers, and eventually exact issue categories, preventing the agent from getting completely stuck.

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

### Running the Test Suite
The environment includes a robust test suite verifying mathematical boundaries and grader logic.
```bash
pip install pytest
PYTHONPATH=. pytest tests/

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
├── models.py                             # Pydantic models with strict defaults
├── openenv.yaml                          # OpenEnv metadata
├── Dockerfile / pyproject.toml / uv.lock
├── server/
│   ├── app.py                            # FastAPI entry point
│   └── code_review_environment.py        # Multi-step engine + random variants
├── tasks/
│   ├── __init__.py                       # Registry, Grader, & Adaptive Hint Engine
│   ├── mutator.py
│   └── variants/
│       ├── style_variants.py             # 3 variants (47 issues)
│       ├── bug_variants.py               # 3 variants (12 issues)
│       ├── concurrency_variants.py       # 2 variants (13 issues)
│       ├── security_variants.py          # 2 variants (16 issues)
│       ├── api_variants.py               # 2 variants (16 issues)
│       └── diff_variants.py              # 2 variants (13 issues)
|       ├── dynamic_variants.py
└── tests/
    ├── test_grader.py                    # Mathematical bounds & adaptive hint testing
    └── test_environment.py               # State transitions & exception handling checks
```
