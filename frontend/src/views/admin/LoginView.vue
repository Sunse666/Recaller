<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useLabels } from '../../utils/labels'
import { api } from '../../api/client'

const router = useRouter()
const auth = useAuthStore()
const labels = useLabels()
const username = ref('')
const password = ref('')
const email = ref('')
const code = ref('')
const error = ref('')
const loading = ref(false)
const mode = ref('password')

const sending = ref(false)
const cooldown = ref(0)
let cdTimer = null

async function doSendLoginCode() {
  if (!email.value || !email.value.includes('@')) {
    error.value = '请输入有效的邮箱地址'; return
  }
  if (cooldown.value > 0) return
  error.value = ''; sending.value = true
  try {
    await api.sendLoginCode(email.value)
    cooldown.value = 60
    cdTimer = setInterval(() => { cooldown.value--; if (cooldown.value <= 0) clearInterval(cdTimer) }, 1000)
  } catch (e) { error.value = e.message }
  finally { sending.value = false }
}

async function doCodeLogin() {
  if (!email.value || !code.value) { error.value = '请填写邮箱和验证码'; return }
  error.value = ''; loading.value = true
  try {
    const data = await api.loginByCode(email.value, code.value)
    auth.username = data.username; auth.role = data.role || ''; auth.uid = data.uid || ''
    auth.verified = true
    localStorage.setItem('username', data.username)
    await auth.checkAuth()
    if (auth.role === 'admin' || auth.role === 'superadmin') router.replace('/admin/dashboard')
    else router.replace(`/${auth.uid}/persons`)
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}

async function doLogin() {
  if (!username.value || !password.value) { error.value = labels.value.loginValidation; return }
  error.value = ''; loading.value = true
  try {
    await auth.login(username.value, password.value)
    if (auth.role === 'admin' || auth.role === 'superadmin') router.replace('/admin/dashboard')
    else router.replace(`/${auth.uid}/persons`)
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-50 via-white to-blue-50">
    <div class="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
      <div class="absolute -top-20 -left-20 w-72 h-72 rounded-full bg-pink-200/20 blur-3xl animate-float" style="animation-delay: 0s" />
      <div class="absolute top-1/2 -right-20 w-80 h-80 rounded-full bg-blue-200/20 blur-3xl animate-float" style="animation-delay: -2s" />
      <div class="absolute -bottom-20 left-1/3 w-64 h-64 rounded-full bg-pink-100/30 blur-3xl animate-float" style="animation-delay: -4s" />
    </div>

    <div class="relative animate-bounce-in bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm border border-pink-100">
      <h1 class="text-xl font-bold text-center mb-6 text-primary">{{ labels.appTitle }}</h1>

      <div class="flex mb-5 border-b border-gray-100 relative">
        <button @click="mode = 'password'; error = ''"
          class="flex-1 pb-2.5 text-sm transition-colors duration-300 relative"
          :class="mode === 'password' ? 'text-primary font-medium' : 'text-gray-400 hover:text-gray-500'"
        >密码登录</button>
        <button @click="mode = 'code'; error = ''"
          class="flex-1 pb-2.5 text-sm transition-colors duration-300 relative"
          :class="mode === 'code' ? 'text-primary font-medium' : 'text-gray-400 hover:text-gray-500'"
        >验证码登录</button>
        <div class="absolute bottom-0 h-0.5 bg-primary rounded-full transition-all duration-300 ease-out"
          :style="{ left: mode === 'password' ? '0%' : '50%', width: '50%' }"
        />
      </div>

      <Transition name="form-slide" mode="out-in">
        <div v-if="mode === 'password'" key="pwd" class="space-y-4">
          <input v-model="username" type="text" placeholder="用户名或邮箱" @keyup.enter="doLogin"
            class="w-full px-4 py-2.5 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:bg-pink-50/30 focus:scale-[1.02] focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]" />
          <input v-model="password" type="password" :placeholder="labels.passwordPlaceholder" @keyup.enter="doLogin"
            class="w-full px-4 py-2.5 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:bg-pink-50/30 focus:scale-[1.02] focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]" />
          <Transition name="error-fade">
            <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>
          </Transition>
          <button @click="doLogin" :disabled="loading"
            class="shimmer-overlay w-full py-2.5 bg-primary text-white rounded-xl font-medium transition-all duration-300 hover:bg-primary-dark hover:shadow-lg hover:shadow-primary/25 active:scale-95 disabled:opacity-50">
            {{ loading ? labels.loggingIn : labels.loginButton }}
          </button>
        </div>

        <div v-if="mode === 'code'" key="code" class="space-y-4">
          <div class="flex gap-2">
            <input v-model="email" type="email" placeholder="邮箱地址"
              class="flex-1 px-4 py-2.5 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:bg-pink-50/30 focus:scale-[1.02] focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]" />
            <button @click="doSendLoginCode" :disabled="sending || cooldown > 0"
              class="px-4 py-2.5 bg-primary text-white text-sm rounded-xl transition-all duration-300 hover:bg-primary-dark active:scale-95 disabled:opacity-50 whitespace-nowrap"
              :class="{ 'animate-pulse-soft': cooldown === 0 && sending }">
              {{ cooldown > 0 ? cooldown + 's' : '发送验证码' }}
            </button>
          </div>
          <input v-model="code" type="text" placeholder="6位验证码" maxlength="6" @keyup.enter="doCodeLogin"
            class="w-full px-4 py-2.5 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:bg-pink-50/30 focus:scale-[1.02] focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]" />
          <Transition name="error-fade">
            <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>
          </Transition>
          <button @click="doCodeLogin" :disabled="loading"
            class="shimmer-overlay w-full py-2.5 bg-primary text-white rounded-xl font-medium transition-all duration-300 hover:bg-primary-dark hover:shadow-lg hover:shadow-primary/25 active:scale-95 disabled:opacity-50">
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </div>
      </Transition>

      <p class="text-center text-sm text-gray-400 mt-5">
        {{ labels.noAccount }}<router-link to="/register" class="text-primary hover:underline ml-1 transition-colors">{{ labels.registerButton }}</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.form-slide-enter-active, .form-slide-leave-active {
  transition: all 0.3s ease-out;
}
.form-slide-enter-from {
  opacity: 0;
  transform: translateX(30px);
}
.form-slide-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

.error-fade-enter-active, .error-fade-leave-active {
  transition: all 0.2s ease;
}
.error-fade-enter-from, .error-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
