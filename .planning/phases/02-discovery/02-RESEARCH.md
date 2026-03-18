# Phase 2: Discovery - Research

**Researched:** 2026-03-18
**Domain:** Flask/SQLAlchemy — many-to-many tagging, album management, browse views
**Confidence:** HIGH

---

## Summary

Phase 2 adds two orthogonal feature sets to the existing Flask photo blog: tags (many-to-many relationship between posts and tag strings) and albums (user-owned collections of posts, also many-to-many). Both fit cleanly into the existing SQLAlchemy pattern already in use — add models, wire them into the existing `posts.create` / `posts.edit` routes, and add new browse blueprints.

The most important architectural decision is the **tag data model**: tags are best stored as a first-class `Tag` model with a normalized `name` column (unique, lowercase, trimmed) and a `post_tags` association table. This avoids duplicating normalization logic across every query and enables efficient tag-page lookups. Albums require a separate `AlbumPost` association table carrying `added_at` metadata, with `album.user_id` enforcing ownership for add/remove operations.

No new Python packages are needed. Flask-Migrate (already installed) handles the schema migration. The UI already uses Bootstrap 5 and Bootstrap Icons, so all new pages can follow the exact card/grid patterns already in `templates/posts/`.

**Primary recommendation:** Use a normalized `Tag` model + `post_tags` secondary table for tags; use `Album` + `AlbumPost` association table for albums. Wire both into existing `posts_bp` routes for CRUD and add two new blueprints — `tags_bp` and `albums_bp` — for browse views.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DISC-01 | Contributor can add tags to a post when creating or editing it | Tags field on `create.html` / `edit.html`; route parses comma-separated input, normalizes, saves via `Post.tags` relationship |
| DISC-02 | Tags are normalized (lowercase, trimmed, deduplicated) before saving | Normalization helper function; `Tag.name` has `unique=True`; `get_or_create` pattern prevents duplicates |
| DISC-03 | User can browse a tag page that lists all posts with that tag | `tags_bp` blueprint with `/tag/<slug>` route; queries `Tag.posts` backref |
| DISC-04 | Post detail view displays the post's tags, each linking to the tag browse page | `detail.html` iterates `post.tags`; each tag links to `/tag/<slug>` |
| DISC-05 | Any authenticated user (reader or contributor) can create an album | `albums_bp` with `/album/create`; `login_required` only, no contributor check |
| DISC-06 | Album creator can add any post (from any contributor) to their album | `POST /album/<id>/add/<post_id>`; ownership check via `album.user_id == current_user.id` |
| DISC-07 | Album creator can remove posts from their album | `POST /album/<id>/remove/<post_id>`; same ownership check |
| DISC-08 | User can browse an album page that shows all posts in that album | `GET /album/<id>` — public, no login required to view |
| DISC-09 | User can view a list of all albums | `GET /albums` — public, paginated list |
</phase_requirements>

---

## Standard Stack

### Core (already installed — no new packages required)

| Library | Version (in use) | Purpose | Why Standard |
|---------|-----------------|---------|--------------|
| Flask-SQLAlchemy | >=3.1.0 | ORM, `db.Table` for secondary association | Already powering all models |
| Flask-Migrate | 4.1.0 | Schema migration via Alembic | Already configured; `flask db migrate && flask db upgrade` |
| Flask-Login | >=0.6.3 | `login_required`, `current_user` | Already handles all auth |
| Bootstrap 5.3 | CDN | UI components | Already in `base.html` |
| Bootstrap Icons 1.11 | CDN | Icons (`bi-tag`, `bi-collection`) | Already in `base.html` |

### No New Packages

All Phase 2 features are achievable with what is already installed. No pip additions needed.

**Version verification:** Confirmed via `requirements.txt` — installed versions are exact project versions.

---

## Architecture Patterns

### Recommended Project Structure Additions

```
models.py                    # Add Tag, Post.tags relationship, Album, AlbumPost
routes/
├── tags.py                  # New: tags_bp — tag browse pages
├── albums.py                # New: albums_bp — album CRUD + browse
templates/
├── tags/
│   └── browse.html          # Posts for a given tag
├── albums/
│   ├── list.html            # All albums
│   ├── detail.html          # Posts in one album
│   └── create.html          # Create album form
```

