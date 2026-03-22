# CoffeeRun - Product Specification

## Overview

CoffeeRun is a multi-team web application for managing daily office coffee orders. Users belong to one or more teams. Within a team, owners and managers maintain the colleague list and coffee preferences. Each morning, any team member selects who is in the office, picks each person's coffee (from their pre-configured options), and generates a consolidated order summary to take to the cafe. The app tracks full order history and provides stats on order frequency and drink popularity.

---

## Architecture

| Layer | Technology | Hosting |
|-------|-----------|---------|
| Frontend | React (Vite SPA), Tailwind CSS, shadcn/ui | Vercel |
| Backend | Python, FastAPI | Docker / homelab |
| Database | PostgreSQL | Docker / homelab |
| ORM | SQLAlchemy + Alembic | — |
| Auth | Email magic links via Resend | — |
| Error Tracking | Sentry (frontend + backend) | — |
| Analytics | Vercel Analytics | — |

### Deployment Topology

- **Frontend**: Vite-built static SPA deployed to Vercel. Includes `@vercel/analytics` and `@sentry/react`.
- **Backend**: FastAPI application running in Docker on core-docker-01, fronted by Caddy reverse proxy. Includes `sentry-sdk[fastapi]`.
- **Database**: PostgreSQL instance in Docker on core-docker-01, connected to the backend via an internal Docker network.
- **Tenancy**: Multi-team. One deployment supports multiple teams; all data is team-scoped.

---

## Authentication & Authorization

### Magic Link Auth Flow

1. User enters their email on the login page.
2. Backend generates a short-lived token (15 min expiry), stores a hash of it, and sends a magic link via Resend.
3. User clicks the link, frontend sends the token to the backend.
4. Backend validates the token, issues a JWT (stored in an httpOnly cookie) with a configurable expiry (default: 7 days).
5. Subsequent requests include the JWT cookie. Backend validates on each request.

### Roles

Roles are **per-team**, stored in `TeamMembership`. A user may have different roles in different teams.

| Role | Capabilities |
|------|-------------|
| **Owner** | All manager capabilities + delete team, transfer ownership, change any member's role |
| **Manager** | Manage colleagues (CRUD), manage coffee options (CRUD), manage menu items, view stats, create/update orders, manage invites |
| **Member** | Select who's in, pick coffees, generate order summary, view shareable link, edit own linked colleague's drink preferences |

The user who creates a team is automatically assigned the **owner** role. Additional users join via team invites.

---

## Data Model

### Tables

#### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| email | VARCHAR(255) | Unique, not null |
| display_name | VARCHAR(100) | Nullable |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### `magic_link_tokens`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK -> users |
| token_hash | VARCHAR(255) | SHA-256 hash of the token |
| expires_at | TIMESTAMP | 15 min from creation |
| used | BOOLEAN | Default: false |
| created_at | TIMESTAMP | |

#### `teams`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| name | VARCHAR(100) | Not null |
| created_by | UUID | FK -> users |
| is_active | BOOLEAN | Default: true. Soft delete flag. |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### `team_memberships`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| team_id | UUID | FK -> teams |
| user_id | UUID | FK -> users |
| role | ENUM('owner', 'manager', 'member') | Per-team role |
| created_at | TIMESTAMP | |

Unique constraint on `(team_id, user_id)`.

#### `team_invites`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| team_id | UUID | FK -> teams |
| email | VARCHAR(255) | Invited email address |
| role | ENUM('owner', 'manager', 'member') | Role to assign on acceptance |
| colleague_id | UUID | FK -> colleagues, nullable. Pre-links invite to an existing colleague record. |
| token_hash | VARCHAR(255) | SHA-256 hash of the invite token |
| invited_by | UUID | FK -> users |
| expires_at | TIMESTAMP | |
| accepted | BOOLEAN | Default: false |
| created_at | TIMESTAMP | |

#### `colleagues`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| team_id | UUID | FK -> teams |
| user_id | UUID | FK -> users, nullable. Links this colleague to a team member for self-service editing. |
| name | VARCHAR(100) | Not null |
| colleague_type | ENUM('colleague', 'visitor') | Default: 'colleague' |
| usually_in | BOOLEAN | Default: true. Pre-selects them each day. Visitors default to false. |
| display_order | INTEGER | For UI ordering |
| is_active | BOOLEAN | Default: true. Soft delete flag. |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### `drink_types`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| team_id | UUID | FK -> teams |
| name | VARCHAR(100) | e.g. "Flat White", "Long Black" |
| display_order | INTEGER | |
| is_active | BOOLEAN | Default: true |

