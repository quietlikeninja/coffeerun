# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CoffeeRun is a team coffee ordering app. Users create daily orders for colleagues, share them via link, and track order history. The stack is React 19 + TypeScript (frontend on Vercel) and FastAPI + PostgreSQL (backend self-hosted on Docker, core-docker-01).

**Active work: Multi-team support.** The app is being refactored from a single-team deployment to support multiple independent teams. See `CoffeeRun_MultiTeam_Roadmap_v2.docx` in the project root for the full roadmap.

## Current Status

**Phase 1 (Schema & Models) ✅ COMPLETE.** Multi-team database schema with teams, team_memberships, team_invites tables. Clean-slate Alembic migration.

**Phase 2 (Auth & Team CRUD) ✅ COMPLETE.** Auth middleware rewritten with `get_team_member` and `require_role()`. Team CRUD, membership management, and invite system all functional. 82 pytest tests passing.

**Phase 3 (Scope Existing Endpoints) ← CURRENT.** See `CoffeeRun_Phase3_Handoff.docx` for the detailed implementation specification. Re-mount resource routers under `/teams/{team_id}/`, add team_id filtering, self-service drink editing, visitor support.

**The resource routers (colleagues, coffee_options, menu, orders, stats) are currently broken** — they use the deprecated `require_admin` shim and don't pass `team_id`. Phase 3 fixes them.

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
# Run dev server
uvicorn app.main:app --reload --port 8000

# Database migrations
alembic upgrade head          # Apply migrations
alembic revision --autogenerate -m "description"  # Create new migration

# Format/lint
ruff format .
ruff check .

# Run tests
pytest             # All tests
pytest -v          # Verbose
pytest -x          # Stop on first failure
pytest tests/test_auth.py   # Single file
```

### Environment Setup
- Backend: copy `backend/.env.example` to `backend/.env`; SQLite is used by default in dev (no Postgres needed)
- Frontend: set `VITE_API_URL` in `frontend/.env` (defaults to `http://localhost:8000`)
- Magic links print to console in dev when `RESEND_API_KEY` is not set

## Architecture

### Frontend
- **Auth flow**: Email → magic link → `/auth/verify?token=` → httpOnly JWT cookie → `AuthContext` loaded via `/auth/me` on mount
- **Protected routes**: `ProtectedRoute` and `AdminRoute` wrappers check `AuthContext`
- **API client**: All fetch calls go through `src/lib/api.ts` (centralized, typed)
- **Shared orders**: `/shared/{shareToken}` is a public route (no auth required)
- **Routing**: React Router v7; Vercel rewrites all paths to `index.html`

### Backend
- **Entry**: `app/main.py` registers all routers under `/api/v1` and mounts CORS middleware
- **Auth middleware**: `app/middleware/auth.py` provides `get_current_user` (any logged-in user), `get_team_member` (resolves team role), and `require_role()` (checks specific roles). The old `require_admin` is a deprecated shim — Phase 3 removes it.
- **Database**: Async SQLAlchemy 2 with `AsyncSession`; PostgreSQL in production, SQLite in dev; all PKs are UUIDs
- **Models**: Team-scoped. `Team` owns `Colleague`, `Order`, `DrinkType`, `Size`, `MilkOption` via `team_id` FK. Roles are per-team via `TeamMembership` (not on User).
- **Order items**: Snapshot drink details at creation time — immutable historical records
- **Soft deletes**: Colleagues, menu items, and teams use `is_active=False`
- **Email service**: `app/services/email.py` sends via Resend; falls back to console logging if API key is absent

### Key Relationships
- A `Team` has many `TeamMembership` rows linking to `User` with a `TeamRole` (owner/manager/member)
- A `Colleague` belongs to a `Team`, has a `colleague_type` (colleague/visitor), and optionally links to a `User` (via `user_id`)
- A `CoffeeOption` belongs to a `Colleague` and stores their drink preferences
- An `Order` belongs to a `Team` and has many `OrderItem` rows (denormalized drink snapshots)

### Test Suite
- pytest with pytest-asyncio and httpx
- File-based SQLite test database (created/destroyed per session)
- Factory helpers in `tests/conftest.py`: `create_test_user`, `create_authenticated_client`, `create_team_with_owner`, `add_team_member`
- 82 tests across 5 files covering auth, teams, members, invites, and services

### Deployment
- **Docker/Dockge** (backend): compose entrypoint runs `alembic upgrade head` then starts gunicorn; image built by GitHub Actions and pushed to GHCR
- **Vercel** (frontend): `vercel.json` rewrites all routes to `index.html` for SPA routing
- Cookie is `SameSite=None; Secure` for cross-origin requests between Vercel and homelab

## Multi-Team Roadmap

Full specification in `CoffeeRun_MultiTeam_Roadmap_v2.docx`. Phase-specific handoff documents provided for each phase.

### Implementation Phases
1. **Phase 1 — Schema & Models** ✅ COMPLETE
2. **Phase 2 — Auth & Team CRUD** ✅ COMPLETE (82 tests passing)
3. **Phase 3 — Scope Existing Endpoints** ← CURRENT. See `CoffeeRun_Phase3_Handoff.docx`
4. **Phase 4 — Frontend: Team Management**: Team switcher, create team, team settings, invite accept, empty state.
5. **Phase 5 — Frontend: Updated Workflows**: Team-scoped dashboard, visitor creation, self-service drink editing, stats scoping.

### Phase 3 Scope (What to Change)
- `backend/app/routers/colleagues.py` — Re-mount under `/teams/{team_id}/`, team_id filtering, visitor support
- `backend/app/routers/coffee_options.py` — Re-mount, self-service editing for linked Members
- `backend/app/routers/menu.py` — Re-mount, team_id filtering on all menu queries
- `backend/app/routers/orders.py` — Re-mount, team_id on orders. Move shared order endpoint out (not team-scoped)
- `backend/app/routers/stats.py` — Re-mount, team-scoped queries, Owner/Manager only
- `backend/app/schemas/colleague.py` — Add colleague_type and user_id to schemas
- `backend/app/main.py` — Update router registration with team-scoped prefixes
- `backend/app/middleware/auth.py` — Remove deprecated `require_admin` shim
- `tests/test_colleagues.py` — NEW: team-scoped colleague CRUD tests
- `tests/test_coffee_options.py` — NEW: coffee option tests + self-service editing
- `tests/test_menu.py` — NEW: team-scoped menu management tests
- `tests/test_orders.py` — NEW: team-scoped order tests
- `tests/test_stats.py` — NEW: team-scoped stats tests
- `tests/conftest.py` — Add helper fixtures for colleagues, coffee options, orders

### Phase 3 Scope (What NOT to Change)
- Auth endpoints and team management endpoints — working from Phase 2
- Database models and migrations — complete from Phase 1
- Existing test files (test_auth, test_teams, test_members, test_invites, test_services) — must continue passing
- All frontend code — updated in Phases 4/5
