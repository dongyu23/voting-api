# Voting API

A lightweight, multi-user voting API service built with FastAPI and SQLite. Create polls, cast votes, and view real-time results — with JWT authentication and one-person-one-vote enforcement at both the application and database levels.

## Features

- **Poll management** — Create, edit, and delete polls with multiple options and UTC expiry times
- **Vote casting** — One vote per user per poll, enforced by DB unique constraint + app-level check
- **Real-time results** — Per-option vote counts with percentages, queryable at any time
- **JWT authentication** — Register/login with password hashing, 24h token expiry, swappable auth hooks
- **Multi-tab ready** — Frontend uses `sessionStorage` so each browser tab can log in a different user
- **Concurrent-safe** — SQLite WAL mode + `busy_timeout` for write contention, UTC timestamps throughout
- **Docker ready** — Single-command deployment with Docker Compose

## Quick Start

### Prerequisites

- Python 3.11+ or Docker

### Local run

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --port 8000
```

Open `http://localhost:8000` — the frontend test page is served by FastAPI.

### Docker

```bash
docker compose up --build
```

The app starts on port 8000. SQLite data is persisted via the `backend/data` volume.

## API Reference

All endpoints return a unified response: `{"code": 200, "message": "success", "data": {...}}`.

### Auth

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | No | Create a user |
| POST | `/api/v1/auth/login` | No | Get JWT token |

### Polls

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/polls` | Yes | List all polls (discovery pool) |
| GET | `/api/v1/polls/mine` | Yes | List my created polls |
| POST | `/api/v1/polls` | Yes | Create a poll with options and expiry |
| GET | `/api/v1/polls/{id}` | Yes | Poll detail with options |
| PUT | `/api/v1/polls/{id}` | Yes | Edit poll (creator only) |
| DELETE | `/api/v1/polls/{id}` | Yes | Delete poll (creator only) |
| POST | `/api/v1/polls/{id}/vote` | Yes | Cast a vote |
| GET | `/api/v1/polls/{id}/results` | Yes | View results |

### Health

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | No | Health check |

### Business error codes

| Range | Meaning |
|-------|---------|
| 1001 | Authentication error / invalid token |
| 1002 | Username already taken |
| 2001 | Poll has expired |
| 2002 | Already voted |
| 2003 | Invalid option |
| 2004 | Poll not found |
| 2005 | Not the poll creator |

## Project Structure

```
demo/
├── CLAUDE.md                  # Project specification (SDD)
├── README.md
├── docker-compose.yml
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── config.py              # Env-based configuration
│   ├── database.py            # SQLite + WAL pragma setup
│   ├── models.py              # SQLAlchemy ORM (User, Poll, Option, Vote)
│   ├── schemas.py             # Pydantic request/response models
│   ├── auth.py                # JWT + bcrypt helpers, get_current_user dependency
│   ├── main.py                # FastAPI app entry, CORS, static frontend mount
│   ├── routers/
│   │   ├── auth.py            # /api/v1/auth/*
│   │   └── polls.py           # /api/v1/polls/*
│   ├── services/
│   │   ├── auth.py            # Register/login logic
│   │   └── polls.py           # Poll CRUD, voting, results
│   └── data/                  # SQLite DB files (gitignored)
└── frontend/
    └── index.html             # Test console (pure HTML/JS)
```

## Architecture Decisions

### SQLite WAL mode

Write-Ahead Logging allows concurrent reads during writes — readers don't block writers. Combined with `busy_timeout=5000ms`, write contention under 20+ concurrent votes is handled gracefully without upgrading to PostgreSQL.

### UTC everywhere

All timestamps are stored and compared in ISO 8601 UTC. The frontend converts local time to UTC on input, and the browser converts UTC back to local on display. This avoids timezone drift between Docker containers and host machines.

### One-person-one-vote: two layers

1. **Application layer** — explicit `SELECT` before `INSERT` in the service, returns a friendly error
2. **Database layer** — `UNIQUE(poll_id, user_id)` constraint on the `votes` table, last-resort guard against race conditions

### Layered backend

```
Router (param validation, HTTP concerns)
  → Service (business logic, cross-module calls)
    → Model (SQLAlchemy ORM, no business logic)
```

ORMs are never returned directly to clients — Pydantic schemas sit between the DB and the HTTP response.

## Multi-User Testing

Open `http://localhost:8000` in multiple browser tabs. Each tab stores its JWT in `sessionStorage`, so multiple users can log in and interact simultaneously from the same browser.

Pre-registered test accounts: `alice`, `bob`, `charlie` (password: `pass123` for all).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+ / FastAPI / SQLAlchemy |
| Database | SQLite (WAL mode) |
| Auth | python-jose (JWT) / bcrypt |
| Frontend | Vanilla HTML/CSS/JS |
| Deploy | Docker Compose |

## License

MIT
