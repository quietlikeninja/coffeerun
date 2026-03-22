# CoffeeRun Test Plan — Execution Tracker

> **Instructions:** Copy this file for each test cycle. Fill in the date and tester, then mark each test as ✅ (pass) or ❌ (fail). Add notes for any failures.

## Test Cycle Info

| Field | Value |
|-------|-------|
| Date | 2026-03-16 |
| Tester | Justin Ward |
| Environment | Local dev (SQLite) |
| Backend version | abd8891 |
| Frontend version | 40c36d2 |

---

## Level 1: Automated Tests (pytest)

```bash
cd backend && pytest -v
```

- ✅ All tests pass (expected: 129, 0 failures)
- ✅ Test count: 129 (180 warnings)

---

## Level 2: Manual Test Cases

### Environment Setup

- ✅ Database reset (`rm -f coffeerun.db && PYTHONPATH=. alembic upgrade head`)
- ✅ Backend running on port 8000
- ✅ Frontend running on port 5173
- ✅ RESEND_API_KEY is NOT set (magic links print to console)
- ✅ Health check: `http://localhost:8000/api/health` returns `{"status": "ok"}`

### Test Data Setup

- ✅ **SET-01** Create owner@test.com account via magic link
    - Magic link was provided but didn't initially work.  When tried again it noted the token had already been used.  Going back to the root page showed the user as logged in.
- ✅ **SET-02** Create "Team Alpha"
    - Initial page says ask an owner or manage to add colleagues even though logged in as an owner
- ✅ **SET-03** Add colleagues: Alice (Lrg Oat Flat White, usually in), Bob (Reg Long Black, usually in), Charlie (Sm Cappuccino 1 sugar, not usually in)
    - when adding a user the colleague/visitor drop down box isn't tall enough (Edge - VASGaming01)
- ✅ **SET-04** Invite manager@test.com as Manager, accept in incognito
- ✅ **SET-05** Invite member@test.com as Member linked to Alice, accept in incognito
- ✅ **SET-06** Create "Team Beta" as owner@test.com
- ✅ **SET-07** Invite multi@test.com to Team Alpha and Team Beta as Member

---

### 4.1 Authentication

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-AUTH-01 | Magic Link Login (New User) | ✅ | Magic link was provided but didn't initially work.  When tried again it noted the token had already been used.  Going back to the root page showed the user as logged in. |
| TC-AUTH-02 | Magic Link Login (Existing User) | ✅ | |
| TC-AUTH-03 | Invalid Email Rejected | ✅ | |
| TC-AUTH-04 | Unauthenticated Access Redirects | ✅ | |

### 4.2 Team Management

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-TEAM-01 | Create Team | ✅ | Initial page says ask an owner or manage to add colleagues even though logged in as an owner |
| TC-TEAM-02 | Team Settings — View Members | ✅ | |
| TC-TEAM-03 | Rename Team | ✅ | |
| TC-TEAM-04 | Delete Team (Soft Delete) | ✅ | |

### 4.3 Invite Flow

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-INV-01 | Invite New User as Manager | ✅ | |
| TC-INV-02 | Invite Existing User as Member with Colleague Linking | ✅ | |
| TC-INV-03 | Invite Email Mismatch | ✅ | |
| TC-INV-04 | Duplicate Invite Resends | ✅ | |
| TC-INV-05 | Revoke Pending Invite | ✅ | |

### 4.4 Role-Based Access Control

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-ROLE-01 | Member Cannot Access Admin Pages | ✅ | Settings gear is visible but doesn't allow access |
| TC-ROLE-02 | Manager Can Access Admin, Cannot Delete Team | ✅ | |
| TC-ROLE-03 | Owner Transfers Ownership | ✅ | |

### 4.5 Daily Ordering Workflow

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-ORD-01 | Create Basic Order | ✅ | |
| TC-ORD-02 | Copy Order to Clipboard | ✅ | |
| TC-ORD-03 | Share Order Link (Public, No Auth) | ✅ | |
| TC-ORD-04 | Change Coffee Selection Before Ordering | ✅ | Editing user on the dashboard has add coffee option but it doesn't work |

### 4.6 Visitors

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-VIS-01 | Add Visitor from Dashboard | ✅ | |
| TC-VIS-02 | Include Visitor in Order | ✅ | |
| TC-VIS-03 | Visitor Persists Across Orders | ✅ | |
| TC-VIS-04 | Promote Visitor to Colleague | ✅ | |
| TC-VIS-05 | Member Cannot Add Visitor | ✅ | |

### 4.7 Self-Service Drink Editing

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-SELF-01 | Member Edits Own Coffee Options | ❌ | The edit option is available but when clicking on Edit for the existing coffee or clicking on add coffee option nothing happens |
| TC-SELF-02 | Member Cannot Edit Others' Options | ✅ | |
| TC-SELF-03 | Owner/Manager Sees Edit on All Cards | ✅ | |

### 4.8 Team Switching

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-SWITCH-01 | Switch Between Teams | ✅ | |
| TC-SWITCH-02 | Active Team Persists Across Refresh | ✅ | |
| TC-SWITCH-03 | Removed from Team While Active | ❌ | Team Beta remains selected and remains an option even after logging out and back in |

### 4.9 Stats

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-STAT-01 | Stats Show Team-Scoped Data | ✅ | |
| TC-STAT-02 | Stats Date Range Filter | ⬜ | |

### 4.10 Menu Management

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-MENU-01 | Add and Remove Menu Items | ✅ | |

### 4.11 Mobile & Responsive

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-MOB-01 | Mobile Layout — Dashboard | ⬜ | |
| TC-MOB-02 | Order Creation on Mobile | ⬜ | |

---

## Summary

| Category | Total | Pass | Fail | Blocked |
|----------|-------|------|------|---------|
| Authentication | 4 | 4 | 0 | 0 |
| Team Management | 4 | 4 | 0 | 0 |
| Invite Flow | 5 | 5 | 0 | 0 |
| Role-Based Access | 3 | 3 | 0 | 0 |
| Ordering | 4 | 4 | 0 | 0 |
| Visitors | 5 | 5 | 0 | 0 |
| Self-Service Editing | 3 | 2 | 1 | 0 |
| Team Switching | 3 | 2 | 1 | 0 |
| Stats | 2 | 1 | 0 | 1 |
| Menu Management | 1 | 1 | 0 | 0 |
| Mobile | 2 | 0 | 0 | 2 |
| **TOTAL** | **36** | **31** | **2** | **3** |

## Defects Found

| # | Test Case | Severity | Description | GitHub Issue |
|---|-----------|----------|-------------|--------------|
| 1 | TC-SELF-01 | Low | The edit icon next to Alice's name is available but when clicking on Edit for the existing coffee or clicking on add coffee option nothing happens. | [#3](https://github.com/quietlikeninja/coffeerun/issues/3) |
| 2 | TC-SWITCH-03 | Low | After Team Beta was deleted by the owner it remains selected for a user and remains an option even after logging out and back in. | [#4](https://github.com/quietlikeninja/coffeerun/issues/4) |
