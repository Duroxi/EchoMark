# EchoMark Phase 1: Cloud Server MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the EchoMark cloud server MVP with 3 APIs: agent registration, rating submission, and rating query.

**Architecture:** FastAPI with synchronous psycopg2 for PostgreSQL. APScheduler embedded in FastAPI for nightly stats update job. API Key auth via Bearer token header.

**Tech Stack:** Python 3.10, FastAPI, uvicorn, psycopg2, APScheduler, passlib+bcrypt

---

## File Structure

```
server/
├── main.py              # FastAPI app, routes, APScheduler setup
├── config.py            # Environment variables (DB URL, etc)
├── models.py            # Pydantic models (request/response)
├── db.py                # psycopg2 connection + helpers
├── auth.py              # API Key verification
├── jobs/
│   └── nightly_update.py # Stats update job
├── migrations/
│   └── init.sql         # Database schema SQL
├── requirements.txt
└── Dockerfile
```

---

## Task 1: Project Setup

**Files:**
- Create: `server/requirements.txt`
- Create: `server/Dockerfile`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.109.0
uvicorn==0.27.0
psycopg2-binary==2.9.9
pydantic==2.6.0
apscheduler==3.10.4
passlib==1.7.4
bcrypt==4.1.2
PyYAML==6.0.1
pytest==8.0.0
pytest-asyncio==0.23.4
httpx==0.26.0
```

- [ ] **Step 2: Create Dockerfile**

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Commit**

```bash
git add server/requirements.txt server/Dockerfile
git commit -m "feat: add server requirements and Dockerfile"
```

---

## Task 2: Database Schema

**Files:**
- Create: `server/migrations/init.sql`
- Modify: `server/db.py` (add execute_sql helper)

- [ ] **Step 1: Create migrations/init.sql**

```sql
-- Create ratings table
CREATE TABLE IF NOT EXISTS ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_name VARCHAR(255) NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL,
    accuracy INTEGER NOT NULL CHECK (accuracy >= 1 AND accuracy <= 5),
    efficiency INTEGER NOT NULL CHECK (efficiency >= 1 AND efficiency <= 5),
    usability INTEGER NOT NULL CHECK (usability >= 1 AND usability <= 5),
    stability INTEGER NOT NULL CHECK (stability >= 1 AND stability <= 5),
    overall DECIMAL(3,1) NOT NULL,
    comment VARCHAR(20),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ratings_tool_name ON ratings(tool_name);
CREATE INDEX IF NOT EXISTS idx_ratings_api_key ON ratings(api_key_hash);
CREATE INDEX IF NOT EXISTS idx_ratings_timestamp ON ratings(timestamp);

-- Create tool_stats table
CREATE TABLE IF NOT EXISTS tool_stats (
    tool_name VARCHAR(255) PRIMARY KEY,
    total_ratings INTEGER NOT NULL DEFAULT 0,
    avg_accuracy DECIMAL(3,1) NOT NULL DEFAULT 0,
    avg_efficiency DECIMAL(3,1) NOT NULL DEFAULT 0,
    avg_usability DECIMAL(3,1) NOT NULL DEFAULT 0,
    avg_stability DECIMAL(3,1) NOT NULL DEFAULT 0,
    avg_overall DECIMAL(3,1) NOT NULL DEFAULT 0,
    last_updated TIMESTAMP
);
```

- [ ] **Step 2: Create db.py with connection pool**

```python
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/echomark")

@contextmanager
def get_db():
    """Get database connection from pool."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()

def execute_sql(sql: str, params: tuple = None, fetch_one=False, fetch_all=False):
    """Execute SQL and optionally fetch results."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetch_one:
                return dict(cur.fetchone())
            if fetch_all:
                return [dict(row) for row in cur.fetchall()]
            conn.commit()
            return cur.rowcount
