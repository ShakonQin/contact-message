<script setup>
import { ref, nextTick, watch } from 'vue'
import { useUserStore } from '../stores/userStore'
import { useChatStore } from '../stores/chatStore'
import MessageBubble from './MessageBubble.vue'

const userStore = useUserStore()
const chatStore = useChatStore()

const inputMessage = ref('')

const sendMessage = () => {
  if (chatStore.sendMessage(inputMessage.value)) {
    inputMessage.value = ''
  }
}

const scrollToBottom = async () => {
  await nextTick()
  const container = document.getElementById('chat-container')
  if (container) container.scrollTop = container.scrollHeight
}

watch(() => chatStore.messages.length, scrollToBottom)

const toggleAgent = () => {
  if (chatStore.activeConversationId !== null) {
    const conv = chatStore.conversations.find(c => c.conversation_id === chatStore.activeConversationId)
    if (conv) {
      chatStore.toggleAgent(conv.conversation_id, !conv.agent_active)
    }
  }
}

const currentAgentActive = () => {
  if (chatStore.activeConversationId === null) return true  // 全局默认启用
  const conv = chatStore.conversations.find(c => c.conversation_id === chatStore.activeConversationId)
  return conv?.agent_active || false
}
</script>

<template>
  <div class="w-3/4 flex flex-col bg-white">
    <!-- 对话头部 -->
    <div class="px-6 py-3 border-b bg-white flex items-center justify-between shrink-0">
      <div class="flex items-center">
        <button
          v-if="chatStore.activeConversationId !== null"
          @click="chatStore.selectGlobalChat()"
          class="mr-3 text-gray-400 hover:text-gray-600 text-lg"
        >
          &larr;
        </button>
        <div>
          <h3 class="font-bold text-base">{{ chatStore.activeConversationName }}</h3>
          <span v-if="chatStore.activeConversationId !== null" class="text-xs text-gray-400">私聊</span>
          <span v-else class="text-xs text-gray-400">所有人可见</span>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-xs text-gray-400">AI助手</span>
        <button
          v-if="chatStore.activeConversationId !== null"
          @click="toggleAgent"
          class="relative w-10 h-5 rounded-full transition-colors"
          :class="currentAgentActive() ? 'bg-purple-500' : 'bg-gray-300'"
        >
          <span
            class="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform"
            :class="currentAgentActive() ? 'left-5' : 'left-0.5'"
          ></span>
        </button>
        <span v-if="chatStore.activeConversationId === null" class="text-[10px] bg-purple-100 text-purple-600 px-1.5 py-0.5 rounded">始终启用</span>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="flex-1 overflow-y-auto p-6 space-y-6" id="chat-container">
      <MessageBubble
        v-for="(msg, index) in chatStore.messages"
        :key="index"
        :msg="msg"
        :isSelf="msg.user_id === userStore.currentUser.id"
        :isAgent="msg.user_id === 0"
      />
    </div>

    <!-- 输入框 -->
    <div class="p-4 border-t bg-white shrink-0">
      <div class="flex items-center space-x-3 bg-gray-50 p-2 rounded-xl border hover:border-blue-300 transition">
        <input
          v-model="inputMessage"
          @keyup.enter="sendMessage"
          type="text"
          class="flex-1 bg-transparent px-3 py-2 focus:outline-none"
          :placeholder="chatStore.activeConversationId !== null ? '发送私聊消息...' : '发送消息... @robot 唤起AI'"
        >
        <button @click="sendMessage" class="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition px-4">发送</button>
      </div>
    </div>
  </div>
</template>
