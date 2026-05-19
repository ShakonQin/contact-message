<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '../stores/userStore'
import { useChatStore } from '../stores/chatStore'

const emit = defineEmits(['close'])

const userStore = useUserStore()
const chatStore = useChatStore()

onMounted(() => {
  userStore.loadUsers()
})

const selectUser = async (user) => {
  await chatStore.startConversation(user.id)
  emit('close')
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="emit('close')">
    <div class="bg-white rounded-xl shadow-xl w-80 max-h-96 flex flex-col">
      <div class="p-4 border-b flex items-center justify-between">
        <h3 class="font-bold text-lg">选择聊天对象</h3>
        <button @click="emit('close')" class="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
      </div>
      <div class="flex-1 overflow-y-auto p-2">
        <div
          v-for="user in userStore.users"
          :key="user.id"
          @click="selectUser(user)"
          class="flex items-center p-3 rounded-lg cursor-pointer hover:bg-gray-100 transition"
        >
          <div class="w-9 h-9 rounded-full bg-gray-300 flex items-center justify-center text-white text-sm font-bold mr-3">
            {{ user.nickname.charAt(0) }}
          </div>
          <span class="text-sm">{{ user.nickname }}</span>
        </div>
        <div v-if="userStore.users.length === 0" class="text-center text-gray-400 text-sm py-8">
          暂无其他用户
        </div>
      </div>
    </div>
  </div>
</template>