```

- [ ] **Step 3: Test database connection**

Run: `cd server && python -c "from db import get_db; print('DB connection OK')"`
Expected: "DB connection OK" or connection error

- [ ] **Step 4: Commit**

```bash
git add server/migrations/init.sql server/db.py
git commit -m "feat: add database schema and connection helper"
```

---

## Task 3: Config and Models

**Files:**
- Create: `server/config.py`
- Create: `server/models.py`

- [ ] **Step 1: Create config.py**

```python
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/echomark")
LAST_UPDATE_FILE = os.getenv("LAST_UPDATE_FILE", "/opt/echomark/last_update")
API_KEY_LENGTH = 32
API_KEY_PREFIX = "ek_"
```

- [ ] **Step 2: Create models.py with Pydantic models**

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Request models
class RatingSubmit(BaseModel):
    tool_name: str = Field(..., min_length=1, max_length=255)
    accuracy: int = Field(..., ge=1, le=5)
    efficiency: int = Field(..., ge=1, le=5)
    usability: int = Field(..., ge=1, le=5)
    stability: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=20)

class RatingResponse(BaseModel):
    id: str
    success: bool
    message: str

class AgentRegisterResponse(BaseModel):
    api_key: str

class ToolStatsResponse(BaseModel):
    tool_name: str
    stats: dict

class ErrorDetail(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    error: ErrorDetail
```

- [ ] **Step 3: Commit**

```bash
git add server/config.py server/models.py
git commit -m "feat: add config and Pydantic models"
```

---

## Task 4: Auth Module

**Files:**
- Create: `server/auth.py`

- [ ] **Step 1: Create auth.py**

```python
import bcrypt
import secrets
import base64
from config import API_KEY_LENGTH, API_KEY_PREFIX

def generate_api_key() -> str:
    """Generate a new API key: ek_ + 32 char Base64 URL-safe."""
    random_bytes = secrets.token_bytes(24)  # 24 bytes = 32 Base64 chars
    key_body = base64.urlsafe_b64encode(random_bytes).decode()[:API_KEY_LENGTH]
    return f"{API_KEY_PREFIX}{key_body}"

def hash_api_key(api_key: str) -> str:
    """Hash API key using bcrypt."""
    return bcrypt.hashpw(api_key.encode(), bcrypt.gensalt()).decode()

def verify_api_key(api_key: str, api_key_hash: str) -> bool:
    """Verify API key against hash."""
    return bcrypt.checkpw(api_key.encode(), api_key_hash.encode())

def extract_key_from_header(authorization: str) -> str:
    """Extract API key from 'Bearer <key>' header."""
    if not authorization.startswith("Bearer "):
        return None
    return authorization[7:]
```

- [ ] **Step 2: Write test for auth module**

```python
# tests/test_auth.py
from auth import generate_api_key, hash_api_key, verify_api_key, extract_key_from_header

def test_generate_api_key():
    key = generate_api_key()
    assert key.startswith("ek_")
    assert len(key) == 35  # "ek_" + 32 chars

def test_hash_and_verify():
    key = generate_api_key()
    hashed = hash_api_key(key)
    assert verify_api_key(key, hashed)
    assert not verify_api_key("wrong_key", hashed)

def test_extract_key_from_header():
    assert extract_key_from_header("Bearer ek_abc123") == "ek_abc123"
    assert extract_key_from_header("Basic abc") is None
```

- [ ] **Step 3: Run tests**

Run: `cd server && python -m pytest tests/test_auth.py -v`
Expected: 3 tests PASS

- [ ] **Step 4: Commit**

```bash
git add server/auth.py tests/test_auth.py
git commit -m "feat: add API key generation and auth helpers"
```

---

## Task 5: Agent Register Endpoint

**Files:**
- Modify: `server/main.py`

- [ ] **Step 1: Add agent registration endpoint**

```python
from fastapi import FastAPI, HTTPException
from auth import generate_api_key, hash_api_key
from models import AgentRegisterResponse

app = FastAPI()

@app.post("/api/v1/agents/register", response_model=AgentRegisterResponse)
def register_agent():
    """Register a new agent and return API key."""
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)

    # Store hash in database (no lookup needed for MVP)
    execute_sql(
        "INSERT INTO ratings (tool_name, api_key_hash, accuracy, efficiency, usability, stability, overall, comment) VALUES ('__agent__', %s, 0, 0, 0, 0, 0, '__register__')",
        (api_key_hash,)
    )

    return AgentRegisterResponse(api_key=api_key)
```

