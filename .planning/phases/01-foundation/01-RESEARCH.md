# Phase 1: Foundation - Research

**Researched:** 2026-03-18
**Domain:** Flask-Migrate (Alembic), SQLite WAL mode, python-dotenv environment configuration
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-01 | Flask-Migrate configured with initial migration baseline so schema changes apply without data loss | Flask-Migrate 4.1.0 setup pattern; `flask db stamp head` procedure for existing databases |
| INFRA-02 | Database configured with WAL mode to support concurrent reads and background thread writes | SQLAlchemy Engine `connect` event listener executing `PRAGMA journal_mode=WAL` |
| INFRA-03 | Anthropic API key loaded from environment variable via `.env` file, not hardcoded | python-dotenv 1.2.2 `load_dotenv()` + startup validation pattern |
| INFRA-04 | All configuration values read from environment variables via python-dotenv | `os.environ.get()` with explicit fallback removal; dotenv loaded before `create_app()` |
</phase_requirements>

---

## Summary

This phase establishes three independent infrastructure pieces on top of the existing Flask/SQLAlchemy/SQLite codebase. No new user-facing features are involved. The existing app uses `db.create_all()` to bootstrap the schema — Flask-Migrate must be layered on top without touching or recreating the live database.

The trickiest requirement is INFRA-01: because the database already exists and was created with `db.create_all()`, the normal `flask db migrate && flask db upgrade` flow will fail or produce a no-op. The safe path is `flask db init` → generate initial migration against an empty temp database → `flask db stamp head` against the real database. After stamping, the standard `migrate/upgrade` cycle works for all future changes.

WAL mode (INFRA-02) is a one-time persistent setting on the SQLite file. The cleanest approach is a SQLAlchemy `Engine`-level `"connect"` event listener that runs `PRAGMA journal_mode=WAL` on every new connection — WAL is idempotent so this is safe. Environment configuration (INFRA-03, INFRA-04) means adding python-dotenv, calling `load_dotenv()` before `create_app()`, and replacing hardcoded config values with `os.environ.get()` calls that fail loudly when required keys are absent.

**Primary recommendation:** Add Flask-Migrate and python-dotenv, wire the WAL pragma via event listener in `create_app()`, and add startup validation that raises/warns when `ANTHROPIC_API_KEY` is not set.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flask-Migrate | 4.1.0 | Alembic-based schema migration CLI for Flask | The canonical Flask migration solution; wraps Alembic cleanly with Flask CLI integration |
| python-dotenv | 1.2.2 | Loads `.env` files into `os.environ` at startup | Flask 3.x explicitly integrates with it; zero dependencies, widely used |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| SQLAlchemy (bundled with Flask-SQLAlchemy 3.1.1) | 2.x | Provides `event.listens_for` for WAL pragma | Already installed; no extra install needed for WAL |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Flask-Migrate (Alembic) | Yoyo-migrations, Flyway | Flask-Migrate is the only option that integrates with SQLAlchemy metadata autogenerate — others require hand-written SQL |
| python-dotenv | environs, pydantic-settings | python-dotenv is simplest; no schema definition required for this phase |

**Installation:**
```bash
pip install Flask-Migrate==4.1.0 python-dotenv==1.2.2
```

**Version verification:** Both versions confirmed against PyPI on 2026-03-18.
- `Flask-Migrate`: latest is 4.1.0
- `python-dotenv`: latest is 1.2.2

---

## Architecture Patterns

### Pattern 1: Flask-Migrate — Existing Database Bootstrap

**What:** When the project already has a live database created by `db.create_all()`, you cannot run a normal first migration. Alembic will either see "no changes" (schema already matches) or will try to CREATE TABLE on tables that already exist.

**Correct procedure:**

```
Step 1 — Add Migrate to extensions.py and create_app()
Step 2 — flask db init          (creates migrations/ directory)
Step 3 — flask db migrate -m "initial schema"
          (generate against an EMPTY database — see pitfall below)
Step 4 — flask db stamp head    (mark existing real DB as current — NO upgrade)
Step 5 — Verify: flask db current  (should show head revision)
```

**Why generate against an empty DB:** Alembic autogenerate compares the current DB state against the models. Against the real populated DB, it sees no diff and generates an empty migration. Against an empty DB, it sees all tables as new and generates the full schema — which becomes the baseline.

