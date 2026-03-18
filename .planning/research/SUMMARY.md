# Project Research Summary

**Project:** Flask Photo Blog — AI-Enhanced Community Platform
**Domain:** AI-enhanced photo blog community (curated, small-membership)
**Researched:** 2026-03-18
**Confidence:** MEDIUM

## Executive Summary

This is a Flask monolith extension project — not a greenfield build. The existing platform already has authentication, posts, images, comments, ratings, direct messaging, and curated admin-only membership. The incoming milestone adds five connected feature domains: tagging/discovery, albums/collections, AI-assisted content creation (vision + text), social graph (follows + activity feed), and in-app notifications. All research confirms this should remain a monolith; no microservices are warranted at this scale. The right approach is to introduce a thin services layer (`services/`), a background task module (`tasks/`), and new blueprints — extending the existing architecture rather than restructuring it.

The recommended stack adds exactly two new packages: `anthropic` (Claude vision API) and `python-dotenv` (API key management). Everything else — social graph, tagging, albums, notifications — is implemented with existing SQLAlchemy patterns and zero additional dependencies. The single most important architectural constraint is that AI vision API calls must never block the upload request; a background thread with proper Flask app context is the correct solution at SQLite scale. Celery is explicitly deferred because it requires broker infrastructure incompatible with the project's SQLite-only, no-infra constraints.

The two highest-consequence risks are: (1) missing database migration infrastructure — the existing `db.create_all()` pattern silently breaks when adding columns to existing tables, and this milestone adds five new tables and new relationships; and (2) synchronous AI API calls in route handlers — a mistake that makes uploads unusable and is hard to retrofit. Both must be fixed before any feature work begins. A third systemic risk is SQLite write contention under social load, mitigated by enabling WAL mode before introducing any fan-out writes.

## Key Findings

### Recommended Stack

The existing stack (Flask 3.x, Flask-SQLAlchemy 3.x, Flask-Login, Werkzeug, Pillow, SQLite) is extended, not replaced. The only new runtime dependencies are `anthropic>=0.25.0` for Claude vision/text API calls and `python-dotenv>=1.0.0` for secure API key management. All social, tagging, album, and notification features are pure SQLAlchemy — no additional libraries required.

For the AI layer, Claude 3 Haiku is recommended for automated photo analysis on upload (cost-efficient, fast, structured output); Claude 3.5 Sonnet for the on-demand writing assistant (higher prose quality justifies cost when the user explicitly requests it). Background AI processing uses Python `threading` (stdlib) with a pushed Flask app context — the correct choice given SQLite's single-writer model and the absence of broker infrastructure. Flask-Migrate (Alembic) is added as a non-negotiable prerequisite for schema management.

**Core technologies:**
- `anthropic` SDK: Claude vision + text API — only viable AI option given no GPU infra; Haiku for batch tagging, Sonnet for writing assistant
- `python-dotenv`: `.env` file loading — required before any API key enters the codebase
- `threading` (stdlib): background AI task dispatch — zero new deps, correct for SQLite scale; Celery upgrade path preserved
- Flask-Migrate (Alembic): schema migrations — non-negotiable given 5 new tables incoming
- SQLAlchemy M2M patterns (built-in): tags, follows, albums — no external library needed

### Expected Features

Research against comparable platforms (Flickr, 500px, Glass, VSCO, Pixelfed) confirms a clear priority ordering. Tags and follows are foundational — without them the platform feels abandoned. Albums and activity feed are expected once follows exist. AI features are differentiating, not expected, which means their absence doesn't damage the product but their presence (done well) is meaningfully valued.

**Must have (table stakes):**
- Tag posts + browse by tag — discoverability baseline; every photo platform has it
- Albums/collections — users expect to group thematically related posts
- Follow other contributors — absent = no reason to return
- Activity feed (followed users) — if follow exists, users expect a personalised feed
- In-app notifications (new follower, new comment, new post from followed) — bell icon is now a universal pattern
- Search extended to include tags — once tags exist, users expect search to cover them