- [ ] **Step 2: Test endpoint with curl**

Run: `uvicorn main:app --reload` (in background)
Run: `curl -X POST http://localhost:8000/api/v1/agents/register`
Expected: `{"api_key":"ek_..."}`

- [ ] **Step 3: Commit**

```bash
git add server/main.py
git commit -m "feat: add agent registration endpoint"
```

---

## Task 6: Rating Submit Endpoint

**Files:**
- Modify: `server/main.py`

- [ ] **Step 1: Add auth dependency**

```python
from fastapi import Header, HTTPException

async def verify_auth(authorization: str = Header(...)):
    """Verify API key from Authorization header."""
    api_key = extract_key_from_header(authorization)
    if not api_key:
        raise HTTPException(status_code=401, detail={"error": {"code": "UNAUTHORIZED", "message": "Invalid authorization header"}})

    # For MVP, we just verify format. Real verification would check against stored hashes.
    # But we don't store agent hashes for lookup in MVP.
    return api_key
```

- [ ] **Step 2: Add rating submission endpoint**

```python
@app.post("/api/v1/ratings", response_model=RatingResponse)
async def submit_rating(rating: RatingSubmit, authorization: str = Header(...)):
    """Submit a rating for a tool."""
    api_key = verify_auth(authorization)

    # Calculate overall score
    overall = (
        rating.accuracy * 0.40 +
        rating.stability * 0.30 +
        rating.efficiency * 0.20 +
        rating.usability * 0.10
    )
    overall = round(overall, 1)

    result = execute_sql(
        """INSERT INTO ratings (tool_name, api_key_hash, accuracy, efficiency, usability, stability, overall, comment)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING id""",
        (rating.tool_name, api_key, rating.accuracy, rating.efficiency, rating.usability, rating.stability, overall, rating.comment)
    )

    rating_id = result[0]['id']
    return RatingResponse(id=str(rating_id), success=True, message="Rating submitted")
```

- [ ] **Step 3: Test with curl**

Run: `curl -X POST http://localhost:8000/api/v1/ratings \
  -H "Authorization: Bearer ek_test123" \
  -H "Content-Type: application/json" \
  -d '{"tool_name":"tavily","accuracy":5,"efficiency":4,"usability":4,"stability":5,"comment":"快稳准"}'`
Expected: `{"id":"...","success":true,"message":"Rating submitted"}`

- [ ] **Step 4: Commit**

```bash
git add server/main.py
git commit -m "feat: add rating submission endpoint"
```

---

## Task 7: Rating Query Endpoint

**Files:**
- Modify: `server/main.py`

- [ ] **Step 1: Add rating query endpoint**

```python
@app.get("/api/v1/ratings/{tool_name}", response_model=ToolStatsResponse)
async def get_rating(tool_name: str, authorization: str = Header(...)):
    """Get rating stats for a tool."""
    api_key = verify_auth(authorization)

    result = execute_sql(
        """SELECT tool_name, total_ratings, avg_accuracy, avg_efficiency,
                  avg_usability, avg_stability, avg_overall, last_updated
           FROM tool_stats WHERE tool_name = %s""",
        (tool_name,),
        fetch_one=True
    )

    if not result:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": f"No ratings found for tool: {tool_name}"}})

    return ToolStatsResponse(
        tool_name=result['tool_name'],
        stats={
            "total_ratings": result['total_ratings'],
            "avg_overall": float(result['avg_overall']),
            "avg_accuracy": float(result['avg_accuracy']),
            "avg_efficiency": float(result['avg_efficiency']),
            "avg_usability": float(result['avg_usability']),
            "avg_stability": float(result['avg_stability']),
            "last_updated": result['last_updated'].isoformat() if result['last_updated'] else None
        }
    )
```

