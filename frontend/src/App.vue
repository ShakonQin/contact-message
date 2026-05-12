<script setup>
import { ref, nextTick } from 'vue';

// --- 配置区域 ---
const BACKEND_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000';

const currentUser = ref(null);
const loginForm = ref({ nickname: '', password: '' });
const uploadForm = ref({ emotion: 'happy' });
const selectedFile = ref(null);
const uploadPreview = ref(null);
const messages = ref([]);
const inputMessage = ref("");
const wsConnected = ref(false);
let socket = null;
let reconnectTimer = null;

// 1. 注册/登录
const register = async () => {
  if (!loginForm.value.nickname.trim()) return alert("请输入昵称");
  if (!loginForm.value.password.trim()) return alert("请输入密码");

  const formData = new FormData();
  formData.append('nickname', loginForm.value.nickname);
  formData.append('password', loginForm.value.password);

  try {
    const res = await fetch(`${BACKEND_URL}/register`, {
      method: 'POST',
      body: formData
    });

    const data = await res.json();

    if (res.ok) {
      currentUser.value = data;
      await loadHistory();
      connectWebSocket();
    } else {
      alert("注册失败: " + (data.detail || "未知错误"));
    }
  } catch (e) {
    console.error(e);
    alert("连接后端失败，请确保后端已启动！");
  }
};

// 2. 加载历史消息
const loadHistory = async () => {
  try {
    const res = await fetch(`${BACKEND_URL}/history?limit=50`);
    if (res.ok) {
      const data = await res.json();
      messages.value = data.map(msg => ({
        ...msg,
        avatar: msg.avatar && !msg.avatar.startsWith('http')
          ? `${BACKEND_URL}${msg.avatar}`
          : msg.avatar
      }));
    }
  } catch (e) {
    console.error("加载历史消息失败:", e);
  }
};

// 3. WebSocket 连接（带断线重连）
const connectWebSocket = () => {
  if (socket && socket.readyState === WebSocket.OPEN) return;

  socket = new WebSocket(`${WS_URL}/ws/${currentUser.value.id}`);

  socket.onopen = () => {
    wsConnected.value = true;
    console.log("WebSocket 已连接");
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    // 如果头像路径是相对路径，需要加上后端地址前缀
    if (data.avatar && !data.avatar.startsWith('http')) {
      data.avatar = `${BACKEND_URL}${data.avatar}`;
    }

    messages.value.push(data);
    scrollToBottom();
  };

  socket.onclose = () => {
    wsConnected.value = false;
    console.log("WebSocket 断开连接，3秒后重连...");
    if (reconnectTimer) clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(() => {
      if (currentUser.value) connectWebSocket();
    }, 3000);
  };

  socket.onerror = (err) => {
    console.error("WebSocket 错误:", err);
  };
};

// 4. 发送消息
const sendMessage = () => {
  if (!inputMessage.value.trim() || !socket || socket.readyState !== WebSocket.OPEN) return;

  socket.send(JSON.stringify({ content: inputMessage.value }));
  inputMessage.value = "";
};

// 5. 文件选择
const handleFileSelect = (event) => {
  const file = event.target.files[0];
  if (file) {
    selectedFile.value = file;
    uploadPreview.value = URL.createObjectURL(file);
  }
};

// 6. 上传头像
const uploadAvatar = async () => {
  if (!selectedFile.value) return;

  const formData = new FormData();
  formData.append('user_id', currentUser.value.id);
  formData.append('emotion', uploadForm.value.emotion);
  formData.append('file', selectedFile.value);

  try {
    const res = await fetch(`${BACKEND_URL}/upload_avatar`, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.status === 'success') {
      alert(`上传成功！情绪 [${uploadForm.value.emotion}] 已绑定。`);
      selectedFile.value = null;
      uploadPreview.value = null;
    } else {
      alert("上传失败: " + (data.detail || "未知错误"));
    }
  } catch (e) {
    alert("上传失败");
  }
};

const scrollToBottom = async () => {
  await nextTick();
  const container = document.getElementById('chat-container');
  if (container) container.scrollTop = container.scrollHeight;
};
</script>