**Should have (differentiators):**
- AI-generated description suggestion (draft-first, non-blocking, contributor reviews before publish)
- AI tag suggestions (checkbox UX, contributor confirms; normalised at write time)
- AI writing assistant (on-demand "Improve" button, modal/side-by-side UX, synchronous call acceptable)
- Tag discovery index (popular tags, counts, recent posts — exploration without searching)

**Defer (v2+):**
- Real-time notifications (WebSockets/SSE) — disproportionate infrastructure for this community size
- Email notifications — requires email service, deliverability, unsubscribe flows
- Rating notifications — noise-to-value ratio too high at low content volume
- Follow counts/leaderboards — degrades small community health with status competition
- Infinite scroll — hard with SSR + SQLite; pagination works fine

### Architecture Approach

The architecture remains a monolith with three additions: a `services/` directory (thin plain-Python functions for AI, social, and notification business logic), a `tasks/` directory (background thread wrapper, swappable to Celery later), and three new blueprints (`ai.py`, `social.py`, `notifications.py`). Existing blueprints are unchanged except `photos.py` (gains AI enqueue hook) and `posts.py` + `comments.py` (gain notification side effects). All new DB changes are additive — five new tables, no column removals, no renaming.

**Major components:**
1. `services/ai_service.py` — builds Claude API payload, base64-encodes images, parses vision response, writes AIResult; called from background task only
2. `services/social_service.py` — follow/unfollow logic, activity feed query with eager loading
3. `services/notif_service.py` — notification creation (bulk insert), inbox query, mark-as-read; called as side effect from follow/post/comment routes
4. `tasks/ai_tasks.py` — background thread wrapper; pushes Flask app context before any DB or API work
5. Models (extended): Tag, PostTag, Album, AlbumPost, Follow, Notification, AIResult — all additive new tables

### Critical Pitfalls

1. **Missing DB migration infrastructure** — `db.create_all()` never alters existing tables; adding columns to `images` or `posts` silently fails in any pre-existing database. Fix: introduce Flask-Migrate as the first task, run `flask db stamp head`, then all subsequent schema changes go through Alembic.

2. **Synchronous AI API calls in route handlers** — vision calls take 5–30 seconds; inline calls freeze the upload endpoint and the entire dev server. Fix: always dispatch to `threading.Thread` after `db.session.commit()`; store `ai_status = 'pending'`; UI polls `/ai/status/<image_id>`.

3. **SQLite write lock deadlocks under social load** — fan-out notification writes (one INSERT per follower on post creation), background AI thread writes, and foreground request writes all compete for SQLite's single write lock. Fix: enable `PRAGMA journal_mode=WAL` before any fan-out writes; set `connect_args={"check_same_thread": False, "timeout": 20}`; batch-insert notifications in a single transaction.

4. **AI tag namespace pollution** — AI generates "golden hour", "Golden Hour", "golden-hour" as separate tags. Fix: normalise all tags at write time (lowercase, consistent separator) via a `normalise_tag()` utility applied to both human input and AI suggestions before any INSERT.

5. **N+1 queries in feed and tag browsing** — SQLAlchemy lazy-loads relationships; a 20-post feed triggers 80–160 queries. Fix: use `joinedload(Post.images)`, `joinedload(Post.author)`, `selectinload(Post.tags)` on all list queries; enable `SQLALCHEMY_ECHO = True` in dev config to surface problems immediately.

## Implications for Roadmap

Based on the combined research, architecture dependency graph, and pitfall phase mapping, the following five-phase structure is recommended:

### Phase 1: DB Migration Infrastructure
**Rationale:** Every subsequent phase touches the DB schema. Without Alembic in place, any schema change risks silent data loss on existing databases. This is a non-negotiable prerequisite — confirmed by both ARCHITECTURE.md and PITFALLS.md (Pitfall 6). Zero new features ship in this phase, but all subsequent phases depend on it.
**Delivers:** Flask-Migrate integrated, existing schema stamped as baseline, `flask db migrate/upgrade` workflow verified, SQLite WAL mode enabled, `db.create_all()` kept as fresh-install fallback only.
**Avoids:** Pitfall 6 (migration without Alembic), Pitfall 3 (SQLite write locks — WAL mode set here).

