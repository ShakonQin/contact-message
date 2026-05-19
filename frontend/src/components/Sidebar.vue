<script setup>
import { ref } from 'vue'
import { useUserStore } from '../stores/userStore'
import { useChatStore } from '../stores/chatStore'
import AvatarUploader from './AvatarUploader.vue'
import ConversationList from './ConversationList.vue'
import UserSelect from './UserSelect.vue'

const userStore = useUserStore()
const chatStore = useChatStore()

const showUserSelect = ref(false)
const showAvatarUploader = ref(false)

const handleLogout = () => {
  chatStore.disconnect()
  userStore.logout()
}
</script>

<template>
  <div class="w-1/4 bg-gray-50 border-r border-gray-200 flex flex-col">
    <!-- 用户信息 -->
    <div class="p-4 border-b text-center shrink-0">
      <h2 class="font-bold text-lg">{{ userStore.currentUser.nickname }}</h2>
      <p class="text-xs text-gray-500">ID: {{ userStore.currentUser.id }}</p>
      <div class="flex items-center justify-center mt-1">
        <span class="w-2 h-2 rounded-full mr-1" :class="chatStore.wsConnected ? 'bg-green-500' : 'bg-red-500'"></span>
        <span class="text-xs text-gray-400">{{ chatStore.wsConnected ? '已连接' : '未连接' }}</span>
      </div>
    </div>

    <!-- 对话列表 -->
    <ConversationList @showUserSelect="showUserSelect = true" />

    <!-- 头像上传折叠 -->
    <div class="border-t">
      <button
        @click="showAvatarUploader = !showAvatarUploader"
        class="w-full px-4 py-2 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition text-left"
      >
        {{ showAvatarUploader ? '收起头像设置 ▲' : '头像设置 ▼' }}
      </button>
      <div v-if="showAvatarUploader" class="p-4 pt-0">
        <AvatarUploader />
      </div>
    </div>

    <!-- 退出 -->
    <div class="p-3 border-t shrink-0">
      <button @click="handleLogout" class="w-full text-sm text-gray-500 hover:text-red-500 py-1 transition">退出登录</button>
    </div>
  </div>

  <!-- 用户选择弹窗 -->
  <UserSelect v-if="showUserSelect" @close="showUserSelect = false" />
</template>
