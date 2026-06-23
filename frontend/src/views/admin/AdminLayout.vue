<script setup>
import { useRouter, useRoute, RouterView } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

if (!auth.isLoggedIn) {
  router.replace('/admin/login')
}

const navItems = [
  { path: '/admin/persons', label: '群友管理' },
  { path: '/admin/groups', label: '群管理' },
]

function isActive(path) {
  return route.path.startsWith(path)
}

async function doLogout() {
  await auth.logout()
  router.replace('/admin/login')
}
</script>

<template>
  <div class="min-h-screen flex bg-gray-100">
    <!-- 左侧菜单 -->
    <aside class="w-56 bg-white border-r border-gray-200 flex flex-col shrink-0">
      <div class="px-5 py-4 border-b border-gray-100">
        <h1 class="text-base font-bold text-[#12b7f5]">记忆助手</h1>
        <p class="text-xs text-gray-400 mt-0.5">{{ auth.username }}</p>
      </div>
      <nav class="flex-1 py-2">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="[
            'block px-5 py-2.5 text-sm transition',
            isActive(item.path)
              ? 'bg-blue-50 text-[#12b7f5] font-medium border-r-2 border-[#12b7f5]'
              : 'text-gray-600 hover:bg-gray-50'
          ]"
        >{{ item.label }}</router-link>
      </nav>
      <div class="px-5 py-3 border-t border-gray-100">
        <button
          @click="doLogout"
          class="text-sm text-gray-400 hover:text-red-500 transition"
        >退出登录</button>
      </div>
    </aside>

    <!-- 右侧内容 -->
    <main class="flex-1 p-6 overflow-y-auto">
      <RouterView />
    </main>
  </div>
</template>
