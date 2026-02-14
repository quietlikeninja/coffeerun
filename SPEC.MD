# CoffeeRun - Product Specification

## Overview

CoffeeRun is a single-team web application for managing daily office coffee orders. An admin manages the colleague list and their coffee preferences. Each morning, a user selects who is in the office, picks each person's coffee (from their pre-configured options), and generates a consolidated order summary to take to the cafe. The app tracks full order history and provides stats on order frequency and drink popularity.

---

## Architecture

| Layer | Technology | Hosting |
|-------|-----------|---------|
| Frontend | React (Vite SPA), Tailwind CSS, shadcn/ui | Vercel |
| Backend | Python, FastAPI | Railway |
| Database | PostgreSQL | Railway |
| ORM | SQLAlchemy + Alembic | — |
| Auth | Email magic links via Resend | — |
| Error Tracking | Sentry (frontend + backend) | — |
| Analytics | Vercel Analytics | — |

### Deployment Topology

- **Frontend**: Vite-built static SPA deployed to Vercel. Includes `@vercel/analytics` and `@sentry/react`.
- **Backend**: FastAPI application deployed to Railway. Exposes a REST API. Includes `sentry-sdk[fastapi]`.
- **Database**: PostgreSQL instance on Railway, connected to the backend via Railway's internal networking.
- **Tenancy**: Single-team. One deployment = one team. No multi-tenancy.

---

## Authentication & Authorization

### Magic Link Auth Flow

1. User enters their email on the login page.
2. Backend generates a short-lived token (15 min expiry), stores a hash of it, and sends a magic link via Resend.
3. User clicks the link, frontend sends the token to the backend.
4. Backend validates the token, issues a JWT (stored in an httpOnly cookie) with a configurable expiry (default: 7 days).
5. Subsequent requests include the JWT cookie. Backend validates on each request.

### Roles

| Role | Capabilities |
|------|-------------|
| **Admin** | Manage colleagues (CRUD), manage coffee options (CRUD), configure colleague defaults, view stats, create orders |
| **Viewer** | Select who's in, pick coffees, generate order summary, view shareable link, view stats |

### Admin Seeding

- The admin email is set via the `ADMIN_EMAIL` environment variable on Railway.
- When that email first logs in, the account is automatically assigned the admin role.
- All other emails that log in are assigned the viewer role.
- Admin can promote other users to admin via the UI.

---

## Data Model

### Tables

#### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| email | VARCHAR(255) | Unique, not null |
| role | ENUM('admin', 'viewer') | Default: 'viewer' |
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

#### `colleagues`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| name | VARCHAR(100) | Not null |
| usually_in | BOOLEAN | Default: true. Pre-selects them each day. |
| display_order | INTEGER | For UI ordering |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### `drink_types`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| name | VARCHAR(100) | e.g. "Flat White", "Long Black" |
| display_order | INTEGER | |
| is_active | BOOLEAN | Default: true |

#### `sizes`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| name | VARCHAR(50) | e.g. "Small", "Regular", "Large" |
| abbreviation | VARCHAR(10) | e.g. "Sm", "Reg", "Lrg" |
| display_order | INTEGER | |
| is_active | BOOLEAN | Default: true |

#### `milk_options`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
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

On first run (via Alembic migration), seed the following:

**Drink Types:** Flat White, Long Black, Cappuccino, Latte, Mocha, Espresso, Macchiato, Hot Chocolate, Chai Latte, Piccolo

**Sizes:** Small (Sm), Regular (Reg), Large (Lrg)

**Milk Options:** Full Cream, Skim, Soy, Oat, Almond

---

## API Design

Base URL: `/api/v1`

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Send magic link to email |
| POST | `/auth/verify` | Verify magic link token, set JWT cookie |
| POST | `/auth/logout` | Clear JWT cookie |
| GET | `/auth/me` | Get current user info |

### Colleagues
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/colleagues` | List all colleagues with their coffee options | Viewer+ |
| POST | `/colleagues` | Create a colleague | Admin |
| PUT | `/colleagues/{id}` | Update colleague details | Admin |
| DELETE | `/colleagues/{id}` | Soft-delete a colleague | Admin |

### Coffee Options
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/colleagues/{id}/coffee-options` | Add a coffee option | Admin |
| PUT | `/coffee-options/{id}` | Update a coffee option | Admin |
| DELETE | `/coffee-options/{id}` | Delete a coffee option | Admin |
| PUT | `/coffee-options/{id}/set-default` | Set as default for that colleague | Admin |

