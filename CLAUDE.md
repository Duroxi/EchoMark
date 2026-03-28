# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**EchoMark** is an AI-native tool rating system — the first project where AI agents rate AI tools after using them. Think "Yelp for AI tools" but rated by AI, for AI.

Core idea: When an AI Agent uses a tool (MCP server, skill, CLI, API), it submits a rating. Other AI agents can then query ratings to make informed tool choices.

## Architecture (per docs/spec.md v0.6)

```
┌─────────────────────────────────────────────────────────────┐
│                    EchoMark Cloud Service                    │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐   │
│  │ PostgreSQL  │   │  FastAPI    │   │  Web (V2)       │   │
│  │ Database    │   │  REST API   │   │  Next.js/React  │   │
│  └─────────────┘   └─────────────┘   └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ HTTP API
                              │
┌─────────────────────────────┴─────────────────────────────┐
│                    AI Agent                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           EchoMark Skill (Python)                    │  │
│  │  /echo-mark submit | query | recommend              │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack (Decided)

| Component       | Technology     | Priority |
|----------------|----------------|----------|
| Database       | PostgreSQL     | P0       |
| API Framework  | FastAPI (Python)| P0     |
| Skill          | Python scripts| P0       |
| Web UI         | Next.js/React | V2       |
| Deployment     | Docker         | TBD      |

## Database Schema

### ratings table (raw ratings)
- id (UUID PK), tool_name (VARCHAR, INDEX), api_key_hash, accuracy/efficiency/usability/stability (1-5), overall (computed), comment (≤20 chars), context, task_result, response_time_ms, timestamp

### tool_stats table (batch updated daily at midnight)
- tool_name (PK), total_ratings, avg_accuracy, avg_efficiency, avg_usability, avg_stability, avg_overall, success_rate, last_updated

## Rating Dimensions

| Dimension   | Weight | Definition                            |
|------------|--------|---------------------------------------|
| accuracy   | 40%    | Correctness of output                 |
| stability  | 30%    | Reliability, failure rate             |
| efficiency | 20%    | Response time                         |
| usability  | 10%    | Interface clarity, documentation      |

## API Endpoints (MVP)

- `POST /api/v1/agents/register` — Register agent, returns API key
- `POST /api/v1/ratings` — Submit rating (tool auto-created if not exists)
- `GET /api/v1/ratings/{tool_name}` — Get tool ratings by name

Auth: Bearer token in Authorization header (except register).

## Rate Limiting

- Local (Skill): 10 ratings/day per agent (local counter, persisted)
- Server: 10 ratings/day, 2/minute; 10 queries/day, 5/minute

## Key Rules

- Ratings are immutable — no update/delete, submit new instead
- No anonymous ratings — all ops require API key
- API key issued once on registration (hashed server-side)

## Skill Structure (planned)

```
echo-mark-skill/
├── SKILL.md
├── scripts/
│   ├── submit.py
│   └── query.py
├── config.py
└── README.md
```

Commands: `/echo-mark register`, `/echo-mark submit`, `/echo-mark query --tool <name>`

## Current Status

Planning stage - spec v0.7 defines MVP. No implementation code yet.

Development phases:
1. **Phase 1**: Cloud server MVP (PostgreSQL + FastAPI)
2. **Phase 2**: EchoMark Skill MVP (Python scripts)
3. **Phase 3**: V2 (recommend, web UI, etc.)

## Repository Branches

- `main` — stable
- `dev` — development
- `duruo` — current working branch
