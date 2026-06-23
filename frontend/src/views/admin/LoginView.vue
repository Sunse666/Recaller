<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function doLogin() {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.replace('/admin/persons')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <div class="bg-white rounded-xl shadow-sm p-8 w-full max-w-sm">
      <h1 class="text-xl font-bold text-center mb-6">群友记忆助手 · 管理后台</h1>
      <div class="space-y-4">
        <div>
          <input
            v-model="username"
            type="text"
            placeholder="用户名"
            class="w-full px-4 py-2.5 text-sm border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]"
            @keyup.enter="doLogin"
          />
        </div>
        <div>
          <input
            v-model="password"
            type="password"
            placeholder="密码"
            class="w-full px-4 py-2.5 text-sm border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]"
            @keyup.enter="doLogin"
          />
        </div>
        <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>
        <button
          @click="doLogin"
          :disabled="loading"
          class="w-full py-2.5 bg-[#12b7f5] text-white rounded-lg font-medium hover:bg-[#0ea0db] disabled:opacity-50 transition"
        >
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </div>
    </div>
  </div>
</template>
