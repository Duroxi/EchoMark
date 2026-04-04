# v0.0.2 认证链路修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复认证链路断裂 — 注册时存储 API Key 哈希到 DB，验证时查 DB 校验，提交评分时存哈希而非明文。

**Architecture:** 新增 `agents` 表存储注册信息（agent_type + api_key_hash）。注册接口改为接受 `agent_type` 参数。`verify_auth()` 从"仅检查格式"改为"查询 DB + bcrypt 验证"。所有错误响应格式统一。

**Tech Stack:** Python 3.10, FastAPI, PostgreSQL (psycopg2), bcrypt

---

## File Map

| File | Responsibility | Action |
|------|---------------|--------|
| `server/migrations/init.sql` | DB schema | Add agents table |
| `server/models.py` | Pydantic models | Add AgentRegisterRequest, update AgentRegisterResponse |
| `server/main.py` | API endpoints + error handlers | Fix handlers, register, verify_auth, submit, get |
| `server/auth.py` | Key generation + bcrypt | No change (already has hash/verify functions) |
| `server/db.py` | DB connection | No change |
| `echomark-skill/scripts/register.py` | Client-side register | Add --type argument |
| `tests/test_models.py` | Model validation tests | Update + add new tests |
| `tests/test_api.py` | API endpoint tests | Update all tests for new interfaces |
| `echomark-skill/tests/test_skill.py` | Skill integration tests | Update register tests |
| `echomark-skill/tests/test_cli.py` | CLI argument tests | Update register CLI tests |

---

### Task 1: Database Schema — 新增 agents 表

**Files:**
- Modify: `server/migrations/init.sql`

- [ ] **Step 1: Add agents table to init.sql**

在 `server/migrations/init.sql` 末尾追加：

```sql

-- Create agents table
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type VARCHAR(255) NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Create index for fast auth lookup
CREATE INDEX IF NOT EXISTS idx_agents_api_key_hash ON agents(api_key_hash);
```

- [ ] **Step 2: Verify SQL syntax**

Run: `python -c "print('SQL ready for manual execution on PostgreSQL')"`
Expected: SQL file updated with agents table definition.

---

### Task 2: Pydantic Models — 新增请求模型，更新响应模型

**Files:**
- Modify: `server/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write failing test for AgentRegisterRequest**

在 `tests/test_models.py` 中 import 添加 `AgentRegisterRequest`，新增测试类：

```python
from models import (
    RatingSubmit, RatingResponse, AgentRegisterResponse, AgentRegisterRequest,
    ToolStatsResponse, ErrorDetail, ErrorResponse
)


class TestAgentRegisterRequest:
    """AgentRegisterRequest 验证测试"""

    def test_valid_request(self):
        req = AgentRegisterRequest(agent_type="claude-code")
        assert req.agent_type == "claude-code"

    def test_agent_type_required(self):
        with pytest.raises(ValidationError):
            AgentRegisterRequest()

    def test_agent_type_min_length(self):
        with pytest.raises(ValidationError):
            AgentRegisterRequest(agent_type="")

    def test_agent_type_max_length(self):
        with pytest.raises(ValidationError):
            AgentRegisterRequest(agent_type="x" * 256)
```

同时更新 `TestAgentRegisterResponse`：

```python
class TestAgentRegisterResponse:
    """AgentRegisterResponse 测试"""

    def test_valid_response(self):
        resp = AgentRegisterResponse(api_key="ek_test123", agent_type="claude-code")
        assert resp.api_key == "ek_test123"
        assert resp.agent_type == "claude-code"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /c/Users/hhhhh/Desktop/EchoMark && python -m pytest tests/test_models.py -v`
Expected: FAIL — `ImportError: cannot import name 'AgentRegisterRequest'`

- [ ] **Step 3: Implement models**

在 `server/models.py` 中，`RatingSubmit` 类之前添加 `AgentRegisterRequest`，并更新 `AgentRegisterResponse`：

```python
class AgentRegisterRequest(BaseModel):
    agent_type: str = Field(..., min_length=1, max_length=255)

class AgentRegisterResponse(BaseModel):
    api_key: str
    agent_type: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /c/Users/hhhhh/Desktop/EchoMark && python -m pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/models.py tests/test_models.py
