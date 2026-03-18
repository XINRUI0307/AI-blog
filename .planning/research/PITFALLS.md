# Domain Pitfalls

**Domain:** AI-enhanced photo blog with social graph and notifications
**Researched:** 2026-03-18
**Confidence:** MEDIUM — based on training knowledge; no live web search available. Core Flask/SQLite/AI API pitfalls are well-documented and stable. Confidence is MEDIUM rather than HIGH because specific library version interactions (Flask 3.0 + threading behaviour, SQLAlchemy 2.0 async nuances) were not live-verified.

---

## Critical Pitfalls

Mistakes that cause rewrites, data loss, or runaway costs.

---

### Pitfall 1: AI API Calls Blocking the Request Thread

**What goes wrong:** An AI vision call (image description, tag suggestion) is made synchronously inside a Flask route handler. The HTTP request hangs for 5–30 seconds while waiting for the API, users see timeouts, and Flask's development server (single-threaded) becomes completely unresponsive to all other requests.

**Why it happens:** Flask routes are synchronous by default. `requests.post()` or `openai.ChatCompletion.create()` inside a route blocks the WSGI thread. The existing codebase has no background task infrastructure and no async patterns established.

**Consequences:**
- Photo upload endpoint becomes unusable — 30-second page loads
- Under Flask's development server, the entire site freezes during AI calls
- If AI API is slow or rate-limited, uploads queue up and time out
- Users retry, triggering duplicate uploads and duplicate API charges

**Prevention:**
- Dispatch AI calls to a background thread or task queue immediately after the file is saved
- Return the upload response to the user first; AI results are applied asynchronously
- Simplest viable approach: `threading.Thread(target=run_ai, args=(post_id,)).start()` — works without Celery but has no retry or failure tracking
- Better approach: Flask-RQ2 or Celery with Redis for retry, progress tracking, and failure logging
- AI results should be stored in nullable DB columns (`ai_description`, `ai_tags_json`); UI shows "AI processing..." and polls or reloads

**Detection (warning signs):**
- Photo upload takes longer than 2 seconds in dev
- Any route where `time.sleep()` or an HTTP client call appears before the final `return`

**Phase mapping:** Address in the AI Features phase — this is the foundational constraint. Do not prototype AI calls inline even temporarily; the "I'll fix it later" pattern always ships.

---

### Pitfall 2: AI API Cost Blowout from Unthrottled Calls

**What goes wrong:** Every photo in a multi-photo upload triggers an individual vision API call. A contributor uploads 8 photos — 8 API calls fire in parallel. If several contributors upload simultaneously, costs multiply. Vision API calls (image analysis) cost significantly more than text calls; analyzing a batch of full-resolution images can cost $0.10–$1.00 per upload depending on provider and image size.

**Why it happens:** The existing upload handler saves all photos in a loop (`routes/photos.py`). Without an explicit cost-control strategy, the natural implementation calls the AI once per image.

**Consequences:**
- Costs scale with content, not revenue — a few active contributors exhaust API budgets
- No visibility into spend until the monthly bill arrives
- If uploads folder grows (no CDN, local disk), images sent to API may be uncompressed originals (up to 10 MB each)

**Prevention:**
- Call AI once per post, not once per photo — send the first (or best) image only for description/tag generation
- Resize images before sending to AI API — most vision APIs charge by token count which correlates to image size; send 800px-wide version, not the 10 MB original
- Cap AI calls per user per day (simple counter in the DB or a Redis key)
- Store AI results and never re-analyse unless explicitly requested by the contributor
- Add a hard monthly spend limit at the API provider level (OpenAI and Anthropic both support this)
- Log every API call: timestamp, user_id, post_id, tokens_used, cost_estimate

**Detection (warning signs):**
- AI call code inside a `for photo in photos` loop
- No resizing step before the API call
- No per-user or per-day rate-limit check

**Phase mapping:** Address before any AI call goes to production. Cost controls must exist on day one of the AI Features phase.

---

### Pitfall 3: SQLite Write Lock Deadlocks Under Social Load

**What goes wrong:** SQLite uses a database-level write lock. When the follow/feed/notification system is active, multiple concurrent writes compete: a new post creates a notification row for every follower, which requires N individual write transactions (one per follower). Under even modest concurrency (5 simultaneous users), `OperationalError: database is locked` exceptions appear.

