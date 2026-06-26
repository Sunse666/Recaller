<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/client'

const logs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const username = ref('')
const action = ref('')
const targetType = ref('')
const loading = ref(false)

const actionOptions = ['', 'create', 'update', 'delete']
const targetOptions = ['', 'user', 'board', 'person', 'account', 'group', 'membership', 'relation', 'meeting', 'nickname_history', 'config']

async function fetchLogs() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (username.value) params.username = username.value
    if (action.value) params.action = action.value
    if (targetType.value) params.target_type = targetType.value
    const r = await api.adminAuditLogs(params)
    logs.value = r.items
    total.value = r.total
  } catch (e) { alert('加载失败: ' + e.message) }
  finally { loading.value = false }
}

function resetFilters() {
  username.value = ''; action.value = ''; targetType.value = ''; page.value = 1
  fetchLogs()
}
function goPage(p) { page.value = p; fetchLogs() }

const totalPages = () => Math.ceil(total.value / pageSize.value) || 1

onMounted(fetchLogs)
</script>

<template>
  <div>
    <h2 class="text-lg font-bold text-gray-900 mb-6">审计日志</h2>

    <div class="flex flex-wrap items-center gap-3 mb-4">
      <input v-model="username" @keyup.enter="fetchLogs" placeholder="操作人..."
        class="px-3 py-1.5 text-sm border border-gray-200 rounded-lg outline-none focus:border-primary w-36 sm:w-44" />
      <select v-model="action" @change="fetchLogs" class="px-3 py-1.5 text-sm border border-gray-200 rounded-lg outline-none">
        <option value="">全部操作</option>
        <option v-for="a in actionOptions.filter(Boolean)" :key="a" :value="a">{{ a }}</option>
      </select>
      <select v-model="targetType" @change="fetchLogs" class="px-3 py-1.5 text-sm border border-gray-200 rounded-lg outline-none">
        <option value="">全部对象</option>
        <option v-for="t in targetOptions.filter(Boolean)" :key="t" :value="t">{{ t }}</option>
      </select>
      <button @click="resetFilters" class="px-3 py-1.5 text-sm text-gray-500 hover:text-primary">重置</button>
      <span class="text-xs text-gray-400 ml-auto">共 {{ total }} 条</span>
    </div>

    <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <div class="overflow-x-auto">
      <table class="w-full text-sm min-w-[600px]">
        <thead class="bg-gray-50 text-gray-500">
          <tr>
            <th class="px-4 py-3 text-left font-medium">时间</th>
            <th class="px-4 py-3 text-left font-medium">用户</th>
            <th class="px-4 py-3 text-left font-medium">操作</th>
            <th class="px-4 py-3 text-left font-medium">对象类型</th>
            <th class="px-4 py-3 text-left font-medium">详情</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in logs" :key="log.id" class="border-t border-gray-50 hover:bg-gray-50/50">
            <td class="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">
              {{ log.created_at ? log.created_at.slice(0, 19) : '-' }}
            </td>
            <td class="px-4 py-3 text-gray-700">{{ log.username }}</td>
            <td class="px-4 py-3">
              <span :class="{
                'bg-green-100 text-green-700': log.action === 'create',
                'bg-blue-100 text-blue-700': log.action === 'update',
                'bg-red-100 text-red-700': log.action === 'delete',
              }" class="px-2 py-0.5 rounded-full text-xs font-medium">{{ log.action }}</span>
            </td>
            <td class="px-4 py-3 text-gray-600">{{ log.target_type }}</td>
            <td class="px-4 py-3 text-gray-500 text-xs max-w-xs truncate">
              {{ log.details ? JSON.stringify(log.details) : '-' }}
            </td>
          </tr>
          <tr v-if="logs.length === 0 && !loading">
            <td colspan="5" class="px-4 py-12 text-center text-gray-400">暂无日志</td>
          </tr>
        </tbody>
      </table>
      </div>
    </div>

    <div v-if="totalPages() > 1" class="flex items-center justify-center gap-2 mt-4">
      <button @click="goPage(page - 1)" :disabled="page <= 1"
        class="px-3 py-1 text-sm border rounded-lg disabled:opacity-30 hover:bg-gray-50">上一页</button>
      <span class="text-sm text-gray-500">{{ page }} / {{ totalPages() }}</span>
      <button @click="goPage(page + 1)" :disabled="page >= totalPages()"
        class="px-3 py-1 text-sm border rounded-lg disabled:opacity-30 hover:bg-gray-50">下一页</button>
    </div>
  </div>
</template>