git commit -m "feat: add AgentRegisterRequest model, update AgentRegisterResponse with agent_type"
```

---

### Task 3: Error Handlers — 修复错误响应格式

**Files:**
- Modify: `server/main.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write failing test for fixed 404 handler**

在 `tests/test_api.py` 中更新 `test_http_exception_handler`：

```python
@pytest.mark.asyncio
async def test_http_exception_handler():
    """Test HTTP exception handler maps status codes to error codes."""
    mock_request = MagicMock()

    # Test 401
    exc_401 = HTTPException(status_code=401, detail="Invalid API key")
    response = await http_exception_handler(mock_request, exc_401)

    assert response.status_code == 401
    import json
    body = json.loads(response.body)
    assert body['error']['code'] == 'UNAUTHORIZED'
    assert isinstance(body['error']['message'], str)

    # Test 404
    exc_404 = HTTPException(status_code=404, detail="No ratings found for tool: unknown")
    response = await http_exception_handler(mock_request, exc_404)

    assert response.status_code == 404
    body = json.loads(response.body)
    assert body['error']['code'] == 'NOT_FOUND'
    assert body['error']['message'] == "No ratings found for tool: unknown"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /c/Users/hhhhh/Desktop/EchoMark && python -m pytest tests/test_api.py::test_http_exception_handler -v`
Expected: FAIL — 404 的 code 是 "ERROR" 而非 "NOT_FOUND"

- [ ] **Step 3: Implement fix**

替换 `server/main.py` 中的 `http_exception_handler`：

```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    code_map = {401: "UNAUTHORIZED", 404: "NOT_FOUND"}
    code = code_map.get(exc.status_code, "ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": str(exc.detail)}}
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /c/Users/hhhhh/Desktop/EchoMark && python -m pytest tests/test_api.py::test_http_exception_handler -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/main.py tests/test_api.py
git commit -m "fix: error handler maps 404 to NOT_FOUND, ensures message is string"
```

---

### Task 4: Register Endpoint — 接受 agent_type，存储哈希

**Files:**
- Modify: `server/main.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write failing test for new register behavior**

更新 `tests/test_api.py` 中的注册测试：

```python
@pytest.mark.asyncio
async def test_register_agent_success(mock_db):
    """Test agent registration with agent_type stores hash in DB."""
    mock_db.return_value = {'id': 'test-uuid'}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/agents/register", json={"agent_type": "claude-code"})

    assert resp.status_code == 200
    data = resp.json()
    assert 'api_key' in data
    assert data['agent_type'] == 'claude-code'
    assert data['api_key'].startswith('ek_')


@pytest.mark.asyncio
async def test_register_agent_returns_35_chars(mock_db):
    """Test API Key is 35 characters long."""
    mock_db.return_value = {'id': 'test-uuid'}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/agents/register", json={"agent_type": "claude-code"})

    assert resp.status_code == 200
    data = resp.json()
    assert len(data['api_key']) == 35


