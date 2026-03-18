---
phase: 01-foundation
plan: "01"
subsystem: infrastructure
tags: [flask-migrate, alembic, dotenv, sqlite-wal, env-config]
dependency_graph:
  requires: []
  provides: [flask-migrate-workflow, wal-mode-sqlite, env-var-config, dotenv-loading]
  affects: [all-future-schema-changes, anthropic-api-key-loading]
tech_stack:
  added: [Flask-Migrate==4.1.0, python-dotenv==1.2.2, alembic>=1.9.0]
  patterns: [app-factory-env-config, wal-event-listener, migration-stamp-existing-db]
key_files:
  created:
    - requirements.txt (extended)
    - extensions.py (extended)
    - app.py (extended)
    - .env.example
    - .env
    - .gitignore
    - .flaskenv
    - migrations/ (entire directory with initial baseline)
  modified:
    - app.py
    - extensions.py
    - requirements.txt
decisions:
  - "Guard _seed_admin()/_purge_old_posts() behind inspector.has_table('users') so app starts cleanly against empty databases during flask db migrate"
  - "Used flask db stamp head (not flask db upgrade) to mark existing database as current without re-running DDL"
  - "Generated initial migration against temp empty DB (not real DB) to get a full CREATE TABLE diff"
metrics:
  duration: "~4 minutes"
  completed: "2026-03-18"
  tasks_completed: 2
  files_changed: 8
requirements_satisfied: [INFRA-01, INFRA-02, INFRA-03, INFRA-04]
---

# Phase 1 Plan 01: Database Migration Infrastructure and Environment Configuration Summary

**One-liner:** Flask-Migrate with Alembic baseline migration for 8-table SQLite schema, WAL mode via SQLAlchemy event listener, and python-dotenv env-var config with ANTHROPIC_API_KEY startup warning.

## What Was Built

- **Flask-Migrate wired:** `Migrate` instance added to `extensions.py`; `migrate.init_app(app, db)` called in `create_app()`; `migrations/` directory initialized with Alembic.
- **Initial baseline migration:** `28e5beea3e43_initial_schema.py` generated against an empty temp database to capture all 8 existing tables (users, posts, images, comments, membership_applications, ratings, messages, sidebar_content) as `op.create_table()` calls.
- **Existing database stamped:** `flask db stamp head` marks the existing `instance/database.db` as at revision `28e5beea3e43` without re-running DDL. Future schema changes use `flask db migrate` / `flask db upgrade`.
- **WAL mode:** SQLAlchemy `@event.listens_for(Engine, "connect")` listener executes `PRAGMA journal_mode=WAL` on every connection.
- **Environment configuration:** All `app.config` values (`SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, `ANTHROPIC_API_KEY`) read from `os.environ.get()`. `load_dotenv()` called in `__main__` block.
- **ANTHROPIC_API_KEY warning:** `warnings.warn(..., RuntimeWarning)` emitted at startup when key is absent — non-crashing, visible.
- **Supporting files:** `.env.example` (template), `.env` (dev values, gitignored), `.gitignore` (protects `.env`, `instance/`, `uploads/`, `*.db`, `.planning/`), `.flaskenv` (`FLASK_APP=app.py` for Flask CLI).

## Verification Results

| Check | Command | Result |
|-------|---------|--------|
| INFRA-01 | `flask db current` | `28e5beea3e43 (head)` |
| INFRA-02 | `PRAGMA journal_mode` query | `wal` |
| INFRA-03 | Startup without ANTHROPIC_API_KEY | RuntimeWarning emitted |
| INFRA-04 | `grep "change-this-in-production" app.py` | No matches |
| Workflow | `flask db migrate -m "test"` | "No changes in schema detected" |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Guard startup functions against empty databases**

- **Found during:** Task 2 (flask db migrate against temp empty DB)
- **Issue:** `_seed_admin()` and `_purge_old_posts()` ran unconditionally inside `create_app()`, causing `OperationalError: no such table: users` when the app initializes against an empty database (as Alembic does during `flask db migrate`).
- **Fix:** Wrapped both calls behind `inspector.has_table('users')` check using `sqlalchemy.inspect(db.engine)`. Functions still run normally when the real database with all tables is present.
- **Files modified:** `app.py`
- **Commit:** `0677f95` (included in Task 2 commit)

## Commits

| Hash | Message |
|------|---------|
| `7931e8a` | feat(01-01): add env config, WAL mode, Flask-Migrate wiring, dotenv loading |
| `0677f95` | feat(01-01): bootstrap Flask-Migrate with initial schema migration |

## Self-Check: PASSED

- `migrations/versions/28e5beea3e43_initial_schema.py` — FOUND
- `migrations/env.py` — FOUND
- `.flaskenv` — FOUND
- `.env.example` — FOUND
- `.gitignore` — FOUND
- Commit `7931e8a` — FOUND
- Commit `0677f95` — FOUND
