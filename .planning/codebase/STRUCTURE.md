# Structure

## Directory Layout

```
blog-ai/
├── app.py                    # Application factory, startup hooks
├── extensions.py             # Shared db + login_manager singletons
├── models.py                 # All SQLAlchemy models
├── utils.py                  # Authorization decorators
├── requirements.txt          # Python dependencies
├── spec.md                   # Original project specification
│
├── routes/                   # Blueprint route handlers
│   ├── __init__.py           # Empty
│   ├── auth.py               # Register, login, logout
│   ├── posts.py              # Post CRUD, ratings
│   ├── photos.py             # Photo upload, serve, delete
│   ├── comments.py           # Comment add, report
│   ├── membership.py         # Membership application
│   ├── profile.py            # Profile view/edit, messages
│   ├── search.py             # Post search
│   └── admin.py              # Admin dashboard
│
├── templates/                # Jinja2 HTML templates
│   ├── base.html             # Base layout with nav, sidebar
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── posts/
│   │   ├── index.html        # Paginated post list
│   │   ├── detail.html       # Single post view
│   │   ├── create.html
│   │   └── edit.html
│   ├── photos/
│   │   └── upload.html
│   ├── profile/
│   │   ├── view.html
│   │   ├── edit.html
│   │   └── messages.html
│   ├── admin/
│   │   ├── dashboard.html
│   │   ├── applications.html
│   │   ├── users.html
│   │   └── reported_comments.html
│   ├── search/
│   │   └── results.html
│   └── errors/
│       ├── 403.html
│       └── 404.html
│
├── static/
│   └── css/
│       └── style.css
│
├── uploads/                  # Runtime-generated, not in git
│   ├── posts/<post_id>/      # Post photos (UUID-named)
│   └── avatars/              # User avatars
│
└── instance/                 # Flask instance folder
    └── database.db           # SQLite database (runtime-generated)
```

## Key Locations

| What | Where |
|------|-------|
| App factory | `app.py:create_app()` |
| All models | `models.py` |
| Auth decorators | `utils.py` |
| DB + login_manager | `extensions.py` |
| Base template | `templates/base.html` |
| SQLite database | `instance/database.db` |
| Uploaded photos | `uploads/posts/<id>/` |

## Naming Conventions

- **Route files**: `snake_case.py`, named after domain (auth, posts, photos)
- **Blueprint vars**: `<name>_bp` (e.g., `auth_bp`, `posts_bp`)
- **Templates**: match route domain, nested in subdirectory
- **Models**: `PascalCase` (User, Post, Image, Comment)
- **DB columns**: `snake_case`
- **URL patterns**: `/post/<id>`, `/post/<id>/edit`, `/photo/<id>/delete`

## No Build System

Pure Python/HTML/CSS — no JavaScript bundler, no npm, no asset pipeline. CSS is a single `static/css/style.css` file.
