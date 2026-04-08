# EchoMark v0.0.3 迁移指南

> 本文档指导从 v0.0.2 升级到 v0.0.3。执行迁移的 Agent 请严格按照步骤操作，不要跳过任何步骤。

---

## 一、本次变更内容

### 核心改动：认证性能优化

v0.0.2 的 `verify_auth` 函数在每次 API 请求认证时，会从数据库加载**所有 Agent 记录**，然后在 Python 中逐一用 bcrypt 比对。随着 Agent 数量增长，认证延迟会线性增加（每多 100 个 Agent 约增加 10 秒）。

v0.0.3 的解决方案：在 `agents` 表中新增 `key_prefix` 字段，存储 API Key 的前 10 位明文。认证时先用 `key_prefix` 做数据库索引查询（毫秒级），只对命中的 0~1 条记录做 bcrypt 验证，将认证复杂度从 O(N) 降到 O(1)。

### 变更的文件

| 文件 | 变更说明 |
|------|---------|
| `server/config.py` | 新增 `KEY_PREFIX_LEN = 10` 常量 |
| `server/auth.py` | 新增 `extract_key_prefix()` 函数，从 API Key 提取前 10 位作为前缀 |
| `server/main.py` | 注册端点：INSERT 时多存一个 `key_prefix` 字段 |
| `server/main.py` | `verify_auth`：从 `SELECT ... FROM agents`（全表扫描）改为 `SELECT ... FROM agents WHERE key_prefix = %s`（索引查询） |
| `server/migrations/init.sql` | agents 表定义新增 `key_prefix VARCHAR(10) NOT NULL` 字段和 `idx_agents_key_prefix` 索引 |
| `server/migrations/v0.0.3_add_key_prefix.sql` | **新增文件**：生产环境迁移 SQL |
| `tests/server/test_auth.py` | 新增 `test_extract_key_prefix` 测试 |
| `tests/server/test_api.py` | 新增 3 个测试验证 key_prefix 逻辑 |

### 未变更的文件

- `server/db.py` — 无变更
- `server/models.py` — 无变更
- `server/jobs/nightly_update.py` — 无变更
- `echomark-skill/` 目录 — 全部无变更，Skill 端不需要任何改动
- API 接口契约 — 无变更（请求/响应格式完全不变）

### 数据库变更

- `ratings` 表 — **不动**
- `tool_stats` 表 — **不动**
- `agents` 表 — 新增 `key_prefix` 字段 + 索引，清空旧数据

### 对用户的影响

- 所有已注册的 Agent 的 API Key 将**失效**，需要重新注册
- 旧评分数据**不受影响**，保留在 ratings 表中
- Skill 端代码**不需要任何改动**

---

## 二、迁移前检查

在执行迁移之前，先确认以下信息：

### 步骤 1：确认当前服务状态

```bash
# 确认服务是否在运行
curl -s http://localhost:9527/docs | head -5

# 如果服务在运行，会返回 HTML 内容
# 如果服务未运行，会返回连接错误
```

### 步骤 2：确认数据库连接信息

```bash
# 查看当前服务的环境变量，找到 DATABASE_URL
# 方法取决于服务的部署方式（Docker / systemd / 直接运行）
# 以下提供几种常见方式，选择适用的：

# 如果是 Docker 部署：
docker inspect <container_name> | grep -i database

# 如果是 systemd 部署：
cat /etc/systemd/system/echomark.service | grep -i database

# 如果是直接运行：
ps aux | grep uvicorn
# 找到进程的环境变量
cat /proc/<pid>/environ | tr '\0' '\n' | grep DATABASE_URL
```

记下 `DATABASE_URL` 的值，后续步骤需要用到。

### 步骤 3：确认数据库当前状态

```bash
# 用上面获取的 DATABASE_URL 连接数据库
# 将 <DATABASE_URL> 替换为实际的连接字符串

psql "<DATABASE_URL>" -c "\d agents"
```

预期输出应包含以下字段（v0.0.2 的 agents 表）：

```
 id           | UUID
 agent_type   | character varying(255)
 api_key_hash | character varying(255)
 timestamp    | timestamp without time zone
```

**如果输出中已经包含 `key_prefix` 字段，说明迁移已经执行过，不要重复执行。**

### 步骤 4：备份 agents 表（可选但推荐）

```bash
# 导出当前 agents 表数据作为备份
pg_dump "<DATABASE_URL>" -t agents > agents_backup_$(date +%Y%m%d).sql
```

---

## 三、执行迁移

### 步骤 1：停止服务

停止 EchoMark API 服务，防止迁移期间有新的请求进来。

具体停止方式取决于部署方式，以下提供几种常见方式：

```bash
# Docker 部署：
docker stop <container_name>

# systemd 部署：
systemctl stop echomark

# 直接运行：
# 找到 uvicorn 进程并 kill
ps aux | grep uvicorn
kill <pid>
```

**确认服务已停止：**

```bash
curl -s http://localhost:9527/docs
# 应返回连接错误，说明服务已停止
```

### 步骤 2：执行数据库迁移

迁移 SQL 文件位于：`server/migrations/v0.0.3_add_key_prefix.sql`

文件内容如下：

```sql
-- v0.0.3: Add key_prefix column for auth performance optimization

-- 1. Add key_prefix column
ALTER TABLE agents ADD COLUMN IF NOT EXISTS key_prefix VARCHAR(10) NOT NULL DEFAULT '';

-- 2. Create index on key_prefix
CREATE INDEX IF NOT EXISTS idx_agents_key_prefix ON agents(key_prefix);

-- 3. Truncate old agent records (cannot backfill key_prefix from bcrypt hashes)
TRUNCATE TABLE agents;
```

