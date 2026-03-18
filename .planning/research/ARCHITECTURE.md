# Architecture Patterns

**Domain:** AI-enhanced photo blog community (Flask monolith extension)
**Researched:** 2026-03-18
**Confidence:** MEDIUM — Flask/SQLAlchemy patterns verified via official docs; async/Celery from official Flask docs; social graph and notification patterns from established SQLAlchemy conventions

---

## Existing Architecture (Baseline)

The current app is a clean monolith:

```
HTTP Request
    → Flask router
        → Blueprint route handler (business logic lives here)
            → SQLAlchemy models (User, Post, Image, Comment, Rating, Message, SidebarContent)
                → SQLite (instance/database.db)
    → render_template() or redirect()
HTTP Response
```

No service layer. No background workers. No event system. All logic is inline in route handlers. The app factory in `app.py` calls `db.create_all()` on startup — meaning the current schema is managed entirely by `db.create_all()`, not migrations.

**Key constraint for new features:** `db.create_all()` is idempotent for existing tables (it adds missing tables, never alters existing columns). This is safe to keep using for net-new tables, but adding columns to existing tables (e.g., adding `ai_status` to `images`) requires either a migration tool or a manual ALTER TABLE.

---

## Recommended Architecture for New Features

The three new feature domains (AI processing, social graph, notifications) each have different integration requirements. They can all remain within the monolith — no microservices needed at this scale.

### Revised Layer Model

```
┌─────────────────────────────────────────────────────────────┐
│                    Templates (Jinja2)                        │  Presentation
├─────────────────────────────────────────────────────────────┤
│                  Routes / Blueprints                         │  Controllers
│   (ai_bp, social_bp, notifications_bp  ← new)               │
├─────────────────────────────────────────────────────────────┤
│              Services Layer  ← NEW (thin)                    │  Business Logic
│   ai_service.py  |  social_service.py  |  notif_service.py  │
├─────────────────────────────────────────────────────────────┤
│                    Models (SQLAlchemy)                        │  Data / ORM
│   + Tag, PostTag, Album, AlbumPost,                          │
│   + Follow, Notification, AIResult  ← new                   │
├─────────────────────────────────────────────────────────────┤
│                 Background Worker  ← NEW                     │  Async Tasks
│   tasks/ai_tasks.py  (threading or Celery)                   │
├─────────────────────────────────────────────────────────────┤
│              SQLite (instance/database.db)                   │  Persistence
└─────────────────────────────────────────────────────────────┘
```

**Why add a thin services layer:** The existing routes mix HTTP concerns with data logic. AI and social features involve multi-step logic (call API, parse result, write to DB, trigger notification) that cannot be cleanly expressed in a single route handler. A `services/` directory with plain Python functions (not classes) keeps routes thin and logic testable without introducing a full repository pattern.

---

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `routes/ai.py` | HTTP endpoints for AI status polling, writing assistant trigger | `services/ai_service.py` |
| `routes/social.py` | Follow/unfollow, activity feed view | `services/social_service.py` |
| `routes/notifications.py` | Render notification inbox, mark read | `services/notif_service.py` |
| `services/ai_service.py` | Build API payload, call vision API, parse response, write AIResult to DB | Vision API (external), `models.AIResult` |
| `services/social_service.py` | Follow/unfollow logic, build feed query | `models.Follow`, `models.Post` |
| `services/notif_service.py` | Create notification records, mark as read | `models.Notification` |
| `tasks/ai_tasks.py` | Deferred AI processing (background thread or Celery task) | `services/ai_service.py`, Flask app context |
| `models.py` (extended) | New tables: Tag, PostTag, Album, AlbumPost, Follow, Notification, AIResult | SQLite via SQLAlchemy |

**Existing blueprints are not modified** except `routes/photos.py`, which gains a post-save hook to enqueue the AI analysis task.

---

## Data Flow: AI Processing (Async)

AI calls must be non-blocking per project constraint. The recommended pattern is a background thread launched from the route handler — simpler than Celery because it requires no broker infrastructure (no Redis, no separate worker process).

