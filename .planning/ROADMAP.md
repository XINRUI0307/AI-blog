# Roadmap: Flask Photo Blog — AI-Enhanced Community Platform

## Overview

Starting from a functioning Flask photo blog, this milestone adds three layers of capability in dependency order: first the infrastructure foundation that makes safe schema changes possible, then discovery features (tags and albums) that make photos findable and organizable, then AI features that help contributors write better descriptions and find relevant tags, and finally the social graph (follows and activity feed) that gives members a reason to return. Each phase delivers a coherent, verifiable capability on top of the last.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - DB migration infrastructure and environment configuration — prerequisite for all schema changes (completed 2026-03-18)
- [ ] **Phase 2: Discovery** - Tags and albums so contributors can organize photos and readers can browse by topic
- [ ] **Phase 3: AI Features** - Background AI photo analysis, description suggestions, tag suggestions, and writing assistant
- [ ] **Phase 4: Social Graph** - Follow/unfollow, activity feed of posts from followed contributors

## Phase Details

### Phase 1: Foundation
**Goal**: The codebase can safely evolve its schema and load secrets from the environment
**Depends on**: Nothing (first phase)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04
**Success Criteria** (what must be TRUE):
  1. Running `flask db migrate` and `flask db upgrade` applies schema changes to the existing database without data loss
  2. The application starts and connects to the database with WAL mode enabled (concurrent reads and background writes do not deadlock)
  3. The Anthropic API key is read from a `.env` file — removing it from `.env` causes a clear startup warning, not a silent failure
  4. All configuration values (secret key, API keys, debug flag) are read from environment variables, not hardcoded
**Plans:** 1/1 plans complete

Plans:
- [x] 01-01-PLAN.md — Environment config, WAL mode, and Flask-Migrate bootstrap

### Phase 2: Discovery
**Goal**: Contributors can organize posts with tags and albums; readers can browse by tag or album
**Depends on**: Phase 1
**Requirements**: DISC-01, DISC-02, DISC-03, DISC-04, DISC-05, DISC-06, DISC-07, DISC-08, DISC-09
**Success Criteria** (what must be TRUE):
  1. Contributor can add tags to a post on the create/edit form and see them displayed on the post detail page, each tag linking to a tag browse page
  2. Tags entered in mixed case or with extra whitespace are stored normalized (lowercase, trimmed) so "Golden Hour" and "golden hour" resolve to the same tag
  3. Any authenticated user can create an album, add posts to it, remove posts from it, and share the album URL with others who can view all posts in it
  4. A user can browse a list of all albums on the platform and open any album to see its posts
**Plans:** 1/2 plans executed

Plans:
- [ ] 02-01-PLAN.md — Tag model, normalization, routes, and templates (DISC-01 through DISC-04)
- [ ] 02-02-PLAN.md — Album model, CRUD routes, templates, and nav link (DISC-05 through DISC-09)

### Phase 3: AI Features
**Goal**: Contributors receive AI-generated description drafts and tag suggestions after uploading photos, and can request AI improvement of their post text at any time
**Depends on**: Phase 2
**Requirements**: AI-01, AI-02, AI-03, AI-04, AI-05, AI-06, AI-07
**Success Criteria** (what must be TRUE):
  1. After a contributor uploads photos, the upload completes immediately (does not wait for AI); the post shows a processing status indicator that updates when AI analysis is ready
  2. When AI analysis is ready, the contributor sees a suggested description they can accept, edit, or discard — accepting replaces the current post description
  3. When AI analysis is ready, the contributor sees suggested tags as a checkbox list they can select, edit, or dismiss individually — confirmed tags are normalized and saved to the post
  4. Contributor can click an "Improve text" button on their post description at any time and receive an AI-rewritten version to accept, edit, or discard
**Plans**: TBD

Plans:
(none yet — populated by plan-phase)

### Phase 4: Social Graph
**Goal**: Users can follow contributors they like and see a personalized feed of their posts
**Depends on**: Phase 1
**Requirements**: SOCL-01, SOCL-02, SOCL-03, SOCL-04, SOCL-05
**Success Criteria** (what must be TRUE):
  1. Authenticated user can follow a contributor from their profile page and the follow is reflected immediately in the follower/following counts on that profile
  2. Authenticated user can unfollow a contributor they already follow from the same profile page
  3. Authenticated user can visit their activity feed and see posts from contributors they follow, ordered newest first, with no posts from contributors they do not follow
  4. Activity feed is paginated so users with many followed contributors are not presented with an unbounded page load
**Plans**: TBD

Plans:
(none yet — populated by plan-phase)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 1/1 | Complete    | 2026-03-18 |
| 2. Discovery | 1/2 | In Progress|  |
| 3. AI Features | 0/TBD | Not started | - |
| 4. Social Graph | 0/TBD | Not started | - |