- [ ] **Step 2: Test with curl (will return 404 since no stats yet)**

Run: `curl http://localhost:8000/api/v1/ratings/tavily -H "Authorization: Bearer ek_test123"`
Expected: `{"error":{"code":"NOT_FOUND","message":"No ratings found for tool: tavily"}}`

- [ ] **Step 3: Commit**

```bash
git add server/main.py
git commit -m "feat: add rating query endpoint"
```

---

## Task 8: Nightly Update Job

**Files:**
- Create: `server/jobs/nightly_update.py`
- Modify: `server/main.py` (add APScheduler)

- [ ] **Step 1: Create nightly_update.py**

```python
import os
from datetime import datetime
from db import execute_sql, get_db

LAST_UPDATE_FILE = os.getenv("LAST_UPDATE_FILE", "/opt/echomark/last_update")

def read_last_update() -> datetime:
    """Read last update timestamp from file."""
    try:
        with open(LAST_UPDATE_FILE, "r") as f:
            content = f.read().strip()
            if content:
                return datetime.fromisoformat(content)
    except (FileNotFoundError, ValueError):
        pass
    # Default to epoch if no file exists
    return datetime(1970, 1, 1)

def write_last_update(dt: datetime):
    """Write current timestamp to file."""
    os.makedirs(os.path.dirname(LAST_UPDATE_FILE), exist_ok=True)
    with open(LAST_UPDATE_FILE, "w") as f:
        f.write(dt.isoformat())

def nightly_update():
    """Update tool_stats with new ratings since last run."""
    last_update = read_last_update()
    now = datetime.now()

    # Get all ratings since last update
    new_ratings = execute_sql(
        """SELECT tool_name, accuracy, efficiency, usability, stability, overall
           FROM ratings WHERE timestamp > %s AND tool_name != '__agent__'""",
        (last_update,),
        fetch_all=True
    )

    if not new_ratings:
        write_last_update(now)
        return

    # Group by tool
    tools = {}
    for r in new_ratings:
        tool = r['tool_name']
        if tool not in tools:
            tools[tool] = []
        tools[tool].append(r)

    # Update each tool's stats
    for tool_name, ratings in tools.items():
        # Get existing stats
        existing = execute_sql(
            "SELECT * FROM tool_stats WHERE tool_name = %s",
            (tool_name,),
            fetch_one=True
        )

        if existing:
            # Incremental update
            old_total = existing['total_ratings']
            new_count = len(ratings)
            new_total = old_total + new_count

            # Calculate new averages
            new_acc = sum(r['accuracy'] for r in ratings) / new_count
            new_eff = sum(r['efficiency'] for r in ratings) / new_count
            new_usa = sum(r['usability'] for r in ratings) / new_count
            new_sta = sum(r['stability'] for r in ratings) / new_count
            new_ovl = sum(r['overall'] for r in ratings) / new_count

            # Weighted merge
            avg_accuracy = round((existing['avg_accuracy'] * old_total + new_acc * new_count) / new_total, 1)
            avg_efficiency = round((existing['avg_efficiency'] * old_total + new_eff * new_count) / new_total, 1)
            avg_usability = round((existing['avg_usability'] * old_total + new_usa * new_count) / new_total, 1)
            avg_stability = round((existing['avg_stability'] * old_total + new_sta * new_count) / new_total, 1)
            avg_overall = round((existing['avg_overall'] * old_total + new_ovl * new_count) / new_total, 1)

            execute_sql(
                """UPDATE tool_stats SET
                   total_ratings = %s, avg_accuracy = %s, avg_efficiency = %s,
                   avg_usability = %s, avg_stability = %s, avg_overall = %s, last_updated = %s
                   WHERE tool_name = %s""",
                (new_total, avg_accuracy, avg_efficiency, avg_usability, avg_stability, avg_overall, now, tool_name)
            )
        else:
            # New tool - calculate from scratch
            count = len(ratings)
            avg_accuracy = round(sum(r['accuracy'] for r in ratings) / count, 1)
            avg_efficiency = round(sum(r['efficiency'] for r in ratings) / count, 1)
            avg_usability = round(sum(r['usability'] for r in ratings) / count, 1)
            avg_stability = round(sum(r['stability'] for r in ratings) / count, 1)
            avg_overall = round(sum(r['overall'] for r in ratings) / count, 1)

            execute_sql(
                """INSERT INTO tool_stats (tool_name, total_ratings, avg_accuracy, avg_efficiency,
                   avg_usability, avg_stability, avg_overall, last_updated)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (tool_name, count, avg_accuracy, avg_efficiency, avg_usability, avg_stability, avg_overall, now)
            )

    write_last_update(now)
    print(f"Nightly update complete: processed {len(new_ratings)} ratings for {len(tools)} tools")
```

