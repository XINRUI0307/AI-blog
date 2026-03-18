---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — test suite is explicitly out of scope for this project |
| **Config file** | none |
| **Quick run command** | N/A — manual verification only |
| **Full suite command** | N/A — manual verification only |
| **Estimated runtime** | ~2 minutes (manual checks) |

---

## Sampling Rate

- **After every task commit:** Run the corresponding manual verification command for that task
- **After every plan wave:** Run all manual checks for completed tasks
- **Before `/gsd:verify-work`:** All 4 manual checks must pass
- **Max feedback latency:** Immediate (manual CLI commands)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | INFRA-01 | manual | `flask db current` shows `(head)` | N/A | ⬜ pending |
| 1-01-02 | 01 | 1 | INFRA-02 | manual | `flask shell` → `db.session.execute(text("PRAGMA journal_mode")).scalar()` returns `"wal"` | N/A | ⬜ pending |
| 1-01-03 | 01 | 1 | INFRA-03 | manual | Remove `ANTHROPIC_API_KEY` from `.env`, run `flask run`, observe warning output | N/A | ⬜ pending |
| 1-01-04 | 01 | 1 | INFRA-04 | manual | `grep -rn "change-this\|hardcoded\|your-api-key" app.py` returns no matches | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

None — no automated test infrastructure is needed or planned for this phase. All verification is via manual CLI commands.

*Existing infrastructure covers all phase requirements (manual verification).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `flask db current` shows head revision after bootstrap | INFRA-01 | No test suite; Flask-Migrate CLI is the verification mechanism | Run `flask db current` in project root — output must include `(head)` |
| WAL mode active on database connection | INFRA-02 | No test suite; pragma must be verified via flask shell | `flask shell` → `from sqlalchemy import text` → `print(db.session.execute(text("PRAGMA journal_mode")).scalar())` → must print `wal` |
| Startup warning when ANTHROPIC_API_KEY absent | INFRA-03 | No test suite; requires live app startup | Remove or comment out `ANTHROPIC_API_KEY` in `.env`, run `flask run`, confirm warning is printed to stderr, restore key |
| All config values from environment, not hardcoded | INFRA-04 | Code review required | `grep -rn "change-this-in-production\|your-api-key" app.py` returns no matches; inspect `app.config` assignments — all must use `os.environ.get()` |

---

## Validation Sign-Off

- [ ] All tasks have manual verify commands documented
- [ ] Sampling continuity: each task has a post-task verification step
- [ ] Wave 0 covers all MISSING references (none required)
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s per manual check
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
