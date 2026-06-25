<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useLabels } from '../../utils/labels'
import { api } from '../../api/client'

const router = useRouter()
const auth = useAuthStore()
const labels = useLabels()
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)
const registrationOpen = ref(true)

onMounted(async () => {
  try {
    const cfg = await api.getPublicConfig()
    registrationOpen.value = cfg.registration_open !== '0'
  } catch {}
})

async function doRegister() {
  if (!username.value || !password.value) {
    error.value = labels.value.registerValidation
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = labels.value.passwordMismatch
    return
  }
  if (password.value.length < 8) {
    error.value = labels.value.passwordTooShort
    return
  }
  error.value = ''
  success.value = ''
  loading.value = true
  try {
    await auth.register(username.value, password.value)
    success.value = labels.value.registerSuccess
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
    <div v-if="!registrationOpen" class="bg-white rounded-xl shadow-lg p-8 w-full max-w-sm border border-pink-100 text-center">
      <p class="text-gray-600 mb-2">注册已关闭</p>
      <p class="text-gray-400 text-sm mb-4">请联系管理员手动添加账号</p>
      <router-link to="/login" class="text-primary hover:underline text-sm">返回登录</router-link>
    </div>

    <div v-else class="bg-white rounded-xl shadow-lg p-8 w-full max-w-sm border border-pink-100">
      <h1 class="text-xl font-bold text-center mb-6 text-primary">{{ labels.registerTitle }}</h1>
      <div class="space-y-4">
        <div>
          <input
            v-model="username"
            type="text" :placeholder="labels.usernamePlaceholder"
            class="w-full px-4 py-2.5 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary focus:bg-pink-50/30 transition"
            @keyup.enter="doRegister"
          />
        </div>
        <div>
          <input
            v-model="password"
            type="password" :placeholder="labels.passwordHint"
            class="w-full px-4 py-2.5 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary focus:bg-pink-50/30 transition"
            @keyup.enter="doRegister"
          />
        </div>
        <div>
          <input
            v-model="confirmPassword"
            type="password" :placeholder="labels.confirmPasswordPlaceholder"
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
          {{ loading ? labels.registering : labels.registerButton }}
        </button>
      </div>
      <p class="text-center text-sm text-gray-400 mt-4">
        {{ labels.hasAccount }}<router-link to="/login" class="text-primary hover:underline">{{ labels.loginButton }}</router-link>
      </p>
    </div>
  </div>
</template>
