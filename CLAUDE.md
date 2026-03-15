# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CoffeeRun is a team coffee ordering app. Users create daily orders for colleagues, share them via link, and track order history. The stack is React 19 + TypeScript (frontend on Vercel) and FastAPI + PostgreSQL (backend self-hosted on Docker, core-docker-01).

**Active work: Multi-team support.** The app is being refactored from a single-team deployment to support multiple independent teams. See `CoffeeRun_MultiTeam_Roadmap_v2.docx` in the project root for the full roadmap. Implementation is split into 5 phases — read sections 9 and 10 of the roadmap for details.

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
- **Auth middleware**: `app/middleware/auth.py` provides `get_current_user` FastAPI dependency (reads JWT from cookie)
- **Database**: Async SQLAlchemy 2 with `AsyncSession`; PostgreSQL in production, SQLite in dev; all PKs are UUIDs
- **Order items**: Snapshot drink details at creation time — they are immutable historical records and do not reference live menu items
- **Soft deletes**: Colleagues and menu items use `is_active=False` rather than hard deletes
- **Email service**: `app/services/email.py` sends via Resend; falls back to console logging if API key is absent
- **Roles**: Currently `UserRole` enum (`admin`/`viewer`) on the `users` table. Being replaced by per-team roles — see Multi-Team Roadmap below.

### Key Relationships
- A `CoffeeOption` belongs to a `Colleague` and stores their default drink preferences
- An `Order` has many `OrderItem` rows; each `OrderItem` stores a snapshot of the drink at order time
- `MagicLinkToken` is consumed on verify and expires after `MAGIC_LINK_EXPIRY_MINUTES`

### Deployment
- **Docker/Dockge** (backend): compose entrypoint runs `alembic upgrade head` then starts gunicorn; image is built by GitHub Actions on push to `main` and pushed to GHCR (`ghcr.io/quietlikeninja/coffeerun:latest`)
- **Vercel** (frontend): `vercel.json` rewrites all routes to `index.html` for SPA routing
- Cookie is `SameSite=None; Secure` to support cross-origin requests between Vercel and the homelab domain

## Multi-Team Roadmap

The full specification is in `CoffeeRun_MultiTeam_Roadmap_v2.docx`. Key points:

### Database State
The production database contains only test data. The migration approach is **clean-slate**: delete all existing Alembic migrations in `alembic/versions/`, drop/recreate the database, and create a single new initial migration with the complete multi-team schema. No data preservation is needed.

To reset the database before running the new migration:
```bash
# SQLite (local dev): delete the database file
rm backend/coffeerun.db

# PostgreSQL (production): drop and recreate
psql -U coffeerun -c "DROP DATABASE coffeerun;"
psql -U coffeerun -c "CREATE DATABASE coffeerun;"

# Then run the new migration
cd backend
PYTHONPATH=. alembic upgrade head
```

### Schema Changes Summary
- **New tables**: `teams`, `team_memberships`, `team_invites`
- **New enums**: `TeamRole` (owner/manager/member), `ColleagueType` (colleague/visitor)
- **Modified**: `users` (remove `role`, add `display_name`), `colleagues` (add `team_id`, `user_id`, `colleague_type`), `orders` (add `team_id`), `drink_types`/`sizes`/`milk_options` (add `team_id`)
- **Removed**: `UserRole` enum from `users` table — roles are now per-team via `team_memberships`
- **Menu seeding**: No longer in the migration. Menu items are seeded per-team at team creation time via `app/services/team.py`

### Implementation Phases
1. **Phase 1 — Schema & Models**: New models, enums, clean-slate migration, menu seeding utility. See roadmap section 10 for exact file changes and acceptance criteria.
2. **Phase 2 — Auth & Team CRUD**: Team management endpoints, invite system, updated auth middleware with `get_team_member` and `require_role()`.
3. **Phase 3 — Scope Existing Endpoints**: Re-mount all resource routers under `/teams/{team_id}/`, team-scoped queries, visitor support.
4. **Phase 4 — Frontend: Team Management**: Team switcher, create team, team settings, invite accept, empty state.
5. **Phase 5 — Frontend: Updated Workflows**: Team-scoped dashboard, visitor creation, self-service drink editing, stats scoping.

### Important: Expected Breakage After Phase 1
After Phase 1 is implemented, the existing API routes **will not function** because they depend on `User.role` (which is removed) and don't pass `team_id` (which is now required). **This is expected.** Do not attempt to fix routers, schemas, middleware, or services during Phase 1. They are updated in Phases 2 and 3.

### Phase 1 Scope (What to Change)
- `backend/app/models/user.py` — Remove `UserRole`, remove `role` from User, add `display_name`
- `backend/app/models/team.py` — NEW: `Team`, `TeamMembership`, `TeamInvite`, `TeamRole`, `ColleagueType`
- `backend/app/models/colleague.py` — Add `team_id`, `user_id`, `colleague_type`
- `backend/app/models/menu.py` — Add `team_id` to all three models
- `backend/app/models/order.py` — Add `team_id` to Order
- `backend/app/models/__init__.py` — Export new models and enums
- `backend/alembic/versions/*` — Delete ALL existing files, create single new migration
- `backend/app/services/team.py` — NEW: `seed_team_menu()` utility
- `backend/app/config.py` — Add `invite_expiry_days: int = 7`

### Phase 1 Scope (What NOT to Change)
- `backend/app/middleware/auth.py` — Updated in Phase 2
- `backend/app/routers/*` — Updated in Phase 3
- `backend/app/schemas/*` — Updated in Phases 2/3
- `backend/app/services/auth.py` — Updated in Phase 2
- All frontend code — Updated in Phases 4/5
