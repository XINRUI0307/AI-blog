# Feature Landscape

**Domain:** AI-enhanced photo blog community (curated, small-membership)
**Researched:** 2026-03-18
**Confidence note:** WebSearch and Brave Search were unavailable during this research session. Analysis draws from training knowledge of platforms including 500px, Flickr, Glass, VSCO, Pixelfed, and common notification/AI-UX patterns as of August 2025. Confidence is MEDIUM on feature expectations, MEDIUM-HIGH on AI UX patterns (well-documented space).

---

## Table Stakes

Features users expect from any photo community. Missing = product feels incomplete or abandoned.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Tag posts | Discoverability baseline — every photo platform has it | Low | Needs tag model, tag input on post form, tag browse page |
| Browse by tag | Paired expectation with tagging — tags with no browse page confuse users | Low | Simple filtered query; reuses post-list template |
| Photo albums / collections | Users expect to group thematically related posts (trip, series, project) | Medium | Needs Album model, many-to-many Album↔Post, album CRUD, album gallery view |
| Follow other contributors | Standard social graph primitive — absent = no reason to return | Medium | Needs Follow join table (follower_id, followed_id), follow/unfollow endpoints |
| Activity feed (followed users) | If follow exists, users expect a personalised feed immediately | Medium | Filtered post query by followed contributor IDs; pagination important |
| In-app notifications | New follower, comment on own post, new post from followed — users expect a bell icon | Medium | Needs Notification model; polling or badge on page load is sufficient; no real-time required |
| Search includes tags | Once tags exist, users expect search to cover them | Low | Extend existing search query to JOIN tags |
| Contributor profile shows their albums | Profile pages feel thin without organised work visible | Low | Relationship query; reuses album list component |

---

## Differentiators

Features that set this platform apart. Not universally expected, but meaningfully valued when present.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| AI-generated description suggestion | Reduces blank-page anxiety; surfaces visual details contributor may not articulate | Medium | Vision API call (Claude/OpenAI) on photo upload; result stored as draft; contributor edits before saving — never auto-published |
| AI tag suggestions | Saves tagging effort; improves consistency of vocabulary across the community | Medium | Same vision API call can return tags alongside description; display as checkboxes contributor confirms or edits |
| AI writing assistant (improve text) | On-demand polish for contributors who have written something but want help refining tone/clarity | Medium | Text-only LLM call (no vision needed); triggered by an explicit "Improve" button on post edit form |
| Curated admission (admin approval) | Signals quality community, not open-signup spam; already exists | None | Already built — preserve and protect this |
| 18-month auto-purge | Keeps feed fresh; unusual and differentiating for small communities | None | Already built |
| Tag-based discovery page | Beyond simple tag filtering — a tags index showing popular tags, count, recent posts per tag | Low | Aggregate query; good for exploration without knowing what to search |

---

## Anti-Features

Features to deliberately NOT build in this milestone.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Real-time notifications (WebSockets) | Adds infrastructure complexity (background thread, connection management) disproportionate to a small curated community | Poll for notification count on page load with a lightweight `/api/notifications/count` endpoint — sufficient for this scale |
| Email notifications | Requires email service integration, deliverability setup, unsubscribe flows — out of scope per PROJECT.md | In-app only; add email later as standalone milestone |
| AI auto-publishing descriptions/tags | If AI output is published without contributor review, trust breaks on first bad output | Always present AI output as a draft/suggestion requiring explicit confirmation |
| AI moderation / content flagging | Complex, high false-positive risk, admin-approval workflow already handles this | Keep human moderation via existing report + admin review flow |
| Nested comments / comment threads | Adds data model complexity for a feature this community hasn't requested | Flat comments work fine at small scale |
| Public hashtag pages (Instagram-style) | Community is curated and semi-public; a fully public tag page changes the access model | Tag browse stays within authenticated member experience |
| Infinite scroll | Hard to implement correctly with Flask/Jinja2 SSR and SQLite; pagination already works | Keep paginated browsing; add "load more" only if users explicitly request it |
| Multiple AI provider abstraction layer | Over-engineering for v1; adds config complexity | Pick one provider (recommend Claude vision or OpenAI), hard-code it, refactor later if needed |
| Follow counts / follower leaderboards | Introduces social anxiety and status competition that degrades small community health | Show follow relationships contextually (e.g., "you follow this person") without public counts |

---

## Feature Dependencies

```
Tag model
  → Add tags to post form
  → Tag browse page
  → Search includes tags
  → AI tag suggestions (tags must exist before AI can suggest from vocabulary)
  → Tag discovery index page

Album model
  → Album CRUD (create, edit, delete)
  → Add/remove posts from album
  → Album browse (by contributor, all albums)
  → Profile shows contributor's albums

Follow model (follower_id, followed_id)
  → Follow / unfollow endpoints
  → Activity feed (depends on Follow to know whose posts to show)
  → Notification: new follower (depends on Follow)
  → Notification: new post from followed user (depends on Follow + post creation hook)

Notification model
  → Notification: new follower         (requires Follow)
  → Notification: comment on own post  (requires Comment already exists -- it does)
  → Notification: new post from followed (requires Follow + post create hook)
  → Notification badge / bell icon in nav
  → Mark notifications read

AI vision call (photo upload hook)
  → AI description suggestion (draft field on post)
  → AI tag suggestions (checkboxes on post form)

AI text call (writing assistant)
  → Improve post description on demand (no dependency on tags or follow)
```

