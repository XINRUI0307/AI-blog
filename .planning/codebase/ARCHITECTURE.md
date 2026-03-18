# Architecture

## Pattern

**Monolithic Flask application** with Blueprint-based route organization. Application factory pattern (`create_app()` in `app.py`). No service layer — business logic lives directly in route handlers.

## Layers

```
┌─────────────────────────────────────┐
│          Templates (Jinja2)          │  Presentation
├─────────────────────────────────────┤
│           Routes / Blueprints        │  Controllers (+ business logic)
├─────────────────────────────────────┤
│         Models (SQLAlchemy)          │  Data / ORM
├─────────────────────────────────────┤
│         SQLite (instance/database.db)│  Persistence
└─────────────────────────────────────┘
```

## Entry Points

- `app.py` — `create_app()` factory, `if __name__ == '__main__': app.run(debug=True)`
- `extensions.py` — shared `db` and `login_manager` instances (avoids circular imports)

## Blueprints

| Blueprint | File | Prefix | Responsibility |
|-----------|------|--------|----------------|
| `auth_bp` | `routes/auth.py` | (none) | Register, login, logout |
| `posts_bp` | `routes/posts.py` | (none) | CRUD posts, ratings |
| `photos_bp` | `routes/photos.py` | (none) | Upload, serve, delete images |
| `comments_bp` | `routes/comments.py` | (none) | Add, report comments |
| `membership_bp` | `routes/membership.py` | (none) | Apply for membership |
| `profile_bp` | `routes/profile.py` | (none) | View/edit profile, messages |
| `search_bp` | `routes/search.py` | (none) | Search posts |
| `admin_bp` | `routes/admin.py` | (none) | Admin dashboard, user management |

## Data Flow

```
HTTP Request
    → Flask router → Blueprint route handler
        → SQLAlchemy query → models (User, Post, Image, etc.)
        → Business logic inline in handler
        → render_template() or redirect()
HTTP Response
```

## Authorization Model

Three-tier role system enforced via decorators in `utils.py`:

- `None` (unapproved) — cannot log in
- `reader` — read full posts, rate, comment, send messages
- `contributor` — reader + create/edit/delete own posts, upload photos (max 10 posts)
- `admin` — full access, manage users, approve applications, seed account

Decorators: `@admin_required`, `@contributor_required`, `@role_required(*roles)`

## Startup Hooks

`create_app()` runs two side effects on startup:
- `_seed_admin()` — creates `admin/admin123` account if no admin exists
- `_purge_old_posts()` — deletes posts older than 18 months

## File Storage

Photos stored at `uploads/posts/<post_id>/<uuid>.ext`. Avatars at `uploads/avatars/<filename>`. Served via `send_from_directory()` — no CDN/object storage.

## Context Processor

`inject_sidebar()` runs on every request, injecting `SidebarContent` from DB into all templates.

## Abstractions

- `utils.py` — authorization decorators only
- `extensions.py` — extension singletons (db, login_manager)
- No service classes, repositories, or domain objects beyond SQLAlchemy models
