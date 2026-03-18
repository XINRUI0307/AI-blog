# Technology Stack

**Analysis Date:** 2026-03-18

## Languages

**Primary:**
- Python 3.x - Backend application logic, routes, models, utilities

## Runtime

**Environment:**
- Python runtime (version unspecified in repository, see requirements.txt for package versions)

**Package Manager:**
- pip (implied from requirements.txt)
- Lockfile: Not detected (no .lock file present)

## Frameworks

**Core:**
- Flask 3.0.0+ - Web framework for routing, templating, request handling
- Flask-SQLAlchemy 3.1.0+ - ORM for database models and relationships
- Flask-Login 0.6.3+ - User session and authentication management
- Werkzeug 3.0.0+ - WSGI utilities included with Flask

**Media Handling:**
- Pillow 10.0.0+ - Image processing and validation (resize detection, format validation)

## Key Dependencies

**Critical:**
- Flask 3.0.0+ - Application framework, core to all routing and request handling
- Flask-SQLAlchemy 3.1.0+ - Database ORM, defines all models and relationships
- Flask-Login 0.6.3+ - User session management, authentication state

**Utilities:**
- Werkzeug 3.0.0+ - WSGI utilities, password hashing (generate_password_hash, check_password_hash)
- Pillow 10.0.0+ - Image validation and metadata extraction

## Configuration

**Environment:**
- SECRET_KEY: Environment variable or default 'change-this-in-production' (app.py line 9)
- SQLALCHEMY_DATABASE_URI: Hardcoded sqlite:///database.db (app.py line 10)
- SQLALCHEMY_TRACK_MODIFICATIONS: False (app.py line 11)
- UPLOAD_FOLDER: `{app.root_path}/uploads` (app.py line 12)
- MAX_CONTENT_LENGTH: 10 MB (app.py line 13)

**Build:**
- No build system detected (Flask runs directly with Python)
- Development: `python app.py` runs with debug=True

## Database

**Type:** SQLite
**Location:** `instance/database.db`
**Connection:** Direct file-based via SQLAlchemy
**Auto-initialization:** Yes - db.create_all() called on app startup (app.py line 54)

## File Storage

**Type:** Local filesystem only
**Location:** `uploads/` directory organized by type:
- `uploads/posts/{post_id}/{filename}` - Post images
- `uploads/avatars/{filename}` - User avatars
**Maximum File Size:** 10 MB (app.py line 13)
**Supported Formats:** jpg, jpeg, png, gif, webp (routes/photos.py line 12)

## Session & Caching

**Session:** Flask-Login session management (cookie-based by default)
**Caching:** Not detected

## Authentication & Security

**Auth Type:** Custom credentials-based with Flask-Login
**Password Hashing:** Werkzeug.security (generate_password_hash, check_password_hash)
**Session Management:** Flask-Login UserMixin pattern (models.py line 7)
**User Loader:** Custom loader in app.py lines 18-21

## Platform Requirements

**Development:**
- Python 3.6+ (Flask 3.0 requires Python 3.7+)
- Operating system: Windows/Linux/macOS (Windows path handling in code)
- 10 MB+ disk space for uploads directory

**Production:**
- WSGI server (Flask development server not suitable for production)
- Environment variable: SECRET_KEY must be set securely
- Database: SQLite or migration to PostgreSQL/MySQL
- Static file serving mechanism needed

---

*Stack analysis: 2026-03-18*
