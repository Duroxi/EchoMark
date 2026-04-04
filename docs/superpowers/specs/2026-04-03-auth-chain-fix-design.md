# v0.0.2 认证链路修复设计

> 修复 MVP 中认证链路断裂问题：接入已有的哈希/验证函数，建立完整的注册-存储-验证闭环。

## 背景

v0.0.1 现状：
- `auth.py` 中 `hash_api_key()` / `verify_api_key()` 已实现但从未被调用
- 注册接口不存储任何信息到数据库
- `verify_auth()` 只检查 Bearer 格式，不验证 Key 真实性
- 提交评分时 `api_key_hash` 字段存的是明文 Key
- 401/404 错误响应格式存在嵌套 bug

## 设计决策

- `agent_type` 字段表示 Agent 类别（如 `claude-code`、`openclaw`），API Key 是具体实例的唯一标识
- 同一个 `agent_type` 可多次注册（每个实例有自己的 Key）
- v0.0.2 只存储 `agent_type`，不做分类统计（留 V2）
- 注册接口本身不需要认证

## 一、数据库变更

新增 `agents` 表：

```sql
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type VARCHAR(255) NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_api_key_hash ON agents(api_key_hash);
```

`ratings` 表结构不变。`api_key_hash` 字段修复后存 bcrypt 哈希值。

## 二、注册流程

请求：
```json
POST /api/v1/agents/register
{"agent_type": "claude-code"}
```

处理：
1. 校验 `agent_type` 非空、不超过 255 字符
2. 生成 API Key（`ek_` + 32 位，现有逻辑不变）
3. `hash_api_key(api_key)` → 存入 `agents` 表
4. 返回明文 Key（仅此一次）

响应：
```json
{
  "api_key": "ek_XyZabcDEF123...",
  "agent_type": "claude-code"
}
```

## 三、认证验证

`verify_auth()` 改造：
1. 从 header 提取 Key → `extract_key_from_header()`
2. 从 `agents` 表查出所有 `api_key_hash`
3. 遍历用 `verify_api_key()` (bcrypt) 逐一比对
4. 验证通过 → 返回 `(api_key_hash, agent_type)`
5. 验证失败 → 返回 401

## 四、提交评分变更

`submit_rating()` 中 `api_key_hash` 字段改为存从 `verify_auth()` 拿到的哈希值，不再存明文。

## 五、错误响应修复

- 统一错误抛出方式：`raise HTTPException(status_code, detail="message string")`，由 `http_exception_handler` 统一包装为 `{"error": {"code": "...", "message": "..."}}`
- `http_exception_handler` 中 404 返回 `"NOT_FOUND"` 而非 `"ERROR"`
- 消除 401 响应嵌套 bug

## 影响范围

| 文件 | 变更类型 |
|------|----------|
| `server/migrations/init.sql` | 新增 agents 表 |
| `server/main.py` | 注册存 DB、verify_auth 接入验证、提交存哈希、错误响应修复 |
| `server/models.py` | 注册请求/响应新增 agent_type 字段 |
| `server/auth.py` | 无变更 |
| `server/db.py` | 无变更 |
| `server/jobs/nightly_update.py` | 无变更 |
| `echomark-skill/scripts/register.py` | 注册请求新增 agent_type 参数 |