### Menu Configuration
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/menu/drink-types` | List drink types | Viewer+ |
| POST | `/menu/drink-types` | Add drink type | Admin |
| PUT | `/menu/drink-types/{id}` | Update drink type | Admin |
| DELETE | `/menu/drink-types/{id}` | Deactivate drink type | Admin |
| GET | `/menu/sizes` | List sizes | Viewer+ |
| POST | `/menu/sizes` | Add size | Admin |
| PUT | `/menu/sizes/{id}` | Update size | Admin |
| DELETE | `/menu/sizes/{id}` | Deactivate size | Admin |
| GET | `/menu/milk-options` | List milk options | Viewer+ |
| POST | `/menu/milk-options` | Add milk option | Admin |
| PUT | `/menu/milk-options/{id}` | Update milk option | Admin |
| DELETE | `/menu/milk-options/{id}` | Deactivate milk option | Admin |

### Orders
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/orders` | Create a new order | Viewer+ |
| GET | `/orders/{id}` | Get order details + consolidated summary | Viewer+ |
| PUT | `/orders/{id}` | Update order (add/remove items) | Viewer+ |
| GET | `/orders` | List past orders (paginated) | Viewer+ |
| GET | `/orders/share/{share_token}` | Get order by share token | **No auth** |

### Stats
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/stats/overview` | Order frequency, busiest days, total orders | Viewer+ |
| GET | `/stats/drinks` | Most popular drinks, trending | Viewer+ |
| GET | `/stats/colleagues` | Per-colleague: frequency, favourite drink | Viewer+ |

---

## Frontend Pages & UX

### Page Structure

1. **Login Page** (`/login`)
   - Email input + "Send magic link" button.
   - Success state: "Check your email for a login link."

2. **Dashboard / New Order** (`/`) — Primary screen
   - Shows list of all colleagues as cards/checkboxes.
   - Colleagues with `usually_in = true` are pre-checked.
   - Each checked colleague shows their default coffee option.
   - If a colleague has multiple options, show a dropdown to switch.
   - "View Order" button at the bottom with a count badge (e.g. "View Order (6)").

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

5. **Admin: Manage Colleagues** (`/admin/colleagues`)
   - CRUD list of colleagues.
   - For each colleague: name, usually_in toggle, and their coffee options.
   - Add/edit coffee options inline or via a modal: select drink type, size, milk, sugar, notes. Set one as default.

6. **Admin: Menu Configuration** (`/admin/menu`)
   - Three sections: Drink Types, Sizes, Milk Options.
   - Add/edit/deactivate items in each category.
   - Drag-to-reorder or manual order numbers.

7. **Stats** (`/stats`)
   - **Order Frequency**: Total orders, orders per week/month chart, busiest day of week.
   - **Drink Popularity**: Top 10 drinks (as a bar chart or ranked list), trends over time.
   - **Per-Colleague**: Who orders most frequently, each person's most-ordered drink.
   - Date range filter (last 7 days, 30 days, 90 days, all time).

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

### Backend (Railway)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (provided by Railway) |
| `ADMIN_EMAIL` | Email address of the initial admin user |
| `RESEND_API_KEY` | API key for Resend email service |
| `JWT_SECRET` | Secret key for signing JWTs |
| `FRONTEND_URL` | Vercel frontend URL (for CORS and magic link URLs) |
| `SENTRY_DSN` | Sentry DSN for backend |
| `ENVIRONMENT` | `production` or `development` |

### Frontend (Vercel)

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Railway backend URL |
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
│   ├── Procfile                 # Railway deployment
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
6. **Single-team deployment**: No multi-tenancy overhead. Simplifies data model, auth, and authorization.

---

## Non-Functional Requirements

- **Performance**: All API responses < 200ms. Frontend initial load < 2s on 4G.
- **Security**: HTTPS only. CORS restricted to frontend domain. JWT httpOnly cookies. Input validation on all endpoints. SQL injection prevention via ORM parameterized queries.
- **Accessibility**: WCAG 2.1 AA compliance. Keyboard navigable. Screen reader friendly labels.
- **Browser Support**: Last 2 versions of Chrome, Safari, Firefox, Edge. iOS Safari 15+.

---

## Future Considerations (Out of Scope for v1)

- Cost tracking and bill splitting
- Multi-team / multi-tenancy
- Slack/Teams bot integration
- Recurring scheduled orders
- Multiple cafe support
- Offline PWA support
- Push notifications ("order is ready")
