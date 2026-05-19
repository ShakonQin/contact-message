<script setup>
import { onMounted } from 'vue'
import { useUserStore } from './stores/userStore'
import { useChatStore } from './stores/chatStore'
import LoginPage from './components/LoginPage.vue'
import Sidebar from './components/Sidebar.vue'
import ChatRoom from './components/ChatRoom.vue'

const userStore = useUserStore()
const chatStore = useChatStore()

onMounted(() => {
  userStore.restoreSession()
  if (userStore.isLoggedIn) {
    chatStore.loadConversations()
    chatStore.loadHistory()
    chatStore.connectWebSocket()
  }
})
</script>

<template>
  <div class="bg-gray-100 h-screen overflow-hidden flex items-center justify-center font-sans">
    <div class="w-full max-w-4xl h-[90vh] bg-white rounded-2xl shadow-2xl overflow-hidden flex relative">

      <LoginPage v-if="!userStore.isLoggedIn" />

      <template v-else>
        <Sidebar />
        <ChatRoom />
      </template>

    </div>
  </div>
</template>
