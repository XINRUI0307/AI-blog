# Coding Conventions

**Analysis Date:** 2026-03-18

## Naming Patterns

**Files:**
- Lowercase with underscores: `app.py`, `auth.py`, `models.py`, `extensions.py`
- Route modules prefixed with function name: `auth.py`, `posts.py`, `photos.py`, `comments.py`, `profile.py`, `search.py`, `admin.py`, `membership.py`
- Utility files: `utils.py` for shared functions

**Functions:**
- Lowercase with underscores: `register()`, `login()`, `logout()`, `create()`, `edit()`, `delete()`
- Private/helper functions prefixed with underscore: `_allowed()`, `_seed_admin()`, `_purge_old_posts()`
- Decorators and wrappers follow snake_case: `role_required()`, `admin_required()`, `contributor_required()`

**Variables:**
- Lowercase with underscores: `user_id`, `post_id`, `author_id`, `comment_id`, `saved`, `pending_count`
- Short loop variables in context: `f` for file objects, `m` for messages
- Constants in UPPERCASE: `ALLOWED_EXTENSIONS`, `MAX_WIDTH`, `MAX_HEIGHT`, `AVATAR_ALLOWED`

**Types:**
- Model classes in PascalCase: `User`, `Post`, `Image`, `Comment`, `Rating`, `Message`, `MembershipApplication`, `SidebarContent`
- Blueprint instances named with `_bp` suffix: `auth_bp`, `posts_bp`, `photos_bp`, `comments_bp`, `membership_bp`, `profile_bp`, `search_bp`, `admin_bp`

## Code Style

**Formatting:**
- No explicit formatter detected, but consistent 4-space indentation throughout
- Line length reasonable, under 100 characters in most cases
- Imports organized at top of files

**Linting:**
- No linting configuration file detected (.eslintrc, .flake8, etc.)
- No PEP 8 configuration files present

## Import Organization

**Order (observed pattern):**
1. Standard library imports: `os`, `datetime`, `uuid`, `functools`
2. Flask framework imports: `from flask import ...`
3. Flask extensions: `from flask_login import ...`, `from flask_sqlalchemy import ...`
4. Third-party libraries: `from werkzeug.security import ...`, `from PIL import Image`
5. Local application imports: `from extensions import ...`, `from models import ...`, `from utils import ...`

**Path Aliases:**
- No path aliases detected. All imports use relative paths from project root.

**Examples:**
```python
# routes/posts.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models import Post, Rating
from utils import contributor_required
```

## Error Handling

**Patterns:**
- HTTP error codes via `abort()`: `abort(403)`, `abort(404)`
- Flask-SQLAlchemy shorthand methods: `.get_or_404()`, `.first_or_404()`
- User feedback via `flash()`: `flash('message', 'category')` where categories are 'success', 'danger', 'warning', 'info'
- Silent exception handling with bare `except Exception:` in file validation (`routes/photos.py:46`, `routes/profile.py:44`)
- No try-except-finally blocks or custom exception classes observed

**Example:**
```python
# routes/photos.py
try:
    img = PilImage.open(f)
    if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
        flash(f'{f.filename}: resolution {img.width}x{img.height} exceeds 1200x800.', 'danger')
        continue
except Exception:
    flash(f'{f.filename} is not a valid image.', 'danger')
    continue
```

## Logging

**Framework:** No logging framework detected. Application uses `flash()` for user-facing messages only.

**Patterns:**
- User feedback via Flask flash messages (displayed in templates)
- No debug/info/error logging to console or files
- Database operations logged implicitly by SQLAlchemy if debugging enabled

## Comments

**When to Comment:**
- Very minimal comments in codebase. Observed comments are rare.
- Comments used for clarification on non-obvious logic: `# None until approved`, `# False until admin approves`, `# pending, approved, rejected`

**JSDoc/TSDoc:**
- Not applicable. No documentation comments observed in Python code.

## Function Design

**Size:** Most functions are short (10-50 lines). Route handlers perform both database queries and view rendering within a single function.

**Parameters:**
- Flask route handlers use URL parameters via function arguments: `def detail(post_id)`
- Request form data accessed via `request.form.get()` or `request.form[]`
- Files accessed via `request.files.get()` or `request.files.getlist()`

**Return Values:**
- Route handlers return `render_template()` response or redirect via `redirect(url_for())`
- Validation methods return boolean: `.check_password()` returns True/False
- Model methods return calculated values: `.average_rating()` returns float or None
- Helper functions return computed filenames or status values

**Example:**
```python
# routes/auth.py
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('posts.index'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account is pending admin approval.', 'warning')
                return render_template('auth/login.html')
            login_user(user)
            return redirect(request.args.get('next') or url_for('posts.index'))
        flash('Invalid username or password.', 'danger')
    return render_template('auth/login.html')
```

## Module Design

**Exports:**
- Each blueprint module creates a single blueprint instance and exports it: `auth_bp = Blueprint('auth', __name__)`
- Models defined in single `models.py` file with all SQLAlchemy ORM classes
- Extensions (db, login_manager) initialized in `extensions.py` and imported everywhere

**Barrel Files:**
- `routes/__init__.py` exists but is empty
- No barrel files (index.ts/py style exports) used for organizing modules

**Application Structure:**
- Blueprint registration happens in app factory: `create_app()` in `app.py`
- All blueprints imported and registered in loops in `app.factory()`
- Database initialization and seeding happens in app factory

---

*Convention analysis: 2026-03-18*
