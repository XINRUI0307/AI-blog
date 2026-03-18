# Technology Stack

**Project:** Flask Photo Blog — AI-Enhanced Community Platform
**Researched:** 2026-03-18
**Confidence note:** External verification tools (WebSearch, WebFetch, Context7) were unavailable during this research session. All recommendations are based on training data (knowledge cutoff August 2025). Versions marked with [VERIFY] should be confirmed against PyPI/official docs before use.

---

## Existing Stack (Do Not Replace)

| Technology | Version | Role |
|------------|---------|------|
| Flask | >=3.0.0 | Web framework, routing, Blueprints |
| Flask-SQLAlchemy | >=3.1.0 | ORM, all models |
| Flask-Login | >=0.6.3 | Session management, auth |
| Werkzeug | >=3.0.0 | WSGI utils, password hashing |
| Pillow | >=10.0.0 | Image validation and processing |
| SQLite | (built-in) | Persistence layer |

All new choices must **extend** this stack, not replace it.

---

## Recommended Stack (New Additions)

### AI / Vision Layer

#### Primary: Anthropic Claude API (`anthropic` Python SDK)

**Confidence: MEDIUM** — Based on training data. Verify current model names and SDK version at https://pypi.org/project/anthropic/

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `anthropic` SDK | >=0.25.0 [VERIFY] | Claude vision API client | Claude 3 Haiku/Sonnet handles image-to-text (description generation, tag suggestion, writing assistance) in a single API. Haiku is cost-effective for automated tagging; Sonnet for writing assistant quality. |

**Model selection rationale:**
- `claude-3-haiku-20240307` — Use for automated photo description and tag generation on upload. Cheapest Claude 3 model, fast, sufficient for structured output tasks.
- `claude-3-5-sonnet-20241022` — Use for the on-demand writing assistant. Better prose quality justifies higher per-call cost when the user explicitly requests help.

**Image passing:** Claude vision accepts base64-encoded images inline in the `messages` array. Since photos are on local disk at `uploads/posts/<post_id>/<uuid>.ext`, they are read, base64-encoded, and sent as `image` content blocks. No external URL required. Supported formats: JPEG, PNG, GIF, WebP — matches what the app already accepts.

**Why not OpenAI GPT-4V:**
- GPT-4o vision capability is comparable. The decision is primarily cost and API simplicity.
- Claude 3 Haiku is cheaper per image analysis call than GPT-4o mini for comparable output quality on photo description tasks. [MEDIUM confidence — pricing changes frequently, verify before committing]
- If the team already has an OpenAI API key or prefers it, `openai>=1.0.0` is a drop-in alternative with the same approach.

**Why not open-source vision models (LLaVA, etc.):**
- Running local vision models requires GPU infrastructure this project does not have (constraints: local dev, SQLite, no infra). Cloud API is the correct choice here.

---

### Async Task Handling (AI Calls Must Not Block Upload)

**The constraint from PROJECT.md:** "AI calls: Must be non-blocking — photo upload must not wait for AI."

There are three realistic options for a Flask + SQLite stack at this scale:

#### Recommended: Python `threading` with Flask app context (built-in, zero deps)

**Confidence: HIGH** — Standard pattern for simple Flask background work.

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `threading` (stdlib) | N/A | Fire-and-forget AI calls after upload | Zero new dependencies. Flask app context can be pushed to background thread. Works with SQLite's write model since the thread does one write (save AI results) per job. Sufficient for a small community app — not Celery-scale. |

**Pattern:**
```python
import threading

def run_ai_analysis(app, post_id, image_paths):
    with app.app_context():
        # call Claude API, write results to DB
        ...

@photos_bp.route('/upload', methods=['POST'])
def upload():
    # ... save files ...
    t = threading.Thread(target=run_ai_analysis, args=(current_app._get_current_object(), post_id, paths))
    t.daemon = True
    t.start()
    return redirect(url_for('posts.edit', post_id=post_id))
```

**Why not Celery + Redis:**
- Celery requires a broker (Redis or RabbitMQ), a separate worker process, and operational overhead that is disproportionate for a small community blog running on SQLite.
- SQLite's single-writer model makes concurrent background workers risky (lock contention). Threading with careful app context is safer.
- Celery is the right choice if this project later migrates to PostgreSQL + production infra, but PROJECT.md explicitly defers production infrastructure.

**Why not Flask-RQ or Dramatiq:**
- Same broker dependency problem as Celery. Overkill for this scale.

**Limitation to flag:** If the AI call fails silently, the contributor sees no description/tags. The implementation must store a `ai_status` field (`pending` / `completed` / `failed`) on the post so the UI can show "AI analysis pending…" rather than a broken state. Threads are not retried automatically — failed jobs are lost. Acceptable for an optional AI feature, but must be documented.

---

### Tagging System

**Confidence: HIGH** — Pure SQLAlchemy pattern, no extra libraries needed.

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| SQLAlchemy many-to-many (built-in) | N/A | Post-tag relationships | The existing ORM already handles M2M. A `Tag` model + `post_tags` association table is idiomatic SQLAlchemy. No additional library warranted. |

**Why not Flask-Taggit or similar:**
- Flask-Taggit is Django-centric. Python-taggit equivalents for Flask are abandoned or thin wrappers around the same SQLAlchemy pattern you'd write yourself. Writing it directly gives full control and no version lock-in.