**Caveat on background threads in Flask:** A background thread spawned from a route handler does not automatically have a Flask application context. The thread must push its own app context or receive `current_app._get_current_object()` before the thread starts. This is the primary implementation risk.

**Celery is the cleaner alternative** (verified: official Flask docs recommend it explicitly) but requires a running broker — Redis is the standard choice, which adds infrastructure. For a dev/hobbyist deployment staying on SQLite, the threading approach is practical. The architecture should be designed so swapping to Celery later is a one-file change in `tasks/ai_tasks.py`.

```
Photo upload (POST /post/<id>/upload)
    → photos_bp.upload() route handler
        → saves file to disk (existing behavior, unchanged)
        → saves Image row (existing behavior, unchanged)
        → db.session.commit()
        → [NEW] enqueue_ai_analysis(image_id, post_id)
            → background thread (or Celery delay())
                → push Flask app context
                → read image file from disk
                → base64-encode image
                → call Vision API (Claude or OpenAI)
                → parse: description, suggested_tags[]
                → write AIResult row (image_id, status, description, tags_json)
                → db.session.commit()
        → redirect to post detail (immediate — does not wait for AI)

Later: contributor visits post edit page
    → polls /ai/status/<image_id>  (JSON endpoint)
        → returns AIResult.status + content if ready
    → JS on page renders suggestions inline
```

**AI result storage schema:**

```
AIResult
    id              INT PK
    image_id        INT FK → images.id
    status          VARCHAR(20)  -- 'pending', 'complete', 'failed'
    description     TEXT         -- AI-generated description suggestion
    tags_json       TEXT         -- JSON array of suggested tag strings
    created_at      DATETIME
    completed_at    DATETIME NULL
```

**No column changes to existing tables.** AI results are additive — they sit in their own table and are optional. The contributor sees them if available; the workflow is unchanged if AI fails.

---

## Data Flow: Writing Assistant (On-Demand)

Different from photo analysis — the writing assistant is triggered explicitly by the contributor on the post edit page, not automatically on upload. This is a synchronous call acceptable because the contributor is actively waiting for it.

```
Contributor clicks "Improve with AI" on post edit page
    → POST /ai/improve-text  (AJAX or form POST, returns JSON)
        → ai_bp route
            → services/ai_service.improve_text(post_id, current_text)
                → call LLM text API (no image, just prompt + text)
                → return improved text suggestion
        → JSON response with suggestion
    → JS inserts suggestion into textarea (contributor accepts/rejects)
```

This is synchronous but fast (text-only LLM call, ~1–3 seconds). No background worker needed.

---

## Data Flow: Social Graph (Follows + Feed)

The social graph is a self-referential many-to-many relationship on the `users` table. The standard SQLAlchemy approach uses an association table.

**New table:**

```
follows (association table)
    follower_id     INT FK → users.id
    followed_id     INT FK → users.id
    created_at      DATETIME
    PK: (follower_id, followed_id)
```

**Adding to User model (additive — no change to existing columns):**

```python
follows_table = db.Table('follows',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('followed_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

# In User model:
following = db.relationship(
    'User',
    secondary=follows_table,
    primaryjoin=(follows_table.c.follower_id == id),
    secondaryjoin=(follows_table.c.followed_id == id),
    backref='followers',
    lazy='dynamic'
)
```

**Activity feed query:** The feed is a filtered version of the existing post feed — posts where `author_id IN (followed user IDs)`. No separate feed table needed at this scale.

```python
# services/social_service.py
def get_feed_for_user(user_id, page=1, per_page=10):
    followed_ids = db.session.query(follows_table.c.followed_id)\
        .filter(follows_table.c.follower_id == user_id).subquery()
    return Post.query\
        .filter(Post.author_id.in_(followed_ids))\
        .order_by(Post.created_at.desc())\
        .paginate(page=page, per_page=per_page)
```

This query is a straight SQLite join — no fan-out, no denormalized feed table. Acceptable for a curated community of dozens to low hundreds of users. Would need rethinking at thousands of follows, but that is not this project's scale.

