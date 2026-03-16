# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CoffeeRun is a multi-team coffee ordering app. Users create teams, invite colleagues, create daily orders, share them via link, and track order history. The stack is React 19 + TypeScript (frontend on Vercel) and FastAPI + PostgreSQL (backend self-hosted on Docker).

## Current Status

**Phase 1 (Schema & Models) ✅ COMPLETE.** Multi-team database schema.

**Phase 2 (Auth & Team CRUD) ✅ COMPLETE.** Auth middleware with `get_team_member` and `require_role()`. Team CRUD, membership management, invite system. 82 pytest tests passing.

**Phase 3 (Scope Existing Endpoints) ← CURRENT.** See `CoffeeRun_Phase3_Handoff.docx`. Re-mount resource routers under `/teams/{team_id}/`, team_id filtering, self-service drink editing, visitor support.

**Phase 4 (Frontend: Team Management) — READY.** See `CoffeeRun_Phase4_Handoff.docx`. Requires Phase 3 backend to be complete. Covers AuthContext refactor, team switcher, create team, team settings, invite accept, routing changes.

## Commands

### Frontend (`frontend/`)
```bash
npm run dev       # Vite dev server on port 5173
npm run build     # tsc -b && vite build
npm run lint      # ESLint
npm run preview   # Preview production build
```

### Backend (`backend/`)
```bash
uvicorn app.main:app --reload --port 8000   # Dev server
alembic upgrade head                         # Apply migrations
ruff format . && ruff check .               # Format/lint
pytest -v                                    # Run tests (82 passing)
```

### Environment Setup
- Backend: copy `backend/.env.example` to `backend/.env`; SQLite by default in dev
- Frontend: set `VITE_API_URL` in `frontend/.env` (defaults to `http://localhost:8000`)
- Magic links print to console when `RESEND_API_KEY` is not set

## Architecture

### Frontend
- **React 19 + TypeScript + Vite + Tailwind CSS v4 + shadcn-style components**
- **Auth flow**: Email → magic link → `/auth/verify?token=` → httpOnly JWT cookie → `AuthContext` loaded via `/auth/me`
- **Routing**: React Router v7; `ProtectedRoute` and `AdminRoute` wrappers (AdminRoute being replaced with role-based check in Phase 4)
- **API client**: `src/api/client.ts` — fetch wrapper with typed interfaces. Currently uses global paths; Phase 4 adds team-scoped helper
- **Shared orders**: `/shared/{shareToken}` — public route, no auth
- **Key note**: The `User` interface still has `role: 'admin' | 'viewer'` and `AuthContext` uses `isAdmin`. Phase 4 removes this in favour of team-role-based permissions (`isOwnerOrManager`)

### Backend
- **FastAPI + async SQLAlchemy 2 + PostgreSQL (prod) / SQLite (dev)**
- **Auth middleware**: `get_current_user` (any user), `get_team_member` (resolves team role), `require_role()` (checks specific roles)
- **Models**: Team-scoped. Roles are per-team via `TeamMembership` (owner/manager/member). Colleagues have `colleague_type` (colleague/visitor)
- **Order items**: Denormalized drink snapshots — immutable historical records
- **Soft deletes**: Colleagues, menu items, teams use `is_active=False`

### Test Suite
- pytest with pytest-asyncio and httpx
- File-based SQLite test database (created/destroyed per session)
- Factory helpers in `tests/conftest.py`
- 82 tests across 5 files (auth, teams, members, invites, services)

## Multi-Team Roadmap

Full spec: `CoffeeRun_MultiTeam_Roadmap_v2.docx`

### Implementation Phases
1. **Phase 1 — Schema & Models** ✅ COMPLETE
2. **Phase 2 — Auth & Team CRUD** ✅ COMPLETE
3. **Phase 3 — Scope Existing Endpoints** ← CURRENT (`CoffeeRun_Phase3_Handoff.docx`)
4. **Phase 4 — Frontend: Team Management** — READY (`CoffeeRun_Phase4_Handoff.docx`)
5. **Phase 5 — Frontend: Updated Workflows** — Not yet specified

### Phase 3 Scope (Backend)
- Re-mount colleagues, coffee_options, menu, orders, stats routers under `/teams/{team_id}/`
- Remove deprecated `require_admin` shim
- Self-service drink editing for linked Members
- Visitor support in orders
- Stats restricted to Owner/Manager
- New pytest test files for all re-scoped endpoints

### Phase 4 Scope (Frontend)
- Refactor `AuthContext`: remove `isAdmin`, add team memberships + active team + `isOwnerOrManager`
- Refactor `api/client.ts`: update `User` type (no role), add `teamApi` helper for team-scoped requests
- New pages: CreateTeam, TeamSettings, InviteAccept, NoTeams (empty state)
- Team switcher in header navigation
- Replace `AdminRoute` with role-based `ManagerRoute`
- Update all page components to use team-scoped API paths
