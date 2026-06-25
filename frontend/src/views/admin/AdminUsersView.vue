<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { api } from '../../api/client'

const router = useRouter()
const auth = useAuthStore()
const users = ref([])
const search = ref('')
const roleFilter = ref('')
const enabledFilter = ref(null)
const loading = ref(false)

async function fetchUsers() {
  loading.value = true
  try {
    const params = {}
    if (search.value) params.search = search.value
    if (roleFilter.value) params.role = roleFilter.value
    if (enabledFilter.value !== null) params.enabled = enabledFilter.value
    users.value = await api.adminListUsers(params)
  } catch (e) { alert('加载失败: ' + e.message) }
  finally { loading.value = false }
}

onMounted(fetchUsers)

function doSearch() { fetchUsers() }
function resetFilters() { search.value = ''; roleFilter.value = ''; enabledFilter.value = null; fetchUsers() }

const showDialog = ref(false)
const dialogMode = ref('create')
const defaultLimits = { upload_rate_per_min: 10, upload_max_size_mb: 10, upload_max_px: 2048 }
const dialogForm = ref({ username: '', password: '', uid: '', role: 'user', enabled: true, limits: { ...defaultLimits } })
const dialogUid = ref('')
const dialogTitle = computed(() => dialogMode.value === 'create' ? '添加用户' : '编辑用户')

function openCreate() {
  dialogMode.value = 'create'
  dialogForm.value = { username: '', password: '', uid: '', role: 'user', enabled: true, limits: { ...defaultLimits } }
  dialogUid.value = ''
  showDialog.value = true
}

function openEdit(u) {
  dialogMode.value = 'edit'
  const tl = u.limits && Object.keys(u.limits).length > 0 ? u.limits : defaultLimits
  dialogForm.value = {
    username: u.username, password: '', role: u.role, enabled: u.enabled,
    limits: { ...tl },
  }
  dialogUid.value = u.uid
  showDialog.value = true
}

async function submitDialog() {
  if (dialogMode.value === 'create') {
    if (!dialogForm.value.password) { alert('请输入密码'); return }
    await api.adminCreateUser(dialogForm.value)
  } else {
    const data = {}
    if (dialogForm.value.username) data.username = dialogForm.value.username
    if (dialogForm.value.role) data.role = dialogForm.value.role
    if (dialogForm.value.enabled !== undefined) data.enabled = dialogForm.value.enabled
    if (dialogForm.value.limits) data.limits = dialogForm.value.limits
    await api.adminUpdateUser(dialogUid.value, data)
  }
  showDialog.value = false
  fetchUsers()
}

async function doDelete(u) {
  if (!confirm(`确定删除用户「${u.username}」及其所有数据？此操作不可恢复。`)) return
  try { await api.adminDeleteUser(u.uid); fetchUsers() }
  catch (e) { alert('删除失败: ' + e.message) }
}

async function doResetPwd(u) {
  if (!confirm(`确定重置用户「${u.username}」的密码？`)) return
  try {
    const r = await api.adminResetPassword(u.uid)
    alert(`密码已重置。\n新密码：${r.new_password}\n请将此密码告知用户。`)
  } catch (e) { alert('重置失败: ' + e.message) }
}

async function doForceLogout(u) {
  if (!confirm(`确定强制下线用户「${u.username}」？`)) return
  try { await api.adminForceLogout(u.uid); alert('已强制下线') }
  catch (e) { alert('操作失败: ' + e.message) }
}