**Why it happens:** The existing codebase already notes this (`CONCERNS.md`). Adding social features makes it dramatically worse. A contributor with 50 followers triggers 50+ write operations when they post. The existing AI background thread (Pitfall 1 fix) also writes to the DB from a non-request thread, which collides with foreground writes.

**Consequences:**
- Notifications silently fail or throw 500 errors
- Feed updates drop — users miss posts from followed contributors
- Under load, the upload endpoint itself can deadlock if the background AI thread is writing simultaneously

**Prevention:**
- Set `PRAGMA journal_mode=WAL` immediately — WAL mode allows concurrent readers and one writer, eliminating most read/write collisions. This is a one-line fix: `db.engine.execute("PRAGMA journal_mode=WAL")` in `create_app()` or via SQLAlchemy event
- Set `connect_args={"check_same_thread": False, "timeout": 20}` on the SQLite engine to avoid same-thread errors from background threads
- Batch-insert notifications in a single transaction rather than one commit per follower
- Accept that SQLite is a hard ceiling. Plan the migration to PostgreSQL as a named future milestone; document the ceiling explicitly so it is not a surprise
- Do not add write-heavy features (fan-out notifications, feed materialisation) until WAL mode is confirmed enabled

**Detection (warning signs):**
- `OperationalError: database is locked` in logs
- Any code path that writes to DB inside a loop proportional to follower count
- Background thread writing DB without checking `check_same_thread`

**Phase mapping:** Fix WAL mode and thread safety in the Social phase, before any fan-out writes are introduced.

---

### Pitfall 4: N+1 Queries in Feed and Tag Browsing

**What goes wrong:** The feed query returns N posts; then for each post the template accesses `post.images`, `post.ratings`, `post.tags`, and `post.author.avatar` — each a separate SELECT. A feed of 20 posts becomes 80–160 queries per page load. The existing codebase already has this problem on the index page (`CONCERNS.md: N+1 query risk`). Social feeds amplify it because they include posts from multiple authors filtered by follow relationships.

**Why it happens:** SQLAlchemy lazy-loads relationships by default. Jinja2 templates that access `post.author.username` look innocent but each traversal hits the DB if the relationship is not eager-loaded. Without a test suite, there is no query-count assertion to catch regressions.

**Consequences:**
- Feed page takes 500ms–3s on 20 posts with SQLite (no query cache)
- Tag browsing pages with many posts become unusably slow
- Developers cannot see the problem without query logging enabled

**Prevention:**
- Enable SQLAlchemy query logging in development: `SQLALCHEMY_ECHO = True` in dev config — this surfaces N+1 problems immediately
- Use `joinedload()` or `selectinload()` for all relationships accessed in list views: `Post.query.options(joinedload(Post.images), joinedload(Post.author), selectinload(Post.tags)).all()`
- Add DB indexes for every foreign key and every column used in WHERE/ORDER BY: `follower_id`, `followed_id`, `post_id`, `tag_id`, `created_at`
- For the follow feed specifically, use a single JOIN query rather than fetching followed users then fetching their posts separately

**Detection (warning signs):**
- Any Jinja2 template accessing `post.something.something` in a loop without confirmed eager loading
- Page loads that slow down linearly as post count grows
- `SQLALCHEMY_ECHO` output showing repeated identical queries with different IDs

**Phase mapping:** Address indexes and eager loading at the start of the Social phase before feed queries are written. Retrofitting is harder than building correctly.

---

### Pitfall 5: Notification Fan-Out on Post Creation Blocking the Upload Response

**What goes wrong:** When a contributor publishes a post, the code creates a Notification row for every follower inline in the route handler. A contributor with 100 followers means 100 INSERTs before the redirect fires. This blocks the response and creates 100 write contention points on SQLite.

**Why it happens:** The natural implementation is "after saving post, create notifications" — all in the same request/transaction. There is no existing background task infrastructure to push this work out of the request.

**Consequences:**
- Post creation becomes slow for popular contributors
- SQLite write lock held for the entire notification fan-out, blocking all other concurrent writes
- If notification creation fails mid-loop, some followers get notified and some do not — no atomicity

