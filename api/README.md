# API

Backend package for UseWise.  
It provides the privacy policy explainer logic and test suite.

## Requirements

- Python 3.9+
- A virtual environment (`venv`)

## Setup

Run from `UseWise/api`:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Environment Variables

The LLM client needs:

```bash
GROQ_API_KEY=your_api_key
```

You can place it in `.env` or export it in your shell.

## Install Test Dependencies

```bash
venv/bin/python -m pip install -e ".[test]"
```

## Run Tests

```bash
venv/bin/python -m pytest
```

## Coverage

Coverage is enabled through pytest options in `pyproject.toml` and generates:

- Terminal report with missing lines
- `coverage.xml`

Run:

```bash
venv/bin/python -m pytest
```

## Exclude Files From Coverage

In `pyproject.toml`:

```toml
[tool.coverage.run]
omit = [
    "usewise/main.py",
]
```

Add more file paths or patterns as needed.

## Script Entry Points

After `pip install -e .`, these commands are available:

- `usewise-sa`: runs static analysis (`mypy` + `ruff`) on the `usewise` package.
- `usewise-test`: runs `pytest` on `tests` and removes generated coverage artifacts (`coverage.xml` and `.coverage`) at the end.
- `usewise-try`: loads `test_data/sample_privacy_policy.txt`, creates a `PrivacyPolicyExplainer`, and sends a sample question to the LLM stream.

Usage:

```bash
usewise-sa
usewise-test
usewise-try
```

## Package Content

`usewise` package layout:

- `usewise/__init__.py`: package marker for `usewise`.
- `usewise/main.py`: utility entry points used by the CLI scripts.
- `usewise/llm/__init__.py`: package marker for LLM-related components.
- `usewise/llm/config.py`: central model configuration.
- `usewise/llm/prompt.py`: prompt construction helpers.
- `usewise/llm/privacy_policy_explainer.py`: main explainer class wrapping the LLM client.

Main functions and class:

- `static_analysis()` in `usewise/main.py`:
  runs `mypy` and `ruff` on the package, then removes `.ruff_cache`.
- `test()` in `usewise/main.py`:
  runs `pytest` on `tests`, then removes generated files (`coverage.xml`, `.coverage`, `.pytest_cache`).
- `try_privacy_policy_explainer()` in `usewise/main.py`:
  loads `test_data/sample_privacy_policy.txt`, creates an explainer instance, and executes a sample question.
- `get_system_message(privacy_policy: str)` in `usewise/llm/prompt.py`:
  builds the `SystemMessage` prompt containing the privacy policy text.
- `PrivacyPolicyExplainer` in `usewise/llm/privacy_policy_explainer.py`:
  initializes a `ChatOpenAI` client with `GROQ_API_KEY`, model, and base URL, then streams answers through `invoke(question)`.

Configuration values (`usewise/llm/config.py`):

- `models`: list of available model IDs.
- `model_name`: default selected model (`models[0]`).
- `llm_url`: OpenAI-compatible Groq endpoint URL.