#### `sizes`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| team_id | UUID | FK -> teams |
| name | VARCHAR(50) | e.g. "Small", "Regular", "Large" |
| abbreviation | VARCHAR(10) | e.g. "Sm", "Reg", "Lrg" |
| display_order | INTEGER | |
| is_active | BOOLEAN | Default: true |

#### `milk_options`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| team_id | UUID | FK -> teams |
| name | VARCHAR(50) | e.g. "Full Cream", "Oat", "Almond" |
| display_order | INTEGER | |
| is_active | BOOLEAN | Default: true |

#### `coffee_options`
A colleague's saved coffee preference. Each colleague has 1+ of these.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| colleague_id | UUID | FK -> colleagues |
| drink_type_id | UUID | FK -> drink_types |
| size_id | UUID | FK -> sizes |
| milk_option_id | UUID | FK -> milk_options, nullable (e.g. Long Black has no milk) |
| sugar | INTEGER | Default: 0 |
| notes | VARCHAR(255) | e.g. "extra hot", "double shot" |
| is_default | BOOLEAN | Default: false. Exactly one per colleague must be true. |
| display_order | INTEGER | |
| created_at | TIMESTAMP | |

#### `orders`
Represents a single coffee run (one per day typically).

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| team_id | UUID | FK -> teams |
| share_token | VARCHAR(64) | Unique, for shareable link |
| created_by | UUID | FK -> users |
| created_at | TIMESTAMP | |

#### `order_items`
Individual coffees within an order.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| order_id | UUID | FK -> orders |
| colleague_id | UUID | FK -> colleagues |
| coffee_option_id | UUID | FK -> coffee_options |
| drink_type_name | VARCHAR(100) | Denormalized snapshot |
| size_name | VARCHAR(50) | Denormalized snapshot |
| size_abbreviation | VARCHAR(10) | Denormalized snapshot |
| milk_option_name | VARCHAR(50) | Nullable, denormalized snapshot |
| sugar | INTEGER | Denormalized snapshot |
| notes | VARCHAR(255) | Denormalized snapshot |
| created_at | TIMESTAMP | |

> **Note:** Order items denormalize coffee details at time of order so that history remains accurate even if drink options are later renamed or deleted.

### Default Seed Data

When a new team is created, the following defaults are seeded for that team:

**Drink Types:** Flat White, Long Black, Cappuccino, Latte, Mocha, Espresso, Macchiato, Hot Chocolate, Chai Latte, Piccolo

**Sizes:** Small (Sm), Regular (Reg), Large (Lrg)

**Milk Options:** Full Cream, Skim, Soy, Oat, Almond

---

## API Design

Base URL: `/api/v1`

### Auth
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/login` | Send magic link to email | Public |
| POST | `/auth/verify` | Verify magic link token, set JWT cookie | Public |
| POST | `/auth/logout` | Clear JWT cookie | Member+ |
| GET | `/auth/me` | Get current user info + list of team memberships | Member+ |

### Teams
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/teams` | List teams the current user belongs to | Member+ |
| POST | `/teams` | Create a new team (caller becomes owner) | Member+ |
| GET | `/teams/{team_id}` | Get team details | Member+ |
| PUT | `/teams/{team_id}` | Update team name | Owner |
| DELETE | `/teams/{team_id}` | Soft-delete team | Owner |

### Team Members
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/teams/{team_id}/members` | List team members | Member+ |
| PUT | `/teams/{team_id}/members/{user_id}` | Update member role | Owner/Manager |
| DELETE | `/teams/{team_id}/members/{user_id}` | Remove member from team | Owner/Manager |

### Invites
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/teams/{team_id}/invites` | Send invite email | Owner/Manager |
| GET | `/teams/{team_id}/invites` | List pending invites | Owner/Manager |
| DELETE | `/teams/{team_id}/invites/{invite_id}` | Revoke invite | Owner/Manager |
| POST | `/invites/accept` | Accept an invite by token | Member+ (or auto on login) |