<template>
  <div class="bg-gray-100 h-screen overflow-hidden flex items-center justify-center font-sans">

    <div class="w-full max-w-4xl h-[90vh] bg-white rounded-2xl shadow-2xl overflow-hidden flex relative">

      <!-- 登录/注册页面 -->
      <div v-if="!currentUser" class="absolute inset-0 z-50 bg-white flex flex-col items-center justify-center p-8">
        <div class="w-full max-w-md space-y-6 text-center">
          <h1 class="text-4xl font-bold text-blue-600">局域网情绪聊天室</h1>
          <div class="bg-gray-50 p-6 rounded-xl border border-gray-200">
            <input v-model="loginForm.nickname" type="text" class="w-full px-4 py-2 rounded-lg border mb-4" placeholder="你的昵称">
            <input v-model="loginForm.password" type="password" class="w-full px-4 py-2 rounded-lg border" placeholder="密码">
          </div>
          <button @click="register" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl">进入</button>
        </div>
      </div>

      <!-- 左侧栏：用户信息 + 头像上传 -->
      <div v-if="currentUser" class="w-1/4 bg-gray-50 border-r border-gray-200 flex flex-col">
        <div class="p-6 border-b text-center">
          <h2 class="font-bold text-xl">{{ currentUser.nickname }}</h2>
          <p class="text-xs text-gray-500">ID: {{ currentUser.id }}</p>
          <div class="flex items-center justify-center mt-2">
            <span class="w-2 h-2 rounded-full mr-1" :class="wsConnected ? 'bg-green-500' : 'bg-red-500'"></span>
            <span class="text-xs text-gray-400">{{ wsConnected ? '已连接' : '未连接' }}</span>
          </div>
        </div>
        <div class="p-4 space-y-4">
          <div class="bg-white p-4 rounded-xl shadow-sm border">
            <h3 class="text-sm font-bold mb-3">上传情绪头像</h3>
            <select v-model="uploadForm.emotion" class="w-full mb-3 p-2 text-sm border rounded">
              <option value="happy">Happy</option>
              <option value="sad">Sad</option>
              <option value="angry">Angry</option>
              <option value="surprised">Surprised</option>
              <option value="neutral">Neutral</option>
            </select>
            <div class="relative w-full h-32 border-2 border-dashed rounded-lg flex items-center justify-center cursor-pointer hover:border-blue-500 overflow-hidden">
              <input type="file" @change="handleFileSelect" accept="image/png,image/jpeg,image/gif" class="absolute inset-0 opacity-0 cursor-pointer z-10">
              <img v-if="uploadPreview" :src="uploadPreview" class="absolute inset-0 w-full h-full object-cover">
              <span v-else class="text-gray-400 text-xs">点击上传</span>
            </div>
            <button @click="uploadAvatar" :disabled="!selectedFile" class="w-full mt-3 bg-gray-800 text-white text-sm py-2 rounded-lg disabled:opacity-50 hover:bg-gray-700">保存</button>
          </div>
        </div>
      </div>

      <!-- 右侧：聊天区域 -->
      <div v-if="currentUser" class="w-3/4 flex flex-col bg-white">
        <div class="flex-1 overflow-y-auto p-6 space-y-6" id="chat-container">
          <div v-for="(msg, index) in messages" :key="index" class="flex w-full" :class="msg.user_id === currentUser.id ? 'justify-end' : 'justify-start'">

            <div v-if="msg.user_id !== currentUser.id" class="mr-3 flex flex-col items-center">
              <img :src="msg.avatar || '/static/default_avatar.svg'" class="w-10 h-10 rounded-full border-2 border-white shadow object-cover" @error="$event.target.src='/static/default_avatar.svg'">
              <span class="text-[10px] bg-gray-100 rounded-full px-1 mt-1 text-gray-500">{{ msg.emotion }}</span>
            </div>

            <div class="max-w-[70%]">
              <div v-if="msg.user_id !== currentUser.id" class="text-xs text-gray-500 mb-1 ml-1">{{ msg.nickname }}</div>
              <div class="px-5 py-3 rounded-2xl shadow-sm text-sm break-words"
                   :class="msg.user_id === currentUser.id ? 'bg-blue-600 text-white rounded-br-none' : 'bg-gray-100 text-gray-800 rounded-bl-none'">
                {{ msg.content }}
              </div>
            </div>

            <div v-if="msg.user_id === currentUser.id" class="ml-3 flex flex-col items-center">
              <img :src="msg.avatar || '/static/default_avatar.svg'" class="w-10 h-10 rounded-full border-2 border-white shadow object-cover" @error="$event.target.src='/static/default_avatar.svg'">
              <span class="text-[10px] bg-gray-100 rounded-full px-1 mt-1 text-gray-500">{{ msg.emotion }}</span>
            </div>
          </div>
        </div>

        <div class="p-4 border-t bg-white">
          <div class="flex items-center space-x-3 bg-gray-50 p-2 rounded-xl border hover:border-blue-300 transition">
            <input v-model="inputMessage" @keyup.enter="sendMessage" type="text" class="flex-1 bg-transparent px-3 py-2 focus:outline-none" placeholder="输入消息... AI 会分析你的情绪">
            <button @click="sendMessage" class="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition px-4">发送</button>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>
