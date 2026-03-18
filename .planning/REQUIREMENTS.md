# Requirements: Flask Photo Blog — AI-Enhanced Community Platform

**Defined:** 2026-03-18
**Core Value:** Members can discover, share, and engage with photography in a curated community where AI helps contributors create better content and makes photos easier to find.

## v1 Requirements

Requirements for this milestone. Each maps to a roadmap phase.

### Infrastructure

- [x] **INFRA-01**: Flask-Migrate is configured and an initial migration baseline exists so schema changes can be applied without data loss
- [x] **INFRA-02**: Database is configured with WAL mode to support concurrent reads and background thread writes
- [x] **INFRA-03**: Anthropic API key is loaded from environment variable (`.env` file, not hardcoded)
- [x] **INFRA-04**: Application reads configuration from environment variables via `python-dotenv`

### Discovery — Tags

- [x] **DISC-01**: Contributor can add tags to a post when creating or editing it
- [x] **DISC-02**: Tags are normalized (lowercase, trimmed, deduplicated) before saving
- [x] **DISC-03**: User can browse a tag page that lists all posts with that tag
- [x] **DISC-04**: Post detail view displays the post's tags, each linking to the tag browse page

### Discovery — Albums

- [ ] **DISC-05**: Any authenticated user (reader or contributor) can create an album with a name and optional description
- [ ] **DISC-06**: Album creator can add any post (from any contributor) to their album
- [ ] **DISC-07**: Album creator can remove posts from their album
- [ ] **DISC-08**: User can browse an album page that shows all posts in that album
- [ ] **DISC-09**: User can view a list of all albums

### AI — Photo Analysis

- [ ] **AI-01**: When a contributor uploads photos to a post, AI description generation is triggered in the background (non-blocking upload)
- [ ] **AI-02**: AI-generated description is surfaced to contributor for review — they can accept, edit, or discard it before it replaces the current post description
- [ ] **AI-03**: Contributor can see the AI processing status on their post (pending / ready / failed)
- [ ] **AI-04**: When photos are uploaded, AI suggests tags for the post based on image content
- [ ] **AI-05**: AI tag suggestions are displayed to contributor for confirmation — they can select, edit, or dismiss individual suggestions before any tags are saved
- [ ] **AI-06**: Contributor can click "Improve text" on their post description to request AI rewriting/enhancement
- [ ] **AI-07**: AI writing assistant returns an improved version for contributor review — they can accept, edit, or discard it

### Social — Follow & Feed

- [ ] **SOCL-01**: Authenticated user can follow another contributor
- [ ] **SOCL-02**: Authenticated user can unfollow a contributor they follow
- [ ] **SOCL-03**: User can see a follower count and following count on a contributor's profile
- [ ] **SOCL-04**: Authenticated user can view an activity feed showing posts from contributors they follow, in reverse chronological order
- [ ] **SOCL-05**: Activity feed is paginated

## v2 Requirements

Deferred to future milestone. Tracked but not in current roadmap.

### Notifications

- **NOTF-01**: User receives in-app notification when someone follows them
- **NOTF-02**: User receives in-app notification when someone comments on their post
- **NOTF-03**: User receives in-app notification when a followed contributor publishes a new post
- **NOTF-04**: User can view a notification list page
- **NOTF-05**: Unread notification count displayed as badge in navigation

### Discovery (Extended)

- **DISC-10**: Search extended to include tags and album names

### Security Hardening

- **SEC-01**: CSRF protection added to all forms
- **SEC-02**: Admin seed credentials replaced with environment-variable-driven setup
- **SEC-03**: Open redirect in login `next` parameter validated

## Out of Scope

| Feature | Reason |
|---------|--------|
| Email notifications | High infrastructure complexity; HTTP polling is sufficient for v1 |
| Real-time features (WebSockets, live feed) | Explicitly out of scope per project decisions |
| Test suite | Deferred — not blocking new features per user priority |
| PostgreSQL / cloud storage migration | Production infrastructure deferred |
| Mobile app | Web-first |
| Video posts | Storage/bandwidth concerns |
| Follow counts / leaderboards | Anti-feature for small curated community |
| Auto-apply AI tags | User decision: require contributor confirmation always |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 1 | Complete |
| INFRA-02 | Phase 1 | Complete |
| INFRA-03 | Phase 1 | Complete |
| INFRA-04 | Phase 1 | Complete |
| DISC-01 | Phase 2 | Complete |
| DISC-02 | Phase 2 | Complete |
| DISC-03 | Phase 2 | Complete |
| DISC-04 | Phase 2 | Complete |
| DISC-05 | Phase 2 | Pending |
| DISC-06 | Phase 2 | Pending |
| DISC-07 | Phase 2 | Pending |
| DISC-08 | Phase 2 | Pending |
| DISC-09 | Phase 2 | Pending |
| AI-01 | Phase 3 | Pending |
| AI-02 | Phase 3 | Pending |
| AI-03 | Phase 3 | Pending |
| AI-04 | Phase 3 | Pending |
| AI-05 | Phase 3 | Pending |
| AI-06 | Phase 3 | Pending |
| AI-07 | Phase 3 | Pending |
| SOCL-01 | Phase 4 | Pending |
| SOCL-02 | Phase 4 | Pending |
| SOCL-03 | Phase 4 | Pending |
| SOCL-04 | Phase 4 | Pending |
| SOCL-05 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-18*
*Last updated: 2026-03-18 — traceability updated after roadmap creation (AI=Phase 3, SOCL=Phase 4)*
