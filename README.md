# Smart Home Controller

Full-stack learning project: a React + TypeScript + Tailwind dashboard backed by a
Python FastAPI service. **This is a software simulation only** — it does not control
physical devices.

---

## Architecture

### Backend (`backend/`)

| Module | Responsibility |
| ------ | -------------- |
| `interfaces.py` | `SmartDevice`, generic `Repository` and `EventPublisher` contracts (ABCs) |
| `domain.py` | Entities, enums and invariants: `Device`, `EnergyMeter`, `Room`, `Schedule`, `AutomationRule`, `ActivityEvent`, `Notification` |
| `devices.py` | `Light`, `Fan`, `AC` + backward-compatible in-memory registry |
| `controller.py` | `control_device()` — polymorphism through `SmartDevice` |
| `exceptions.py` | `SmartHomeError` hierarchy with HTTP status/code policy |
| `repositories.py` | Thread-safe in-memory repository (immutable snapshots) |
| `persistence.py` | Optional SQLite repository behind the same contract (stdlib only) |
| `events.py` | Event broker with topic subscriptions and an event log |
| `services.py` | Use-case layer: devices, rooms, schedules, rules, energy, activity, notifications |
| `container.py` | Composition root / dependency injection wiring |
| `scheduler.py` | Background thread applying due schedules |
| `realtime.py` | WebSocket connection manager and event fan-out |
| `schemas.py` | Pydantic request/response validation |
| `main.py` | HTTP boundary: routes, CORS, error handling, lifespan, `/ws` |
| `logging_config.py` | Central logging setup (`LOG_LEVEL`) |

Layers are one-way: `main` → `services` → `interfaces`/`domain`. Concrete storage is
chosen only in `container`, so services and routes depend on abstractions. State
changes are written back through the repository and published as domain events;
activity history, notifications, automations and WebSocket clients subscribe to
those events.

### Frontend (`src/`)

`App.tsx` owns the tab layout and a reconnecting WebSocket client. `api/` contains a
typed REST client, `hooks/useFetch.ts` handles loading/error/stale responses,
`views/` implements each feature, and `components/` holds the shared presentational
components. `config/api.ts` derives all REST and WS URLs from `VITE_API_BASE_URL`.

---

## Features

- **Devices** — on/off control, live online/offline status, per-device energy reading
- **Rooms** — create/edit/delete rooms and reassign devices
- **Schedules** — time + weekday based actions, enable/pause, run-due-now
- **Automation rules** — when a device reaches a state, act on another device
- **Energy monitoring** — watt-hours accumulated while devices are on
- **Activity history** — state, connectivity, schedule and automation events
- **Notifications** — inbox with unread count, mark-read, delete, clear
- **Real-time updates** — `/ws` broadcasts domain events to the dashboard

The original endpoints and response shapes are unchanged; every new capability is
additive.

---

## REST API

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/` | Health check |
| GET | `/devices` | All devices (`{devices: [{id, name, status}]}`) |
| POST | `/devices/{id}/on` · `/devices/{id}/off` | Set power |
| GET | `/devices/{id}/status` | Full detail: status, online, room, wattage, energy |
| POST | `/devices/{id}/online` · `/devices/{id}/offline` | Set connectivity |
| PUT | `/devices/{id}/room` | Assign/unassign room (`{"room_id": null}`) |
| GET | `/devices/{id}/activity` | Activity for one device |
| GET/POST | `/rooms` | List / create rooms |
| GET/PUT/DELETE | `/rooms/{id}` | Read / update / delete room |
| GET | `/rooms/{id}/devices` | Devices in a room |
| GET/POST | `/schedules` | List / create schedules |
| GET/PUT/DELETE | `/schedules/{id}` | Read / update / delete schedule |
| POST | `/schedules/{id}/toggle` | Enable/pause a schedule |
| POST | `/schedules/run-now` | Apply any due schedules now |
| GET/POST | `/rules` | List / create automation rules |
| GET/PUT/DELETE | `/rules/{id}` | Read / update / delete rule |
| GET | `/energy` · `/energy/{id}` | Energy summary / single reading |
| GET | `/activity?device_id=&limit=` | Activity history (newest first) |
| GET | `/notifications` | Inbox + `unread_count` |
| POST | `/notifications/{id}/read` | Mark as read |
| DELETE | `/notifications/{id}` · `/notifications` | Delete one / clear all |
| WS | `/ws` | Real-time event feed |

Validation errors return FastAPI's standard `422`; domain errors return
`{"detail": "...", "code": "..."}` with the matching HTTP status. Interactive docs
are at `/docs`.

---

## Run locally

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate              # Windows
# source .venv/bin/activate         # macOS/Linux
pip install -r requirements-dev.txt
uvicorn backend.main:app --reload --port 8000
```