---

## Data Flow: Notifications

Notifications are generated as side effects of social actions. They are stored in DB and polled on page load — no WebSockets (out of scope per PROJECT.md).

**New table:**

```
notifications
    id              INT PK
    recipient_id    INT FK → users.id
    actor_id        INT FK → users.id NULL  -- who triggered it
    type            VARCHAR(30)  -- 'new_follower', 'comment_on_post', 'new_post_from_followed'
    ref_post_id     INT FK → posts.id NULL  -- relevant post, if any
    is_read         BOOLEAN default FALSE
    created_at      DATETIME
```

**Where notifications are created:**

| Trigger | Location | Notification type |
|---------|----------|------------------|
| User A follows User B | `social_bp.follow()` route, after `db.session.commit()` | `new_follower` → B |
| User comments on post | `comments_bp.add()` route, after commit | `comment_on_post` → post.author |
| Contributor creates post | `posts_bp.create()` route, after commit | `new_post_from_followed` → each follower |

The notification creation for "new post from followed" requires iterating `post.author.followers` — this can be slow if a contributor has many followers, but acceptable at community scale. This logic lives in `services/notif_service.py`, called from the route.

**Notification display:** A count badge on the nav (injected via the existing `context_processor` pattern or a new one), plus a `/notifications` inbox page.

---

## DB Migration Strategy

**Current state:** The app uses `db.create_all()` in `app.py`. This creates missing tables but does not alter existing ones.

**Recommended approach:** Introduce Flask-Migrate (Alembic) for the new milestone.

**Migration setup for existing database (critical steps):**

1. Add `Flask-Migrate` to `requirements.txt`, init `Migrate(app, db)` in `create_app()`
2. Run `flask db init` — creates `migrations/` directory
3. Run `flask db stamp head` — tells Alembic "the current DB is already at the latest revision" without running any migration. This is the key step that prevents Alembic from trying to recreate existing tables.
4. Add new models to `models.py`
5. Run `flask db migrate -m "add social and ai tables"` — generates migration script
6. Run `flask db upgrade` — applies it

**SQLite ALTER TABLE limitation:** SQLite does not support `ALTER TABLE ... ADD COLUMN` with constraints (no NOT NULL without default, no FK constraints added after creation). All new columns on new tables avoid this because new tables are created in full. If a column must be added to an existing table (e.g., adding `ai_status` to `images`), it must be nullable or have a default value — Alembic handles this automatically for SQLite via `batch_alter_table`.

**Do not remove `db.create_all()` immediately.** Keep it as a fallback for fresh installs. It is harmless once Alembic is managing the schema (Alembic tracks its own state in `alembic_version` table).

---

## Tags and Albums (Discovery Layer)

Tags and albums are simpler than social/AI — pure relational data, no async concerns.

**New tables:**

```
tags
    id          INT PK
    name        VARCHAR(50) UNIQUE

post_tags (association)
    post_id     INT FK → posts.id
    tag_id      INT FK → tags.id
    PK: (post_id, tag_id)

albums
    id          INT PK
    title       VARCHAR(200)
    description TEXT
    owner_id    INT FK → users.id
    created_at  DATETIME

album_posts (association)
    album_id    INT FK → albums.id
    post_id     INT FK → posts.id
    added_at    DATETIME
    PK: (album_id, post_id)
```

Tags are shared across all contributors (normalized). AI will suggest tag names from the `tags` vocabulary, or create new tags if no match is found.

---

## Patterns to Follow

### Pattern 1: Thin Route Handlers

Keep route handlers to HTTP concerns only (parse request, call service, render/redirect). Move multi-step logic into `services/`.

**Example — photo upload with AI enqueue:**
```python
@photos_bp.route('/post/<int:post_id>/upload', methods=['POST'])
@login_required
def upload(post_id):
    # ... existing file validation and save ...
    image = Image(post_id=post_id, filename=filename)
    db.session.add(image)
    db.session.commit()
    enqueue_ai_analysis(image.id, post_id)  # fire-and-forget
    flash(f'Photo uploaded.', 'success')
    return redirect(url_for('posts.detail', post_id=post_id))
```