---

## AI Features: UX Pattern Detail

This section documents established UX patterns for AI-assisted photo content, since these are non-obvious to implement well.

### AI Description Generation

**Pattern:** Suggest, don't impose.

1. Contributor uploads photo(s) and submits the post form.
2. Upload succeeds immediately (non-blocking). Post is saved with whatever description the contributor typed (may be blank).
3. AI vision call runs asynchronously in a background thread (or via `threading.Thread` since no task queue exists).
4. When AI response arrives, store it in a `ai_description_draft` column on Post (or a separate AiSuggestion table).
5. Contributor sees a dismissible banner on the post edit page: "AI generated a description suggestion — [view/use it]".
6. Clicking opens the suggestion in a text area pre-populated alongside the current description; contributor chooses to replace, merge, or discard.
7. Saved only when contributor clicks Save.

**Why this pattern:** Contributors retain authorship. AI output is never auto-published. Bad AI output doesn't damage the post. Fits the PROJECT.md constraint "AI as optional enhancement — AI features augment, never block contributor workflow."

**Complexity note:** Requires a background thread or simple task-polling mechanism. Flask's `threading.Thread` works for SQLite scale. Celery is overkill here.

### AI Tag Suggestions

**Pattern:** Checkbox confirmation, not auto-apply.

1. AI call (same or separate call as description) returns a list of 5–10 tag candidates.
2. Stored in `ai_tag_suggestions` (JSON column or separate table).
3. On post edit page, shown as a row of checkbox pills: "AI suggested: [landscape] [golden hour] [mountain] [fog] [wide angle]".
4. Contributor checks the ones they want; unchecked suggestions are discarded.
5. Contributor can also add free-text tags not in the AI list.

**Why checkboxes not free-text:** Reduces friction while maintaining control. Avoids AI hallucinated tags silently entering the tag vocabulary.

### AI Writing Assistant

**Pattern:** On-demand, in-place, non-destructive.

1. On the post create/edit form, an "Improve" button sits next to the description textarea.
2. Clicking sends current description text to LLM (text-only, no vision needed) with a prompt to improve clarity and tone for a photography audience.
3. Response shown in a modal or side-by-side diff view.
4. Contributor clicks "Apply" to replace description or "Discard" to keep original.
5. No auto-save triggered — contributor still controls Save.

**Why on-demand not automatic:** Automatic rewrites feel presumptuous and erase contributor voice. On-demand respects that some contributors want raw authenticity.

---

## Notification Patterns for Small Communities

### What to notify

| Event | Recipient | Priority |
|-------|-----------|----------|
| Someone follows you | Followed user | Medium |
| Someone comments on your post | Post author | High |
| A contributor you follow publishes a new post | Follower | Medium |
| Someone rates your post | Post author | Low — HIGH NOISE, recommend omitting |

**Recommendation:** Omit rating notifications entirely. At low content volume, every rating pinging the author creates noise without value. Add only if users request it.

### Notification delivery

- In-app only (per PROJECT.md constraints).
- Unread count badge in nav bar, fetched on each page load (simple DB count query).
- Notification list page (paginated) showing event type, actor, target, timestamp.
- Mark all read / mark individual read.
- No push, no email, no WebSockets — HTTP polling on page load is correct for this community size.

### Notification data model minimum

```
Notification:
  id
  recipient_id (FK users)
  actor_id (FK users, nullable — system notifications have no actor)
  type (enum: 'new_follower', 'new_comment', 'new_post_from_followed')
  target_type ('post', 'user')
  target_id (integer)
  is_read (boolean, default False)
  created_at (datetime)
```

---

## MVP Recommendation

Given the existing platform already has authentication, posts, comments, ratings, and direct messaging, the MVP for this milestone should deliver:

**Priority 1 — Discovery foundation (unblock everything else)**
1. Tag model + add tags to posts + browse by tag (tags are dependency for AI suggestions)
2. Extend search to include tags

**Priority 2 — Organisation**
3. Albums model + CRUD + post-album association + browse

**Priority 3 — Social graph**
4. Follow model + follow/unfollow
5. Activity feed (posts from followed users)

**Priority 4 — Notifications**
6. Notification model + in-app badge + notification list
7. Trigger: new follower, new comment on own post, new post from followed contributor

**Priority 5 — AI features (highest complexity, most value)**
8. AI description suggestion (async, draft-first UX)
9. AI tag suggestions (checkbox UX)
10. AI writing assistant (on-demand, modal UX)

**Defer:**
- Tag discovery index page: low-effort but non-critical; add after core tags work
- Album browse across all contributors: secondary to per-contributor album view
- Rating notifications: noise-to-value ratio too high for v1

---

## Sources

- Analysis based on training knowledge of photo community platforms (Flickr, 500px, Glass, VSCO, Pixelfed) as of August 2025 — MEDIUM confidence
- AI description/tagging UX patterns from documented implementations (Google Photos, Apple Photos, Anthropic Claude vision demos) — MEDIUM-HIGH confidence
- Notification patterns: standard industry patterns for small community platforms — MEDIUM-HIGH confidence
- WebSearch and Brave Search unavailable during this session — external source verification not performed
- All existing platform analysis based on direct codebase read (PROJECT.md, models.py, CONCERNS.md, spec.md) — HIGH confidence
