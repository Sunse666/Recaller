<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api/client'
import { useBoardStore } from '../../stores/boards'

const route = useRoute()
const router = useRouter()
const boardStore = useBoardStore()

const uid = route.params.uid
const user = ref(null)
const boards = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    user.value = null
    boards.value = await api.listBoards(uid)
    const allUsers = await api.adminListUsers({})
    user.value = allUsers.find(u => u.uid === uid) || null
  } catch (e) { alert('加载失败: ' + e.message) }
  finally { loading.value = false }
})

function goManageBoard(boardId) {
  boardStore.targetUid = uid
  boardStore.boards = boards.value
  boardStore.currentBoardId = boardId
  router.push(`/admin/users/${uid}/boards/${boardId}/persons`)
}

function goBack() {
  router.push('/admin/users')
}
</script>

<template>
  <div>
    <button @click="goBack" class="text-sm text-gray-400 hover:text-primary mb-4">&larr; 返回用户列表</button>

    <div v-if="loading" class="text-sm text-gray-400">加载中...</div>
    <div v-else-if="!user" class="text-sm text-gray-400">用户不存在</div>
    <div v-else>
      <div class="bg-white rounded-xl border border-gray-100 p-5 mb-6">
        <div class="flex items-center gap-4">
          <img v-if="user.avatar" :src="user.avatar" class="w-12 h-12 rounded-full object-cover" />
          <div v-else class="w-12 h-12 rounded-full bg-gradient-to-br from-pink-400 to-blue-400 flex items-center justify-center text-white text-lg font-bold">
            {{ (user.username || '?')[0].toUpperCase() }}
          </div>
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <h3 class="text-lg font-bold text-gray-900">{{ user.username }}</h3>
              <span :class="user.role === 'superadmin' ? 'bg-purple-100 text-purple-700' : user.role === 'admin' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'"
                class="px-2 py-0.5 rounded-full text-xs font-medium">{{ user.role === 'superadmin' ? '超级管理员' : user.role === 'admin' ? '管理员' : '用户' }}</span>
              <span :class="user.enabled ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
                class="px-2 py-0.5 rounded-full text-xs font-medium">{{ user.enabled ? '已启用' : '已禁用' }}</span>
            </div>
            <div class="flex gap-4 mt-1 text-xs text-gray-400">
              <span>UID: {{ user.uid }}</span>
              <span>注册: {{ user.created_at ? user.created_at.slice(0, 10) : '-' }}</span>
              <span>最后登录: {{ user.last_login ? user.last_login.slice(0, 10) : '从未' }}</span>
            </div>
            <div v-if="user.limits && Object.keys(user.limits).length > 0" class="flex gap-3 mt-2 text-xs">
              <span class="bg-gray-100 px-2 py-0.5 rounded">
                上传: {{ user.limits.upload_rate_per_min === 0 ? '不限' : user.limits.upload_rate_per_min + '次/分' }}
              </span>
              <span class="bg-gray-100 px-2 py-0.5 rounded">
                大小: {{ user.limits.upload_max_size_mb === 0 ? '不限' : user.limits.upload_max_size_mb + 'MB' }}
              </span>
              <span class="bg-gray-100 px-2 py-0.5 rounded">
                像素: {{ user.limits.upload_max_px === 0 ? '不限' : user.limits.upload_max_px + 'px' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <h3 class="text-base font-bold text-gray-800 mb-3">画板 ({{ boards.length }})</h3>
      <div v-if="boards.length === 0" class="text-sm text-gray-400">该用户暂无画板</div>
      <div v-else class="grid gap-3">
        <div v-for="b in boards" :key="b.id"
          class="flex items-center justify-between bg-white rounded-xl border border-gray-100 p-4 hover:border-pink-200 transition">
          <div class="flex items-center gap-3">
            <span class="text-2xl font-bold text-gray-400">{{ b.icon || '' }}</span>
            <div>
              <p class="font-medium text-gray-800">{{ b.name }}</p>
              <p class="text-xs text-gray-400">{{ b.board_type === 'image' ? '图组' : b.board_type === 'friend' ? '群友' : '说说' }} · {{ b.card_label || '图片' }} · {{ b.is_public ? '公开' : '私密' }}</p>
            </div>
          </div>
          <button @click="goManageBoard(b.id)"
            class="px-4 py-1.5 bg-primary text-white text-sm rounded-lg hover:bg-primary-dark transition">
            管理
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
