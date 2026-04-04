# EchoMark 服务端更新指南

> 更新前请先停止服务，更新完成后重启。

## 第一步：拉取最新代码

```bash
cd /path/to/EchoMark
git pull origin dev
```

## 第二步：重置数据库（必须）

v0.0.2 重写了认证逻辑，旧数据中的 API Key 为明文存储且无法迁移，需要清空数据库并重建。

### 2.1 进入 PostgreSQL 命令行

```bash
sudo -u postgres psql
```

或者如果你的 PostgreSQL 用户有密码：

```bash
psql -U postgres -d echomark
```

### 2.2 切换到 echomark 数据库（如果上一步没指定 -d）

```sql
\c echomark
```

### 2.3 删除旧表

```sql
DROP TABLE IF EXISTS ratings;
DROP TABLE IF EXISTS tool_stats;
DROP TABLE IF EXISTS agents;
```

预期输出：
```
DROP TABLE
DROP TABLE
DROP TABLE
```

### 2.4 重新建表

逐行复制粘贴以下 SQL，在 psql 命令行中执行：

```sql
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

CREATE INDEX IF NOT EXISTS idx_ratings_tool_name ON ratings(tool_name);
CREATE INDEX IF NOT EXISTS idx_ratings_api_key ON ratings(api_key_hash);
CREATE INDEX IF NOT EXISTS idx_ratings_timestamp ON ratings(timestamp);

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

CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type VARCHAR(255) NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_api_key_hash ON agents(api_key_hash);
```

预期输出：
```
CREATE TABLE
CREATE INDEX
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
```

### 2.5 验证三张表都已创建

```sql
\dt
```

预期输出：
```
             List of relations
 Schema |    Name    | Type  |  Owner
--------+------------+-------+----------
 public | agents     | table | postgres
 public | ratings    | table | postgres
 public | tool_stats | table | postgres
```

### 2.6 退出 PostgreSQL

```sql
\q
```

## 第三步：重启服务

先找到并停止旧进程：

```bash
# 查找 uvicorn 进程
ps aux | grep uvicorn

# 停止进程（替换 <PID> 为实际进程号）
kill <PID>
```

重新启动：

```bash
cd /path/to/EchoMark/server
DATABASE_URL="你的数据库连接地址" \
LAST_UPDATE_FILE="/home/ruoxi/.echomark/last_update" \
nohup uvicorn main:app --host 0.0.0.0 --port 9527 > echomark.log 2>&1 &
```

## 第四步：验证更新成功

### 4.1 测试注册接口（变更点）

之前：无参数调用
```bash
curl -X POST http://localhost:9527/api/v1/agents/register
```

现在：需要传 agent_type
```bash
curl -X POST http://localhost:9527/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{"agent_type": "test-agent"}'
```

预期返回：
```json
{"api_key": "ek_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", "agent_type": "test-agent"}
```

### 4.2 测试认证验证（变更点）

用上一步拿到的 api_key 测试提交评分：

```bash
curl -X POST http://localhost:9527/api/v1/ratings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <上一步返回的api_key>" \
  -d '{"tool_name":"test-tool","accuracy":5,"efficiency":4,"usability":4,"stability":5}'
```

预期返回：
```json
{"id": "uuid", "success": true, "message": "Rating submitted"}
```

### 4.3 测试无效 Key 被拒绝

```bash
curl -X POST http://localhost:9527/api/v1/ratings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer fake_key_that_was_not_registered" \
  -d '{"tool_name":"test","accuracy":5,"efficiency":4,"usability":4,"stability":5}'
```

预期返回 401：
```json
{"error": {"code": "UNAUTHORIZED", "message": "Invalid API key"}}
```

## 变更摘要

| 变更项 | v0.0.1（旧） | v0.0.2（新） |
|--------|-------------|-------------|
| 注册接口 | 无参数，不存 DB | 需要 `{"agent_type":"..."}`，存 DB |
| 认证验证 | 只检查 Bearer 格式 | 查 DB + bcrypt 验证 |
| 评分提交 | 明文存 Key | 哈希存 Key |
| 无效 Key | 能通过认证 | 返回 401 |
| 数据库 | 2 张表 | 3 张表（新增 agents） |
