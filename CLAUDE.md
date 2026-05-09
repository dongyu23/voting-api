# Voting API - 多人投票服务

## 项目概述

**一句话定义**：一个面向小团队的多人投票 API 服务，支持创建投票、提交选票、查询实时结果，配套简单前端测试页。

**核心功能**：
- 用户注册/登录（JWT 认证，24h 过期，预留认证切换钩子）
- 创建投票（标题 + 多个选项 + 截止时间）
- 编辑/删除投票（仅创建者可操作）
- 提交选票（一人一票、过期不可投）
- 查询实时结果（各选项得票数与比例）
- 简单前端测试页（多 Tab 多用户并行测试）

**明确不做什么**：
- 匿名投票（不做）
- 投票分享/公开链接（不做）
- 评论/讨论功能（不做）
- 第三方 API 开放（不做）
- 邮件通知/提醒（不做）

## 核心约束

| 维度 | 约束 |
|------|------|
| 团队 | 1 人 |
| 目标用户 | ~10 人，内部使用 |
| 并发 | 20+ 并发请求 |
| 部署 | Docker Compose，先本地测试后上云端，轻量应用服务器 |
| 时间 | 一小时内核心链路跑通 |
| 前端 | 纯 HTML 单页，以测试为目的，AI 辅助编写 |
| 多用户测试 | 同一浏览器多 Tab，每 Tab 登录不同用户 |

## 技术栈

| 层 | 选型 | 说明 |
|---|------|------|
| 后端 | Python 3.11+ / FastAPI | 用户最熟悉 |
| 数据库 | SQLite (WAL 模式) | 轻量，单文件，Docker volume 持久化 |
| 认证 | JWT (python-jose + passlib) | 24h 过期，预留认证切换扩展点 |
| 部署 | Docker Compose | 单容器 FastAPI + volume 挂载 SQLite |
| 前端 | 纯 HTML/CSS/JS | 单页，sessionStorage 存 token，无框架 |

## 数据模型

### 表结构（4 张表）

**users**
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK AUTOINCREMENT | |
| username | TEXT | UNIQUE NOT NULL | |
| password_hash | TEXT | NOT NULL | bcrypt 哈希 |
| created_at | TEXT | NOT NULL | ISO 8601 UTC |

**polls**
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK AUTOINCREMENT | |
| title | TEXT | NOT NULL | |
| creator_id | INTEGER | FK→users.id, NOT NULL | 创建者 |
| expires_at | TEXT | NOT NULL | ISO 8601 UTC，截止时间 |
| created_at | TEXT | NOT NULL | ISO 8601 UTC |
| updated_at | TEXT | NOT NULL | ISO 8601 UTC |

**options**
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK AUTOINCREMENT | |
| poll_id | INTEGER | FK→polls.id, NOT NULL | |
| text | TEXT | NOT NULL | 选项文本 |

**votes**
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK AUTOINCREMENT | |
| poll_id | INTEGER | FK→polls.id, NOT NULL | |
| option_id | INTEGER | FK→options.id, NOT NULL | |
| user_id | INTEGER | FK→users.id, NOT NULL | |
| created_at | TEXT | NOT NULL | ISO 8601 UTC |
| UNIQUE(poll_id, user_id) | — | 一人一票最后防线 |

### 索引规则
- `users.username` — 唯一索引（登录查询）
- `polls.creator_id` — 普通索引
- `options.poll_id` — 普通索引
- `votes.poll_id` — 普通索引
- `votes(poll_id, user_id)` — 唯一约束自动建索引

### 数据库规范
- **主键**：INTEGER AUTOINCREMENT
- **时间字段**：TEXT 存 ISO 8601 UTC，永远不用本地时间
- **NULL**：核心业务字段一律 NOT NULL，可选字段才允许 NULL
- **外键**：数据库层不建 FOREIGN KEY 约束（SQLite 默认关闭），应用层维护引用完整性
- **无软删除**：这个项目数据量小，直接物理删除
- **字符集**：默认 UTF-8
- **不要 SELECT \*** — 必须显式列名
- **不要 UPDATE/DELETE 不带 WHERE**

## API 设计

### URL 约定
- RESTful，前缀 `/api/v1/`
- 资源名用复数：`/polls`、`/options`、`/votes`
- 非 CRUD 操作用动词路径：`POST /api/v1/polls/{id}/vote`
- URL 全小写，单词用连字符