Everything else (posts routes, post templates) gets targeted additions, not new files.

### Pattern 1: Normalized Tag Model with Secondary Table

**What:** A standalone `Tag` model with a unique normalized `name` column, linked to `Post` via a secondary association table.

**When to use:** Any time tags are shared across records and must be browseable. Avoids storing raw strings on the post.

**Example:**
```python
# models.py

# Secondary association table — no model needed
post_tags = db.Table(
    'post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('tag_id',  db.Integer, db.ForeignKey('tags.id'),  primary_key=True),
)

class Tag(db.Model):
    __tablename__ = 'tags'
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    posts = db.relationship('Post', secondary=post_tags, back_populates='tags')

    def __repr__(self):
        return f'<Tag {self.name}>'

# Add to Post model:
#   tags = db.relationship('Tag', secondary=post_tags, back_populates='posts')
```

### Pattern 2: Tag Normalization Helper

**What:** A small utility function that converts raw user input into a deduplicated list of lowercase, trimmed tag names.

**When to use:** Called in every route that accepts tag input (create, edit).

**Example:**
```python
# utils.py

def normalize_tags(raw: str) -> list[str]:
    """
    Parse comma-separated tag input, normalize each token.
    Returns a deduplicated list of lowercase, stripped tag names.
    Skips empty tokens. Limits tag length to 50 chars.
    """
    seen = set()
    result = []
    for token in raw.split(','):
        name = token.strip().lower()[:50]
        if name and name not in seen:
            seen.add(name)
            result.append(name)
    return result
```

### Pattern 3: get_or_create for Tag Upsert

**What:** Query for an existing `Tag` by normalized name; create it if absent. Avoids IntegrityError on the unique constraint.

**When to use:** In post create/edit routes after calling `normalize_tags()`.

**Example:**
```python
# Inside posts.create / posts.edit route handler

def get_or_create_tag(name: str) -> Tag:
    tag = Tag.query.filter_by(name=name).first()
    if not tag:
        tag = Tag(name=name)
        db.session.add(tag)
    return tag

# Usage:
raw = request.form.get('tags', '')
post.tags = [get_or_create_tag(n) for n in normalize_tags(raw)]
db.session.commit()
```

### Pattern 4: Album with Ownership-Guarded Association

**What:** `Album` model owned by a user; `AlbumPost` association table with `added_at`. Add/remove operations check `album.user_id == current_user.id`.

**When to use:** Any user-curated collection.

**Example:**
```python
# models.py

album_posts = db.Table(
    'album_posts',
    db.Column('album_id', db.Integer, db.ForeignKey('albums.id'), primary_key=True),
    db.Column('post_id',  db.Integer, db.ForeignKey('posts.id'),  primary_key=True),
    db.Column('added_at', db.DateTime, default=datetime.utcnow),
)

class Album(db.Model):
    __tablename__ = 'albums'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship('User', backref='albums')
    posts = db.relationship('Post', secondary=album_posts, backref='albums')
```

### Pattern 5: Blueprint Registration (following existing convention)

```python
# app.py — add inside create_app()
from routes.tags   import tags_bp
from routes.albums import albums_bp

for bp in (..., tags_bp, albums_bp):
    app.register_blueprint(bp)
```

### Pattern 6: Tag Input as Plain Text Field (comma-separated)

**What:** Single text input, value rendered as comma-joined tag names. No JavaScript required.

**Why:** Keeps the implementation simple; no new JS dependencies; consistent with the project's existing form style.

**Template snippet:**
```html
<!-- In create.html and edit.html -->
<div class="mb-4">
  <label class="form-label">
    <i class="bi bi-tags me-1"></i>Tags
    <span class="text-muted fw-normal">(optional, comma-separated)</span>
  </label>
  <input type="text" name="tags" class="form-control"
         placeholder="e.g. landscape, golden hour, film"
         value="{{ post.tags | map(attribute='name') | join(', ') if post.tags else '' }}"
         maxlength="500">
</div>
```

### Anti-Patterns to Avoid