**Prevention:**
- Treat notification creation as a background job, not part of the post-creation transaction
- Use the same background thread mechanism introduced for AI calls (Pitfall 1) — keeps infrastructure consistent
- Write notifications in a single bulk INSERT rather than a loop: `db.session.bulk_insert_mappings(Notification, [...])`
- For phase 1, cap max notifications per event at a reasonable number (e.g., 500) and add a TODO for proper queue infrastructure

**Detection (warning signs):**
- Notification INSERT inside the same `db.session.commit()` as the post INSERT
- Any loop that creates DB rows proportional to follower count in a request handler

**Phase mapping:** Address in the Social phase when follow/notify features are designed.

---

### Pitfall 6: Migration Without a Test Suite Breaking Existing Features

**What goes wrong:** Adding new columns, tables, and relationships to `models.py` while running `db.create_all()` on startup does NOT apply ALTER TABLE to existing databases. New columns silently don't exist in production. Queries against new columns fail with `OperationalError: no such column`. The no-test-suite constraint means there is no regression safety net.

**Why it happens:** `db.create_all()` only creates tables that do not exist — it never alters existing tables. The existing codebase uses this pattern (`app.py line 54`). This has worked so far because no schema changes were needed. The incoming milestone adds ~5 new tables and multiple new columns.

**Consequences:**
- New features silently fail in any environment where the DB was created before the schema change
- Contributors lose work (post created but tags not saved) with no error message
- Recovery requires manual `ALTER TABLE` or a full DB recreate (losing all data)

**Prevention:**
- Introduce Flask-Migrate (Alembic) at the start of this milestone — this is non-negotiable given the schema changes ahead
- First migration: capture the current schema as the baseline
- Every subsequent schema change goes through `flask db migrate` + `flask db upgrade`
- Never rely on `db.create_all()` for schema evolution going forward
- Before each migration: back up `instance/database.db` — automated or manual, but documented

**Detection (warning signs):**
- A new column added to a model class that doesn't appear when you query an existing record
- `OperationalError: no such column` in logs after adding a model attribute
- Route that uses a new relationship returning empty results unexpectedly

**Phase mapping:** Must be addressed as the first task of this milestone — before any other schema changes. All subsequent phases depend on this being correct.

---

### Pitfall 7: AI Tag Suggestions Polluting the Tag Namespace

**What goes wrong:** AI generates free-text tag suggestions like "golden hour", "Golden Hour", "golden-hour", "goldenHour". All are stored as separate tags. The tag browse page becomes a mess of near-duplicates. Search by tag misses posts because the user searched "golden hour" but the post was tagged "golden-hour".

**Why it happens:** Without normalisation at write time, each AI call produces its own formatting. Human contributors add their own variations. No deduplication logic.

**Consequences:**
- Tag browse is unusable — 200 tags when there are really 40 concepts
- Tag-based search returns incomplete results
- AI tag suggestions look low-quality, undermining trust in the feature

**Prevention:**
- Normalise all tags at write time: lowercase, strip leading/trailing whitespace, replace spaces with hyphens (or vice versa — pick one and enforce it consistently)
- Apply normalisation in the Tag model's `__init__` or in a dedicated `normalise_tag()` utility function
- When AI suggests tags, pass them through the same normalisation before INSERT
- Use `INSERT OR IGNORE` / `first_or_create` pattern to avoid duplicate tag rows
- Consider a tag allowlist or human-review step for AI-generated tags before they are visible

**Detection (warning signs):**
- Tags table has near-duplicate entries differing only in case or punctuation
- Tag cloud shows many single-post tags

**Phase mapping:** Address in the AI Features phase when tag suggestion is built. The normalisation function must exist before the first AI tag is written.

---

## Moderate Pitfalls

---

### Pitfall 8: App Context Lost in Background Threads

**What goes wrong:** Flask's application context (and therefore SQLAlchemy's `db.session`) is request-scoped. A background thread that calls `db.session.query(...)` outside a request context raises `RuntimeError: Working outside of application context`.

**Why it happens:** The AI background thread (introduced to fix Pitfall 1) runs outside the HTTP request. This is a known Flask footgun that catches every developer the first time.

**Consequences:** AI processing silently fails; the thread dies with an unlogged exception; the `ai_description` column is never populated.