### Phase 2: Discovery Layer (Tags + Albums)
**Rationale:** Tags are a dependency for AI tag suggestions (AI needs the tag vocabulary to exist before it can suggest from it). Albums are pure CRUD with no async concerns, no social dependencies — lowest-risk phase to build. Both are table-stakes features with well-documented patterns.
**Delivers:** Tag model, PostTag association, tag input on post form, tag browse page, search extended to tags; Album model, AlbumPost association, album CRUD, album gallery, profile shows contributor albums.
**Uses:** SQLAlchemy M2M patterns (built-in), Flask-Migrate for schema changes.
**Implements:** Discovery layer components; extends existing `posts.py` route minimally.
**Avoids:** Pitfall 7 (tag namespace pollution — normalise_tag() utility built here before any AI tags are written).

### Phase 3: AI Features
**Rationale:** Depends on Phase 2 (tag vocabulary must exist for AI tag suggestions). Self-contained — no social dependency. This is the highest-complexity phase and the project's primary differentiator. Must be built correctly the first time; retrofit is prohibitively expensive (Pitfall 1).
**Delivers:** `anthropic` SDK integration, `python-dotenv` `.env` setup, AIResult model, background thread task runner, AI description suggestion (draft UX), AI tag suggestions (checkbox UX), AI writing assistant (on-demand modal UX), `/ai/status/<image_id>` polling endpoint, per-post API call cap, image resizing before API submission.
**Uses:** `anthropic>=0.25.0`, `python-dotenv>=1.0.0`, `threading` (stdlib), Claude 3 Haiku (analysis), Claude 3.5 Sonnet (writing assistant).
**Avoids:** Pitfall 1 (blocking API calls), Pitfall 2 (cost blowout), Pitfall 8 (app context lost in threads), Pitfall 12 (file path access in background thread), Pitfall 14 (AI output bypassing contributor review).

### Phase 4: Social Graph (Follows + Activity Feed)
**Rationale:** Depends only on Phase 1 (Alembic). No dependency on tags or AI. Comes before notifications because the Follow model is a prerequisite for the `new_follower` notification type and `new_post_from_followed` notification type.
**Delivers:** Follow association table, User model extended with `following`/`followers` relationships, follow/unfollow endpoints, activity feed (posts from followed users with pagination), DB indexes on `follows.follower_id` and `follows.followed_id`.
**Implements:** `services/social_service.py`, `routes/social.py` blueprint.
**Avoids:** Pitfall 3 (SQLite write locks — WAL already set in Phase 1), Pitfall 4 (N+1 queries — joinedload on feed), Pitfall 10 (missing indexes on follow table).

### Phase 5: Notifications
**Rationale:** Cross-cutting feature wired into multiple existing routes as side effects. Building last minimises the blast radius of wiring notification creation into comments, posts, and follow routes. Depends on Phase 4 (Follow model for `new_follower` and `new_post_from_followed` types).
**Delivers:** Notification model, `services/notif_service.py`, `/notifications` inbox page, unread count badge in nav (via context processor), mark-as-read (bulk and individual), notification side effects wired into `comments_bp`, `posts_bp`, `social_bp`. Sidebar context processor cached (low-effort, reduces cumulative query load from new pages).
**Implements:** `routes/notifications.py` blueprint, notification side effects in existing routes.
**Avoids:** Pitfall 5 (fan-out blocking response — bulk INSERT, background job if needed), Pitfall 9 (notification spam — group by type + time window), Pitfall 15 (sidebar query amplified by new pages — cache here).

### Phase Ordering Rationale

- Migrations first: every phase adds DB schema; building on a broken migration foundation causes cascading failures.
- Tags before AI: the AI tag suggestion feature needs the `tags` table and `normalise_tag()` utility to already exist or it either fails silently or creates a polluted namespace from day one.
- AI before social: AI is self-contained (no social dependency), higher complexity, higher value — better to isolate the hardest phase before introducing social complexity.
- Social before notifications: `new_follower` and `new_post_from_followed` notification types require the Follow model; wiring order prevents forward references.
- Notifications last: they are side effects wired into multiple existing routes; doing this last means all the routes they hook into are already stable.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (AI Features):** Claude API current model names, SDK version, and pricing should be verified at docs.anthropic.com and pypi.org/project/anthropic before implementation — all MEDIUM confidence due to unavailable web search during research. The threading + Flask app context pattern needs a working spike before committing to the implementation design.
- **Phase 1 (DB Migration):** The `flask db stamp head` procedure for existing databases without prior Alembic history is well-documented but should be tested against a copy of the production database before running in place.