@pytest.mark.asyncio
async def test_register_agent_requires_body(mock_db):
    """Test registration without body returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/agents/register")

    assert resp.status_code == 422
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /c/Users/hhhhh/Desktop/EchoMark && python -m pytest tests/test_api.py::test_register_agent_success tests/test_api.py::test_register_agent_returns_35_chars tests/test_api.py::test_register_agent_requires_body -v`
Expected: FAIL — POST 无 body 仍然返回 200（旧行为）

- [ ] **Step 3: Implement register endpoint**

更新 `server/main.py` 中的 import 和 `register_agent`：

import 行改为：
```python
from auth import generate_api_key, hash_api_key, verify_api_key, extract_key_from_header
from models import AgentRegisterRequest, AgentRegisterResponse, RatingSubmit, RatingResponse, ToolStatsResponse
```

register_agent 改为：
```python
@app.post("/api/v1/agents/register", response_model=AgentRegisterResponse)
def register_agent(req: AgentRegisterRequest):
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    execute_sql(
        "INSERT INTO agents (agent_type, api_key_hash) VALUES (%s, %s) RETURNING id",
        (req.agent_type, key_hash),
        fetch_one=True
    )
    return AgentRegisterResponse(api_key=api_key, agent_type=req.agent_type)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /c/Users/hhhhh/Desktop/EchoMark && python -m pytest tests/test_api.py -k "register" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/main.py tests/test_api.py
git commit -m "feat: register endpoint accepts agent_type, stores API key hash in agents table"
```

---

### Task 5: Auth Verification — verify_auth 接入 DB 验证

**Files:**
- Modify: `server/main.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write failing test for real auth verification**

在 `tests/test_api.py` 中添加：

```python
@pytest.mark.asyncio
async def test_verify_auth_valid_key(mock_db):
    """Test verify_auth returns (hash, agent_type) for valid key."""
    from auth import generate_api_key, hash_api_key
    test_key = "ek_testkey1234567890abcdefghijklmnop"
    test_hash = hash_api_key(test_key)

    mock_db.return_value = [{'api_key_hash': test_hash, 'agent_type': 'claude-code'}]

    from main import verify_auth
    result = await verify_auth(f"Bearer {test_key}")

    assert result[0] == test_hash
    assert result[1] == 'claude-code'


@pytest.mark.asyncio
async def test_verify_auth_invalid_key(mock_db):
    """Test verify_auth raises 401 for invalid key."""
    from auth import hash_api_key
    test_hash = hash_api_key("ek_correct_key")

    mock_db.return_value = [{'api_key_hash': test_hash, 'agent_type': 'claude-code'}]

    from main import verify_auth
    with pytest.raises(HTTPException) as exc_info:
        await verify_auth("Bearer ek_wrong_key")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_verify_auth_no_agents(mock_db):
    """Test verify_auth raises 401 when no agents registered."""
    mock_db.return_value = []

    from main import verify_auth
    with pytest.raises(HTTPException) as exc_info:
        await verify_auth("Bearer ek_any_key")

    assert exc_info.value.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /c/Users/hhhhh/Desktop/EchoMark && python -m pytest tests/test_api.py -k "verify_auth" -v`
Expected: FAIL — verify_auth 目前返回字符串，不返回 tuple

- [ ] **Step 3: Implement verify_auth**

替换 `server/main.py` 中的 `verify_auth`：

```python
async def verify_auth(authorization: str = Header(...)):
    api_key = extract_key_from_header(authorization)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    agents = execute_sql(
        "SELECT api_key_hash, agent_type FROM agents",
        fetch_all=True
    )

    for agent in agents:
        if verify_api_key(api_key, agent['api_key_hash']):
            return agent['api_key_hash'], agent['agent_type']

    raise HTTPException(status_code=401, detail="Invalid API key")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /c/Users/hhhhh/Desktop/EchoMark && python -m pytest tests/test_api.py -k "verify_auth" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/main.py tests/test_api.py
git commit -m "feat: verify_auth queries agents table with bcrypt verification"
```

---

### Task 6: Submit + Query Rating — 使用哈希值

**Files:**
- Modify: `server/main.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Update mock_verify_auth fixture and tests**

更新 `tests/test_api.py` 中的 `mock_verify_auth` fixture：

```python
@pytest.fixture
def mock_verify_auth():
    """Mock verify_auth to return (api_key_hash, agent_type)."""
    with patch('main.verify_auth', new_callable=AsyncMock) as mock:
        mock.return_value = ('$2b$12$mock_hash_value_placeholder', 'claude-code')
        yield mock
```

更新 `test_submit_rating_without_auth` 和 `test_query_rating_without_auth`（直接测试 handler）：

```python
@pytest.mark.asyncio
async def test_submit_rating_without_auth():
    """Test 401 error response format is correct."""
    mock_request = MagicMock()
    exc = HTTPException(status_code=401, detail="Invalid API key")

    response = await http_exception_handler(mock_request, exc)

    assert response.status_code == 401
    import json
    body = json.loads(response.body)
    assert body['error']['code'] == 'UNAUTHORIZED'
    assert isinstance(body['error']['message'], str)


@pytest.mark.asyncio
async def test_query_rating_without_auth():
    """Test 401 error response format is correct."""
    mock_request = MagicMock()
    exc = HTTPException(status_code=401, detail="Invalid API key")

    response = await http_exception_handler(mock_request, exc)

    assert response.status_code == 401
    import json
    body = json.loads(response.body)
    assert body['error']['code'] == 'UNAUTHORIZED'
    assert isinstance(body['error']['message'], str)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/Users/hhhhh/Desktop/EchoMark && python -m pytest tests/test_api.py -v`
Expected: FAIL — submit/query 仍将 verify_auth 返回值当字符串用

- [ ] **Step 3: Update submit_rating and get_rating**

在 `server/main.py` 中，更新 `submit_rating`：

```python
@app.post("/api/v1/ratings", response_model=RatingResponse)
async def submit_rating(rating: RatingSubmit, authorization: str = Header(...)):
    api_key_hash, _ = await verify_auth(authorization)

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
        (rating.tool_name, api_key_hash, rating.accuracy, rating.efficiency, rating.usability, rating.stability, overall, rating.comment),
        fetch_one=True
    )

    rating_id = result['id']
    return RatingResponse(id=str(rating_id), success=True, message="Rating submitted")
```

更新 `get_rating`：

```python
@app.get("/api/v1/ratings/{tool_name}", response_model=ToolStatsResponse)
async def get_rating(tool_name: str, authorization: str = Header(...)):
    await verify_auth(authorization)

    result = execute_sql(
        """SELECT tool_name, total_ratings, avg_accuracy, avg_efficiency,
                  avg_usability, avg_stability, avg_overall, last_updated
           FROM tool_stats WHERE tool_name = %s""",
        (tool_name,),
        fetch_one=True
    )

    if not result:
        raise HTTPException(status_code=404, detail=f"No ratings found for tool: {tool_name}")

    return ToolStatsResponse(
        tool_name=result['tool_name'],
        stats={
            "total_ratings": result['total_ratings'],
            "avg_overall": float(result['avg_overall']) if result['avg_overall'] else 0.0,
            "avg_accuracy": float(result['avg_accuracy']) if result['avg_accuracy'] else 0.0,
            "avg_efficiency": float(result['avg_efficiency']) if result['avg_efficiency'] else 0.0,
            "avg_usability": float(result['avg_usability']) if result['avg_usability'] else 0.0,
            "avg_stability": float(result['avg_stability']) if result['avg_stability'] else 0.0,
            "last_updated": result['last_updated'].isoformat() if result['last_updated'] else None
        }
    )
```

- [ ] **Step 4: Run all server tests**

Run: `cd /c/Users/hhhhh/Desktop/EchoMark && python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add server/main.py tests/test_api.py
git commit -m "feat: submit_rating stores hash, get_rating uses real auth, fix 404 detail format"
```

---

### Task 7: Skill Client — register.py 新增 --type 参数

**Files:**
- Modify: `echomark-skill/scripts/register.py`

- [ ] **Step 1: Implement register.py changes**

更新 `echomark-skill/scripts/register.py`：

```python
#!/usr/bin/env python3
"""Register an AI Agent and obtain API Key."""
import sys
import os

# Add current directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from config import ECHO_MARK_API_URL, API_TIMEOUT, CONFIG_DIR, API_KEY_FILE


def register(agent_type):
    """Register agent with EchoMark cloud service."""
    url = f"{ECHO_MARK_API_URL}/api/v1/agents/register"

    response = requests.post(url, json={"agent_type": agent_type}, timeout=API_TIMEOUT)
    response.raise_for_status()

    data = response.json()
    api_key = data["api_key"]

    # Save API Key to config file
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(API_KEY_FILE, "w") as f:
        f.write(api_key)

    # Set file permissions to user-only (Unix)
    try:
        os.chmod(API_KEY_FILE, 0o600)
    except PermissionError:
        pass  # Windows may not support this

    return {"success": True, "api_key": api_key, "agent_type": data["agent_type"]}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Register an AI Agent with EchoMark")
    parser.add_argument("--type", required=True, help="Agent type (e.g., claude-code, openclaw)")

    args = parser.parse_args()

    try:
        result = register(args.type)
        print(f"Successfully registered as [{result['agent_type']}]! API Key saved to {API_KEY_FILE}")
        print(f"API Key: {result['api_key']}")
    except requests.RequestException as e:
        print(f"Registration failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add echomark-skill/scripts/register.py
git commit -m "feat: register.py accepts --type argument for agent type"
```

---

### Task 8: Skill Tests — 更新 register 相关测试

**Files:**
- Modify: `echomark-skill/tests/test_skill.py`
- Modify: `echomark-skill/tests/test_cli.py`

- [ ] **Step 1: Update test_skill.py register tests**

更新 `echomark-skill/tests/test_skill.py` 中 `TestRegister` 类：

```python
class TestRegister:
    """Tests for register module."""

    @patch("requests.post")
    def test_register_success(self, mock_post):
        """Test successful agent registration."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"api_key": "ek_test123", "agent_type": "claude-code"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with patch.object(skill_config, 'API_KEY_FILE', mock_api_key_file):
            result = register.register("claude-code")

        assert result["success"] is True
        assert result["api_key"] == "ek_test123"
        assert result["agent_type"] == "claude-code"
        assert os.path.exists(mock_api_key_file)

    @patch("requests.post")
    def test_register_saves_api_key(self, mock_post):
        """Test that register saves API Key to file."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"api_key": "ek_saved_key", "agent_type": "claude-code"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with patch.object(skill_config, 'API_KEY_FILE', mock_api_key_file):
            register.register("claude-code")

        with open(mock_api_key_file, "r") as f:
            saved_key = f.read().strip()
        assert saved_key == "ek_saved_key"

    @patch("requests.post")
    def test_register_sends_agent_type(self, mock_post):
        """Test that register sends agent_type in request body."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"api_key": "ek_test", "agent_type": "openclaw"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with patch.object(skill_config, 'API_KEY_FILE', mock_api_key_file):
            register.register("openclaw")

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["agent_type"] == "openclaw"
```

- [ ] **Step 2: Update test_cli.py register tests**

更新 `echomark-skill/tests/test_cli.py` 中 `TestRegisterCLI` 类：

```python
class TestRegisterCLI:
    """Tests for register CLI."""

    @patch("requests.post")
    def test_register_main_success(self, mock_post):
        """Test register main normal call."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"api_key": "ek_test123", "agent_type": "claude-code"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with patch.object(skill_config, 'API_KEY_FILE', mock_api_key_file):
            with patch.object(sys, 'argv', ['register', '--type', 'claude-code']):
                try:
                    register.main()
                except SystemExit:
                    pass

        mock_post.assert_called_once()

    @patch("requests.post")
    def test_register_main_missing_type(self, mock_post):
        """Test register without --type exits."""
        with patch.object(sys, 'argv', ['register']):
            try:
                register.main()
            except SystemExit:
                pass

        mock_post.assert_not_called()

    @patch("requests.post")
    def test_register_main_network_error(self, mock_post):
        """Test register main network error."""
        import requests
        mock_post.side_effect = requests.RequestException("Network error")

        with patch.object(sys, 'argv', ['register', '--type', 'claude-code']):
            try:
                register.main()
            except SystemExit as e:
                assert e.code == 1
```

- [ ] **Step 3: Run all skill tests**

Run: `cd /c/Users/hhhhh/Desktop/EchoMark && python -m pytest echomark-skill/tests/ -v`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add echomark-skill/tests/test_skill.py echomark-skill/tests/test_cli.py
git commit -m "test: update skill tests for new register --type argument"
```

---

### Task 9: Full Test Suite — 全量回归测试

- [ ] **Step 1: Run all tests**

Run: `cd /c/Users/hhhhh/Desktop/EchoMark && python -m pytest tests/ echomark-skill/tests/ -v`
Expected: ALL PASS

- [ ] **Step 2: Verify no regressions**

确认所有测试通过，无 import 错误或类型不匹配。

---

## Self-Review Checklist

| Spec 需求 | 对应 Task |
|-----------|----------|
| 新增 agents 表 (id, agent_type, api_key_hash, timestamp) | Task 1 |
| 注册接受 agent_type 参数 | Task 2, 4 |
| 注册时生成 Key → 哈希 → 存 DB → 返回明文 | Task 4 |
| 响应包含 api_key + agent_type | Task 2, 4 |
| verify_auth 查 DB + bcrypt 验证 | Task 5 |
| verify_auth 返回 (hash, agent_type) | Task 5 |
| submit_rating 存哈希而非明文 | Task 6 |
| 401 响应 code=UNAUTHORIZED, message=string | Task 3 |
| 404 响应 code=NOT_FOUND, message=string | Task 3 |
| Skill register.py 新增 --type 参数 | Task 7 |
