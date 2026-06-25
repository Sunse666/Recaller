<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useLabels } from '../../utils/labels'

const router = useRouter()
const auth = useAuthStore()
const labels = useLabels()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function doLogin() {
  if (!username.value || !password.value) {
    error.value = labels.value.loginValidation
    return
  }
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    if (auth.role === 'admin') {
      router.replace('/admin/dashboard')
    } else {
      router.replace(`/${auth.uid}/persons`)
    }
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
      <h1 class="text-xl font-bold text-center mb-6 text-primary">{{ labels.appTitle }}</h1>
      <div class="space-y-4">
        <div>
          <input
            v-model="username"
            type="text"
            :placeholder="labels.usernamePlaceholder"
            class="w-full px-4 py-2.5 text-sm border border-pink-100 rounded-lg outline-none focus:border-primary focus:bg-pink-50/30 transition"
            @keyup.enter="doLogin"
          />
        </div>
        <div>
          <input
            v-model="password"
            type="password"
            :placeholder="labels.passwordPlaceholder"
            class="w-full px-4 py-2.5 text-sm border border-pink-100 rounded-lg outline-none focus:border-primary focus:bg-pink-50/30 transition"
            @keyup.enter="doLogin"
          />
        </div>
        <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>
        <button
          @click="doLogin"
          :disabled="loading"
          class="w-full py-2.5 bg-primary text-white rounded-lg font-medium hover:bg-primary-dark disabled:opacity-50 transition"
        >
          {{ loading ? labels.loggingIn : labels.loginButton }}
        </button>
      </div>
      <p class="text-center text-sm text-gray-400 mt-4">
        {{ labels.noAccount }}<router-link to="/register" class="text-primary hover:underline">{{ labels.registerButton }}</router-link>
      </p>
    </div>
  </div>
</template>