**Prevention:**
- Wrap all background thread DB work in `with app.app_context():` — pass the `app` instance (not `current_app`) to the thread
- Pattern: `def background_task(app, post_id): with app.app_context(): ...`
- Add logging in the background thread's exception handler — silent failures are worse than noisy ones

**Detection (warning signs):** `RuntimeError: Working outside of application context` — usually only visible if the thread has a try/except that logs it.

**Phase mapping:** AI Features phase — implement correctly from the start.

---

### Pitfall 9: Notification Spam Driving Users Away

**What goes wrong:** A followed contributor posts 10 photos in one session. The user receives 10 separate "new post" notifications. A comment thread with 30 replies sends 30 notifications to the original poster. Users disable notifications or disengage entirely.

**Why it happens:** Naive "create notification on event" logic without deduplication or grouping.

**Consequences:** Notification bell has 50+ unread items; users mark all as read without looking; the feature provides no signal.

**Prevention:**
- Group notifications by type and source within a time window: "3 new posts from @alice" not 3 separate items
- For comments: notify only on first comment per post per commenter per session window, not on every reply
- Add "notification preferences" UI in a later phase — start simple (one notification type per event, grouped) rather than building full preferences infrastructure on day one
- Mark as read in bulk (single UPDATE, not N UPDATEs)

**Detection (warning signs):** Manual testing — follow an active contributor and count how many notifications appear after a single post session.

**Phase mapping:** Social phase — design grouping logic before writing the notification creation code.

---

### Pitfall 10: Feed Query Returning Stale or Incorrect Results Due to Missing Index on Follow Relationship

**What goes wrong:** The follow feed query joins `posts` to a `follows` table on `follower_id`. Without an index on `follows.follower_id`, every feed page load does a full scan of the follows table. At 1,000 users with an average of 20 follows each, this is 20,000 rows scanned per feed load.

**Why it happens:** The existing codebase has no indexes on foreign keys (`CONCERNS.md`). New tables added without explicit index declarations continue this pattern.

**Prevention:**
- Add `Index('ix_follows_follower_id', 'follower_id')` to the Follow model at creation time
- Add `Index('ix_follows_followed_id', 'followed_id')` as well (needed for "who follows me" queries)
- Add `Index('ix_notifications_user_id', 'user_id')` on the Notification model
- Add `Index('ix_post_tags_tag_id', 'tag_id')` and `('post_id')` on the post-tag association table
- Review all existing models and add FK indexes in the first migration

**Phase mapping:** Social phase foundation — create indexes in the migration that introduces the follow tables.

---

### Pitfall 11: CSRF Vulnerability Worsened by New POST Endpoints

**What goes wrong:** The existing app has no CSRF protection. New endpoints — follow/unfollow, mark notification read, add tag, generate AI description — are all POST endpoints. Each new endpoint increases the attack surface. A malicious page can cause authenticated users to silently follow accounts, generate AI calls (incurring cost), or mark all notifications read.

**Why it happens:** The existing codebase explicitly defers CSRF fixes. New features built on the same pattern inherit the vulnerability.

**Consequences:** Follow-spamming attacks, forced AI API calls burning the application's budget, notification manipulation.

**Prevention:**
- The milestone explicitly defers full CSRF hardening, but new AJAX endpoints (AI generation trigger, follow/unfollow) should at minimum check `X-Requested-With: XMLHttpRequest` header as a minimal CSRF mitigation for XHR-only endpoints
- Document each new POST endpoint in `CONCERNS.md` at the time it is added
- Plan Flask-WTF CSRF integration as a named task in a future security milestone — not during this milestone, but not indefinitely deferred either

**Phase mapping:** Note in each phase where new POST endpoints are added. Full fix in a dedicated security phase.

---

### Pitfall 12: Local File Storage Incompatible with Multi-Process Deployment

**What goes wrong:** Photos are stored in `uploads/` on local disk. If the application is ever run with multiple worker processes (gunicorn with 2+ workers), workers on different machines or processes cannot see each other's uploads. Even on a single machine, a redeploy that replaces the app directory loses all uploads.

