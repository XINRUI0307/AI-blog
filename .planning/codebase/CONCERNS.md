# Concerns

## Security Issues

| Issue | Location | Severity |
|-------|----------|----------|
| Hardcoded admin credentials | `app.py:_seed_admin()` — `admin/admin123` | **HIGH** |
| SECRET_KEY fallback in code | `app.py:9` — `'change-this-in-production'` | **HIGH** |
| No CSRF protection | All POST forms (no Flask-WTF or CSRF tokens) | **HIGH** |
| Open redirect | `routes/auth.py:55` — `next` param not validated | **MEDIUM** |
| Broad exception in upload | `routes/photos.py:46` — bare `except Exception` hides errors | **MEDIUM** |
| No rate limiting | Login endpoint — brute-force susceptible | **MEDIUM** |
| Photo served without auth check | `serve_post_photo` is public; full content should require role | **LOW** |
| Debug mode in `__main__` | `app.py:81` — `debug=True` — must not run in production | **LOW** |

## Technical Debt

| Item | Location | Impact |
|------|----------|--------|
| No test suite | Entire codebase | **HIGH** — zero confidence in changes |
| SQLite in production | `app.py:10` — hardcoded URI | **HIGH** — no concurrent writes, no backup |
| Business logic in routes | All `routes/*.py` | **MEDIUM** — untestable, hard to reuse |
| No input sanitization | Forms throughout | **MEDIUM** — relies on Jinja2 autoescaping only |
| No logging | Entire codebase | **MEDIUM** — no audit trail |
| `Post.query.get()` deprecated | `routes/photos.py:87` — SQLAlchemy 2.0 deprecation | **LOW** |
| No DB indexes | `models.py` — no explicit indexes on FKs or query fields | **LOW** |
| Sidebar queried on every request | `app.py:40-43` context processor | **LOW** — uncached |

## Known Bugs

| Bug | Location | Notes |
|-----|----------|-------|
| Deleted photo file not checked on upload | `routes/photos.py` — orphaned DB records if file save fails mid-batch | Race condition |
| `_purge_old_posts()` runs on every app startup | `app.py:55` | Slow startup on large DB |
| No check if post has images before displaying | `templates/posts/detail.html` | May render empty gallery |
| Messages not paginated | `routes/profile.py` | Can grow unbounded |
| Search not paginated | `routes/search.py` | Can return all posts |

## Performance Bottlenecks

| Item | Location | Notes |
|------|----------|-------|
| No DB indexes on foreign keys | `models.py` | Full table scans on post/user lookups |
| N+1 query risk | `posts/index.html` — eager loading not configured | Images/ratings per post |
| Sidebar DB query per request | `app.py` context processor | No caching |
| No image compression on upload | `routes/photos.py` | Stores original file |
| SQLite write lock | `instance/database.db` | Blocks concurrent requests |

## Fragile Areas

| Area | Risk |
|------|------|
| File storage | `uploads/` is local disk — lost on redeploy, no backup |
| Role system | Single `role` column — changing roles requires careful migration |
| Admin seed | Runs on every startup — relies on "no admin exists" check |
| Photo delete | Deletes file + DB record separately — can desync on error |
| `_purge_old_posts()` | Destructive, runs automatically, no dry-run or confirmation |

## Missing Features (from spec)

- AI-generated descriptions (spec mentions AI integration)
- Email notifications
- Image compression/optimization pipeline
- Environment-based configuration (`.env` file)
- Production WSGI setup (gunicorn/uwsgi config)