**Empty DB trick:**
```python
# Temporarily point DATABASE_URL at a fresh file, run flask db migrate,
# then delete the temp file. The generated script in migrations/versions/
# is what matters — not which DB it was generated from.
```

**After initial setup — ongoing workflow:**
```
flask db migrate -m "add tags table"
flask db upgrade
```

### Pattern 2: WAL Mode via SQLAlchemy Event Listener

**What:** Execute `PRAGMA journal_mode=WAL` on every new SQLite connection.

**When to use:** Any Flask/SQLAlchemy app using SQLite where background threads write while the web thread reads (Phase 3 AI jobs will write from background threads).

**Implementation in `app.py` create_app():**
```python
# Source: https://docs.sqlalchemy.org/en/20/dialects/sqlite.html
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()
```

Place this at module level (not inside `create_app`) because it listens on the `Engine` class, not an instance. WAL is persistent on the file — once set it survives reconnects.

**Alternative:** Pass via `SQLALCHEMY_ENGINE_OPTIONS`:
```python
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'check_same_thread': False}
}
```
The event listener is preferred because `connect_args` with `journal_mode` is not a standard sqlite3 keyword argument in Python's standard library driver.

### Pattern 3: python-dotenv with Startup Validation

**What:** Load `.env` before app creation; validate required keys exist; warn clearly if missing.

**Where to call `load_dotenv()`:**
```python
# In the entry point (run.py or __main__ block in app.py),
# BEFORE create_app() is called.
from dotenv import load_dotenv
load_dotenv()  # reads .env from cwd, sets os.environ

app = create_app()
```

**Startup validation pattern for ANTHROPIC_API_KEY:**
```python
import os
import warnings

def create_app():
    # ...
    if not os.environ.get('ANTHROPIC_API_KEY'):
        warnings.warn(
            "ANTHROPIC_API_KEY is not set. AI features will not work.",
            stacklevel=2
        )
    app.config['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY', '')
    # ...
```

Or raise `RuntimeError` if the key is truly required at startup (Phase 3 concern — for Phase 1 a warning is sufficient to satisfy INFRA-03).

**Remove hardcoded fallbacks:**
```python
# Before (bad):
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-in-production')

# After (Phase 1 — keep fallback for SECRET_KEY, remove for API keys):
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
app.config['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY')  # no fallback
```

### Recommended Project Structure Changes

```
blog-ai/
├── .env                  # NEW — gitignored; holds ANTHROPIC_API_KEY, SECRET_KEY
├── .env.example          # NEW — committed; shows required keys without values
├── app.py                # MODIFIED — load_dotenv, WAL listener, config cleanup
├── extensions.py         # MODIFIED — add Migrate()
├── migrations/           # NEW — created by flask db init; commit to git
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│       └── xxxx_initial_schema.py
├── requirements.txt      # MODIFIED — add Flask-Migrate, python-dotenv
└── ...existing files...
```

### Anti-Patterns to Avoid

- **Running `flask db upgrade` on the existing database after first `migrate`:** This will try to CREATE tables that already exist and will fail or corrupt data. Use `flask db stamp head` instead.
- **Calling `load_dotenv()` inside `create_app()`:** The function may be called multiple times in testing; call once at the entry point.
- **Registering `@event.listens_for(db.engine, "connect")` inside `create_app()`:** `db.engine` requires an active app context and the engine is created lazily — the class-level `Engine` listener is safer and cleaner.
- **Keeping `db.create_all()` in `create_app()` after Flask-Migrate is installed:** This creates a conflict. Once Migrate is active, schema management moves to migrations exclusively. Remove `db.create_all()` from the factory after the initial stamp is complete.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema migration tracking | Custom SQL version table | Flask-Migrate (Alembic) | Alembic handles column renames, type changes, constraint diffs, downgrade paths — all hard to implement correctly |
| Env file parsing | `open('.env')` + string parsing | python-dotenv | Edge cases: quoted values, multiline, comments, export prefix, encoding |
| Migration baseline for existing DB | Custom "skip migration" logic | `flask db stamp head` | Built-in command; adding custom logic creates a fork from standard Alembic behavior |

**Key insight:** The `flask db stamp head` command is specifically designed for this exact scenario (adopting Alembic on an existing database). It is the canonical, documented solution — not a workaround.

