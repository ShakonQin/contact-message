import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const BACKEND_URL = 'http://localhost:8000'

export const useUserStore = defineStore('user', () => {
  const currentUser = ref(null)
  const token = ref(null)
  const users = ref([])

  const isLoggedIn = computed(() => !!currentUser.value && !!token.value)

  function restoreSession() {
    const saved = sessionStorage.getItem('chat_session')
    if (saved) {
      try {
        const data = JSON.parse(saved)
        currentUser.value = data.user
        token.value = data.token
      } catch (e) {
        sessionStorage.removeItem('chat_session')
      }
    }
  }

  async function login(nickname, password) {
    const formData = new FormData()
    formData.append('nickname', nickname)
    formData.append('password', password)

    const res = await fetch(`${BACKEND_URL}/register`, {
      method: 'POST',
      body: formData
    })

    const data = await res.json()

    if (!res.ok) {
      throw new Error(data.detail || '登录失败')
    }

    currentUser.value = data.user
    token.value = data.access_token

    sessionStorage.setItem('chat_session', JSON.stringify({
      user: data.user,
      token: data.access_token
    }))

    return data.user
  }

  async function loadUsers() {
    if (!token.value) return
    try {
      const res = await fetch(`${BACKEND_URL}/users?token=${token.value}`)
      if (res.ok) {
        users.value = await res.json()
      }
    } catch (e) {
      console.error('加载用户列表失败:', e)
    }
  }

  function logout() {
    currentUser.value = null
    token.value = null
    users.value = []
    sessionStorage.removeItem('chat_session')
  }

  return { currentUser, token, users, isLoggedIn, restoreSession, login, loadUsers, logout }
})
