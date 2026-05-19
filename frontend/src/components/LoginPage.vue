<script setup>
import { ref } from 'vue'
import { useUserStore } from '../stores/userStore'
import { useChatStore } from '../stores/chatStore'

const userStore = useUserStore()
const chatStore = useChatStore()

const loginForm = ref({ nickname: '', password: '' })
const loading = ref(false)
const errorMsg = ref('')

const handleLogin = async () => {
  if (!loginForm.value.nickname.trim()) return (errorMsg.value = '请输入昵称')
  if (!loginForm.value.password.trim()) return (errorMsg.value = '请输入密码')

  loading.value = true
  errorMsg.value = ''

  try {
    await userStore.login(loginForm.value.nickname, loginForm.value.password)
    await chatStore.loadConversations()
    await chatStore.loadHistory()
    chatStore.connectWebSocket()
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="absolute inset-0 z-50 bg-white flex flex-col items-center justify-center p-8">
    <div class="w-full max-w-md space-y-6 text-center">
      <h1 class="text-4xl font-bold text-blue-600">聊天室</h1>
      <div class="bg-gray-50 p-6 rounded-xl border border-gray-200">
        <input v-model="loginForm.nickname" type="text" class="w-full px-4 py-2 rounded-lg border mb-4" placeholder="你的昵称">
        <input v-model="loginForm.password" type="password" class="w-full px-4 py-2 rounded-lg border" placeholder="密码" @keyup.enter="handleLogin">
      </div>
      <p v-if="errorMsg" class="text-red-500 text-sm">{{ errorMsg }}</p>
      <button @click="handleLogin" :disabled="loading" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl disabled:opacity-50">
        {{ loading ? '连接中...' : '进入' }}
      </button>
    </div>
  </div>
</template>
