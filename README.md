# Project Juliana

Project Juliana is a privacy-conscious, local mental-health companion built with Flask. It offers a rule-guarded, intent-based chatbot, private journals, self-guided topics, assessments, and mindfulness exercises. It is not a therapist, does not diagnose, and is not a substitute for professional or emergency support.

If someone may be in immediate danger, contact local emergency services or an appropriate crisis service rather than relying on this application.

## What it does

- Account registration, login, password reset, profile management, and account deletion.
- A TensorFlow/Keras intent classifier with a separate crisis-safety layer, language normalization, emotion-aware response selection, and safe fallback responses.
- Private, authenticated journal entries with editing, deletion, searching, and pagination.
- Chat history restricted to the signed-in account; user data is never shown in the administration area.
- Opt-in, aggregate-only administration insights.
- A review-first learning flow: only redacted, low-confidence non-crisis messages can become candidates; training and model promotion happen outside web requests.

## Architecture

| Area | Implementation |
| --- | --- |
| Web application | Flask application factory in `ChatbotWebsite.create_app` |
| Data | SQLAlchemy with SQLite or MySQL-compatible SQLAlchemy URLs |
| Authentication | Flask-Login and Flask-Bcrypt |
| Forms and CSRF | Flask-WTF with global CSRF protection |
| Database migrations | Flask-Migrate / Alembic |
| Chatbot | Local TensorFlow/Keras bag-of-words intent model |
| Safety | Separate, higher-priority crisis detector; it never depends on intent confidence |
| Language support | Conservative English, Kiswahili, Sheng, and Dholuo/Luo normalization and reviewed examples |
| Frontend | Bootstrap with custom responsive CSS and a local theme preference |

The chatbot loads a validated current model from `models/current/` when present and otherwise uses the legacy artifacts (`chatbot-model.h5` and `data.pickle`). Training creates a new model under `models/candidates/`; it never overwrites a working model.

The legacy artifacts are intentionally version-controlled deployment assets. They are required for the existing trained chatbot to reply on a fresh deployment until a reviewed `models/current/` replacement is promoted.

## Requirements

- Python 3.11–3.13
- A supported SQLAlchemy database URL (SQLite is easiest for local use)
- Optional SMTP credentials only when password-reset email is enabled

## Local setup

1. Create and activate a virtual environment.

   ```powershell
   py -3.13 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install the project, including its development tools.

   ```powershell
   pip install -e .[dev]
   ```

3. Copy `.env.example` to `.env`, then set at least `SECRET_KEY` and `DATABASE_URL`.

   ```ini
   JULIANA_ENV=development
   SECRET_KEY=generate-a-long-random-value
   DATABASE_URL=sqlite:///instance/juliana-dev.db
   MAIL_ENABLED=false
   ```

4. Create or apply database migrations. Do not use `db.create_all()` for deployed databases.

   ```powershell
   $env:FLASK_APP = "run:app"
   flask db upgrade
   ```

   For a brand-new empty Render database while the first committed migration is
   being prepared, a one-time bootstrap is acceptable: run `db.create_all()`
   from the Render Shell, then establish and commit the migration history before
   making future schema changes. Never use this bootstrap on a database that
   already contains production data.

   On Render's free tier, where Shell and pre-deploy commands are unavailable,
   set `AUTO_CREATE_SCHEMA=true` for one deploy against a brand-new empty
   database. It creates missing tables at application startup. Immediately set
   it back to `false` after the service starts; it is not a migration system.

   This repository includes the Flask-Migrate integration but does not ship a generated migration revision for the learning/model tables. Generate and review a migration in the target environment before enabling learning candidates:

   ```powershell
   flask db migrate -m "add learning and model metadata"
   flask db upgrade
   ```

5. Run the development server.

   ```powershell
   python run.py
   ```

Open `http://127.0.0.1:5000`.

## Configuration

Never commit `.env`. All sensitive values belong in environment variables.

