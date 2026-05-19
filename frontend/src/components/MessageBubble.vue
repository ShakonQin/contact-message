<script setup>
const props = defineProps({
  msg: { type: Object, required: true },
  isSelf: { type: Boolean, required: true },
  isAgent: { type: Boolean, default: false }
})
</script>

<template>
  <!-- 系统通知 -->
  <div v-if="msg.type === 'system'" class="flex justify-center w-full">
    <span class="text-xs text-gray-400 bg-gray-50 px-3 py-1 rounded-full">{{ msg.content }}</span>
  </div>

  <div v-else class="flex w-full" :class="isSelf ? 'justify-end' : 'justify-start'">

    <!-- 对方头像（非自己） -->
    <div v-if="!isSelf" class="mr-3 flex flex-col items-center">
      <div v-if="isAgent" class="w-10 h-10 rounded-full bg-purple-500 flex items-center justify-center text-white text-lg border-2 border-white shadow">
        AI
      </div>
      <img v-else :src="msg.avatar || '/static/default_avatar.svg'" class="w-10 h-10 rounded-full border-2 border-white shadow object-cover" @error="$event.target.src='/static/default_avatar.svg'">
      <span class="text-[10px] rounded-full px-1 mt-1"
        :class="isAgent ? 'bg-purple-100 text-purple-600' : 'bg-gray-100 text-gray-500'">
        {{ isAgent ? 'AI' : msg.emotion }}
      </span>
    </div>

    <!-- 消息气泡 -->
    <div class="max-w-[70%]">
      <div v-if="!isSelf" class="text-xs mb-1 ml-1" :class="isAgent ? 'text-purple-500 font-medium' : 'text-gray-500'">
        {{ isAgent ? 'AI助手' : msg.nickname }}
      </div>
      <div class="px-5 py-3 rounded-2xl shadow-sm text-sm break-words"
           :class="{
             'bg-blue-600 text-white rounded-br-none': isSelf,
             'bg-purple-100 text-purple-900 rounded-bl-none': isAgent,
             'bg-gray-100 text-gray-800 rounded-bl-none': !isSelf && !isAgent,
           }">
        {{ msg.content }}
      </div>
    </div>

    <!-- 自己头像 -->
    <div v-if="isSelf" class="ml-3 flex flex-col items-center">
      <img :src="msg.avatar || '/static/default_avatar.svg'" class="w-10 h-10 rounded-full border-2 border-white shadow object-cover" @error="$event.target.src='/static/default_avatar.svg'">
      <span class="text-[10px] bg-gray-100 rounded-full px-1 mt-1 text-gray-500">{{ msg.emotion }}</span>
    </div>
  </div>
</template>
