<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useLabels } from '../../utils/labels'
import { api } from '../../api/client'

const router = useRouter()
const labels = useLabels()
const email = ref('')
const code = ref('')
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)
const sending = ref(false)
const cooldown = ref(0)
const registrationOpen = ref(true)
let cdTimer = null

onMounted(async () => {
  try {
    const cfg = await api.getPublicConfig()
    registrationOpen.value = cfg.registration_open !== '0'
  } catch {}
})

async function doSendCode() {
  if (!email.value || !email.value.includes('@')) {
    error.value = '请输入有效的邮箱地址'
    return
  }
  if (cooldown.value > 0) return
  error.value = ''
  sending.value = true
  try {
    await api.sendCode(email.value)
    cooldown.value = 60
    cdTimer = setInterval(() => {
      cooldown.value--
      if (cooldown.value <= 0) clearInterval(cdTimer)
    }, 1000)
  } catch (e) {
    error.value = e.message
  } finally {
    sending.value = false
  }
}

async function doRegister() {
  if (!email.value || !code.value) {
    error.value = '请填写邮箱和验证码'
    return
  }
  if (!username.value || !password.value) {
    error.value = '请填写用户名和密码'
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
    await api.registerEmail(email.value, code.value, username.value, password.value)
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
    <div class="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
      <div class="absolute -top-20 -right-20 w-72 h-72 rounded-full bg-pink-200/20 blur-3xl animate-float" style="animation-delay: 0s" />
      <div class="absolute top-1/3 -left-20 w-80 h-80 rounded-full bg-blue-200/20 blur-3xl animate-float" style="animation-delay: -2s" />
      <div class="absolute -bottom-20 right-1/3 w-64 h-64 rounded-full bg-pink-100/30 blur-3xl animate-float" style="animation-delay: -4s" />
    </div>

    <div v-if="!registrationOpen" class="relative animate-bounce-in bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm border border-pink-100 text-center">
      <p class="text-gray-600 mb-2">注册已关闭</p>
      <p class="text-gray-400 text-sm mb-4">请联系管理员手动添加账号</p>
      <router-link to="/login" class="text-primary hover:underline text-sm transition-colors">返回登录</router-link>
    </div>

    <div v-else class="relative animate-bounce-in bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm border border-pink-100">
      <h1 class="text-xl font-bold text-center mb-6 text-primary">{{ labels.registerTitle }}</h1>
      <div class="space-y-4 animate-stagger">
        <div>
          <div class="flex gap-2">
            <input v-model="email" type="email" placeholder="邮箱地址"
              class="flex-1 px-4 py-2.5 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:bg-pink-50/30 focus:scale-[1.02] focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]" />
            <button @click="doSendCode" :disabled="sending || cooldown > 0"
              class="px-4 py-2.5 bg-primary text-white text-sm rounded-xl transition-all duration-300 hover:bg-primary-dark active:scale-95 disabled:opacity-50 whitespace-nowrap"
              :class="{ 'animate-pulse-soft': cooldown === 0 && sending }">
              {{ cooldown > 0 ? cooldown + 's' : sending ? '发送中...' : '发送验证码' }}
            </button>
          </div>
        </div>
        <div>
          <input v-model="code" type="text" placeholder="6位验证码" maxlength="6"
            class="w-full px-4 py-2.5 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:bg-pink-50/30 focus:scale-[1.02] focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]"
            @keyup.enter="doRegister" />
        </div>
        <div>
          <input v-model="username" type="text" :placeholder="labels.usernamePlaceholder"
            class="w-full px-4 py-2.5 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:bg-pink-50/30 focus:scale-[1.02] focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]"
            @keyup.enter="doRegister" />
        </div>
        <div>
          <input v-model="password" type="password" :placeholder="labels.passwordHint"
            class="w-full px-4 py-2.5 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:bg-pink-50/30 focus:scale-[1.02] focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]"
            @keyup.enter="doRegister" />
        </div>
        <div>
          <input v-model="confirmPassword" type="password" :placeholder="labels.confirmPasswordPlaceholder"
            class="w-full px-4 py-2.5 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:bg-pink-50/30 focus:scale-[1.02] focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]"
            @keyup.enter="doRegister" />
        </div>
        <Transition name="error-fade">
          <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>
        </Transition>
        <Transition name="success-bounce">
          <p v-if="success" class="text-green-500 text-sm text-center font-medium">{{ success }}</p>
        </Transition>
        <button @click="doRegister" :disabled="loading"
          class="shimmer-overlay w-full py-2.5 bg-primary text-white rounded-xl font-medium transition-all duration-300 hover:bg-primary-dark hover:shadow-lg hover:shadow-primary/25 active:scale-95 disabled:opacity-50">
          {{ loading ? '注册中...' : labels.registerButton }}
        </button>
      </div>
      <p class="text-center text-sm text-gray-400 mt-5">
        {{ labels.hasAccount }}<router-link to="/login" class="text-primary hover:underline ml-1 transition-colors">{{ labels.loginButton }}</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.error-fade-enter-active, .error-fade-leave-active {
  transition: all 0.2s ease;
}
.error-fade-enter-from, .error-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
.success-bounce-enter-active {
  animation: bounceIn 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}
.success-bounce-leave-active {
  transition: all 0.2s ease;
}
.success-bounce-leave-to {
  opacity: 0;
}
</style>
