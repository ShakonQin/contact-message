import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useUserStore } from './userStore'

const BACKEND_URL = 'http://localhost:8000'
const WS_URL = 'ws://localhost:8000'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const conversations = ref([])
  const activeConversationId = ref(null)  // null = 全局聊天
  const wsConnected = ref(false)
  let socket = null
  let reconnectTimer = null

  const activeConversationName = computed(() => {
    if (activeConversationId.value === null) return '全局聊天'
    const conv = conversations.value.find(c => c.conversation_id === activeConversationId.value)
    return conv?.other_user?.nickname || '私聊'
  })

  function _fixAvatarUrl(msg) {
    if (msg.avatar && !msg.avatar.startsWith('http')) {
      msg.avatar = `${BACKEND_URL}${msg.avatar}`
    }
    return msg
  }

  // 加载对话列表
  async function loadConversations() {
    const userStore = useUserStore()
    try {
      const res = await fetch(`${BACKEND_URL}/conversations?token=${userStore.token}`)
      if (res.ok) {
        conversations.value = await res.json()
      }
    } catch (e) {
      console.error('加载对话列表失败:', e)
    }
  }

  // 切换到全局聊天
  async function selectGlobalChat() {
    activeConversationId.value = null
    await loadHistory()
  }

  // 切换到指定对话
  async function selectConversation(conversationId) {
    activeConversationId.value = conversationId
    await loadHistory()
  }

  // 发起新对话
  async function startConversation(targetUserId) {
    const userStore = useUserStore()
    try {
      const res = await fetch(`${BACKEND_URL}/conversations?token=${userStore.token}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_user_id: targetUserId }),
      })
      if (res.ok) {
        const data = await res.json()
        await loadConversations()
        await selectConversation(data.conversation_id)
        return data
      }
    } catch (e) {
      console.error('创建对话失败:', e)
    }
  }

  // 切换 Agent 状态
  async function toggleAgent(conversationId, active) {
    const userStore = useUserStore()
    try {
      const res = await fetch(`${BACKEND_URL}/conversations/${conversationId}/agent?token=${userStore.token}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active }),
      })
      if (res.ok) {
        const data = await res.json()
        const conv = conversations.value.find(c => c.conversation_id === conversationId)
        if (conv) conv.agent_active = data.agent_active
        return data
      }
    } catch (e) {
      console.error('切换 Agent 失败:', e)
    }
  }

  // 加载历史消息（根据当前活跃对话）
  async function loadHistory() {
    const userStore = useUserStore()
    try {
      let url
      if (activeConversationId.value === null) {
        url = `${BACKEND_URL}/history?limit=50&token=${userStore.token}`
      } else {
        url = `${BACKEND_URL}/conversations/${activeConversationId.value}/messages?limit=50&token=${userStore.token}`
      }
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        messages.value = data.map(msg => _fixAvatarUrl({ ...msg }))
      }
    } catch (e) {
      console.error('加载历史消息失败:', e)
    }
  }

  // WebSocket 连接
  function connectWebSocket() {
    const userStore = useUserStore()
    if (socket && socket.readyState === WebSocket.OPEN) return

    socket = new WebSocket(`${WS_URL}/ws/${userStore.currentUser.id}?token=${userStore.token}`)

    socket.onopen = () => {
      wsConnected.value = true
      console.log('WebSocket 已连接')
    }

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)

      // 系统通知（加入/离开）
      if (data.type === 'system') {
        messages.value.push({
          type: 'system',
          content: data.content,
          online_count: data.online_count,
          timestamp: new Date().toISOString(),
        })
        loadConversations()
        return
      }

      _fixAvatarUrl(data)

      // 如果消息属于当前活跃对话，添加到消息列表
      if (data.conversation_id === activeConversationId.value) {
        messages.value.push(data)
      } else if (data.conversation_id === undefined && activeConversationId.value === null) {
        // 兼容：旧格式全局消息
        messages.value.push(data)
      }

      // 更新对话列表中的最后消息预览
      const conv = conversations.value.find(c => c.conversation_id === data.conversation_id)
      if (conv) {
        conv.last_message = {
          content: data.content.slice(0, 50),
          timestamp: new Date().toISOString(),
          sender_nickname: data.nickname,
        }
      }
    }

    socket.onclose = () => {
      wsConnected.value = false
      console.log('WebSocket 断开连接，3秒后重连...')
      if (reconnectTimer) clearTimeout(reconnectTimer)
      reconnectTimer = setTimeout(() => {
        if (userStore.isLoggedIn) connectWebSocket()
      }, 3000)
    }

    socket.onerror = (err) => {
      console.error('WebSocket 错误:', err)
    }
  }

  // 发送消息
  function sendMessage(content) {
    if (!content.trim() || !socket || socket.readyState !== WebSocket.OPEN) return false
    const payload = { content }
    if (activeConversationId.value !== null) {
      payload.conversation_id = activeConversationId.value
    }
    socket.send(JSON.stringify(payload))
    return true
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (socket) {
      socket.close()
      socket = null
    }
    wsConnected.value = false
  }

  return {
    messages,
    conversations,
    activeConversationId,
    activeConversationName,
    wsConnected,
    loadConversations,
    selectGlobalChat,
    selectConversation,
    startConversation,
    toggleAgent,
    loadHistory,
    connectWebSocket,
    sendMessage,
    disconnect,
  }
})
