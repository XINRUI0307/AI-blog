---
phase: 2
slug: discovery
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — test suite is explicitly out of scope for this project |
| **Config file** | none |
| **Quick run command** | N/A — manual browser verification only |
| **Full suite command** | N/A — manual browser verification only |
| **Estimated runtime** | ~5 minutes (full manual checklist) |

---

## Sampling Rate

- **After every task commit:** Manual smoke test in browser for that task's feature
- **After every plan wave:** Run full manual checklist against all 9 success criteria
- **Before `/gsd:verify-work`:** All 9 success criteria confirmed manually
- **Max feedback latency:** Immediate (manual browser checks)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Manual Steps | Status |
|---------|------|------|-------------|-----------|--------------|--------|
| 2-xx-01 | tags | 1 | DISC-01, DISC-02 | manual | Submit create post form with tags "Golden Hour, landscape" → verify DB stores `golden-hour`, `landscape` | ⬜ pending |
| 2-xx-02 | tags | 1 | DISC-03, DISC-04 | manual | Visit `/tag/golden-hour` → verify post listed; visit post detail → verify tag links present | ⬜ pending |
| 2-xx-03 | albums | 1 | DISC-05, DISC-06, DISC-07 | manual | Log in as reader → create album → add post → remove post → verify each step | ⬜ pending |
| 2-xx-04 | albums | 1 | DISC-08, DISC-09 | manual | Visit `/album/<id>` (unauthenticated) → verify posts shown; visit `/albums` → verify list shown | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

None — no automated test infrastructure is needed or planned. All verification is manual browser testing.

*Existing infrastructure covers all phase requirements (manual verification).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Tags field on create/edit form | DISC-01 | No test suite | Load `/post/create` and `/post/<id>/edit` — confirm tags text input is present |
| Tag normalization | DISC-02 | No test suite | Submit post with tags `"Golden Hour, landscape"` → `flask shell` → `Tag.query.all()` → names must be `golden-hour`, `landscape` |
| Tag browse page | DISC-03 | No test suite | Visit `/tag/golden-hour` — post must appear in listing |
| Tag links on post detail | DISC-04 | No test suite | Visit post detail — tags must appear as links pointing to `/tag/<slug>` |
| Authenticated album creation | DISC-05 | No test suite | Log in as reader (non-contributor) → visit `/album/create` → submit form → album created |
| Add any post to album | DISC-06 | No test suite | As album owner, add a post from a different contributor → confirm it appears in album |
| Remove post from album | DISC-07 | No test suite | As album owner, remove a previously added post → confirm it is gone from album |
| Album browse page (public) | DISC-08 | No test suite | Log out → visit `/album/<id>` → posts visible without login |
| Albums list page (public) | DISC-09 | No test suite | Log out → visit `/albums` → all albums listed without login |

---

## Validation Sign-Off

- [ ] All tasks have manual verification steps documented
- [ ] Sampling continuity: each task has a post-task browser check
- [ ] Wave 0 covers all MISSING references (none required)
- [ ] No watch-mode flags
- [ ] Feedback latency < 300s per manual check
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