### 统一响应格式
```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

### 空值约定
- 列表为空：返回 `[]`
- 字符串为空：返回 `""`
- 对象不存在：返回 `{code: 404, message: "xxx not found", data: null}`
- 数字为空：返回 `0`

### 接口列表

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/auth/register | 注册 | 否 |
| POST | /api/v1/auth/login | 登录，返回 JWT | 否 |
| GET | /api/v1/polls | 投票列表 | 是 |
| POST | /api/v1/polls | 创建投票 | 是 |
| GET | /api/v1/polls/{id} | 投票详情（含选项） | 是 |
| PUT | /api/v1/polls/{id} | 编辑投票（仅创建者） | 是 |
| DELETE | /api/v1/polls/{id} | 删除投票（仅创建者） | 是 |
| POST | /api/v1/polls/{id}/vote | 投票（option_id） | 是 |
| GET | /api/v1/polls/{id}/results | 查询实时结果 | 是 |
| GET | /health | 健康检查 | 否 |

### 错误码分段
| 范围 | 模块 |
|------|------|
| 1000-1999 | 通用（参数校验、认证、系统异常） |
| 2000-2999 | 投票业务（过期、重复投票、权限不足） |

## 关键可靠性设计

### SQLite 并发写入（WAL 模式）
```python
# 启动时必须执行
PRAGMA journal_mode=WAL;      # Write-Ahead Logging，读写不互斥
PRAGMA busy_timeout=5000;     # 写锁等待 5 秒
```
这是方案 A，不换 PostgreSQL。应用层捕获 `database locked` 异常后重试一次作为兜底。

### 时区（全 UTC）
- 前端：用户选本地时间 → `new Date(localTime).toISOString()` → 发 UTC 给后端
- 后端：所有时间存 UTC，过期判断用 `datetime.utcnow()`
- SQLite：存 ISO 8601 TEXT，字符串比较天然支持排序
- 展示：前端拿到 UTC → `new Date(utcTime)` → 浏览器自动转本地时区

### 一人一票双保险
- 前端：检查投票状态，投过就隐藏按钮 + 提示 "您已投过票"
- 后端：`votes` 表 `UNIQUE(poll_id, user_id)` 约束 + 业务层显式检查
- 过期投票：`expires_at < datetime.utcnow()` 拒绝

### 密码安全
- passlib + bcrypt 哈希存储
- 即使是 10 人内部使用，也不存明文

### CORS 配置
- 前端 HTML 文件和后端不同端口，必须配置 CORS
- 本地开发允许 `*`，生产环境限制具体域名

## 分层职责（FastAPI 项目）

```
backend/
  main.py          # FastAPI app 入口，注册路由，CORS，异常处理
  database.py      # SQLite 连接，WAL 配置，SessionLocal
  models.py        # SQLAlchemy ORM 模型（表定义）
  schemas.py       # Pydantic 请求/响应模型（DTO）
  auth.py          # JWT 生成/验证，密码哈希，get_current_user 依赖
  routers/
    auth.py        # /api/v1/auth/*
    polls.py       # /api/v1/polls/*
  services/
    auth.py        # 注册/登录业务逻辑
    polls.py       # 投票 CRUD + 投票 + 结果统计
```

| 层 | 可以做什么 | 不能做什么 |
|----|----------|----------|
| Router | 参数校验，调 Service，返回响应 | 不能写业务逻辑 |
| Service | 业务规则、流程编排、调 DB | 不能直接操作 HTTP 请求/响应对象 |
| Model | 表结构定义 | 不包含业务逻辑 |
| Schema | 请求/响应校验 | 不操作数据库 |

- ORM 对象（Model）不直接返回给客户端，通过 Schema 转换
- Service 层负责 Model ↔ Schema 转换

## 表决规则（业务约束代码化）

1. **过期不可投**：`if poll.expires_at < datetime.utcnow(): raise ExpiredPollError`
2. **一人一票**：`if existing_vote: raise AlreadyVotedError`
3. **只有创建者可编辑/删除**：`if poll.creator_id != current_user.id: raise ForbiddenError`
4. **不能投不存在的选项**：`if option.poll_id != poll.id: raise InvalidOptionError`

## 前端规范

- 纯 HTML + CSS + JS，单文件 `frontend/index.html`
- Token 存在 `sessionStorage`（多 Tab 多用户并行测试）
- 页面加载时读 sessionStorage 判断登录态
- 投票状态 UI 防范：已投票隐藏按钮 + 提示
- 不做前端框架，追求最小可测试页面

## 部署

### Docker Compose
```yaml
services:
  app:
    build: ./backend
    ports: ["8000:8000"]
    volumes: ["./data:/app/data"]
    environment:
      - DATABASE_URL=sqlite:///./data/voting.db
      - JWT_SECRET=${JWT_SECRET}
      - JWT_EXPIRES_HOURS=24
```

### 关键配置
- JWT_SECRET：环境变量注入，不写代码里
- SQLite 文件：挂 volume，容器重启不丢数据
- 健康检查：`/health` 返回 `{"code": 200, "message": "ok"}`

## AI 行为指令

### 写代码时
- 用最简单直接的方式实现，不做过度抽象（一小时项目）
- 不引入 requirements.txt 之外的依赖
- 所有配置用环境变量，不硬编码
- 不需要写测试（时间不够，能跑通即可）

### 改代码时
- 先理解现有代码再动手
- 不顺手修改无关模块
- 改动前说明影响范围

### 不确定时
- 给出 2-3 个方案对比，由用户拍板
- 规范没覆盖的情况：先问，不自创规则
