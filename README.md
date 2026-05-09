<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/SQLite-WAL-003B57?logo=sqlite" alt="SQLite"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker" alt="Docker"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT"/>
</p>

<h1 align="center">Voting API</h1>
<p align="center"><strong>一个基于 FastAPI + SQLite 的轻量多人投票服务，面向小团队内部决策场景——注册即投、一人一票、实时看结果。</strong></p>

## 这是什么

团队里时不时需要投票决定一件事——午饭吃什么、方案选哪个、要不要加班团建。微信群接龙太乱，在线问卷太重，开一个 Google Form 又小题大做。

Voting API 就是解决这个问题的：**Docker 一键拉起来，创建一个投票，把链接丢到群里，大家打开浏览器就能投。** 不做匿名、不做分享、不做评论——就是一个极简的投票工具，够用就好。

## 能做什么

- **创建投票** — 标题 + 多个选项 + 截止时间，创建者可以编辑或删除
- **一人一票** — 应用层校验 + 数据库唯一约束双保险，并发场景下不会重复投
- **实时结果** — 随时查看每个选项的得票数和百分比
- **账号体系** — 注册/登录，密码 bcrypt 哈希，JWT 24 小时过期
- **多 Tab 并行测试** — `sessionStorage` 隔离 token，同一个浏览器开多个 Tab 各登各的号
- **并发安全** — SQLite WAL 模式 + `busy_timeout`，20+ 并发写入不丢数据

## 快速开始

### 前置条件

- Python 3.11+，或者 Docker

### 本地跑起来

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

浏览器打开 `http://localhost:8000`，后端直接托管前端测试页。

```bash
# 验证一下服务是否正常
curl http://localhost:8000/health
# → {"code":200,"message":"ok"}
```

### Docker 部署

```bash
docker compose up --build
```

服务监听 8000 端口，SQLite 数据通过 `backend/data` 目录持久化。

### 测试账号

预注册了三个用户，开箱即用：`alice`、`bob`、`charlie`，密码都是 `pass123`。

打开多个 Tab，各自登录不同用户，就能模拟多人投票场景。

## API 概览

所有接口统一响应格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 注册新用户 |
| POST | `/api/v1/auth/login` | 登录，返回 JWT |

### 投票（需要 Bearer Token）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/polls` | 全部投票列表 |
| GET | `/api/v1/polls/mine` | 我创建的投票 |
| POST | `/api/v1/polls` | 创建投票 |
| GET | `/api/v1/polls/{id}` | 投票详情 |
| PUT | `/api/v1/polls/{id}` | 编辑投票（仅创建者） |
| DELETE | `/api/v1/polls/{id}` | 删除投票（仅创建者） |
| POST | `/api/v1/polls/{id}/vote` | 提交选票 |
| GET | `/api/v1/polls/{id}/results` | 查看实时结果 |

### 错误码

| 码段 | 含义 |
|------|------|
| 1001 | 认证失败 / token 无效 |
| 1002 | 用户名已被注册 |
| 2001 | 投票已过期 |
| 2002 | 已经投过票了 |
| 2003 | 选项不存在 |
| 2004 | 投票不存在 |
| 2005 | 无权操作（非创建者） |

## 技术栈

| 层 | 选型 | 为什么选它 |
|---|------|-----------|
| 框架 | FastAPI | 异步支持好，自动生成 API 文档 |
| 数据库 | SQLite (WAL 模式) | 单文件零运维，读写不互斥 |
| 认证 | python-jose + bcrypt | JWT 24h 过期，预留认证切换钩子 |
| 前端 | 原生 HTML/CSS/JS | 纯测试用，不引入框架 |
| 部署 | Docker Compose | 单容器一键拉起 |

## 项目结构

```
├── backend/
│   ├── main.py           # FastAPI 入口，CORS，静态文件托管
│   ├── database.py       # SQLite 连接 + WAL 配置
│   ├── models.py         # SQLAlchemy ORM（User, Poll, Option, Vote）
│   ├── schemas.py        # Pydantic 请求/响应模型
│   ├── auth.py           # JWT + bcrypt，get_current_user 依赖
│   ├── config.py         # 环境变量配置
│   ├── routers/          # 路由层（参数校验 → 调 Service）
│   ├── services/         # 业务逻辑层（规则、流程、DB 操作）
│   └── data/             # SQLite 数据库文件（git 忽略）
├── frontend/
│   └── index.html        # 测试控制台（多 Tab 多用户）
├── docker-compose.yml
└── CLAUDE.md             # 项目规范（给 AI 看，不是给用户看）
```

## 关键设计决策

**为什么用 SQLite 而不是 PostgreSQL？** 10 人小团队用 PostgreSQL 是杀鸡用牛刀。SQLite 开 WAL 模式后读写不互斥，配合 5 秒写锁等待，20+ 并发完全够用。单文件、零运维。

**一人一票怎么保证？** 两层防护：应用层先查是否已投 → 返回友好提示；数据库层 `UNIQUE(poll_id, user_id)` 兜底。代码检查 + 数据库约束，并发竞态也伤不到。

**时间怎么处理？** 全链路 UTC。前端 `new Date(localTime).toISOString()` 发给后端，后端存 ISO 8601 文本，展示时浏览器自动转本地时区。Docker 容器和宿主机时区不一致也没事。

## License

MIT