- [ ] **Step 2: Integrate APScheduler in main.py**

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from jobs.nightly_update import nightly_update

scheduler = AsyncIOScheduler()
scheduler.add_job(nightly_update, 'cron', hour=0, minute=5)

@app.on_event("startup")
async def startup():
    scheduler.start()

@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()
```

- [ ] **Step 3: Test nightly update manually**

Run: `cd server && python -c "from jobs.nightly_update import nightly_update; nightly_update(); print('Done')"`
Expected: "Nightly update complete..."

- [ ] **Step 4: Commit**

```bash
git add server/jobs/nightly_update.py server/main.py
git commit -m "feat: add nightly stats update job with APScheduler"
```

---

## Task 9: Error Handling and Validation

**Files:**
- Modify: `server/main.py`

- [ ] **Step 1: Add exception handlers**

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": str(exc)}}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "UNAUTHORIZED" if exc.status_code == 401 else "ERROR", "message": exc.detail}}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}
    )
```

- [ ] **Step 2: Test 422 error**

Run: `curl -X POST http://localhost:8000/api/v1/ratings \
  -H "Authorization: Bearer ek_test" \
  -H "Content-Type: application/json" \
  -d '{"tool_name":"test","accuracy":6}'`  # 6 is invalid (should be 1-5)
Expected: `{"error":{"code":"VALIDATION_ERROR",...}}`

- [ ] **Step 3: Commit**

```bash
git add server/main.py
git commit -m "feat: add error handlers"
```

---

## Task 10: Integration Test

**Files:**
- Create: `tests/test_api.py`

- [ ] **Step 1: Write integration test**

```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_full_flow():
    # Register
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/v1/agents/register")
        assert resp.status_code == 200
        api_key = resp.json()["api_key"]

        # Submit rating
        resp = await client.post(
            "/api/v1/ratings",
            json={
                "tool_name": "test-tool",
                "accuracy": 5,
                "efficiency": 4,
                "usability": 4,
                "stability": 5,
                "comment": "好用"
            },
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert resp.status_code == 200

        # Query (will be empty since no nightly update yet)
        resp = await client.get(
            "/api/v1/ratings/test-tool",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert resp.status_code == 404  # No stats yet
```

- [ ] **Step 2: Run integration test**

Run: `cd server && python -m pytest tests/test_api.py -v`
Expected: 1 test PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_api.py
git commit -m "test: add integration test for full API flow"
```

---

## Self-Review Checklist

1. **Spec coverage:**
   - ✅ POST /api/v1/agents/register - Task 5
   - ✅ POST /api/v1/ratings - Task 6
   - ✅ GET /api/v1/ratings/{tool_name} - Task 7
   - ✅ API Key generation with ek_ prefix - Task 4
   - ✅ Bearer token auth - Task 6
   - ✅ Error response format - Task 9
   - ✅ Nightly update job - Task 8
   - ✅ Database schema with ratings + tool_stats - Task 2
   - ✅ Weighted overall calculation - Task 6

2. **Placeholder scan:** No TBD/TODO found. All code is complete.

3. **Type consistency:** All function signatures and field names match the spec.

---

**Plan complete.** Save to `docs/superpowers/plans/2026-03-29-echomark-phase1-server.md`.