**Schema sketch:**
```python
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
```

---

### Social / Follow System

**Confidence: HIGH** — Standard SQLAlchemy self-referential M2M pattern.

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| SQLAlchemy self-referential M2M (built-in) | N/A | User follows | A `follows` association table between users. No external library needed. |

**Schema sketch:**
```python
follows = db.Table('follows',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)
```

**Activity feed:** Query posts WHERE author_id IN (followed user IDs), order by created_at DESC. With SQLite at community scale (~100–500 users), this is fast enough without caching. If the followed list grows beyond ~500 users, add a DB index on `post.created_at`.

---

### In-App Notifications

**Confidence: HIGH** — Pure DB polling pattern, appropriate for this scale.

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| SQLAlchemy `Notification` model (built-in) | N/A | Store notifications in DB | No WebSockets, no push, no Redis pub/sub — just a `notifications` table polled on page load via a Jinja2 context processor (same pattern as the existing `inject_sidebar()`). |

**Why not real-time (WebSockets, SSE, Flask-SocketIO):**
- PROJECT.md explicitly out-of-scopes real-time features: "Real-time features (WebSockets, live feed) — too complex for v1 extension."
- DB-polled notifications are sufficient for a community blog. Notification count badge updates on next page load, not instantly.

**Flask-SocketIO** (`flask-socketio>=5.3.0`) is noted as a future upgrade path if real-time is added later, but should NOT be introduced now.

**Notification schema:**
```python
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    type = db.Column(db.String(30), nullable=False)  # 'new_follower', 'comment', 'new_post'
    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
```

---

### Albums / Collections

**Confidence: HIGH** — Pure SQLAlchemy, no extra library.

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| SQLAlchemy `Album` model (built-in) | N/A | Group posts into collections | A standard M2M between User-owned Album and Posts. No library needed. |

---

### Environment Configuration

**Confidence: HIGH** — Standard Flask practice.

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `python-dotenv` | >=1.0.0 [VERIFY] | Load `.env` file into environment | The app currently has `SECRET_KEY` hardcoded as a fallback. `python-dotenv` loaded in `app.py` before config reads enables `ANTHROPIC_API_KEY` and `SECRET_KEY` to be stored in `.env` without code changes. Essential before adding an AI API key to the codebase. |

**Why this is required:** The AI API key must never be committed to source control. `python-dotenv` is the minimal, idiomatic solution for Flask projects. It is not a security solution (`.env` must be in `.gitignore`) but prevents the key from landing in git history.

---

## Complete New Dependencies

```
# requirements.txt additions
anthropic>=0.25.0          # Claude vision API — VERIFY version at pypi.org/project/anthropic
python-dotenv>=1.0.0       # .env file loading for API key management
```

No other new packages are required. All social, tagging, album, and notification features are implemented using existing SQLAlchemy patterns.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| AI vision API | `anthropic` (Claude Haiku/Sonnet) | `openai` (GPT-4o) | Both are viable. Claude Haiku cost-per-call is lower for bulk tagging at time of research. If OpenAI key already exists, it is an equal substitute with minimal code change. |
| Background tasks | `threading` (stdlib) | Celery + Redis | Celery requires broker infra incompatible with SQLite-only constraint and deferred production infra scope. |
| Background tasks | `threading` (stdlib) | Flask-RQ | Same broker dependency as Celery. |
| Notifications | DB polling | Flask-SocketIO | Real-time is explicitly out of scope in PROJECT.md. |
| Tagging | Raw SQLAlchemy | Flask-Taggit | Django-focused, abandoned equivalents. Self-implemented gives full control. |
| Config | `python-dotenv` | `dynaconf` / `pydantic-settings` | Overkill for single-env Flask app. dotenv is the standard. |

---

## Installation

```bash
# Activate your virtualenv first
pip install anthropic python-dotenv

# Add to requirements.txt
echo "anthropic>=0.25.0" >> requirements.txt
echo "python-dotenv>=1.0.0" >> requirements.txt
```

Create `.env` in project root (add to `.gitignore`):
```
SECRET_KEY=your-secure-random-string
ANTHROPIC_API_KEY=sk-ant-...
```

Load in `app.py` before `create_app()`:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Sources

| Claim | Source | Confidence |
|-------|--------|------------|
| Claude 3 model names and vision capability | Training data (Aug 2025 cutoff) — verify at docs.anthropic.com/en/docs/about-claude/models | MEDIUM |
| anthropic SDK version >=0.25.0 | Training data — verify at pypi.org/project/anthropic | MEDIUM |
| python-dotenv version >=1.0.0 | Training data — verify at pypi.org/project/python-dotenv | MEDIUM |
| threading pattern for Flask background tasks | Well-established Flask pattern, training data | HIGH |
| SQLAlchemy M2M for tags/follows/albums | Core SQLAlchemy documented pattern, training data | HIGH |
| DB-polled notifications in Flask | Standard approach for non-realtime Flask apps, training data | HIGH |
| PROJECT.md real-time explicitly out of scope | Direct read of .planning/PROJECT.md | HIGH |
| SQLite single-writer risk with Celery | SQLite documentation characteristic, training data | HIGH |

**Note:** External verification tools (WebSearch, WebFetch, Context7, Brave Search) were all unavailable during this research session. All MEDIUM confidence items should be spot-checked against official docs before implementation.
