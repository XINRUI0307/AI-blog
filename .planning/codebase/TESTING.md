# Testing

## Current State

**No test suite exists.** No test files, no test framework configured, no CI pipeline.

## Framework (None Configured)

No `pytest`, `unittest`, or other test framework installed. `requirements.txt` does not include any testing dependencies.

## Recommended Setup

For this Flask app, standard approach would be:

```
pytest
flask[testing]         # built-in test client
pytest-flask           # Flask-specific fixtures
```

## What Needs Testing

### Critical Paths (High Priority)

| Area | What to Test |
|------|-------------|
| Authorization | Role decorators block unauthorized access (403 responses) |
| Auth flow | Register → pending → admin approve → login |
| Post limits | Contributors capped at 10 posts |
| File upload | Allowed extensions, size limit, resolution limit |
| Ratings | One rating per user per post (unique constraint) |
| Admin seed | `_seed_admin()` creates admin only if none exists |
| Post purge | `_purge_old_posts()` removes posts older than 18 months |

### Secondary Paths

| Area | What to Test |
|------|-------------|
| Comments | Add, report, admin view reported |
| Messages | Send, receive, mark read |
| Search | Returns matching posts |
| Profile | Edit username/bio/avatar |
| Membership | Application submit, admin approve/reject |

## Test File Structure (Recommended)

```
tests/
├── conftest.py          # App factory fixture, test DB setup
├── test_auth.py         # Register, login, logout
├── test_posts.py        # CRUD, ratings, pagination
├── test_photos.py       # Upload validation, serve, delete
├── test_comments.py     # Add, report
├── test_admin.py        # Dashboard, user management
├── test_authorization.py # Role enforcement across all routes
└── test_membership.py   # Application workflow
```

## Coverage Gaps

- No unit tests for `utils.py` decorators
- No integration tests for full auth flow
- No tests verifying role boundaries
- No tests for file upload edge cases
- No tests for the auto-purge of old posts
- No tests for admin seed uniqueness
