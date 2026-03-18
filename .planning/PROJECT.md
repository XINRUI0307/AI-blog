# Flask Photo Blog — AI-Enhanced Community Platform

## What This Is

A semi-public photo blog platform where members share photography in a curated community. Admins approve new members (reader or contributor roles), contributors post photos with descriptions, and readers engage through ratings and comments. The goal is to evolve this into a full-featured photo community with albums, discovery, social connections, and AI-assisted content creation.

## Core Value

Members can discover, share, and engage with photography in a curated community where AI helps contributors create better content and makes photos easier to find.

## Requirements

### Validated

<!-- Inferred from existing codebase — these capabilities already work. -->

- ✓ User authentication with email/password — existing
- ✓ Role-based access control (admin, contributor, reader, pending) — existing
- ✓ Admin approval workflow for new member applications — existing
- ✓ Contributors can create blog posts with title, description, location — existing
- ✓ Contributors can upload multiple photos per post (jpg, png, gif, webp, max 10MB, 1200x800) — existing
- ✓ Readers can rate posts (1–5 stars, one rating per user per post) — existing
- ✓ Authenticated users can comment on posts — existing
- ✓ Admin can manage users, view/approve applications, handle reported comments — existing
- ✓ User profiles with bio and avatar — existing
- ✓ Direct messaging between users — existing
- ✓ Full-text post search — existing
- ✓ Paginated post feed (10 per page) — existing
- ✓ Editable sidebar content (admin-managed) — existing
- ✓ Auto-purge of posts older than 18 months — existing

### Active

<!-- Current scope — building toward these. -->

**Discovery & Organization**
- [ ] User can create photo albums/collections to group related posts
- [ ] User can add tags to posts
- [ ] User can browse posts by tag
- [ ] User can browse posts by category/album
- [ ] Search extended to include tags and album names

**Social**
- [ ] User can follow other contributors
- [ ] User can view an activity feed of posts from followed contributors
- [ ] User receives in-app notifications (new follower, comment on own post, new post from followed user)

**AI Features**
- [ ] AI generates a description suggestion when contributor uploads photos
- [ ] AI suggests tags based on photo content
- [ ] AI writing assistant helps contributor improve post text on demand

### Out of Scope

- Full security hardening (CSRF, credential rotation) — deferred, not blocking new features
- Automated test suite — deferred
- Production infrastructure (PostgreSQL, cloud storage, WSGI) — deferred
- Mobile app — web-first
- Real-time features (WebSockets, live feed) — too complex for v1 extension
- Video posts — storage/bandwidth concerns

## Context

**Existing codebase:** Flask app with Blueprint-based routing, SQLAlchemy + SQLite, Flask-Login for auth, Pillow for image processing. No test suite. Application factory pattern in `app.py`. All models in `models.py`.

**Known issues to watch:** Hardcoded admin seed credentials (`admin/admin123`), no CSRF protection on forms, SQLite limits concurrent writes. These won't be fixed in this milestone but should be noted when touching affected code.

**AI integration:** Will use an LLM API (e.g., Claude/OpenAI vision) for photo analysis. Specific provider TBD during research phase.

## Constraints

- **Tech stack**: Extend existing Flask/SQLAlchemy/SQLite stack — no framework rewrites
- **Backward compatibility**: All existing URLs and data must continue to work
- **No breaking changes**: Existing users, posts, and roles unaffected by new features
- **AI calls**: Must be non-blocking (async or background) — photo upload must not wait for AI

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| New features first, fix debt later | User explicitly prioritized features over foundation work | — Pending |
| Extend Flask rather than rewrite | Existing codebase is functional; rewrite not justified | — Pending |
| AI as optional enhancement | AI features augment, never block contributor workflow | — Pending |

---
*Last updated: 2026-03-18 after initialization*