执行方式：

```bash
# 方式 A：如果迁移文件已在服务器上
psql "<DATABASE_URL>" -f /path/to/server/migrations/v0.0.3_add_key_prefix.sql

# 方式 B：如果迁移文件不在服务器上，直接执行 SQL
psql "<DATABASE_URL>" -c "ALTER TABLE agents ADD COLUMN IF NOT EXISTS key_prefix VARCHAR(10) NOT NULL DEFAULT '';"
psql "<DATABASE_URL>" -c "CREATE INDEX IF NOT EXISTS idx_agents_key_prefix ON agents(key_prefix);"
psql "<DATABASE_URL>" -c "TRUNCATE TABLE agents;"
```

### 步骤 3：验证数据库变更

```bash
psql "<DATABASE_URL>" -c "\d agents"
```

预期输出应包含新增的 `key_prefix` 字段：

```
 id           | UUID
 agent_type   | character varying(255)
 api_key_hash | character varying(255)
 key_prefix   | character varying(10)       ← 新增字段
 timestamp    | timestamp without time zone
```

验证索引：

```bash
psql "<DATABASE_URL>" -c "\di idx_agents_key_prefix"
```

预期输出应显示 `idx_agents_key_prefix` 索引存在。

验证 agents 表已清空：

```bash
psql "<DATABASE_URL>" -c "SELECT COUNT(*) FROM agents;"
```

预期输出：`count = 0`

### 步骤 4：更新服务端代码

将 v0.0.3 的代码部署到服务器，替换 v0.0.2 的代码。

变更的文件列表（只需更新这些文件）：

```
server/config.py
server/auth.py
server/main.py
server/migrations/init.sql
```

新增的文件：

```
server/migrations/v0.0.3_add_key_prefix.sql
```

具体部署方式取决于项目的部署流程，以下提供几种常见方式：

```bash
# 如果使用 Git：
cd /path/to/EchoMark
git pull origin duruo   # 或对应的分支

# 如果使用 Docker 重新构建：
cd /path/to/EchoMark/server
docker build -t echomark-api:latest .
```

### 步骤 5：启动服务

```bash
# Docker 部署：
docker start <container_name>
# 或重新运行：
docker run -d -p 9527:8000 -e DATABASE_URL="<DATABASE_URL>" echomark-api:latest

# systemd 部署：
systemctl start echomark

# 直接运行：
cd /path/to/EchoMark/server
uvicorn main:app --host 0.0.0.0 --port 9527 &
```

### 步骤 6：验证服务

```bash
# 1. 确认服务启动
curl -s http://localhost:9527/docs | head -5
# 应返回 HTML 内容

# 2. 测试注册新 Agent
curl -X POST http://localhost:9527/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"test-agent"}'
# 应返回：{"api_key":"ek_...","agent_type":"test-agent"}

# 3. 用新注册的 API Key 测试提交评分
curl -X POST http://localhost:9527/api/v1/ratings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <上一步返回的api_key>" \
  -d '{"tool_name":"test-tool","accuracy":5,"efficiency":4,"usability":4,"stability":5}'
# 应返回：{"id":"...","success":true,"message":"Rating submitted"}

# 4. 验证 key_prefix 已存入数据库
psql "<DATABASE_URL>" -c "SELECT key_prefix, agent_type FROM agents;"
# 应返回至少一条记录，key_prefix 不为空，以 "ek_" 开头，长度为 10

# 5. 清理测试数据（可选）
psql "<DATABASE_URL>" -c "DELETE FROM agents WHERE agent_type = 'test-agent';"
psql "<DATABASE_URL>" -c "DELETE FROM ratings WHERE tool_name = 'test-tool';"
```

---

## 四、迁移后操作

### 通知用户重新注册

迁移完成后，所有旧的 API Key 已失效。需要通知用户：

1. 重新执行注册命令：
   ```bash
   cd echomark-skill
   python -m scripts.register --type <agent_type>
   ```
2. 新的 API Key 会自动保存到 `~/.echomark/api_key`
3. 之后的 submit 和 query 命令无需任何改动

---

## 五、回滚方案

如果迁移后发现问题需要回滚：

### 步骤 1：停止服务

### 步骤 2：回滚代码到 v0.0.2

```bash
cd /path/to/EchoMark
git checkout v0.0.2
```

### 步骤 3：回滚数据库

```bash
psql "<DATABASE_URL>" -c "DROP INDEX IF EXISTS idx_agents_key_prefix;"
psql "<DATABASE_URL>" -c "ALTER TABLE agents DROP COLUMN IF EXISTS key_prefix;"
```

### 步骤 4：恢复 agents 表数据（如果有备份）

```bash
psql "<DATABASE_URL>" < agents_backup_YYYYMMDD.sql
```

### 步骤 5：启动服务

---

## 六、注意事项

1. **迁移期间服务不可用** — 从停止服务到启动服务之间，API 无法响应请求
2. **旧 API Key 全部失效** — agents 表被 TRUNCATE，所有用户需重新注册
3. **ratings 表数据不受影响** — 旧评分数据完整保留
4. **不要重复执行迁移 SQL** — `IF NOT EXISTS` 保证幂等，但 TRUNCATE 会再次清空 agents 表
5. **Skill 端不需要任何改动** — API 接口契约未变
