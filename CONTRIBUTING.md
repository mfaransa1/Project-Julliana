# Contributing to Project Juliana

Thanks for helping improve Project Juliana. This project handles sensitive mental-health-adjacent information, so stability, privacy, and safety come before features.

## Development workflow

1. Create a branch and use a virtual environment with Python 3.11–3.13.
2. Copy `.env.example` to `.env`; never commit `.env`, credentials, real user data, or model artifacts generated from private material.
3. Install development dependencies with `pip install -e .[dev]`.
4. Run `python -m pytest` before submitting a change.
5. Keep a change small and explain its effect on safety, privacy, and database migrations.

## Required safeguards

- Do not expose journal entries, raw conversations, email addresses, passwords, tokens, or profile uploads in logs, error pages, analytics, or admin views.
- Every user-data query must filter by the authenticated user’s ID unless the data is designed to be aggregate-only.
- Do not train on raw user conversation data. Candidate training examples must be redacted, reviewed, approved, and excluded if crisis-related.
- Do not move model training into a Flask request or replace a validated model in place.
- Do not make diagnostic or clinical claims in chatbot responses.
- Keep crisis detection independent of model confidence and add regression tests for any safety-rule change.

## Database changes

Use Flask-Migrate for schema changes:

```powershell
$env:FLASK_APP = "run:app"
flask db migrate -m "describe the change"
flask db upgrade
```

Review generated migrations carefully. Never delete or rebuild a deployed database to apply a schema change, and document rollback steps in the pull request.

## Tests to add

Add or update tests for behavior changes. At minimum, cover authorization, ownership boundaries, input validation, and failure paths for changes that touch users, journals, chat, safety, learning, or administration.

## Style

Use explicit imports, focused functions, type hints where they clarify behavior, and docstrings for public or safety-sensitive code. Prefer a direct, maintainable solution over a new abstraction or dependency.