**Why it happens:** This is already flagged in `CONCERNS.md` as a fragile area. AI features worsen it: AI tag/description results are stored in the DB, but the original images that were sent to the AI must be readable at AI-call time, which happens in a background thread potentially after the HTTP response has completed.

**Prevention:**
- Ensure AI calls happen before the upload request context ends, OR pass the full file path (not a file handle) to the background thread
- Do not add object storage migration to this milestone, but ensure the AI integration does not assume the file will be reachable at an arbitrary later time (e.g., scheduled reprocessing jobs will fail if uploads are wiped)
- Document the local-storage constraint explicitly in the AI Features phase plan

**Phase mapping:** AI Features phase — verify file path access in background thread before shipping.

---

## Minor Pitfalls

---

### Pitfall 13: `db.create_all()` Race on Startup with Background Thread

**What goes wrong:** `db.create_all()` runs at startup. If an AI background thread fires before `create_all()` completes (theoretically possible if a request arrives during startup), it may see an incomplete schema.

**Prevention:** Ensure `db.create_all()` (or `flask db upgrade`) completes before the first request is served. In practice this is not an issue with Flask's development server but worth noting for production WSGI deployments.

**Phase mapping:** Infrastructure phase if production deployment is added.

---

### Pitfall 14: AI Description/Tag Results Displayed Before Moderation

**What goes wrong:** AI generates a tag "nude" or a description with inappropriate content for an ambiguous photo. This is surfaced directly to other users without admin review.

**Prevention:**
- Store AI suggestions in a "pending" state visible only to the contributor
- Contributor accepts/edits before tags or description become public
- This is also good UX — contributors feel in control of AI suggestions

**Phase mapping:** AI Features phase — the accept/edit flow is part of the feature design, not an afterthought.

---

### Pitfall 15: Sidebar Context Processor Queries Amplified by New Pages

**What goes wrong:** Every request fires a `SidebarContent` DB query. The incoming milestone adds new page types (tag browse, feed, notification list, album view). Each new page hits this query. Currently noted as LOW impact in `CONCERNS.md` but cumulative impact grows with new endpoints.

**Prevention:** Add simple `functools.lru_cache` or Flask-Caching with a 60-second TTL to the `inject_sidebar()` context processor during this milestone. The sidebar content changes rarely; caching it is trivial and eliminates the growing per-request cost.

**Phase mapping:** Any phase — low-effort fix worth doing alongside other route work.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| AI Features — photo upload | Blocking API call (Pitfall 1) | Background thread + nullable result columns |
| AI Features — tag generation | Cost blowout (Pitfall 2) | Single call per post, resize before send, daily cap |
| AI Features — tag generation | Tag namespace pollution (Pitfall 7) | Normalise tags at write time |
| AI Features — background thread | App context loss (Pitfall 8) | `with app.app_context():` wrapper |
| AI Features — local file read | File path access in thread (Pitfall 12) | Pass absolute path, verify access before thread starts |
| Social — follow system | SQLite write lock (Pitfall 3) | WAL mode before any fan-out writes |
| Social — follow system | Missing indexes (Pitfall 10) | Declare indexes in the follow table migration |
| Social — feed | N+1 queries (Pitfall 4) | `joinedload()` + `SQLALCHEMY_ECHO` in dev |
| Social — notifications | Fan-out blocking response (Pitfall 5) | Background job, bulk INSERT |
| Social — notifications | Notification spam (Pitfall 9) | Group by type + time window |
| Any phase — schema change | Migration without Alembic (Pitfall 6) | Flask-Migrate first task of milestone |
| Any phase — new POST endpoint | CSRF surface growth (Pitfall 11) | Document each endpoint; plan WTF migration |

---

## Sources

- Training knowledge: Flask documentation on application context and threading
- Training knowledge: SQLAlchemy documentation on eager loading and WAL mode
- Training knowledge: OpenAI/Anthropic vision API pricing models (MEDIUM confidence — verify current pricing before budgeting)
- Training knowledge: SQLite WAL mode behaviour under concurrent writes
- Existing codebase analysis: `.planning/codebase/CONCERNS.md`, `.planning/codebase/ARCHITECTURE.md`
- Note: Live web search was unavailable during this research session. All claims are MEDIUM confidence. Verify Flask 3.0 + SQLAlchemy 2.0 specific behaviours against current official documentation before implementation.
