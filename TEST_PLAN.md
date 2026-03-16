# CoffeeRun Test Plan — Execution Tracker

> **Instructions:** Copy this file for each test cycle. Fill in the date and tester, then mark each test as ✅ (pass) or ❌ (fail). Add notes for any failures.

## Test Cycle Info

| Field | Value |
|-------|-------|
| Date | _YYYY-MM-DD_ |
| Tester | _name_ |
| Environment | Local dev (SQLite) |
| Backend version | _git commit hash_ |
| Frontend version | _git commit hash_ |

---

## Level 1: Automated Tests (pytest)

```bash
cd backend && pytest -v
```

- [ ] All tests pass (expected: 129, 0 failures)
- [ ] Test count: ___

---

## Level 2: Manual Test Cases

### Environment Setup

- [ ] Database reset (`rm -f coffeerun.db && PYTHONPATH=. alembic upgrade head`)
- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] RESEND_API_KEY is NOT set (magic links print to console)
- [ ] Health check: `http://localhost:8000/api/health` returns `{"status": "ok"}`

### Test Data Setup

- [ ] **SET-01** Create owner@test.com account via magic link
- [ ] **SET-02** Create "Team Alpha"
- [ ] **SET-03** Add colleagues: Alice (Lrg Oat Flat White, usually in), Bob (Reg Long Black, usually in), Charlie (Sm Cappuccino 1 sugar, not usually in)
- [ ] **SET-04** Invite manager@test.com as Manager, accept in incognito
- [ ] **SET-05** Invite member@test.com as Member linked to Alice, accept in incognito
- [ ] **SET-06** Create "Team Beta" as owner@test.com
- [ ] **SET-07** Invite multi@test.com to Team Alpha and Team Beta as Member

---

### 4.1 Authentication

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-AUTH-01 | Magic Link Login (New User) | ⬜ | |
| TC-AUTH-02 | Magic Link Login (Existing User) | ⬜ | |
| TC-AUTH-03 | Invalid Email Rejected | ⬜ | |
| TC-AUTH-04 | Unauthenticated Access Redirects | ⬜ | |

### 4.2 Team Management

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-TEAM-01 | Create Team | ⬜ | |
| TC-TEAM-02 | Team Settings — View Members | ⬜ | |
| TC-TEAM-03 | Rename Team | ⬜ | |
| TC-TEAM-04 | Delete Team (Soft Delete) | ⬜ | |

### 4.3 Invite Flow

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-INV-01 | Invite New User as Manager | ⬜ | |
| TC-INV-02 | Invite Existing User as Member with Colleague Linking | ⬜ | |
| TC-INV-03 | Invite Email Mismatch | ⬜ | |
| TC-INV-04 | Duplicate Invite Resends | ⬜ | |
| TC-INV-05 | Revoke Pending Invite | ⬜ | |

### 4.4 Role-Based Access Control

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-ROLE-01 | Member Cannot Access Admin Pages | ⬜ | |
| TC-ROLE-02 | Manager Can Access Admin, Cannot Delete Team | ⬜ | |
| TC-ROLE-03 | Owner Transfers Ownership | ⬜ | |

### 4.5 Daily Ordering Workflow

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-ORD-01 | Create Basic Order | ⬜ | |
| TC-ORD-02 | Copy Order to Clipboard | ⬜ | |
| TC-ORD-03 | Share Order Link (Public, No Auth) | ⬜ | |
| TC-ORD-04 | Change Coffee Selection Before Ordering | ⬜ | |

### 4.6 Visitors

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-VIS-01 | Add Visitor from Dashboard | ⬜ | |
| TC-VIS-02 | Include Visitor in Order | ⬜ | |
| TC-VIS-03 | Visitor Persists Across Orders | ⬜ | |
| TC-VIS-04 | Promote Visitor to Colleague | ⬜ | |
| TC-VIS-05 | Member Cannot Add Visitor | ⬜ | |

### 4.7 Self-Service Drink Editing

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-SELF-01 | Member Edits Own Coffee Options | ⬜ | |
| TC-SELF-02 | Member Cannot Edit Others' Options | ⬜ | |
| TC-SELF-03 | Owner/Manager Sees Edit on All Cards | ⬜ | |

### 4.8 Team Switching

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-SWITCH-01 | Switch Between Teams | ⬜ | |
| TC-SWITCH-02 | Active Team Persists Across Refresh | ⬜ | |
| TC-SWITCH-03 | Removed from Team While Active | ⬜ | |

### 4.9 Stats

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-STAT-01 | Stats Show Team-Scoped Data | ⬜ | |
| TC-STAT-02 | Stats Date Range Filter | ⬜ | |

### 4.10 Menu Management

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-MENU-01 | Add and Remove Menu Items | ⬜ | |

### 4.11 Mobile & Responsive

| ID | Test Case | Result | Notes |
|----|-----------|--------|-------|
| TC-MOB-01 | Mobile Layout — Dashboard | ⬜ | |
| TC-MOB-02 | Order Creation on Mobile | ⬜ | |

---

## Summary

| Category | Total | Pass | Fail | Blocked |
|----------|-------|------|------|---------|
| Authentication | 4 | | | |
| Team Management | 4 | | | |
| Invite Flow | 5 | | | |
| Role-Based Access | 3 | | | |
| Ordering | 4 | | | |
| Visitors | 5 | | | |
| Self-Service Editing | 3 | | | |
| Team Switching | 3 | | | |
| Stats | 2 | | | |
| Menu Management | 1 | | | |
| Mobile | 2 | | | |
| **TOTAL** | **36** | | | |

## Defects Found

| # | Test Case | Severity | Description | GitHub Issue |
|---|-----------|----------|-------------|-------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