---

## Common Pitfalls

### Pitfall 1: "No changes detected" on first `flask db migrate`
**What goes wrong:** Running `flask db migrate` against the existing populated database produces an empty migration because Alembic sees the schema already matches the models.
**Why it happens:** Alembic compares current DB schema to SQLAlchemy models. If the DB was built from those same models via `db.create_all()`, there is no diff.
**How to avoid:** Generate the initial migration against an empty temporary database. The migration script captures the full schema; then `stamp head` on the real DB.
**Warning signs:** Migration file body contains only `pass` or empty `upgrade()`/`downgrade()` functions.

### Pitfall 2: Running `flask db upgrade` on existing data
**What goes wrong:** `flask db upgrade` runs the initial migration's `upgrade()` function, which calls `CREATE TABLE` for every existing table. SQLite raises `OperationalError: table X already exists`.
**Why it happens:** The migration was generated from models, not from the existing DB state.
**How to avoid:** Always use `flask db stamp head` (not `upgrade`) when bootstrapping an existing database.
**Warning signs:** Any `OperationalError` involving `table already exists` on first upgrade.

### Pitfall 3: WAL PRAGMA outside transaction requirement
**What goes wrong:** `PRAGMA journal_mode=WAL` fails with `cannot change into wal mode from within a transaction`.
**Why it happens:** SQLAlchemy may start an implicit transaction before the PRAGMA runs, depending on the isolation level.
**How to avoid:** The event listener on `"connect"` fires before any transaction begins — this is the safe hook. Do not execute the PRAGMA inside a `db.session` operation.
**Warning signs:** `sqlite3.OperationalError: cannot change into wal mode from within a transaction`.

### Pitfall 4: `.env` file committed to git
**What goes wrong:** API keys and secret keys are exposed in version history.
**Why it happens:** Forgetting to add `.env` to `.gitignore`.
**How to avoid:** Add `.env` to `.gitignore` immediately. Commit `.env.example` with placeholder values instead.
**Warning signs:** `git status` shows `.env` as untracked/staged.

### Pitfall 5: `migrations/` directory not committed
**What goes wrong:** Other developers (or deployment) cannot run `flask db upgrade` because migration scripts don't exist.
**Why it happens:** Treating `migrations/` like a build artifact.
**How to avoid:** The `migrations/` directory is source code — commit it to git alongside model changes.

---

## Code Examples

### Flask-Migrate setup in extensions.py
```python
# Source: https://flask-migrate.readthedocs.io/
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
```

### Wiring Migrate in create_app() (app.py)
```python
# Source: https://flask-migrate.readthedocs.io/
from extensions import db, login_manager, migrate

def create_app():
    app = Flask(__name__)
    # ... config ...
    db.init_app(app)
    migrate.init_app(app, db)
    # ... blueprints, etc ...
    return app
```

### WAL mode event listener (module level in app.py)
```python
# Source: https://docs.sqlalchemy.org/en/20/dialects/sqlite.html
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()
```

### Entry point with load_dotenv (app.py __main__ block)
```python
# Source: https://pypi.org/project/python-dotenv/
from dotenv import load_dotenv
load_dotenv()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
```

### .env.example template
```
SECRET_KEY=change-me-in-production
ANTHROPIC_API_KEY=your-api-key-here
```