### Colleagues
All colleague routes are scoped under `/teams/{team_id}/`.

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/teams/{team_id}/colleagues` | List all colleagues (and visitors) with coffee options | Member+ |
| POST | `/teams/{team_id}/colleagues` | Create a colleague or visitor | Owner/Manager |
| PUT | `/teams/{team_id}/colleagues/{id}` | Update colleague details | Owner/Manager |
| DELETE | `/teams/{team_id}/colleagues/{id}` | Soft-delete a colleague | Owner/Manager |

### Coffee Options
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/teams/{team_id}/colleagues/{id}/coffee-options` | Add a coffee option | Owner/Manager (or Member for own linked colleague) |
| PUT | `/teams/{team_id}/coffee-options/{id}` | Update a coffee option | Owner/Manager (or Member for own) |
| DELETE | `/teams/{team_id}/coffee-options/{id}` | Delete a coffee option | Owner/Manager (or Member for own) |
| PUT | `/teams/{team_id}/coffee-options/{id}/set-default` | Set as default for that colleague | Owner/Manager (or Member for own) |

### Menu Configuration
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/teams/{team_id}/menu/drink-types` | List drink types | Member+ |
| POST | `/teams/{team_id}/menu/drink-types` | Add drink type | Owner/Manager |
| PUT | `/teams/{team_id}/menu/drink-types/{id}` | Update drink type | Owner/Manager |
| DELETE | `/teams/{team_id}/menu/drink-types/{id}` | Deactivate drink type | Owner/Manager |
| GET | `/teams/{team_id}/menu/sizes` | List sizes | Member+ |
| POST | `/teams/{team_id}/menu/sizes` | Add size | Owner/Manager |
| PUT | `/teams/{team_id}/menu/sizes/{id}` | Update size | Owner/Manager |
| DELETE | `/teams/{team_id}/menu/sizes/{id}` | Deactivate size | Owner/Manager |
| GET | `/teams/{team_id}/menu/milk-options` | List milk options | Member+ |
| POST | `/teams/{team_id}/menu/milk-options` | Add milk option | Owner/Manager |
| PUT | `/teams/{team_id}/menu/milk-options/{id}` | Update milk option | Owner/Manager |
| DELETE | `/teams/{team_id}/menu/milk-options/{id}` | Deactivate milk option | Owner/Manager |

### Orders
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/teams/{team_id}/orders` | Create a new order | Member+ |
| GET | `/teams/{team_id}/orders/{id}` | Get order details + consolidated summary | Member+ |
| PUT | `/teams/{team_id}/orders/{id}` | Update order (add/remove items) | Member+ |
| GET | `/teams/{team_id}/orders` | List past orders (paginated) | Member+ |
| GET | `/orders/share/{share_token}` | Get order by share token | **No auth** |