| Variable | Purpose |
| --- | --- |
| `JULIANA_ENV` | `development`, `testing`, or `production` |
| `SECRET_KEY` | Required in production; protects sessions and CSRF tokens |
| `DATABASE_URL` | Required in production; SQLAlchemy database URL |
| `MAIL_ENABLED` | Enables password-reset mail when `true` |
| `MAIL_*` | SMTP connection and sender settings |
| `LEARNING_CANDIDATES_ENABLED` | Defaults to `false`; requires reviewed migration and governance before enabling |
| `LEARNING_CONFIDENCE_THRESHOLD` | Low-confidence candidate threshold, default `0.60` |
| `LEARNING_TRAINING_THRESHOLD` | Approved examples before a training run is considered, default `20` |
| `LEARNING_AUTO_TRAIN` | Defaults to `false`; training must never run in a web request |
| `ADMIN_USERNAMES` | Optional comma-separated account usernames permitted to view aggregate-only `/admin/` insights |

Production refuses to start without `SECRET_KEY` and `DATABASE_URL`. Set `JULIANA_ENV=production`; secure cookie settings are enabled by the production configuration. Serve production traffic only over HTTPS.

For Render PostgreSQL, set `DATABASE_URL` to the database's **Internal Database URL**. The project normalizes Render's `postgres://` or `postgresql://` URL to use the included `psycopg` driver; do not use the database display name as the URL.

## Chatbot training and model lifecycle

Run training as a separate process, never through the web application:

```powershell
python scripts/validate_training_data.py
python -m ChatbotWebsite.chatbot.trainer
# or, after installation:
juliana-train
```

Training combines the baseline intent data with reviewed examples in `training_data/`. It produces a timestamped candidate directory containing `model.keras`, `data.pickle`, and `metadata.json`.

Before promotion, validate the candidate against known intents, unknown input, local-language cases, and crisis checks. Set its metadata to `status: validated` and `safety_tests_passed: true` only after review. `ModelManager.promote_candidate(version)` archives the previous active model and copies the validated candidate to `models/current/`. Retain archived models for rollback.

## Testing

Run the suite after installing the development dependencies:

```powershell
python -m pytest
```

The suite covers configuration, crisis safety, authentication flows, private journal and chat ownership boundaries, account deletion, chat persistence, and aggregate-only admin access. Add a regression test whenever changing safety, authorization, or privacy behavior.

Before deploying, verify that the chatbot brain is present:

```powershell
python scripts/check_model.py
```

## Privacy and safety

- Journals and stored conversations are private to their owner.
- Account deletion removes the account, its stored chat history, journals, and a custom profile picture.
- The admin dashboard exposes totals and groupings only; it does not query or render journal content, conversation content, or email addresses.
- Learning candidates are redacted for URLs, emails, and phone numbers, and crisis messages are excluded. They remain disabled by default.
- Crisis screening runs before normal model classification. The app gives supportive direction but does not provide a diagnosis or replace emergency support.
- Avoid logging passwords, journal text, or full private messages.

## Deployment checklist

1. Use a managed database and apply reviewed migrations before the release.
2. Set `JULIANA_ENV=production`, a unique `SECRET_KEY`, and `DATABASE_URL` in the deployment secret store.
3. Configure HTTPS, a reverse proxy, and static-file serving.
4. Run with a production WSGI server, for example on Linux:

   ```bash
   gunicorn --workers 2 --bind 0.0.0.0:8000 wsgi:app
   ```

5. Run `python scripts/check_model.py` in the build or release process. A deployment without either the legacy artifact pair or a complete `models/current/` pair can only return safe fallbacks.
6. Keep model artifacts on durable storage and run training in a separate worker or scheduled process.
7. Set `ADMIN_USERNAMES` only for accounts that need aggregate insights.
8. Back up the database and model directories; test restoration before relying on it.
9. Monitor server errors without recording private user content.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Keep changes incremental, preserve existing behavior, and treat safety and privacy regressions as release blockers.

## License

MIT. See [LICENSE](LICENSE).
