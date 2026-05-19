# 聊天室

一个支持全局群聊和 1 对 1 私聊的实时聊天应用，集成 AI 情绪分析、AI 聊天助手和用户习惯总结功能。

---

## 项目结构

```
contact-message/
├── backend/
│   ├── app/
│   │   ├── main.py                # 程序入口 (FastAPI + WebSocket + 对话管理)
│   │   ├── auth.py                # JWT 认证模块
│   │   ├── models.py              # SQLAlchemy 数据库模型
│   │   ├── database.py            # 数据库连接与会话管理
│   │   ├── crud.py                # 数据库 CRUD 操作
│   │   ├── agent.py               # AI 情绪分析引擎 (关键词过滤 + LRU 缓存 + API)
│   │   ├── chat_agent.py          # AI 聊天助手 (读取用户档案 + 短句回复)
│   │   └── summary_agent.py       # 用户习惯总结 Agent (生成 skill.md 档案)
│   ├── data/
│   │   └── skills/                # 用户聊天习惯档案 (user_{id}.md)
│   ├── static/
│   │   ├── avatars/               # 用户上传的头像文件
│   │   └── default_avatar.svg     # 默认头像
│   ├── chat.db                    # SQLite 数据库文件
│   ├── requirements.txt           # Python 依赖
│   ├── .env                       # 环境变量 (不提交到 Git)
│   └── init_db.py                 # 初始化/迁移数据库
│
├── frontend/
│   ├── src/
│   │   ├── App.vue                # 根组件 (会话恢复 + 路由分发)
│   │   ├── main.js                # 入口 (注册 Pinia)
│   │   ├── style.css              # Tailwind 基础样式
│   │   ├── stores/
│   │   │   ├── userStore.js       # 用户状态 (登录/Token/会话恢复/用户列表)
│   │   │   └── chatStore.js       # 聊天状态 (消息/WebSocket/对话切换)
│   │   └── components/
│   │       ├── LoginPage.vue      # 登录/注册页
│   │       ├── ChatRoom.vue       # 聊天主区域 (消息列表 + 输入框 + Agent 开关)
│   │       ├── MessageBubble.vue  # 单条消息气泡 (自己/他人/AI助手/系统通知)
│   │       ├── Sidebar.vue        # 侧边栏 (用户信息 + 对话列表 + 头像设置)
│   │       ├── ConversationList.vue # 对话列表 (全局聊天 + 私聊)
│   │       ├── UserSelect.vue     # 用户选择弹窗 (发起新私聊)
│   │       └── AvatarUploader.vue # 头像上传组件
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## 功能概览

### 核心功能

| 功能 | 说明 |
|------|------|
| 用户认证 | 昵称+密码注册/登录，bcrypt 哈希存储，JWT Token 认证 |
| 全局群聊 | 所有在线用户可见的公共聊天频道 |
| 1 对 1 私聊 | 选择任意用户发起独立对话，消息仅双方可见 |
| AI 情绪分析 | 发送消息时自动分析情绪 (happy/sad/angry/surprised/neutral)，切换对应头像 |
| AI 聊天助手 | 基于外部 API 自动生成短句回复，读取用户档案个性化对话 |
| 用户习惯总结 | 每 10 条消息自动总结用户聊天风格，存入个人档案供 AI 参考 |
| 实时通信 | WebSocket 全双工通信，支持消息广播和对话路由 |
| 用户状态通知 | 用户加入/离开聊天室时实时通知所有在线用户 |

### AI 情绪分析策略

三级优化以降低延迟和 API 调用成本：

1. **关键词前置过滤** — 内置情绪关键词库，短消息或强情绪词直接命中，零延迟返回
2. **LRU 缓存** — 相同内容的分析结果被缓存（最多 256 条），重复消息直接返回缓存
3. **AI API 分析** — 前两级未命中时，调用配置的 AI 模型分析情绪，10 秒超时防阻塞

### AI 聊天助手策略

- **群聊**：仅响应以 `@robot` 或 `@ai` 开头的消息（如 `@robot 你好`），前缀会被自动剥离
- **私聊**：响应所有消息（需在对话设置中启用 AI 助手开关）
- **个性化回复**：每次回复前读取目标用户的 `skill.md` 档案，了解其聊天风格
- **上下文感知**：基于最近 10 条聊天记录生成回复
- **短句输出**：回复自动拆分为不超过 20 字的短消息，模拟真实聊天节奏
- **自动总结**：每 10 条消息触发总结 Agent，更新用户的聊天习惯档案

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| 数据库 | SQLite + SQLAlchemy 2.x |
| 认证 | bcrypt 密码哈希 + JWT Token |
| 情绪分析 | OpenAI 兼容 API (可配置第三方) |
| 聊天/总结 Agent | OpenAI 兼容 API (可配置不同模型) |
| 实时通信 | WebSocket (Token 认证 + 对话路由) |
| 前端框架 | Vue 3 + Vite |
| 状态管理 | Pinia |
| 样式 | Tailwind CSS |

---

## 本地部署

### 1. 安装依赖

**后端：**

```bash
cd backend
pip install -r requirements.txt
```

**前端：**

```bash
cd frontend
npm install
```

### 2. 配置环境变量

复制 `backend/.env.example` 为 `backend/.env`，填入实际配置：

```bash
cp backend/.env.example backend/.env
```

`backend/.env` 内容：

```env
# JWT 认证密钥 (必填)
SECRET_KEY=your-random-secret-key

