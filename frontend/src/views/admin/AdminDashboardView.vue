<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/client'

const stats = ref({
  total_users: 0, total_boards: 0, total_persons: 0, total_accounts: 0,
  new_users_7d: 0, new_persons_7d: 0, total_storage_bytes: 0, user_storage: [],
})

function fmtBytes(b) {
  if (b < 1024) return b + ' B'
  if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB'
  if (b < 1024 * 1024 * 1024) return (b / (1024 * 1024)).toFixed(1) + ' MB'
  return (b / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}

onMounted(async () => {
  try { stats.value = await api.adminDashboard() } catch {}
})
</script>

<template>
  <div>
    <h2 class="text-lg font-bold text-gray-900 mb-6">仪表盘</h2>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-5 border border-blue-200">
        <p class="text-3xl font-bold text-blue-700">{{ stats.total_users }}</p>
        <p class="text-sm text-blue-500 mt-1">总用户数</p>
        <p class="text-xs text-blue-400 mt-1">近7日 +{{ stats.new_users_7d }}</p>
      </div>
      <div class="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-5 border border-green-200">
        <p class="text-3xl font-bold text-green-700">{{ stats.total_boards }}</p>
        <p class="text-sm text-green-500 mt-1">总画板数</p>
      </div>
      <div class="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-5 border border-purple-200">
        <p class="text-3xl font-bold text-purple-700">{{ stats.total_persons }}</p>
        <p class="text-sm text-purple-500 mt-1">总联系人数</p>
        <p class="text-xs text-purple-400 mt-1">近7日 +{{ stats.new_persons_7d }}</p>
      </div>
      <div class="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-5 border border-orange-200">
        <p class="text-3xl font-bold text-orange-700">{{ fmtBytes(stats.total_storage_bytes) }}</p>
        <p class="text-sm text-orange-500 mt-1">存储总用量</p>
      </div>
    </div>

    <h3 class="text-base font-bold text-gray-800 mb-3">用户存储用量（TOP {{ stats.user_storage.length }}）</h3>
    <div v-if="stats.user_storage.length > 0" class="space-y-2">
      <div v-for="item in stats.user_storage" :key="item.uid"
        class="flex items-center justify-between px-4 py-3 bg-gray-50 rounded-lg text-sm">
        <span class="text-gray-700 font-medium">UID: {{ item.uid }}</span>
        <span class="text-gray-500">{{ fmtBytes(item.size_bytes) }}</span>
      </div>
    </div>
    <p v-else class="text-sm text-gray-400">暂无上传数据</p>
  </div>
</template>
