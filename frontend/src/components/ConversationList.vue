<script setup>
import { useChatStore } from '../stores/chatStore'
import { useUserStore } from '../stores/userStore'

const emit = defineEmits(['showUserSelect'])

const chatStore = useChatStore()
const userStore = useUserStore()

const selectGlobal = () => {
  chatStore.selectGlobalChat()
}

const selectConv = (conv) => {
  chatStore.selectConversation(conv.conversation_id)
}
</script>

<template>
  <div class="flex-1 overflow-y-auto">
    <div class="p-2">
      <!-- 全局聊天 -->
      <div
        @click="selectGlobal"
        class="flex items-center p-3 rounded-lg cursor-pointer transition mb-1"
        :class="chatStore.activeConversationId === null ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-100'"
      >
        <div class="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white text-sm font-bold mr-3">
          全
        </div>
        <div class="flex-1 min-w-0">
          <div class="font-medium text-sm">全局聊天</div>
          <div class="text-xs text-gray-400 truncate">
            {{ chatStore.activeConversationId === null ? '当前' : '所有人可见' }}
          </div>
        </div>
      </div>

      <!-- 私聊对话列表 -->
      <div
        v-for="conv in chatStore.conversations"
        :key="conv.conversation_id"
        @click="selectConv(conv)"
        class="flex items-center p-3 rounded-lg cursor-pointer transition mb-1"
        :class="chatStore.activeConversationId === conv.conversation_id ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-100'"
      >
        <div class="w-10 h-10 rounded-full bg-gray-400 flex items-center justify-center text-white text-sm font-bold mr-3">
          {{ conv.other_user?.nickname?.charAt(0) || '?' }}
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between">
            <span class="font-medium text-sm">{{ conv.other_user?.nickname || '未知' }}</span>
            <span v-if="conv.agent_active" class="text-[10px] bg-purple-100 text-purple-600 px-1 rounded">AI</span>
          </div>
          <div class="text-xs text-gray-400 truncate">
            {{ conv.last_message?.content || '暂无消息' }}
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 新建对话按钮 -->
  <div class="p-3 border-t">
    <button
      @click="emit('showUserSelect')"
      class="w-full py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition text-gray-600"
    >
      + 新对话
    </button>
  </div>
</template>