### Pattern 2: App Context in Background Threads

```python
def enqueue_ai_analysis(image_id, post_id):
    app = current_app._get_current_object()
    def run():
        with app.app_context():
            ai_service.analyze_image(image_id)
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
```

The `daemon=True` prevents the thread from blocking server shutdown. Capture `_get_current_object()` before the thread starts — do not pass `current_app` proxy into the thread.

### Pattern 3: Additive DB Changes Only

Never rename or remove columns from existing tables. Add new tables. Add nullable columns to existing tables if absolutely necessary. This preserves backward compatibility with existing data.

### Pattern 4: Notification Side Effects at Commit Point

Create notifications inside route handlers after the primary `db.session.commit()` succeeds. This prevents phantom notifications if the primary write fails. Use a try/except around notification creation to ensure a failed notification does not roll back the user-facing action.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Synchronous Vision API Calls in Route Handlers

**What:** Calling the vision API inline during photo upload.
**Why bad:** Vision API calls take 2–10 seconds. The upload HTTP request blocks until the API responds. If the API is slow or down, uploads appear broken.
**Instead:** Always enqueue as a background task. Store status as `pending`, poll for completion.

### Anti-Pattern 2: SQLite Concurrent Writes from Background Threads

**What:** Background AI thread writing to SQLite while the web process is also writing.
**Why bad:** SQLite uses file-level locking. Concurrent writes from multiple threads cause `OperationalError: database is locked`.
**Instead:** Use `SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"timeout": 15}}` to add a retry window. Keep background writes short (single AIResult row). For the writing assistant endpoint (synchronous), use the main thread only.

### Anti-Pattern 3: Fan-Out Notification Writes on Post Create

**What:** Creating one notification row per follower synchronously during `POST /post/create`.
**Why bad:** If a contributor has 50 followers, post creation makes 50 DB writes before returning.
**Instead:** For this project's scale (curated community), 50 writes is acceptable. If it becomes a concern, move notification fan-out to the background thread pattern. Do not pre-optimize.

### Anti-Pattern 4: Storing AI Results in Existing Tables

**What:** Adding `ai_description`, `ai_tags` columns to the `images` table.
**Why bad:** Requires ALTER TABLE on existing table (SQLite limitations), ties AI state to the core image record, makes it hard to track pending/failed/retried states.
**Instead:** Use the separate `AIResult` table with a status column.

### Anti-Pattern 5: Using `db.create_all()` Alone After Alembic Is Introduced

**What:** Continuing to rely on `db.create_all()` for schema management after Flask-Migrate is added.
**Why bad:** `db.create_all()` silently skips existing tables; Alembic tracks state in `alembic_version`. They will diverge.
**Instead:** Use `flask db upgrade` for all schema changes after Alembic is initialized. Keep `db.create_all()` only as a fallback for brand-new installs where Alembic hasn't been run yet.

---

## Scalability Considerations

| Concern | At current scale (10s of users) | At 500 users | At 10K users |
|---------|----------------------------------|--------------|--------------|
| Activity feed query | Simple IN subquery on SQLite — fast | Still fine | Query time grows with follows; add index on `posts.author_id, posts.created_at` |
| Notification fan-out | Sync writes, acceptable | Acceptable | Move to background worker |
| AI task queue | Single background thread per upload | Multiple concurrent uploads may pile up threads | Switch to Celery + Redis |
| SQLite write contention | Background thread + main thread share DB; manageable with timeout | Risk increases | Migrate to PostgreSQL |
| Follow graph queries | Full scan acceptable | Add index on `follows.follower_id` | Denormalize follow counts |

**Recommended indexes to add with new tables:**

```sql
CREATE INDEX idx_follows_follower ON follows(follower_id);
CREATE INDEX idx_notifications_recipient ON notifications(recipient_id, is_read);
CREATE INDEX idx_post_tags_tag ON post_tags(tag_id);
CREATE INDEX idx_ai_results_image ON ai_results(image_id);
```