- **Storing tags as a comma-separated string column on `Post`:** Makes tag-page queries require a LIKE scan across every post's string. The separate `Tag` model + secondary table allows a simple join query.
- **Normalizing only at display time:** If stored un-normalized, "Golden Hour" and "golden hour" become two different tags. Normalize at write time.
- **Allowing any authenticated user to modify any album:** Albums are owned; always check `album.user_id == current_user.id` (or admin role) before add/remove.
- **No deduplication in `post.tags` assignment:** Assigning the same `Tag` object twice to the secondary relationship will raise a database constraint error. The `get_or_create` + `normalize_tags` pipeline prevents this.
- **Using `db.relationship(..., lazy='dynamic')` on `Post.tags`:** The project already uses `lazy=True` (select) consistently. Stick to the existing pattern; dynamic loading adds complexity for no benefit here.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema migration | Manual `ALTER TABLE` SQL | `flask db migrate && flask db upgrade` | Flask-Migrate already configured; handles SQLite column additions correctly |
| Tag normalization edge cases | Custom unicode normalization | `str.strip().lower()` | Sufficient for a photography blog; no full-text search normalization needed |
| Ownership check middleware | Custom decorator | Inline `abort(403)` after `album.user_id` check | Consistent with how `posts.edit` already does it |
| Tag input UI widget | JavaScript tag-chip component | Plain `<input type="text">` comma-separated | No JS dependencies; works without any JS; project has no existing JS beyond Bootstrap |

**Key insight:** This phase is pure CRUD + relationship wiring. The existing patterns (Blueprint, SQLAlchemy relationship, `db.session.commit()`) cover everything. Complexity comes from getting the data model right upfront, not from the route logic.

---

## Common Pitfalls

### Pitfall 1: Orphan Tags After Post Edit

**What goes wrong:** When a contributor removes all tags from a post during edit, the `Tag` rows remain in the `tags` table forever (orphan accumulation).

**Why it happens:** The secondary table rows are deleted (SQLAlchemy handles that), but `Tag` objects with `posts` count = 0 persist.

**How to avoid:** Orphan cleanup is acceptable for v1 — the `tags` table stays small on a photo blog. Do NOT add cascade delete on the `Tag` model itself (that would delete the tag for all posts). If cleanup is desired later, a scheduled job can prune tags with empty `posts` relationships.

**Warning signs:** `SELECT COUNT(*) FROM tags` growing much larger than the number of distinct tags actually in use.

### Pitfall 2: SQLite and `added_at` Default in Secondary Table

**What goes wrong:** Using `db.Column('added_at', db.DateTime, default=datetime.utcnow)` in a `db.Table()` (not a model class) does not invoke the Python-side default — it is only applied if using an ORM model class.

**Why it happens:** `db.Table` is a Core construct; Python-side `default=` only works reliably on Column objects inside a mapped class.

