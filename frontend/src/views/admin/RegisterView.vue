<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)

async function doRegister() {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致'
    return
  }
  if (password.value.length < 8) {
    error.value = '密码长度不能少于8位'
    return
  }
  error.value = ''
  success.value = ''
  loading.value = true
  try {
    await auth.register(username.value, password.value)
    success.value = '注册成功！即将跳转到登录页...'
    setTimeout(() => router.push('/login'), 1500)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-50 via-white to-blue-50">
    <div class="bg-white rounded-xl shadow-lg p-8 w-full max-w-sm border border-pink-100">
      <h1 class="text-xl font-bold text-center mb-6 text-primary">注册账号</h1>
      <div class="space-y-4">
        <div>
          <input
            v-model="username"
            type="text" placeholder="用户名"
            class="w-full px-4 py-2.5 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary focus:bg-pink-50/30 transition"
            @keyup.enter="doRegister"
          />
        </div>
        <div>
          <input
            v-model="password"
            type="password" placeholder="密码（至少8位，含字母和数字）"
            class="w-full px-4 py-2.5 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary focus:bg-pink-50/30 transition"
            @keyup.enter="doRegister"
          />
        </div>
        <div>
          <input
            v-model="confirmPassword"
            type="password" placeholder="确认密码"
            class="w-full px-4 py-2.5 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary focus:bg-pink-50/30 transition"
            @keyup.enter="doRegister"
          />
        </div>
        <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>
        <p v-if="success" class="text-green-500 text-sm">{{ success }}</p>
        <button
          @click="doRegister"
          :disabled="loading"
          class="w-full py-2.5 bg-primary text-white rounded-xl font-medium hover:bg-primary-dark disabled:opacity-50 transition"
        >
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </div>
      <p class="text-center text-sm text-gray-400 mt-4">
        已有账号？<router-link to="/login" class="text-primary hover:underline">登录</router-link>
      </p>
    </div>
  </div>
</template>
