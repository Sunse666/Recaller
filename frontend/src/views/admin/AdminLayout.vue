<script setup>
import { ref, onMounted, computed, provide } from 'vue'
import { useRouter, useRoute, RouterView } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useBoardStore } from '../../stores/boards'
import { useLabels } from '../../utils/labels'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const boardStore = useBoardStore()
const labels = useLabels()

if (!auth.isLoggedIn) {
  router.replace('/login')
}

provide('currentBoardId', computed(() => boardStore.currentBoardId))

const navItems = computed(() => [
  { path: '/admin/persons', label: labels.value.cardManage },
  { path: '/admin/groups', label: labels.value.groupManage },
  { path: '/admin/settings', label: '画板设置' },
])

function isActive(path) {
  return route.path.startsWith(path)
}

async function doLogout() {
  await auth.logout()
  router.replace('/login')
}

function switchBoard(boardId) {
  boardStore.setCurrentBoard(Number(boardId))
}

const showNewBoard = ref(false)
const newBoardName = ref('')
const newBoardIcon = ref('')

async function createBoard() {
  if (!newBoardName.value.trim()) return
  await boardStore.createBoard({
    name: newBoardName.value.trim(),
    icon: newBoardIcon.value || '📋',
    card_label: boardStore.currentBoard?.card_label || '群友',
    cards_label: boardStore.currentBoard?.cards_label || '群友们',
    group_label: boardStore.currentBoard?.group_label || '群',
    groups_label: boardStore.currentBoard?.groups_label || '群组',
  })
  newBoardName.value = ''
  newBoardIcon.value = ''
  showNewBoard.value = false
}

onMounted(async () => {
  const ok = await auth.checkAuth()
  if (!ok) {
    router.replace('/login')
    return
  }
  await boardStore.fetchBoards()
})
</script>

<template>
  <div class="min-h-screen flex bg-gradient-to-br from-pink-50/50 via-white to-blue-50/50 p-4 gap-4">
    <aside class="w-56 bg-white rounded-2xl border border-pink-100 flex flex-col shrink-0 shadow-sm overflow-hidden">
      <div class="px-5 py-5 border-b border-pink-50 bg-gradient-to-r from-pink-50 to-white">
        <h1 class="text-base font-bold text-primary">记忆助手</h1>
        <p class="text-xs text-gray-400 mt-0.5">{{ auth.username }}</p>
      </div>

      <div class="px-3 py-2 border-b border-pink-50">
        <select
          v-if="boardStore.boards.length > 0"
          :value="boardStore.currentBoardId"
          @change="switchBoard(($event.target).value)"
          class="w-full text-sm px-3 py-2 border border-pink-100 rounded-xl outline-none bg-white focus:border-primary transition"
        >
          <option v-for="b in boardStore.boards" :key="b.id" :value="b.id">
            {{ b.icon || '📋' }} {{ b.name }}
          </option>
        </select>
        <button @click="showNewBoard = !showNewBoard" class="w-full text-xs text-primary hover:underline mt-1 text-center">
          {{ showNewBoard ? labels.cancel : '+ 新建画板' }}
        </button>
        <div v-if="showNewBoard" class="mt-2 flex gap-1">
          <input v-model="newBoardIcon" placeholder="📋" class="w-10 px-2 py-1.5 text-sm border border-pink-100 rounded-lg outline-none focus:border-primary" maxlength="2" />
          <input v-model="newBoardName" placeholder="画板名称" class="flex-1 px-2 py-1.5 text-sm border border-pink-100 rounded-lg outline-none focus:border-primary" @keyup.enter="createBoard" />
          <button @click="createBoard" class="px-2 py-1.5 bg-primary text-white text-xs rounded-lg hover:bg-primary-dark">{{ labels.save }}</button>
        </div>
      </div>

      <nav class="flex-1 py-2 px-2">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="[
            'block px-4 py-2.5 text-sm rounded-xl transition',
            isActive(item.path)
              ? 'bg-primary text-white font-medium shadow-sm'
              : 'text-gray-600 hover:bg-pink-50'
          ]"
        >{{ item.label }}</router-link>
      </nav>
      <div class="px-5 py-3 border-t border-pink-50">
        <button
          @click="doLogout"
          class="text-sm text-gray-400 hover:text-primary transition"
        >退出登录</button>
      </div>
    </aside>

    <main class="flex-1 overflow-y-auto bg-white rounded-2xl border border-pink-100 shadow-sm p-6">
      <RouterView />
    </main>
  </div>
</template>
