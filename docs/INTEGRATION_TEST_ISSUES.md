# EchoMark 集成测试问题记录

> 更新日期：2026-03-29

---

## 问题 1：注册 API 违反数据库 CHECK 约束

**状态**：✅ 已修复

**修复方案**：注册时不操作数据库，直接返回 API key

**修复内容**：
- `main.py`: 移除 `register_agent` 中插入 ratings 表的代码
- 移除 `hash_api_key` 的 import（不再需要）

---

## 问题 2：fetch_one 返回 None 时报错

**状态**：✅ 已修复

**修复方案**：db.py 中 `fetch_one=True` 时检查结果是否为 None

---

## 问题 3：nightly_update 中 existing 判断问题

**状态**：✅ 已修复

**修复内容**：`if existing:` → `if existing is not None:`

---

## 问题 4：提交评分时 verify_auth 未 await

**状态**：✅ 已修复

---

## 测试结果

| 测试项 | 结果 |
|--------|------|
| POST /api/v1/agents/register | ✅ 成功，返回 API key |
| POST /api/v1/ratings | ✅ 成功，评分提交成功 |
| GET /api/v1/ratings/{tool_name} | ✅ 成功，返回统计信息 |



**错误信息**：
```
psycopg2.errors.CheckViolation: new row for relation "ratings" violates check constraint "ratings_accuracy_check"
DETAIL:  Failing row contains (xxx, __agent__, $2b$12$..., 0, 0, 0, 0, 0.0, __register__, 2026-03-29 20:15:06.295046)
```

**问题描述**：
- `register_agent` 函数试图在 `ratings` 表中插入一条记录来存储 API key 的 hash
- 数据库约束要求 `accuracy、efficiency、usability、stability` 必须是 1-5
- 代码传的是 0，违反约束

**老杜的方案**（待确认）：
- 注册时不进行任何数据库操作
- 直接返回 API key 给调用者
- 后续评分时不需要严格验证 API key（信任模型）

**若晞的疑问**：
- 如果不存储 API key hash，如何验证请求者是真的注册过的 agent？
- 可能的方案：
  1. MVP 阶段不做验证，带 key 就用（信任模型）
  2. 使用独立的 `agents` 表存储 API key hash
  3. 其他方案？

**待确认问题**：
1. MVP 阶段是否需要严格的 API key 验证？
2. 如果需要验证，存储在哪里？