---

## Suggested Build Order

Dependencies between components determine sequencing:

```
Phase 1: DB Migration Infrastructure
    Flask-Migrate setup → stamp existing DB → verify migrations work
    (Everything else depends on clean migration tooling)

Phase 2: Discovery Layer (Tags + Albums)
    Models: Tag, PostTag, Album, AlbumPost
    No async concerns. No social dependencies.
    Route changes: post create/edit gets tag input; new albums blueprint.
    Search extended to tags/albums.
    → Safe to build first; pure CRUD, no dependencies on social or AI.

Phase 3: AI Processing
    Models: AIResult
    Services: ai_service.py
    Background task: tasks/ai_tasks.py (threading)
    Routes: ai_bp (status poll, writing assistant)
    Template changes: upload page, post edit page show AI suggestions
    → Depends on Phase 2 (tags table must exist — AI suggests tags to save)
    → Self-contained: no social dependency

Phase 4: Social Graph (Follows + Feed)
    Models: Follow (association table), extend User model
    Services: social_service.py
    Routes: social_bp (follow/unfollow, feed view)
    → Depends on Phase 1 (migrations)
    → No dependency on AI or tags

Phase 5: Notifications
    Models: Notification
    Services: notif_service.py
    Routes: notifications_bp (inbox, mark read)
    Nav badge via context_processor
    Side effects wired into: comments_bp, posts_bp, social_bp
    → Depends on Phase 4 (Follow model must exist for new_follower type)
    → Depends on Phase 3 (optional: notify on AI complete — can defer)
    → Wire-in to existing routes last to minimize blast radius
```

**Build order rationale:**
- Migrations first because every subsequent phase touches the DB schema
- Tags/Albums before AI because AI tag suggestions need the tags vocabulary to exist
- Social before notifications because the Follow relationship is referenced by the `new_follower` notification type
- Notifications last because they are cross-cutting side effects wired into multiple existing routes — doing this last reduces the risk of partially-wired notification logic

---

## File Structure Additions

```
blog-ai/
├── services/                   ← NEW
│   ├── __init__.py
│   ├── ai_service.py           # Vision API calls, text improvement
│   ├── social_service.py       # Follow logic, feed query
│   └── notif_service.py        # Notification creation, inbox query
│
├── tasks/                      ← NEW
│   ├── __init__.py
│   └── ai_tasks.py             # Background thread or Celery task wrapper
│
├── routes/
│   ├── ... (existing, unchanged except photos.py + posts.py + comments.py get notif side effects)
│   ├── ai.py                   ← NEW
│   ├── social.py               ← NEW
│   └── notifications.py        ← NEW
│
├── models.py                   ← EXTENDED (new model classes appended)
├── migrations/                 ← NEW (Flask-Migrate managed)
│   └── ...
```

---

## Sources

- Flask background tasks / Celery integration: https://flask.palletsprojects.com/en/stable/patterns/celery/ (HIGH confidence — official Flask docs)
- Flask async/await limitations: https://flask.palletsprojects.com/en/stable/async-await/ (HIGH confidence — official Flask docs)
- Flask application factory pattern: https://flask.palletsprojects.com/en/stable/patterns/appfactories/ (HIGH confidence — official Flask docs)
- SQLAlchemy self-referential many-to-many: SQLAlchemy official docs (MEDIUM confidence — standard documented pattern, verified against docs.sqlalchemy.org)
- Flask-Migrate stamp command for existing DBs: MEDIUM confidence — established community pattern, WebFetch blocked; based on Alembic's documented `stamp` command purpose
- SQLite concurrent write behavior: MEDIUM confidence — SQLite documentation and SQLAlchemy connection pool docs; file-level locking is documented SQLite behavior
- Background threading app context pattern: MEDIUM confidence — documented in Flask/Werkzeug `LocalProxy` behavior; `_get_current_object()` is the established workaround