Phases with standard patterns (skip research-phase):
- **Phase 2 (Tags + Albums):** Pure SQLAlchemy CRUD — well-documented, no async concerns, no external APIs. Standard patterns apply.
- **Phase 4 (Social Graph):** Self-referential SQLAlchemy M2M is a documented pattern. Feed query is a standard filtered post query. No exotic patterns.
- **Phase 5 (Notifications):** DB-polled notifications with a context processor badge are a well-established Flask pattern. No new infrastructure.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | `anthropic` SDK version and Claude model names are training-data-based; verify at pypi.org and docs.anthropic.com before implementation. `python-dotenv` and Flask-Migrate patterns are HIGH confidence. Threading + app context is HIGH confidence (established Flask pattern). |
| Features | MEDIUM | Table stakes analysis based on training knowledge of comparable platforms (Flickr, 500px, Glass, VSCO). No live platform research available. Feature prioritisation is HIGH confidence (derived directly from existing PROJECT.md constraints). |
| Architecture | MEDIUM-HIGH | Flask/SQLAlchemy patterns verified via official Flask docs (Celery integration doc, async-await doc, app factory doc). SQLite WAL mode and concurrent write behaviour are documented. Services layer pattern is established. |
| Pitfalls | MEDIUM | Core Flask/SQLite pitfalls (blocking calls, WAL mode, N+1, app context) are well-documented and stable. Specific Flask 3.0 + SQLAlchemy 2.0 interaction edge cases not live-verified. |

**Overall confidence:** MEDIUM

### Gaps to Address

- **Claude API current state:** Model names (`claude-3-haiku-20240307`, `claude-3-5-sonnet-20241022`), SDK version (`>=0.25.0`), and pricing must be verified at docs.anthropic.com and pypi.org before the AI Features phase begins. If these have changed, the implementation choices may shift (e.g., a newer cheaper model changes the Haiku vs Sonnet split).
- **`flask db stamp head` on existing database:** Must be tested against a copy of `instance/database.db` in a staging environment before running in production. Alembic's stamp procedure is documented but carries risk if the existing schema has drifted from what models.py describes.
- **AI cost per call at current pricing:** Pitfall 2 prevention (per-post cap, image resizing) is essential but the specific thresholds (daily cap numbers, image resize dimensions) should be calibrated against current Anthropic pricing before the AI phase ships.
- **SQLite WAL mode persistence:** WAL mode set via `PRAGMA` is persistent across connections for the same database file, but verify this holds under the WSGI server being used (dev server vs gunicorn) before relying on it.

## Sources

### Primary (HIGH confidence)
- Flask official docs (patterns/celery, async-await, appfactories) — background task patterns, app context, app factory
- SQLAlchemy official docs — M2M patterns, self-referential relationships, eager loading
- Direct codebase read (PROJECT.md, models.py, CONCERNS.md, spec.md) — existing constraints and scope

### Secondary (MEDIUM confidence)
- Training knowledge of photo community platforms (Flickr, 500px, Glass, VSCO, Pixelfed, August 2025 cutoff) — feature expectations
- Training knowledge of Anthropic Claude API (models, vision capability, SDK) — AI stack choices
- Training knowledge of SQLite WAL mode and concurrent write behaviour — Pitfall 3 mitigation
- Training knowledge of AI description/tagging UX patterns (Google Photos, Apple Photos) — UX pattern recommendations

### Tertiary (LOW confidence — verify before use)
- `anthropic` SDK version >=0.25.0 — verify at pypi.org/project/anthropic
- Claude 3 model names and availability — verify at docs.anthropic.com/en/docs/about-claude/models
- Current AI API pricing — verify at console.anthropic.com before budgeting cost controls

---
*Research completed: 2026-03-18*
*Ready for roadmap: yes*
