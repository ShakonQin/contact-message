```
LAN-Chat-App/
├── backend/                   # 后端代码
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # 程序入口 
│   │   ├── models.py          # 数据库模型 
│   │   ├── database.py        # 数据库连接与会话管理
│   │   ├── schemas.py         # Pydantic 模型 
│   │   ├── crud.py            # 数据库操作
│   │   └── agent.py           # AI 核心 
│   ├── static/                # 静态资源目录
│   │   └── avatars/           # 用户上传的头像文件存放在这里 
│   ├── chat.db                # SQLite 数据库文件 
│   ├── requirements.txt       # Python 依赖列表
│   ├── .env                   # 环境变量
│   └── init_db.py             # 初始化数据库
│
├── frontend/                  # 前端代码 (Vue.js)
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   └── HellowWorld.vue # 聊天主窗口
│   │   ├── services/
│   │   │   └── socket.js      # WebSocket 连接逻辑
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
│
└── README.md                  # 项目说明文档
```
### 本地部署步骤：  
#### 首先下载必要的依赖：
1. 后端依赖：  
```Bash
cd backend
pip install -r requirements.txt
```
2. 前端依赖：  
需要先安装 Node.js 和 npm，然后在 frontend 目录下运行：
```Bash
cd frontend
npm install
```
如果发现npm install下载完成后，运行时，提示缺少依赖，可以尝试删除 node_modules 文件夹和 package-lock.json 文件，然后重新运行 npm install。  
或者使用以下命令强制安装特定版本：
```Bash
npm install -D tailwindcss@3.4.17 postcss autoprefixer
```
#### 初始化数据库
在 backend 目录下运行以下命令来创建并初始化 SQLite 数据库：

```Bash
python init_db.py
```
#### 配置模型API
在 backend/.env 文件中，找到以下行：

```
MODELSCOPE_API_KEY=ms # Replace with your actual ModelScope API key
MODELSCOPE_MODEL=Qwen/Qwen3-8B # Replace with your desired ModelScope model
```
将 MODELSCOPE_API_KEY 替换为你从 ModelScope 获取的 API 密钥，将 MODELSCOPE_MODEL 替换为你想使用的模型名称（例如 Qwen/Qwen3-8B）。

#### 启动服务
启动后端 (数据库+ AI + WebSocket)：  
打开一个终端窗口，进入 backend 目录：  

```Bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
启动前端 (界面)：  
打开另一个终端窗口，进入 frontend 目录：

```Bash
npm run dev
```
现在已经成功在本地运行了后端和前端，你可以在浏览器中访问 http://localhost:5173 来使用聊天应用。
本地运行多个浏览器窗口或标签页，访问 http://localhost:5173 来测试多用户聊天功能。
如果有局域网的访问需求，请继续往下看。

#### 局域网内互联
##### 第一步：获取你的局域网 IP
1. 打开一个新的终端 (PowerShell 或 CMD)。
2. 输入命令：ipconfig
3. 找到 无线局域网适配器 WLAN (如果你是用 Wi-Fi) 或者 以太网适配器 (如果你插网线)。
4. 找到 IPv4 地址 一行，它通常长这样：192.168.x.x (例如 192.168.1.5)。
记下这个 IP，我们后面叫它 HOST_IP。
##### 第二步：修改前端配置 
目前的 frontend/src/App.vue 里写的是 localhost。
打开 frontend/src/App.vue。
找到最上面的配置区域，修改如下（把 192.168.1.5 换成你刚才查到的真实 IP）：
```javascript
// --- 配置区域 ---
// 必须改成局域网 IP，否则其他人连不上后端
const HOST_IP = '192.168.1.5'; // <--- 这里填你的 IPv4 地址

const BACKEND_URL = `http://${HOST_IP}:8000`; 
const WS_URL = `ws://${HOST_IP}:8000`;
```

##### 第三步：重启服务 (开启局域网模式)
修改完代码后，我们需要用特定的命令重启前后端，允许外部连接。
1. 后端 (Backend)  
在后端终端运行（注意 --host 0.0.0.0 是关键，表示“对所有人开放”）：

```PowerShell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
2.  前端 (Frontend)  
在前端终端运行（注意 -- --host 是关键，让 Vite 暴露服务）：

```PowerShell
npm run dev -- --host
```

### 使用说明  
使用时，选择对应情绪标签后上传图像。  
之后再聊天天窗口输入消息，AI 会根据你的聊天语气来为你更换头像。  
默认只有一个聊天窗口，为局域网内的所有人共享。