function goToUser(u) {
  router.push(`/admin/users/${u.uid}`)
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-lg font-bold text-gray-900">用户管理</h2>
      <button @click="openCreate" class="px-4 py-2 bg-primary text-white text-sm rounded-xl hover:bg-primary-dark transition">
        + 添加用户
      </button>
    </div>

    <div class="flex flex-wrap items-center gap-3 mb-4">
      <div class="flex items-center gap-2">
        <input v-model="search" @keyup.enter="doSearch" placeholder="搜索用户名..."
          class="px-3 py-1.5 text-sm border border-gray-200 rounded-lg outline-none focus:border-primary w-48" />
      </div>
      <select v-model="roleFilter" @change="doSearch" class="px-3 py-1.5 text-sm border border-gray-200 rounded-lg outline-none">
        <option value="">全部角色</option>
        <option value="superadmin">超级管理员</option>
        <option value="admin">管理员</option>
        <option value="user">普通用户</option>
      </select>
      <select v-model="enabledFilter" @change="doSearch" class="px-3 py-1.5 text-sm border border-gray-200 rounded-lg outline-none">
        <option :value="null">全部状态</option>
        <option :value="true">已启用</option>
        <option :value="false">已禁用</option>
      </select>
      <button @click="resetFilters" class="px-3 py-1.5 text-sm text-gray-500 hover:text-primary">重置</button>
    </div>

    <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-gray-500">
          <tr>
            <th class="px-4 py-3 text-left font-medium">用户</th>
            <th class="px-4 py-3 text-left font-medium">角色</th>
            <th class="px-4 py-3 text-left font-medium">状态</th>
            <th class="px-4 py-3 text-left font-medium">画板数</th>
            <th class="px-4 py-3 text-left font-medium">注册时间</th>
            <th class="px-4 py-3 text-left font-medium">最后登录</th>
            <th class="px-4 py-3 text-right font-medium">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.uid" class="border-t border-gray-50 hover:bg-gray-50/50">
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <img v-if="u.avatar" :src="u.avatar" class="w-7 h-7 rounded-full object-cover" />
                <div v-else class="w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center text-xs text-gray-500 font-bold">
                  {{ (u.username || '?')[0].toUpperCase() }}
                </div>
                <span class="font-medium text-gray-800">{{ u.username }}</span>
              </div>
            </td>
            <td class="px-4 py-3">
              <span :class="u.role === 'superadmin' ? 'bg-purple-100 text-purple-700' : u.role === 'admin' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'"
                class="px-2 py-0.5 rounded-full text-xs font-medium">{{ u.role === 'superadmin' ? '超级管理员' : u.role === 'admin' ? '管理员' : '用户' }}</span>
            </td>
            <td class="px-4 py-3">
              <span :class="u.enabled ? 'text-green-600' : 'text-red-500'">{{ u.enabled ? '启用' : '禁用' }}</span>
              <span v-if="u.limits && Object.keys(u.limits).some(k => u.limits[k] !== 10 && u.limits[k] !== 2048 && u.limits[k] !== 0)"
                class="ml-1 text-yellow-500 text-xs font-bold" title="自定义限额">*</span>
            </td>
            <td class="px-4 py-3 text-gray-600">{{ u.board_count }}</td>
            <td class="px-4 py-3 text-gray-500 text-xs">{{ u.created_at ? u.created_at.slice(0, 10) : '-' }}</td>
            <td class="px-4 py-3 text-gray-500 text-xs">{{ u.last_login ? u.last_login.slice(0, 10) : '从未' }}</td>
            <td class="px-4 py-3 text-right">
              <div class="flex items-center justify-end gap-1">
                <button @click="goToUser(u)" class="px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded">查看</button>
                <button @click="openEdit(u)" class="px-2 py-1 text-xs text-primary hover:bg-pink-50 rounded">编辑</button>
                <button @click="doResetPwd(u)" class="px-2 py-1 text-xs text-orange-600 hover:bg-orange-50 rounded">重置密码</button>
                <button @click="doForceLogout(u)" class="px-2 py-1 text-xs text-yellow-600 hover:bg-yellow-50 rounded">强制下线</button>
                <button @click="doDelete(u)" class="px-2 py-1 text-xs text-red-500 hover:bg-red-50 rounded">删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="users.length === 0 && !loading">
            <td colspan="7" class="px-4 py-12 text-center text-gray-400">暂无用户数据</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showDialog" class="fixed inset-0 bg-black/30 flex items-center justify-center z-50" @click.self="showDialog = false">
      <div class="bg-white rounded-2xl p-6 w-full max-w-sm shadow-xl">
        <h3 class="text-lg font-bold text-gray-900 mb-4">{{ dialogTitle }}</h3>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-gray-500 block mb-1">用户名</label>
            <input v-model="dialogForm.username" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl outline-none focus:border-primary" />
          </div>
          <div v-if="dialogMode === 'create'">
            <label class="text-xs text-gray-500 block mb-1">密码</label>
            <input v-model="dialogForm.password" type="text" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl outline-none focus:border-primary" />
          </div>
          <div v-if="dialogMode === 'create'">
            <label class="text-xs text-gray-500 block mb-1">UID（留空自动分配，从 11 开始）</label>
            <input v-model="dialogForm.uid" placeholder="自动分配" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl outline-none focus:border-primary" />
          </div>
          <div v-if="dialogMode === 'create' || auth.isAdmin">
            <label class="text-xs text-gray-500 block mb-1">角色</label>
            <select v-model="dialogForm.role" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl outline-none">
              <option value="user">普通用户</option>
              <option value="admin">管理员</option>
              <option v-if="auth.role === 'superadmin'" value="superadmin">超级管理员</option>
            </select>
          </div>
          <div class="flex items-center gap-2">
            <input type="checkbox" v-model="dialogForm.enabled" id="dlg-enabled" class="rounded" />
            <label for="dlg-enabled" class="text-sm text-gray-700">启用账号</label>
          </div>
          <hr class="border-gray-100" />
          <p class="text-xs font-medium text-gray-500">上传限制（0 = 不限）</p>
          <div class="grid grid-cols-3 gap-2">
            <div>
              <label class="text-xs text-gray-400 block">每分钟次数</label>
              <input v-model.number="dialogForm.limits.upload_rate_per_min" type="number" min="0"
                class="w-full px-2 py-1.5 text-sm border border-gray-200 rounded-lg outline-none focus:border-primary" />
            </div>
            <div>
              <label class="text-xs text-gray-400 block">文件大小(MB)</label>
              <input v-model.number="dialogForm.limits.upload_max_size_mb" type="number" min="0"
                class="w-full px-2 py-1.5 text-sm border border-gray-200 rounded-lg outline-none focus:border-primary" />
            </div>
            <div>
              <label class="text-xs text-gray-400 block">最大像素</label>
              <input v-model.number="dialogForm.limits.upload_max_px" type="number" min="0"
                class="w-full px-2 py-1.5 text-sm border border-gray-200 rounded-lg outline-none focus:border-primary" />
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-5">
          <button @click="showDialog = false" class="px-4 py-2 text-sm text-gray-500 hover:text-gray-700">取消</button>
          <button @click="submitDialog" class="px-4 py-2 bg-primary text-white text-sm rounded-xl hover:bg-primary-dark">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>
