```
LAN-Chat-App/
├── backend/                   # 后端代码
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # 程序入口 (FastAPI + WebSocket)
│   │   ├── models.py          # SQLAlchemy 数据库模型
│   │   ├── database.py        # 数据库连接与会话管理
│   │   ├── schemas.py         # Pydantic 模型
│   │   ├── crud.py            # 数据库 CRUD 操作
│   │   └── agent.py           # AI 情绪分析引擎
│   ├── static/                # 静态资源目录
│   │   ├── avatars/           # 用户上传的头像文件存放在这里
│   │   └── default_avatar.svg # 默认头像
│   ├── chat.db                # SQLite 数据库文件
│   ├── requirements.txt       # Python 依赖列表
│   ├── .env                   # 环境变量 (不提交到 Git)
│   └── init_db.py             # 初始化数据库
│
├── frontend/                  # 前端代码 (Vue 3)
│   ├── src/
│   │   ├── App.vue            # 聊天主界面
│   │   ├── main.js
│   │   └── style.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
└── README.md                  # 项目说明文档
```

---

## 项目简介

这是一个**局域网情绪聊天室**应用。核心功能：

1. 用户通过昵称+密码注册/登录
2. 用户为不同情绪标签（happy/sad/angry/surprised/neutral）上传对应头像
3. 发送消息时，AI（Qwen3-8B via ModelScope API）自动分析消息情绪
4. 根据分析结果自动切换该条消息显示的头像
5. 所有消息通过 WebSocket 实时广播给局域网内所有在线用户

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| 数据库 | SQLite + SQLAlchemy 2.x |
| AI 引擎 | OpenAI SDK (调用 ModelScope Qwen3-8B) |
| 实时通信 | WebSocket |
| 前端框架 | Vue 3 + Vite |
| 样式 | Tailwind CSS |

### AI 情绪分析策略

采用**两级分析**策略以降低延迟和 API 调用成本：

1. **关键词前置过滤**：内置情绪关键词库，短消息或强情绪词直接命中，零延迟返回结果
2. **AI API 分析**：关键词未命中时，调用 Qwen3-8B 模型，结合最近 10 条历史消息上下文进行情绪判断

---

## 本地部署步骤

### 1. 下载依赖

**后端依赖：**

```bash
cd backend
pip install -r requirements.txt
```

**前端依赖：**

需要先安装 Node.js 和 npm，然后在 frontend 目录下运行：

```bash
cd frontend
npm install
```

如果发现缺少依赖，可以尝试删除 `node_modules` 文件夹和 `package-lock.json` 文件，然后重新运行 `npm install`。或者手动安装：

```bash
npm install -D tailwindcss@3.4.17 postcss autoprefixer
```

### 2. 初始化数据库

在 backend 目录下运行以下命令来创建并初始化 SQLite 数据库：

```bash
python init_db.py
```

### 3. 配置模型 API

在 `backend/.env` 文件中，配置你的 ModelScope API 密钥：

```
MODELSCOPE_API_KEY=your_api_key_here
MODELSCOPE_MODEL=Qwen/Qwen3-8B
```

将 `MODELSCOPE_API_KEY` 替换为你从 ModelScope 获取的 API 密钥。

### 4. 启动服务

**启动后端**（数据库 + AI + WebSocket）：

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**启动前端**（界面）：

```bash
cd frontend
npm run dev
```

访问 http://localhost:5173 即可使用聊天应用。打开多个浏览器窗口可测试多用户聊天。

---

## 局域网内互联

### 第一步：获取局域网 IP

- **Windows**: 打开 PowerShell，输入 `ipconfig`，找到无线或以太网适配器的 IPv4 地址（如 `192.168.1.5`）
- **macOS/Linux**: 终端输入 `ifconfig` 或 `ip addr`

记下这个 IP（以下称为 `HOST_IP`）。

### 第二步：修改前端配置

打开 `frontend/src/App.vue`，修改配置区域：

```javascript
// --- 配置区域 ---
const HOST_IP = '192.168.1.5'; // 替换为你的局域网 IP
const BACKEND_URL = `http://${HOST_IP}:8000`;
const WS_URL = `ws://${HOST_IP}:8000`;
```

### 第三步：重启服务

**后端：**

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**前端：**

```bash
npm run dev -- --host
```

---

## 使用说明

1. 输入昵称和密码进入聊天室（新用户自动注册，老用户验证登录）
2. 在左侧栏选择情绪标签，上传对应的头像图片（建议上传 5 种情绪的头像以获得最佳体验）
3. 在聊天窗口输入消息，AI 会自动分析你的情绪并切换头像
4. 页面刷新后会自动加载最近 50 条历史消息
5. WebSocket 断开后会自动重连（3 秒间隔）

---

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/register` | 注册/登录（FormData: nickname, password） |
| POST | `/upload_avatar` | 上传头像（FormData: user_id, emotion, file） |
| GET | `/history?limit=50` | 获取历史消息（带头像 URL） |
| WS | `/ws/{user_id}` | WebSocket 聊天通道 |
