# Voting API

基于 FastAPI + SQLite 的轻量级多人投票 API 服务。支持创建投票、提交选票、查询实时结果——JWT 身份认证 + 一人一票（应用层 + 数据库层双重保障）。

## 功能

- **投票管理** — 创建、编辑、删除投票，支持多选项和 UTC 截止时间
- **选票提交** — 每人每投票限投一次，数据库唯一约束 + 应用层校验双保险
- **实时结果** — 每个选项的得票数和百分比，随时查询
- **JWT 认证** — 注册/登录，密码 bcrypt 哈希，token 24 小时过期，预留认证方式切换钩子
- **多 Tab 测试** — 前端使用 `sessionStorage` 存储 token，同一浏览器多 Tab 可同时登录不同用户
- **并发安全** — SQLite WAL 模式 + `busy_timeout` 处理写竞争，全链路 UTC 时间戳
- **一键部署** — Docker Compose 启动

## 快速开始

### 环境要求

- Python 3.11+ 或 Docker

### 本地运行

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --port 8000
```

浏览器打开 `http://localhost:8000`，FastAPI 直接托管前端测试页面。

### Docker

```bash
docker compose up --build
```

服务监听 8000 端口，SQLite 数据通过 `backend/data` 目录持久化。

## API 文档

所有接口统一返回格式：`{"code": 200, "message": "success", "data": {...}}`。

### 认证

| 方法 | 接口 | 需要登录 | 说明 |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | 否 | 注册 |
| POST | `/api/v1/auth/login` | 否 | 登录，返回 JWT |

### 投票

| 方法 | 接口 | 需要登录 | 说明 |
|--------|----------|------|-------------|
| GET | `/api/v1/polls` | 是 | 所有投票列表（发现 + 投票池） |
| GET | `/api/v1/polls/mine` | 是 | 我创建的投票 |
| POST | `/api/v1/polls` | 是 | 创建投票（含选项和截止时间） |
| GET | `/api/v1/polls/{id}` | 是 | 投票详情 |
| PUT | `/api/v1/polls/{id}` | 是 | 编辑投票（仅创建者） |
| DELETE | `/api/v1/polls/{id}` | 是 | 删除投票（仅创建者） |
| POST | `/api/v1/polls/{id}/vote` | 是 | 提交选票 |
| GET | `/api/v1/polls/{id}/results` | 是 | 查询实时结果 |

### 健康检查

| 方法 | 接口 | 需要登录 | 说明 |
|--------|----------|------|-------------|
| GET | `/health` | 否 | 健康检查 |

### 业务错误码

| 范围 | 含义 |
|-------|---------|
| 1001 | 认证失败 / token 无效 |
| 1002 | 用户名已被占用 |
| 2001 | 投票已过期 |
| 2002 | 已经投过票 |
| 2003 | 无效的选项 |
| 2004 | 投票不存在 |
| 2005 | 非创建者无权修改 |

## 项目结构

```
demo/
├── CLAUDE.md                  # 项目规范文档（SDD）
├── README.md
├── docker-compose.yml
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── config.py              # 环境变量配置
│   ├── database.py            # SQLite 连接 + WAL 配置
│   ├── models.py              # SQLAlchemy ORM（User、Poll、Option、Vote）
│   ├── schemas.py             # Pydantic 请求/响应模型
│   ├── auth.py                # JWT + bcrypt，get_current_user 依赖注入
│   ├── main.py                # FastAPI 入口，CORS，前端静态文件托管
│   ├── routers/
│   │   ├── auth.py            # /api/v1/auth/*
│   │   └── polls.py           # /api/v1/polls/*
│   ├── services/
│   │   ├── auth.py            # 注册/登录逻辑
│   │   └── polls.py           # 投票 CRUD、投票、结果统计
│   └── data/                  # SQLite 数据库文件（git 忽略）
└── frontend/
    └── index.html             # 测试控制台（纯 HTML/JS）
```

## 架构决策

### SQLite WAL 模式

WAL（Write-Ahead Logging）允许写入期间并发读取——读不阻塞写。配合 `busy_timeout=5000ms`，20+ 并发投票下的写竞争可以平滑处理，无需升级到 PostgreSQL。

### 全链路 UTC

所有时间戳以 ISO 8601 UTC 存储和比较。前端输入时将本地时间转为 UTC 发给后端，展示时浏览器自动转回本地时区。避免 Docker 容器与宿主机之间的时区漂移问题。

### 一人一票：双重保障

1. **应用层** — Service 中显式查询是否已投，返回友好错误提示
2. **数据库层** — `votes` 表 `UNIQUE(poll_id, user_id)` 约束，并发竞态的最后防线

### 后端分层

```
Router（参数校验、HTTP 相关）
  → Service（业务逻辑、跨模块调用）
    → Model（SQLAlchemy ORM，不含业务逻辑）
```

ORM 对象不直接返回给客户端，通过 Pydantic Schema 转换——数据库表结构变更不会直接暴露到 API 响应中。

## 多用户测试

在浏览器中打开多个 Tab，每个 Tab 的 JWT 存在独立的 `sessionStorage` 中，可以同时登录不同用户进行交互测试。

预注册测试账号：`alice`、`bob`、`charlie`（密码均为 `pass123`）。

## 技术栈

| 层 | 技术 |
|-------|-----------|
| 后端 | Python 3.11+ / FastAPI / SQLAlchemy |
| 数据库 | SQLite（WAL 模式） |
| 认证 | python-jose（JWT）/ bcrypt |
| 前端 | 原生 HTML/CSS/JS |
| 部署 | Docker Compose |

## License

MIT