### Stats
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/teams/{team_id}/stats/overview` | Order frequency, busiest days, total orders | Owner/Manager |
| GET | `/teams/{team_id}/stats/drinks` | Most popular drinks | Owner/Manager |
| GET | `/teams/{team_id}/stats/colleagues` | Per-colleague: frequency, favourite drink | Owner/Manager |

---

## Frontend Pages & UX

### Page Structure

1. **Login Page** (`/login`)
   - Email input + "Send magic link" button.
   - Success state: "Check your email for a login link."

2. **Dashboard / New Order** (`/`) — Primary screen
   - Team-scoped: shows colleagues and visitors for the active team.
   - **Colleagues** section: those with `usually_in = true` are pre-checked.
   - **Visitors** section: shown separately; not pre-checked.
   - Each checked person shows their default coffee option; dropdown to switch if multiple options exist.
   - **Members** can edit their own linked colleague's drink preferences via a pencil icon.
   - **Owners/Managers** can edit any colleague's drink preferences inline.
   - Owners/Managers can add a visitor (name + initial drink) directly from the dashboard.
   - "View Order" button at the bottom with a count badge (e.g. "View Order (6)").
   - If the user has no active team, the NoTeams empty state is shown.

3. **Order Summary** (`/order/{id}`)
   - Consolidated view: grouped by identical drinks (type + size + milk + sugar + notes all match).
   - Format: `{count}x {size_abbreviation} {drink_type}` with milk/sugar/notes shown as needed.
   - Example:
     ```
     2x Lrg Long Black
     1x Reg Oat Flat White
     1x Lrg Cappuccino, 2 sugars
     1x Sm Oat Latte (extra hot)
     ```
   - "Copy to clipboard" button — copies the summary as plain text.
   - "Share link" button — copies a URL like `{domain}/shared/{share_token}`.
   - The shareable link is **live** (always shows current order state, no locking).

4. **Shared Order View** (`/shared/{share_token}`)
   - Public (no auth required). Shows the same consolidated summary.
   - Read-only. Auto-refreshes on an interval (e.g. every 30 seconds) or via polling.
   - Minimal UI — just the order summary, app branding, and a timestamp.

5. **Invite Accept** (`/invite?token=`)
   - Handles team invite links sent via email.
   - If the user is not logged in, stores the token in localStorage and redirects to `/login`. After successful magic link login, the invite is auto-accepted.
   - If the user is already logged in, accepts the invite immediately and redirects to the dashboard.

6. **Create Team** (`/teams/new`)
   - Name input form. On submit, creates the team and switches to it.

7. **Team Settings** (`/teams/:teamId/settings`) — Owner/Manager only
   - **Members** tab: list of all members with roles. Owners can change roles and remove members. Current user shown as "(you)".
   - **Invites** tab: send new invite (email + role + optional colleague pre-link). Lists pending invites with revoke option.
   - **Danger zone**: owner can rename the team or delete it (soft delete).

8. **Manage Colleagues** (`/admin/colleagues`) — Owner/Manager only
   - CRUD list of colleagues and visitors, each marked with a type badge.
   - For each person: name, type, usually_in toggle, and their coffee options.
   - Visitors can be promoted to colleagues.
   - Add/edit coffee options per colleague: select drink type, size, milk, sugar, notes. Set one as default.

9. **Menu Configuration** (`/admin/menu`) — Owner/Manager only
   - Three sections: Drink Types, Sizes (with abbreviations), Milk Options.
   - Add/deactivate items in each category.

10. **Stats** (`/stats`) — Owner/Manager only
    - **Order Frequency**: Total orders, orders per week/month chart, busiest day of week.
    - **Drink Popularity**: Top 10 drinks (as a bar chart or ranked list), trends over time.
    - **Per-Colleague**: Who orders most frequently, each person's most-ordered drink.
    - Date range filter (last 7 days, 30 days, 90 days, all time).

11. **No Teams** (inline state on Dashboard)
    - Shown when the logged-in user has no team memberships.
    - Options to create a new team or wait for an invite.

### UI/UX Principles

- **Mobile-first**: Primary use is on a phone at the cafe. Touch-friendly, large tap targets.
- **Fast daily flow**: The path from opening the app to having a consolidated order should be 2-3 taps maximum (open app -> adjust who's in -> view order).
- **PWA**: Add web app manifest for "add to home screen" capability. No offline/service worker caching required — the app always needs connectivity.
- **Component library**: shadcn/ui with Tailwind CSS. Use the default shadcn theme as a starting point, adjusting the primary color to a warm coffee brown.

---

## Consolidated Order Logic

### Grouping Rules

Two order items are grouped into a single line if and only if ALL of the following match exactly:
- Drink type
- Size
- Milk option (including "none")
- Sugar count
- Notes (case-insensitive string match; empty and null treated as equal)

### Display Format

```
{count}x {size_abbreviation} {drink_type_name}[, {milk}][, {sugar} sugar(s)][, ({notes})]
```

- Milk is omitted if null/none (e.g. Long Black).
- Sugar is omitted if 0.
- Notes are shown in parentheses if present.
- Items are sorted by count descending, then alphabetically.

### Copy-to-Clipboard Format

Same as display format, one line per item, plain text. Example:
```
2x Lrg Long Black
1x Reg Oat Flat White
1x Lrg Cappuccino, 2 sugars
1x Sm Oat Latte (extra hot)
```

---

## PWA Configuration

- `manifest.json` with:
  - `name`: "CoffeeRun"
  - `short_name`: "CoffeeRun"
  - `start_url`: "/"
  - `display`: "standalone"
  - `theme_color`: Coffee brown
  - `background_color`: White
  - Icons at 192x192 and 512x512
- No service worker / no offline caching. The app requires network connectivity.
- `<meta name="apple-mobile-web-app-capable" content="yes">` for iOS support.

---

## Error Tracking (Sentry)

### Frontend
- Initialize `@sentry/react` at app startup.
- Capture unhandled exceptions and unhandled promise rejections.
- Add React Error Boundary integration.
- Set environment tag (`production`, `development`).
- Attach user context (email, role) after login.

### Backend
- Initialize `sentry_sdk` with FastAPI integration.
- Capture all unhandled exceptions in request handlers.
- Set environment and release tags.
- Attach user context to events via middleware.
- Filter out expected errors (e.g. 401, 404) to reduce noise.

---

## Analytics (Vercel)

- Install `@vercel/analytics` package.
- Initialize in the app root component.
- Default page view tracking (automatic with the package).
- No custom events required for v1.

---

## Environment Variables

### Backend (Docker / Dockge)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `sqlite:///./coffeerun.db` | PostgreSQL connection string in production |
| `JWT_SECRET` | Yes | `dev-secret-change-in-production` | Secret key for signing JWTs — **change in production** |
| `FRONTEND_URL` | Yes | `http://localhost:5173` | Frontend URL for CORS and magic link/invite URLs |
| `ADMIN_EMAIL` | No | `admin@example.com` | Email address seeded as the first user on initial deploy |
| `RESEND_API_KEY` | No* | _(empty)_ | API key for Resend email service. *Required in production |
| `EMAIL_FROM` | No | `CoffeeRun <noreply@example.com>` | From address for outgoing emails |
| `SENTRY_DSN` | No | _(empty)_ | Sentry DSN for backend error tracking |
| `ENVIRONMENT` | No | `development` | `production` or `development` |
| `JWT_EXPIRY_DAYS` | No | `7` | JWT token lifetime in days |
| `MAGIC_LINK_EXPIRY_MINUTES` | No | `15` | Magic link expiry in minutes |
| `INVITE_EXPIRY_DAYS` | No | `7` | Team invite token lifetime in days |