# 情绪分析 API (OpenAI 兼容格式，可接入任意第三方 API)
EMOTION_API_BASE_URL=https://api-inference.modelscope.cn/v1
EMOTION_API_KEY=your_api_key_here
EMOTION_API_MODEL=Qwen/Qwen3-8B

# 聊天 Agent + 总结 Agent (OpenAI 兼容格式，可与上面相同或不同)
CHAT_AGENT_BASE_URL=https://api-inference.modelscope.cn/v1
CHAT_AGENT_API_KEY=your_api_key_here
CHAT_AGENT_MODEL=Qwen/Qwen3-8B
```

| 变量 | 说明 |
|------|------|
| `SECRET_KEY` | JWT 签名密钥，建议使用随机字符串 |
| `EMOTION_API_BASE_URL` | 情绪分析 API 地址 |
| `EMOTION_API_KEY` | 情绪分析 API 密钥 |
| `EMOTION_API_MODEL` | 情绪分析模型 ID |
| `CHAT_AGENT_BASE_URL` | 聊天/总结 Agent 的 API 地址 |
| `CHAT_AGENT_API_KEY` | 聊天/总结 Agent 的 API 密钥 |
| `CHAT_AGENT_MODEL` | 聊天/总结 Agent 的模型 ID |

### 3. 初始化数据库

```bash
cd backend
python init_db.py
```

首次运行会创建所有表。如果数据库已存在，会自动添加新字段（如 `conversation_id`）。

### 4. 启动服务

**后端：**

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**前端：**

```bash
cd frontend
npm run dev
```

访问 `http://localhost:5173` 即可使用。打开多个浏览器窗口可测试多用户聊天。

---

## 局域网部署

### 获取局域网 IP

- **Windows**: PowerShell 输入 `ipconfig`，找到 IPv4 地址（如 `192.168.1.5`）
- **macOS/Linux**: 终端输入 `ifconfig` 或 `ip addr`

### 修改前端配置

编辑 `frontend/src/stores/userStore.js` 和 `frontend/src/stores/chatStore.js`，将 `localhost` 替换为你的局域网 IP：

```javascript
// userStore.js & chatStore.js
const BACKEND_URL = 'http://192.168.1.5:8000'
const WS_URL = 'ws://192.168.1.5:8000'
```

### 启动服务

```bash
# 后端
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 前端 (加 --host 允许局域网访问)
cd frontend
npm run dev -- --host
```

---

## 使用说明

### 登录/注册

输入昵称和密码进入聊天室。新用户自动注册，老用户验证登录。登录后 Token 有效期 24 小时，刷新页面自动恢复会话。

### 全局聊天

