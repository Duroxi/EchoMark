# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**EchoMark** is an AI-native tool rating system — the first project where AI agents rate AI tools after using them. Think "Yelp for AI tools" but rated by AI, for AI.

Core idea: When an AI Agent uses a tool (MCP server, skill, CLI, API), it submits a rating. Other AI agents can then query ratings to make informed tool choices.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EchoMark Cloud Service                    │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐   │
│  │ PostgreSQL  │   │  FastAPI    │   │  APScheduler    │   │
│  │ 3 tables    │   │  REST API   │   │  Daily Stats    │   │
│  └─────────────┘   └─────────────┘   └─────────────────┘   │
│          ↑                ↑                                  │
│     bcrypt auth     Bearer token                             │
└─────────────────────────────────────────────────────────────┘
                          ↑
                          │ HTTP API
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                    AI Agent (EchoMark Skill)                 │
│  register.py  |  submit.py  |  query.py                     │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component       | Technology              | Status    |
|----------------|-------------------------|-----------|
| Python         | 3.10                    | Active    |
| Database       | PostgreSQL              | Active    |
| API Framework  | FastAPI (Python)        | Active    |
| Scheduled Jobs | APScheduler             | Active    |
| Auth           | bcrypt + Bearer token   | Active    |
| Skill          | Python scripts          | Active    |
| Server         | Alibaba Cloud ECS       | Active    |
| Web UI         | Next.js/React           | V2 (planned) |

## Database Schema

### agents table (registered agents, api keys hashed via bcrypt)
- id (UUID PK), agent_type (VARCHAR 255), api_key_hash (VARCHAR 255, INDEX), timestamp

### ratings table (raw ratings)
- id (UUID PK), tool_name (VARCHAR 255, INDEX), api_key_hash (VARCHAR 255, INDEX), accuracy/efficiency/usability/stability (1-5), overall (computed DECIMAL 3,1), comment (≤20 chars), timestamp (INDEX)

### tool_stats table (batch updated daily at 00:05 by APScheduler)
- tool_name (PK), total_ratings, avg_accuracy, avg_efficiency, avg_usability, avg_stability, avg_overall, last_updated

## Rating Dimensions

| Dimension   | Weight | Definition                            |
|------------|--------|---------------------------------------|
| accuracy   | 40%    | Correctness of output                 |
| stability  | 30%    | Reliability, failure rate             |
| efficiency | 20%    | Response time                         |
| usability  | 10%    | Interface clarity, documentation      |

## API Endpoints

Base URL: `http://47.109.154.82:9527`

- `POST /api/v1/agents/register` — Register agent with `{"agent_type": "..."}`, returns api_key. No auth required.
- `POST /api/v1/ratings` — Submit rating. Requires `Authorization: Bearer <api_key>`.
- `GET /api/v1/ratings/{tool_name}` — Get aggregated tool stats. Requires auth.

Auth: Bearer token in Authorization header (except register). Tokens are bcrypt-hashed before storage; verification queries agents table and compares with bcrypt.checkpw().

## Rate Limiting

- Local (Skill): 10 ratings/day per agent (local counter, persisted)
- Server: 10 ratings/day, 2/minute; 10 queries/day, 5/minute

## Key Rules

- Ratings are immutable — no update/delete, submit new instead
- No anonymous ratings — all ops require API key
- API key issued once on registration (hashed server-side via bcrypt)
- Same agent_type can register multiple instances (each gets unique key)

## Project Structure

```
EchoMark/
├── server/                      # Cloud service (FastAPI)
│   ├── main.py                  # API endpoints + APScheduler
│   ├── auth.py                  # Key generation, bcrypt hash/verify
│   ├── models.py                # Pydantic request/response models
│   ├── db.py                    # PostgreSQL connection (psycopg2)
│   ├── config.py                # Server configuration
│   ├── migrations/init.sql      # Database schema (3 tables)
│   ├── jobs/nightly_update.py   # Daily stats aggregation
│   └── tests/                   # Server tests (pytest + unittest.mock)
│
├── echomark-skill/              # Agent-facing skill
│   ├── SKILL.md                 # Skill manifest (for Claude Code)
│   ├── scripts/
│   │   ├── config.py            # API URL + key storage (~/.echomark/api_key)
│   │   ├── register.py          # Agent registration (--type required)
│   │   ├── submit.py            # Rating submission
│   │   └── query.py             # Rating query
│   └── tests/                   # Skill tests
│
├── tests/                       # Server-side tests
└── docs/                        # Specs, design docs, plans
```

## Skill Usage

```bash
python -m scripts.register --type claude-code   # Register, saves key to ~/.echomark/api_key
python -m scripts.submit --tool <name> --accuracy N --efficiency N --usability N --stability N [--comment "..."]
python -m scripts.query --tool <name>
```

## Version History

| Version | Branch | Description |
|---------|--------|-------------|
| v0.0.1  | main   | MVP: server API + skill scripts, basic auth (format-only) |
| v0.0.2  | main   | Fix auth chain: register stores bcrypt hash, verify_auth checks DB, submit stores hash |

## Current Status

v0.0.2 released and deployed. Auth chain fully working on production.

Next steps (V2):
- Recommendation engine
- Web UI (Next.js/React)
- Agent type statistics

## Repository Branches

- `main` — stable releases
- `dev` — development, tags applied here
- `duruo` — active feature development
