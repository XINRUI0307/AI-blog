# External Integrations

**Analysis Date:** 2026-03-18

## APIs & External Services

**Third-Party APIs:**
- None detected - Application does not integrate with external APIs

**Payment Processing:**
- Not integrated

**Email Service:**
- Not detected

**SMS/Communications:**
- Not detected

## Data Storage

**Databases:**
- SQLite (default)
  - Connection: Direct file-based via SQLAlchemy URI `sqlite:///database.db`
  - Client: Flask-SQLAlchemy ORM
  - Auto-initialized: Yes, schema created on startup via `db.create_all()` (app.py line 54)
  - Models defined in: `models.py`

**File Storage:**
- Local filesystem only
  - Storage path: `uploads/` directory (app.py line 12)
  - Post photos: `uploads/posts/{post_id}/{filename}` (routes/photos.py)
  - User avatars: `uploads/avatars/{filename}` (routes/photos.py)
  - Supported formats: jpg, jpeg, png, gif, webp (routes/photos.py line 12)
  - Max file size: 10 MB per file (routes/photos.py line 38)
  - Max content length: 10 MB (app.py line 13)
  - Image processing: PIL/Pillow for validation and dimension checking

**Caching:**
- None detected

## Authentication & Identity

**Auth Provider:**
- Custom (self-hosted)
  - Implementation: Flask-Login with custom User model
  - Password hashing: Werkzeug password hashing (models.py lines 30-34)
  - User loader: Custom implementation (app.py lines 18-21)
  - Session management: Flask-Login session middleware

**User Model:**
- Location: `models.py` User class
- Fields: username, email, password_hash, role, is_active, created_at, avatar_filename, bio
- Roles: admin, contributor, reader, None (pending approval)
- State: Users created with is_active=False, require admin approval (routes/auth.py lines 28-35)

**Membership Workflow:**
- Location: `routes/membership.py`, `models.py` MembershipApplication
- Registration creates MembershipApplication with status='pending' (routes/auth.py lines 33-35)
- Admin approves/rejects via admin panel (routes/admin.py lines 39-59)

## Monitoring & Observability

**Error Tracking:**
- Not detected - Application has custom error handlers (app.py lines 45-51) but no external service

**Logging:**
- Not detected - No logging framework integrated

**Error Handlers:**
- 403 Forbidden: `templates/errors/403.html` (app.py lines 45-47)
- 404 Not Found: `templates/errors/404.html` (app.py lines 49-51)

## CI/CD & Deployment

**Hosting:**
- Not specified - Application is self-contained Flask app
- Suitable for: Any WSGI-compatible server (Gunicorn, uWSGI, etc.)

**CI Pipeline:**
- Not detected

**Deployment Method:**
- Manual - No automation tools present

## Environment Configuration

**Required Environment Variables:**
- `SECRET_KEY` - Flask session secret (app.py line 9, defaults to 'change-this-in-production')

**Optional Environment Variables:**
- None detected beyond SECRET_KEY

**Secrets Location:**
- Not configured - Relies on manual environment variable setup
- Warning: Default SECRET_KEY hardcoded in source (security risk in production)

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- None detected

## Data Flow & Initialization

**Application Startup (app.py lines 53-56):**
1. Database initialization: `db.create_all()` - Creates all SQLAlchemy tables
2. Admin seeding: `_seed_admin()` - Creates default admin user if missing (app.py lines 61-67)
3. Post cleanup: `_purge_old_posts()` - Deletes posts older than 18 months (app.py lines 70-76)

**Admin User Defaults:**
- Username: 'admin'
- Email: 'admin@blog.com'
- Password: 'admin123'
- Note: Created only if no admin user exists (app.py line 63)

## Integration Gaps & Notes

**No external integrations currently in use:**
- No API calls to third-party services
- No OAuth/SSO
- No email notifications
- No image hosting CDN (all images local)
- No analytics services
- No payment processing
- No SMS communications
- No backup systems

**Architectural Implications:**
- All data persisted locally (no distributed storage)
- No real-time updates (HTTP only)
- File upload limited to 10 MB per file
- No webhooks or async job processing
- Image processing happens synchronously on upload (routes/photos.py lines 42-48)

---

*Integration audit: 2026-03-18*