### Frontend (Vercel)

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API URL |
| `VITE_SENTRY_DSN` | Sentry DSN for frontend |
| `VITE_ENVIRONMENT` | `production` or `development` |

---

## Project Structure

```
coffeerun/
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── alembic.ini
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, CORS, Sentry init
│   │   ├── config.py            # Settings via pydantic-settings
│   │   ├── database.py          # SQLAlchemy engine, session
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── colleague.py
│   │   │   ├── coffee_option.py
│   │   │   ├── menu.py
│   │   │   └── order.py
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── colleague.py
│   │   │   ├── menu.py
│   │   │   └── order.py
│   │   ├── routers/             # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── colleagues.py
│   │   │   ├── menu.py
│   │   │   ├── orders.py
│   │   │   └── stats.py
│   │   ├── services/            # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── email.py
│   │   │   └── order.py
│   │   └── middleware/
│   │       ├── __init__.py
│   │       └── auth.py
│   ├── requirements.txt
│   ├── Procfile                 # Legacy Railway start command (superseded by compose entrypoint)
│   └── pyproject.toml
├── frontend/
│   ├── public/
│   │   ├── manifest.json
│   │   └── icons/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/                 # API client (fetch wrapper)
│   │   │   └── client.ts
│   │   ├── components/
│   │   │   ├── ui/              # shadcn/ui components
│   │   │   ├── ColleagueCard.tsx
│   │   │   ├── OrderSummary.tsx
│   │   │   ├── CoffeeOptionPicker.tsx
│   │   │   └── Layout.tsx
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── OrderView.tsx
│   │   │   ├── SharedOrder.tsx
│   │   │   ├── AdminColleagues.tsx
│   │   │   ├── AdminMenu.tsx
│   │   │   └── Stats.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useOrder.ts
│   │   ├── context/
│   │   │   └── AuthContext.tsx
│   │   └── lib/
│   │       └── utils.ts
│   ├── index.html
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── package.json
└── SPEC.md
```

---

## Key Technical Decisions

1. **Denormalized order items**: Order history snapshots drink details at time of ordering. This ensures historical accuracy if menu items change.
2. **No cost tracking**: Out of scope for v1. The data model could support it later by adding a `price` column to `coffee_options` and `order_items`.
3. **No locking on live share links**: Changes are always reflected immediately. Simplifies the implementation and matches the small-team, low-contention use case.
4. **Soft-delete for colleagues**: Mark as inactive rather than hard-delete, preserving order history references.
5. **JWT in httpOnly cookies**: More secure than localStorage tokens. CSRF protection via SameSite=Lax + CORS origin checking.
6. **Multi-team with team-scoped data**: Every resource is scoped to a team. Roles are per-team via `TeamMembership`, not global. Users can belong to and switch between multiple teams.

---

## Non-Functional Requirements

- **Performance**: All API responses < 200ms. Frontend initial load < 2s on 4G.
- **Security**: HTTPS only. CORS restricted to frontend domain. JWT httpOnly cookies. Input validation on all endpoints. SQL injection prevention via ORM parameterized queries.
- **Accessibility**: WCAG 2.1 AA compliance. Keyboard navigable. Screen reader friendly labels.
- **Browser Support**: Last 2 versions of Chrome, Safari, Firefox, Edge. iOS Safari 15+.

---

## Future Considerations (Out of Scope for v1)

- Cost tracking and bill splitting
- Slack/Teams bot integration
- Recurring scheduled orders
- Multiple cafe support
- Offline PWA support
- Push notifications ("order is ready")