### Initial migration bootstrap procedure (shell commands)
```bash
# Step 1: Install
pip install Flask-Migrate==4.1.0 python-dotenv==1.2.2

# Step 2: Init migrations directory
flask db init

# Step 3: Generate initial migration against EMPTY temp db
# (temporarily use a different DB URI so Alembic sees a full diff)
SQLALCHEMY_DATABASE_URI=sqlite:///temp_migration.db flask db migrate -m "initial schema"
# Then delete temp_migration.db

# Step 4: Stamp the REAL existing database (not upgrade!)
flask db stamp head

# Step 5: Verify
flask db current
# Expected output: <revision_id> (head)

# Step 6: Clean up temp db
rm instance/temp_migration.db
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `db.create_all()` only | Flask-Migrate (Alembic) for schema evolution | On adoption of migrations | Enables zero-downtime schema changes with rollback |
| Hardcoded secrets in source | Environment variables + python-dotenv | Industry standard | Prevents credential exposure; enables per-environment config |
| SQLite default journal mode (DELETE) | WAL mode | SQLite 3.7.0+ (2010) | Concurrent readers + writer without deadlocking |
| `os.getenv('KEY', 'hardcoded-fallback')` | No fallback; explicit startup validation | Best practice | Fails loudly instead of running with insecure defaults |

**Deprecated/outdated in this codebase:**
- `db.create_all()` in `create_app()`: Must be removed after Migrate bootstrap (or moved to a separate `init-db` CLI command for first-time setup only)
- `SECRET_KEY = 'change-this-in-production'` fallback: Replace with env-only after Phase 1

---

## Open Questions

1. **`db.create_all()` removal timing**
   - What we know: `db.create_all()` conflicts with Alembic once migrations are active
   - What's unclear: Whether to remove it entirely or move to a CLI command (`flask init-db`) for fresh deployments
   - Recommendation: Remove from `create_app()` after successful stamp; note in plan that fresh deployments should run `flask db upgrade` instead

2. **Flask CLI `load_dotenv` auto-detection**
   - What we know: Flask 3.x automatically calls `load_dotenv()` when python-dotenv is installed if `.env` or `.flaskenv` exists in the working directory, before running CLI commands
   - What's unclear: Whether this automatic behavior applies when running via `python app.py` (not `flask run`)
   - Recommendation: Call `load_dotenv()` explicitly in `app.py`'s `__main__` block regardless — belt-and-suspenders

3. **INFRA-03 warning vs. error**
   - What we know: The requirement says "clear startup warning, not silent failure"
   - What's unclear: Whether `warnings.warn()` or a `print()` to stderr is preferred
   - Recommendation: Use `warnings.warn(RuntimeWarning)` — it is visible in Flask's dev server output and is the Pythonic approach

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None — test suite is explicitly out of scope (see REQUIREMENTS.md Out of Scope) |
| Config file | None |
| Quick run command | N/A |
| Full suite command | N/A |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01 | `flask db current` shows head after bootstrap | manual-only | `flask db current` | N/A — CLI verification |
| INFRA-02 | `PRAGMA journal_mode` returns `wal` | manual-only | `flask shell` → `db.session.execute(text("PRAGMA journal_mode")).scalar()` | N/A |
| INFRA-03 | Startup prints warning when key absent | manual-only | Remove key from `.env`, run `flask run`, observe output | N/A |
| INFRA-04 | Config values read from env, not source | manual-only | `grep -r "hardcoded" app.py` + code review | N/A |

**Note:** Because the project has no automated test suite and tests are explicitly deferred, validation for this phase is manual verification steps. The Validation Architecture section documents the manual verification commands the planner should include as acceptance criteria in each task.

### Sampling Rate
- **Per task:** Run the corresponding manual verification command listed above
- **Phase gate:** All 4 manual checks passing before `/gsd:verify-work`

### Wave 0 Gaps
None — no automated test infrastructure is needed or planned for this phase.

---

## Sources

### Primary (HIGH confidence)
- Flask-Migrate readthedocs.io — setup pattern, `stamp` command documentation
- https://docs.sqlalchemy.org/en/20/dialects/sqlite.html — WAL event listener pattern
- https://pypi.org/project/Flask-Migrate/ — version 4.1.0 confirmed
- https://pypi.org/project/python-dotenv/ — version 1.2.2 confirmed
- PyPI version index queried directly via `pip index versions` on 2026-03-18

### Secondary (MEDIUM confidence)
- https://blog.miguelgrinberg.com/post/how-to-add-flask-migrate-to-an-existing-project — existing DB bootstrap procedure (author is Flask-Migrate maintainer)
- https://github.com/miguelgrinberg/Flask-Migrate/discussions/516 — community discussion confirming stamp approach for existing databases
- https://til.simonwillison.net/sqlite/enabling-wal-mode — WAL mode persistence behavior

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions confirmed from PyPI directly
- Architecture: HIGH — Flask-Migrate bootstrap procedure from official maintainer blog; WAL listener from SQLAlchemy official docs
- Pitfalls: HIGH — INFRA-01/INFRA-02 pitfalls confirmed by official docs and GitHub issues; others are standard practice

**Research date:** 2026-03-18
**Valid until:** 2026-06-18 (stable libraries — 90 days)