登录后默认进入全局聊天。所有在线用户的消息实时可见。发送消息时 AI 自动分析情绪并切换头像。

### AI 聊天助手

- **群聊**：输入 `@robot 你好` 或 `@ai 你好` 唤起 AI 助手
- **私聊**：点击对话头部的 AI 开关启用/禁用，启用后所有消息都会触发 AI 回复
- AI 回复以紫色气泡显示，每条不超过 20 字
- 发送 10 条消息后，总结 Agent 会自动更新你的聊天习惯档案

### 私聊

1. 点击侧边栏底部的 **"+ 新对话"** 按钮
2. 在弹出的用户列表中选择聊天对象
3. 进入私聊界面，消息仅双方可见
4. 点击左上角 **←** 返回全局聊天

### 头像设置

在侧边栏底部展开头像设置面板，为不同情绪标签（happy/sad/angry/surprised/neutral）上传对应头像。

---

## API 接口

所有受保护接口需携带 `token` 参数（Query 或 Form）。

### 用户与认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/register` | 注册/登录，返回 `{ user, access_token }` |
| GET | `/users?token=xxx` | 获取所有用户列表（用于发起私聊） |
| POST | `/upload_avatar` | 上传头像 (FormData: user_id, emotion, file, token) |
| GET | `/history?limit=50&token=xxx` | 获取全局历史消息 |

### 对话管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/conversations?token=xxx` | 创建/获取私聊对话 (Body: `{ target_user_id }`) |
| GET | `/conversations?token=xxx` | 获取当前用户的所有对话列表 |
| GET | `/conversations/{id}/messages?token=xxx` | 获取对话中的消息 |
| POST | `/conversations/{id}/agent?token=xxx` | 启用/禁用对话的 AI 助手 (Body: `{ active }`) |

### 实时通信

| 方法 | 路径 | 说明 |
|------|------|------|
| WS | `/ws/{user_id}?token=xxx` | WebSocket 聊天通道 |

**WebSocket 消息格式：**

```json
// 全局消息
{ "content": "消息内容" }

// 私聊消息
{ "content": "消息内容", "conversation_id": 1 }
```

---

## 架构设计

### 数据库模型

- **User** — 用户表 (id, nickname, password, ip_address)
- **Avatar** — 头像表 (user_id, image_path, emotion_tag)
- **Conversation** — 对话表 (id, is_group, agent_active, created_at)
- **ConversationParticipant** — 对话参与者 (conversation_id, user_id)
- **Message** — 消息表 (user_id, conversation_id, content, detected_emotion, timestamp)

### Agent 系统

| Agent | 文件 | 职责 |
|-------|------|------|
| 情绪分析 Agent | `agent.py` | 分析消息情绪，三级优化 (关键词 → 缓存 → API) |
| 聊天 Agent | `chat_agent.py` | 读取用户 skill.md + 最近 10 条消息，生成短句回复 |
| 总结 Agent | `summary_agent.py` | 每 10 条消息总结用户聊天风格，写入 skill.md |

### 消息路由

- `conversation_id = null` → 全局广播（所有在线用户可见）
- `conversation_id = N` → 仅发送给对话 N 的参与者
- Agent 回复使用 `user_id = 0`（AI助手），前端以紫色气泡区分显示
- 系统通知（加入/离开）通过 WebSocket 广播，不存入数据库

### 安全机制

- **密码安全**：所有密码使用 bcrypt 哈希存储
- **接口认证**：所有 API 和 WebSocket 连接均需 JWT Token
- **Token 有效期**：登录后 24 小时，刷新页面自动恢复会话
- **对话隔离**：私聊消息仅对话双方可见

---

## 常见问题

### 情绪分析/聊天 Agent 不工作

检查 `backend/.env` 中的 API Key 是否正确，API 地址是否可访问。查看后端日志中的错误信息。

### WebSocket 连接失败

确保后端已启动且端口正确。局域网部署时检查防火墙是否放行 8000 端口。

### 数据库迁移

运行 `python init_db.py` 会自动添加新字段，不会丢失已有数据。