Render-style startup from inside `backend/`:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port $PORT
```

The backend reads environment variables with `os.getenv`; it does not load `.env`
automatically. `backend/.env.example` is a tracked reference only.

### Frontend

```bash
copy .env.example .env.local        # Windows — local backend URL
# cp .env.example .env.local        # macOS/Linux
npm install
npm run dev
```

`VITE_API_BASE_URL` must be set before starting or building the frontend.

---

## Environment variables

| Variable | Used by | Purpose |
| -------- | ------- | ------- |
| `VITE_API_BASE_URL` | Frontend | Backend base URL, embedded at build time |
| `FRONTEND_ORIGIN` | Backend | Allowed Vercel origin for CORS (localhost origins stay allowed) |
| `BACKEND_CORS_ORIGINS` | Backend | Optional extra comma-separated origins |
| `LOG_LEVEL` | Backend | Optional logging level, default `INFO` |
| `SMART_HOME_DB_PATH` | Backend | Optional SQLite file; unset means in-memory state |

No secrets or credentials are stored in this repository. Set hosting variables in
the Vercel and Render dashboards.

---

## Persistence

By default all state is in memory and resets on restart. Set `SMART_HOME_DB_PATH`
to a writable file path to store devices, rooms, schedules, rules, activity and
notifications in SQLite using only the standard library. The same `Repository`
interface serves both backends, so no service or route changes are required.

Keep a single backend instance for this learning project: the in-memory store is
per-process and the bundled scheduler runs once per process.

---

## Tests and checks

```bash
python -m pytest backend/tests -q    # 61 tests
python -m backend.demo               # polymorphism demo
npm run build                        # TypeScript + production build
npm run lint                         # Oxlint
```

Coverage includes OOP contracts and polymorphism, domain validation, repository
thread safety and persistence, all REST endpoints, original contract compatibility,
event-driven automation, schedules, error shapes, query bounds, WebSocket broadcast
and SQLite round-trips.

---

## Deployment

### Render (Python API)

`render.yaml` defines the service: root directory `backend`, build
`pip install -r requirements.txt`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`,
health check `/`, `PYTHON_VERSION=3.13`, and `FRONTEND_ORIGIN` set to the Vercel
domain. Add `LOG_LEVEL` or `SMART_HOME_DB_PATH` only if needed. Deploy branch `main`
must contain the `backend/` folder.

### Vercel (React frontend)

Framework preset **Vite**, root directory repository root, build `npm run build`,
output `dist`. Add `VITE_API_BASE_URL` pointing at the Render service and redeploy
after changing it (Vite embeds it at build time). The backend's `FRONTEND_ORIGIN`
must match the Vercel domain exactly. `ws://`/`wss://` for the live feed is derived
from `VITE_API_BASE_URL` automatically.

---

## PostgreSQL database

### Tables

| Table | Purpose | Key relationships |
| ----- | ------- | ----------------- |
| `users` | Owners of all data | One-to-many to rooms, devices, schedules, automations, history, notifications |
| `rooms` | Rooms with stable IDs (`living-room`, `bedroom`) | Belongs to a user; has many devices; many-to-many with users via `room_members` |
| `room_members` | Shared room access | Composite PK `(user_id, room_id)` |
| `devices` | Device state (stable IDs `light`/`fan`/`ac`, type, status, online, wattage) | Belongs to user and optional room; child history/energy/schedules/rules |
| `device_history` | Append-only state/connectivity audit | Device FK, optional actor user FK, source check |
| `energy_logs` | One row per ON interval | Device FK; `measurement_source = 'estimated'` enforced by CHECK |
| `schedules` / `schedule_days` | Time + weekday rules | Device/user FKs; days child table with `0..6` CHECK |
| `automations` | Trigger → target rules | Two separate FKs to `devices`, plus owner FK |
| `notifications` | Event inbox | User FK, level CHECK |

ORM models live in `backend/models.py`; repositories in `backend/db_repositories.py`
translate rows to the existing domain dataclasses. Domain, controllers, services
signatures and API response shapes are preserved.

### Migration procedure

From `backend/`, with `DATABASE_URL` exported in the shell:

```bash
alembic upgrade head      # applies 0001_initial_schema (CREATE TABLE only)
alembic check             # verifies models match the migrated schema
```

The app never runs migrations at startup. The initial revision creates tables and
inserts no data. To load the demo user, rooms and devices explicitly:

```bash
# only after reviewing the target database
set SEED_DEMO_DATA=true   # Windows; export on macOS/Linux
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Leave `DATABASE_URL` unset to keep the original in-memory behaviour. Revision
`0002_sensor_timezone_rules` adds simulated temperature input, IANA schedule
timezones and temperature-threshold automation columns; it is additive and does
not remove or rewrite existing rows.

### Sensor honesty and richer automation

Temperature values are user-supplied **simulated inputs** (`PUT
/devices/{id}/temperature`), stored with `temperature_source = 'simulated'`. Rules
can use `device_state`, `temperature_above` or `temperature_below` triggers; a
temperature rule requires `threshold_c` and is validated before reaching the
database. Schedules accept an IANA `timezone` (for example
`America/New_York`) and due checks are evaluated in that local time, including
daylight-saving transitions.

`GET /energy/stats` returns estimated interval count, average and peak device;
all values remain clearly labelled estimates.

### Energy data honesty

Energy values are **estimates** calculated as `rated watts × on-time / 3600`. They
are not sensor measurements. `/energy/logs` returns `measurement_source: "estimated"`
and an explicit note; the database CHECK constraint forbids any other source.

### Render + hosted PostgreSQL

A local PostgreSQL instance is not reachable from Render. For production you must
provision a hosted PostgreSQL database (e.g. Render Postgres or another managed
provider) and set `DATABASE_URL` as a Render dashboard environment variable. The
blueprint declares the variable with `sync: false`, so no credential is stored in
Git. Apply `alembic upgrade head` as a deliberate release step after reviewing the
target database. Set `APP_ENV=production` so localhost origins are excluded from
CORS; keep `FRONTEND_ORIGIN` equal to the Vercel domain.