**How to avoid:** Either omit `added_at` from the secondary table (simplest, and sufficient for this phase — DISC-06 through DISC-08 don't require it), or promote `AlbumPost` to a full association object model.

**Recommendation:** For this phase, use a plain secondary table without `added_at`. The requirements don't need ordering by add date.

### Pitfall 3: Tag Slug vs. Tag Name in URL

**What goes wrong:** A tag named "new york" produces a URL `/tag/new york` which requires URL encoding and breaks `url_for('tags.browse', tag_name='new york')` in some browsers.

**Why it happens:** Spaces aren't valid in URL paths without encoding.

**How to avoid:** Since tags are already normalized to lowercase and trimmed, replace spaces with hyphens for the URL slug but store the original normalized name in the database. The route accepts the hyphenated slug and converts it back: `name = slug.replace('-', ' ')`.

**Alternative (simpler):** Disallow spaces in tags by also replacing spaces during normalization (`name.replace(' ', '-')`). This is slightly more aggressive but eliminates the slug/name duality entirely.

**Recommendation:** Replace spaces with hyphens at normalization time. Store `golden-hour`, not `golden hour`. This simplifies URLs and queries.

### Pitfall 4: Album Detail Page Performance on SQLite

**What goes wrong:** Loading an album with 50+ posts, each with eager-loaded images, comments, and ratings, fires N+1 queries.

**Why it happens:** `lazy=True` (select) on relationships loads each related object separately when accessed in the template.

**How to avoid:** In the album detail route, use `joinedload` or limit the template to only accessing `post.images[0]` (cover photo) and `post.average_rating()`. The existing post index page faces the same issue and accepts it — be consistent.

**Warning signs:** Slow page load on album pages with many posts.

### Pitfall 5: Flask-Migrate Not Detecting Secondary Tables

**What goes wrong:** `flask db migrate` generates an empty migration when `post_tags` / `album_posts` tables are added.

**Why it happens:** Alembic detects changes via model introspection. `db.Table` objects defined at module level ARE detected, but only if they are imported before `flask db migrate` runs (i.e., only if `models.py` is imported).

**How to avoid:** This is not actually a problem for this project — `app.py` already imports models inside the app context. Just ensure the new `db.Table` objects are defined in `models.py` (not in route files) and imported before the migration command.

---

## Code Examples

### Tags Route Blueprint (tags.py)

```python
# routes/tags.py
from flask import Blueprint, render_template
from models import Tag

tags_bp = Blueprint('tags', __name__)

@tags_bp.route('/tag/<tag_name>')
def browse(tag_name):
    tag = Tag.query.filter_by(name=tag_name).first_or_404()
    return render_template('tags/browse.html', tag=tag, posts=tag.posts)
```

### Albums Route Blueprint (albums.py)

```python
# routes/albums.py  — key routes only
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models import Album, Post

albums_bp = Blueprint('albums', __name__)

@albums_bp.route('/albums')
def list_albums():
    albums = Album.query.order_by(Album.created_at.desc()).all()
    return render_template('albums/list.html', albums=albums)

@albums_bp.route('/album/<int:album_id>')
def detail(album_id):
    album = Album.query.get_or_404(album_id)
    return render_template('albums/detail.html', album=album)

@albums_bp.route('/album/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            flash('Album name is required.', 'danger')
            return render_template('albums/create.html')
        album = Album(
            user_id=current_user.id,
            name=name,
            description=request.form.get('description', '').strip()
        )
        db.session.add(album)
        db.session.commit()
        flash('Album created.', 'success')
        return redirect(url_for('albums.detail', album_id=album.id))
    return render_template('albums/create.html')

@albums_bp.route('/album/<int:album_id>/add/<int:post_id>', methods=['POST'])
@login_required
def add_post(album_id, post_id):
    album = Album.query.get_or_404(album_id)
    if album.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    post = Post.query.get_or_404(post_id)
    if post not in album.posts:
        album.posts.append(post)
        db.session.commit()
        flash('Post added to album.', 'success')
    return redirect(request.referrer or url_for('albums.detail', album_id=album_id))

@albums_bp.route('/album/<int:album_id>/remove/<int:post_id>', methods=['POST'])
@login_required
def remove_post(album_id, post_id):
    album = Album.query.get_or_404(album_id)
    if album.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    post = Post.query.get_or_404(post_id)
    if post in album.posts:
        album.posts.remove(post)
        db.session.commit()
        flash('Post removed from album.', 'success')
    return redirect(request.referrer or url_for('albums.detail', album_id=album_id))
```

### Tag Normalization (utils.py addition)

```python
def normalize_tags(raw: str) -> list[str]:
    seen = set()
    result = []
    for token in raw.split(','):
        name = token.strip().lower().replace(' ', '-')[:50]
        if name and name not in seen:
            seen.add(name)
            result.append(name)
    return result
```

### Alembic Migration (generated by flask db migrate)

The migration will create three new tables. The planner should instruct running:

```bash
flask db migrate -m "add tags and albums"
flask db upgrade
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Storing tags as `text` column with comma-separated values | Separate `Tag` model + secondary association table | Standard since SQLAlchemy 0.x | Enables join queries, enforces normalization, avoids LIKE scans |
| `db.session.query(Model).filter(...)` | `Model.query.filter_by(...)` (already in use in this codebase) | Flask-SQLAlchemy >= 2.x | No change needed; existing style is fine |
| `Post.query.get(id)` | `db.session.get(Post, id)` (SQLAlchemy 2.x preferred) | SQLAlchemy 2.0 | Codebase uses `.get()` in `app.py`; for this phase, match existing `.get_or_404()` usage from `routes/posts.py` for consistency |

**Deprecated/outdated:**
- `db.session.query(Model)` legacy-style queries: Not deprecated yet but the codebase uses `Model.query` style consistently — continue that pattern.

---

## Open Questions

1. **Where does the "Add to Album" button appear?**
   - What we know: DISC-06 says album creator can add any post. The obvious placement is on the post detail page or on the album detail page.
   - What's unclear: Should it be a button on every post detail, or should the user navigate to an album page and search/add from there?
   - Recommendation: Put "Add to Album" as a dropdown or simple form on the post detail page (visible to logged-in users who own at least one album). This is the most discoverable UX. The planner should decide placement — either approach is straightforward to implement.

2. **Tag input UX: comma-separated plain text vs. tag chips**
   - What we know: Plain text is sufficient for v1 and requires no JS. Bootstrap 5 has no built-in tag-chip component.
   - What's unclear: Whether the contributor experience of typing tags as plain text is acceptable.
   - Recommendation: Use plain text comma-separated input. Consistent with project's no-extra-JS stance. Can be upgraded in v2 if needed.

3. **Album visibility: public vs. private?**
   - What we know: DISC-09 says users can view a list of ALL albums; DISC-08 says users can browse an album's posts.
   - What's unclear: Should all albums be public to anyone (including unauthenticated visitors)?
   - Recommendation: Make album list and detail pages public (no `@login_required`) — consistent with how the main post feed works. Creating/editing albums requires login.

---

## Validation Architecture

`nyquist_validation` is enabled in `.planning/config.json`.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None detected — project has no test suite (deferred per REQUIREMENTS.md Out of Scope) |
| Config file | None — Wave 0 gap |
| Quick run command | N/A — manual verification |
| Full suite command | N/A |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Notes |
|--------|----------|-----------|-------|
| DISC-01 | Tags field appears on create/edit form | manual-only | No test suite; verify by loading the form in browser |
| DISC-02 | "Golden Hour" normalized to "golden-hour" | manual-only | Submit form with mixed-case tag, inspect DB |
| DISC-03 | `/tag/landscape` shows posts tagged landscape | manual-only | Create tagged post, visit tag URL |
| DISC-04 | Post detail displays tags as links | manual-only | Inspect rendered HTML |
| DISC-05 | Authenticated user can create album | manual-only | Log in as reader, create album |
| DISC-06 | Album owner can add any post | manual-only | Add post from another contributor |
| DISC-07 | Album owner can remove post | manual-only | Remove previously added post |
| DISC-08 | Album page shows all posts | manual-only | View `/album/<id>` |
| DISC-09 | Albums list page shows all albums | manual-only | View `/albums` |

**All tests are manual-only.** The project has no automated test suite and the out-of-scope declaration in REQUIREMENTS.md explicitly defers it.

### Sampling Rate

- **Per task commit:** Manual smoke test in browser (create tagged post, verify tag page, create album, add/remove post)
- **Per wave merge:** Full manual checklist against all 9 success criteria
- **Phase gate:** All 9 success criteria confirmed manually before `/gsd:verify-work`

### Wave 0 Gaps

- No test infrastructure to create — project explicitly defers automated tests.
- Manual checklist document recommended but not required by project config.

*(Automated test infrastructure is out of scope per project decisions.)*

---

## Sources

### Primary (HIGH confidence)

- Direct codebase inspection: `models.py`, `routes/posts.py`, `app.py`, `extensions.py`, `utils.py`, `requirements.txt`, `migrations/versions/28e5beea3e43_initial_schema.py`
- `.planning/REQUIREMENTS.md` — requirement definitions
- `.planning/PROJECT.md` — stack constraints and decisions

### Secondary (MEDIUM confidence)

- Flask-SQLAlchemy many-to-many pattern: standard documented pattern; consistent with SQLAlchemy 2.x docs. Secondary table approach is the canonical documented method.
- Flask-Migrate behavior with `db.Table` objects: standard Alembic behavior; `db.Table` objects in module scope ARE detected by autogenerate.

### Tertiary (LOW confidence)

- None — all findings are based on direct codebase inspection and well-established SQLAlchemy patterns.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — confirmed via `requirements.txt` and direct codebase inspection
- Architecture: HIGH — derived from existing patterns in the codebase; many-to-many with secondary table is standard SQLAlchemy
- Pitfalls: HIGH — derived from SQLAlchemy/Flask-Migrate documented behavior and the specific characteristics of this codebase

**Research date:** 2026-03-18
**Valid until:** 2026-06-18 (stable stack — Flask-SQLAlchemy and Flask-Migrate APIs are stable)
