<script setup>
import { ref } from 'vue'
import { useUserStore } from '../stores/userStore'

const BACKEND_URL = 'http://localhost:8000'

const userStore = useUserStore()

const uploadForm = ref({ emotion: 'happy' })
const selectedFile = ref(null)
const uploadPreview = ref(null)
const uploading = ref(false)

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
    uploadPreview.value = URL.createObjectURL(file)
  }
}

const uploadAvatar = async () => {
  if (!selectedFile.value) return
  uploading.value = true

  const formData = new FormData()
  formData.append('user_id', userStore.currentUser.id)
  formData.append('emotion', uploadForm.value.emotion)
  formData.append('file', selectedFile.value)
  formData.append('token', userStore.token)

  try {
    const res = await fetch(`${BACKEND_URL}/upload_avatar`, {
      method: 'POST',
      body: formData
    })
    const data = await res.json()
    if (data.status === 'success') {
      alert(`上传成功！情绪 [${uploadForm.value.emotion}] 已绑定。`)
      selectedFile.value = null
      uploadPreview.value = null
    } else {
      alert('上传失败: ' + (data.detail || '未知错误'))
    }
  } catch (e) {
    alert('上传失败')
  } finally {
    uploading.value = false
  }
}
</script>

<template>
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
    <button @click="uploadAvatar" :disabled="!selectedFile || uploading" class="w-full mt-3 bg-gray-800 text-white text-sm py-2 rounded-lg disabled:opacity-50 hover:bg-gray-700">
      {{ uploading ? '上传中...' : '保存' }}
    </button>
  </div>
</template>
