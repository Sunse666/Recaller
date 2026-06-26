<script setup>
import { ref, onMounted, computed, provide, watch } from 'vue'
import { useRouter, useRoute, RouterView } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useBoardStore } from '../../stores/boards'
import { useLabels, TYPE_DEFAULTS } from '../../utils/labels'
import { getThumbUrl } from '../../utils/images'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const boardStore = useBoardStore()
const labels = useLabels()
const mobileSidebarOpen = ref(false)
const sidebarReady = ref(false)
function closeSidebar() { mobileSidebarOpen.value = false }

provide('currentBoardId', computed(() => boardStore.currentBoardId))

const isAdmin = computed(() => auth.verified && (auth.role === 'admin' || auth.role === 'superadmin'))
const basePath = computed(() => {
  const uid = route.params.uid
  return uid ? `/${uid}` : '/admin'
})

const adminUserUid = computed(() => route.path.match(/^\/admin\/users\/(\d+)\/boards/) ? route.params.uid : null)
const adminBoardId = computed(() => adminUserUid.value ? route.params.boardId : null)

const navItems = computed(() => {
  if (adminUserUid.value) {
    const bu = `/admin/users/${adminUserUid.value}/boards/${adminBoardId.value}`
    return [
      { path: `${bu}/persons`, label: labels.value.cardManage },
      { path: `${bu}/settings`, label: labels.value.settingsTitle },
      { path: `${bu}/images`, label: labels.value.imagesTitle },
    ]
  }
  if (isAdmin.value) {
    return [
      { path: '/admin/dashboard', label: '仪表盘' },
      { path: '/admin/users', label: '用户管理' },
      { path: '/admin/persons', label: labels.value.cardManage },
      { path: '/admin/settings', label: labels.value.settingsTitle },
      { path: '/admin/images', label: labels.value.imagesTitle },
      { path: '/admin/audit', label: '审计日志' },
      { path: '/admin/system', label: '系统设置' },
    ]
  }
  const b = basePath.value
  return [
    { path: `${b}/persons`, label: labels.value.cardManage },
    { path: `${b}/settings`, label: labels.value.settingsTitle },
    { path: `${b}/images`, label: labels.value.imagesTitle },
  ]
})

function isActive(path) {
  if (adminUserUid.value) return route.path.startsWith(path)
  if (isAdmin.value) return route.path === path
  return route.path.startsWith(path)
}

async function doLogout() {
  await auth.logout()
  router.replace('/login')
}

function switchBoard(boardId) {
  boardStore.setCurrentBoard(Number(boardId))
  if (adminUserUid.value) {
    router.push(`/admin/users/${adminUserUid.value}/boards/${boardId}/persons`)
  }
}

const showNewBoard = ref(false)
const newBoardName = ref('')
const newBoardIcon = ref('')
const newBoardType = ref('image')

const editingUser = ref(false)
const newUserName = ref('')
function doChangeUsername() {
  editingUser.value = false
  const name = newUserName.value.trim()
  if (!name || name === auth.username) return
  auth.changeUsername(name).catch(e => alert(labels.value.usernameChangeFail + ': ' + e.message))
}

async function createBoard() {
  if (!newBoardName.value.trim()) return
  const td = TYPE_DEFAULTS[newBoardType.value] || TYPE_DEFAULTS.image
  await boardStore.createBoard({
    name: newBoardName.value.trim(),
    icon: newBoardIcon.value || td.icon,
    card_label: td.card_label,
    cards_label: td.cards_label,
    group_label: td.group_label,
    groups_label: td.groups_label,
    board_type: newBoardType.value,
  })
  newBoardName.value = ''
  newBoardIcon.value = ''
  newBoardType.value = 'image'
  showNewBoard.value = false
}

async function loadBoards() {
  if (adminUserUid.value) {
    await boardStore.fetchBoards(adminUserUid.value)
    if (adminBoardId.value) {
      boardStore.setCurrentBoard(Number(adminBoardId.value))
    }
  } else if (boardStore.targetUid) {
    await boardStore.fetchOwnBoards()
  } else {
    await boardStore.fetchBoards()
  }
}

const isManagementPage = computed(() => {
  const name = route.name
  if (!name) return false
  return name.endsWith('-persons') || name.endsWith('-settings') || name.endsWith('-images') || name.startsWith('admin-user-board-')
})

watch(isManagementPage, (isMgmt, wasMgmt) => {
  if (isMgmt && !wasMgmt) {
    loadBoards()
  }
  if (!isMgmt && wasMgmt && boardStore.targetUid) {
    boardStore.fetchOwnBoards()
  }
})

onMounted(async () => {
  const isProfilePage = route.name === 'user-profile' || route.name === 'user-person-detail'
  const ok = await auth.checkAuth()
  if (!ok && !isProfilePage) {
    router.replace('/login')
    return
  }
  if (!isProfilePage && route.name !== 'user-person-detail') {
    await loadBoards()
  }
  requestAnimationFrame(() => { sidebarReady.value = true })
})
</script>

<template>
  <div v-if="route.name === 'user-profile' || route.name === 'user-person-detail'" class="min-h-screen">
    <RouterView />
  </div>

  <div v-else class="min-h-screen flex bg-gradient-to-br from-pink-50/50 via-white to-blue-50/50 p-2 lg:p-4 gap-2 lg:gap-4">
    <Transition name="overlay-fade">
      <div v-if="mobileSidebarOpen" class="fixed inset-0 bg-black/40 z-20 lg:hidden" @click="closeSidebar" />
    </Transition>

    <aside
      :class="[
        'bg-white rounded-2xl border border-pink-100 flex flex-col shrink-0 shadow-sm overflow-hidden',
        'fixed inset-y-2 left-2 z-30 w-56 lg:static lg:w-56 lg:inset-auto lg:left-auto',
        'transition-all duration-400 ease-out',
        mobileSidebarOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-[calc(100%+2rem)] lg:translate-x-0',
        sidebarReady ? 'opacity-100' : 'opacity-0 lg:animate-slide-in-left'
      ]"
    >
      <div class="px-5 py-5 border-b border-pink-50 bg-gradient-to-r from-pink-50 to-white flex items-center justify-between">
        <div class="flex items-center gap-3">
          <router-link :to="`/${auth.uid}`" class="shrink-0">
            <img v-if="auth.avatar" :src="getThumbUrl(auth.avatar)" class="w-8 h-8 rounded-full object-cover hover:shadow-md transition-all duration-300 hover:scale-110" @error="e => { if (auth.avatar && e.target.src !== auth.avatar) e.target.src = auth.avatar }" />
            <div v-else class="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-blue-400 flex items-center justify-center text-white text-sm font-bold hover:shadow-md transition-all duration-300 hover:scale-110">{{ (auth.username || '?')[0].toUpperCase() }}</div>
          </router-link>
          <div>
            <h1 class="text-base font-bold text-primary">{{ labels.appTitle }}</h1>
            <div class="flex items-center gap-1">
              <p v-if="!editingUser" class="text-xs text-gray-400" @dblclick="editingUser = true; newUserName = auth.username" :title="labels.changeUsernameHint">{{ auth.username }}</p>
              <input v-else v-model="newUserName" @keyup.enter="doChangeUsername" @blur="doChangeUsername" class="text-xs px-2 py-0.5 border border-pink-100 rounded-lg outline-none focus:border-primary flex-1 min-w-0 transition-all duration-300" ref="userInput" />
            </div>
          </div>
          <button @click="closeSidebar" class="lg:hidden w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:bg-pink-50 text-lg transition-all duration-300 hover:scale-110">&times;</button>
        </div>
      </div>

      <div v-if="adminUserUid" class="px-3 py-2 bg-yellow-50 border-b border-yellow-100 animate-fade-in-down">
        <p class="text-xs text-yellow-700 mb-1">管理用户 UID: {{ adminUserUid }}</p>
        <router-link to="/admin/users" class="text-xs text-primary hover:underline transition-colors">&larr; 返回用户管理</router-link>
      </div>
      <div class="px-3 py-2 border-b border-pink-50">
        <select
          v-if="boardStore.boards.length > 0"
          :value="boardStore.currentBoardId"
          @change="switchBoard(($event.target).value)"
          class="w-full text-sm px-3 py-2 border border-pink-100 rounded-xl outline-none bg-white transition-all duration-300 focus:border-primary focus:shadow-[0_0_0_3px_rgba(236,72,153,0.1)] cursor-pointer hover:border-primary/50"
        >
          <option v-for="b in boardStore.boards" :key="b.id" :value="b.id">
            {{ b.icon || '' }} {{ b.name }}
          </option>
        </select>
        <button v-if="!adminUserUid" @click="showNewBoard = !showNewBoard" class="w-full text-xs text-primary hover:underline mt-1 text-center transition-all duration-300">
          {{ showNewBoard ? labels.cancel : labels.newBoard }}
        </button>
        <Transition name="slide-down">
          <div v-if="showNewBoard" class="mt-2 space-y-1.5">
            <div class="flex gap-1">
              <input v-model="newBoardIcon" :placeholder="labels.defaultBoardIcon" class="w-10 sm:w-12 px-2 py-1.5 text-sm border border-pink-100 rounded-lg outline-none transition-all duration-300 focus:border-primary" maxlength="2" />
              <input v-model="newBoardName" :placeholder="labels.boardNamePlaceholder" class="flex-1 px-2 py-1.5 text-sm border border-pink-100 rounded-lg outline-none transition-all duration-300 focus:border-primary" @keyup.enter="createBoard" />
            </div>
            <select v-model="newBoardType" class="w-full px-2 py-1.5 text-xs border border-pink-100 rounded-lg outline-none transition-all duration-300">
              <option value="image">图组模式</option>
              <option value="friend">群友模式</option>
              <option value="shuoshuo">说说模式</option>
            </select>
            <button @click="createBoard" class="w-full py-1.5 bg-primary text-white text-xs rounded-lg transition-all duration-300 hover:bg-primary-dark active:scale-95">{{ labels.confirm }}</button>
          </div>
        </Transition>
      </div>

      <nav class="flex-1 py-2 px-2 animate-stagger">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="[
            'block px-4 py-2.5 text-sm rounded-xl transition-all duration-300 ease-out',
            isActive(item.path)
              ? 'bg-primary text-white font-medium shadow-sm scale-[1.02]'
              : 'text-gray-600 hover:bg-pink-50 hover:translate-x-1'
          ]"
        >{{ item.label }}</router-link>
      </nav>
      <div class="px-5 py-3 border-t border-pink-50">
        <button
          @click="doLogout"
          class="text-sm text-gray-400 hover:text-primary transition-all duration-300 hover:translate-x-1"
        >{{ labels.logoutButton }}</button>
      </div>
    </aside>

    <main class="flex-1 overflow-y-auto bg-white rounded-2xl border border-pink-100 shadow-sm p-3 lg:p-6 animate-fade-in-up">
      <button @click="mobileSidebarOpen = !mobileSidebarOpen" class="lg:hidden mb-3 w-8 h-8 flex items-center justify-center rounded-lg bg-pink-50 text-primary text-lg transition-all duration-300 hover:scale-110 active:scale-95">&equiv;</button>
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.overlay-fade-enter-active, .overlay-fade-leave-active {
  transition: opacity 0.3s ease;
}
.overlay-fade-enter-from, .overlay-fade-leave-to {
  opacity: 0;
}

.slide-down-enter-active {
  animation: fadeInDown 0.3s ease-out;
  overflow: hidden;
}
.slide-down-leave-active {
  transition: all 0.2s ease-in;
  overflow: hidden;
}
.slide-down-enter-from, .slide-down-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
}
</style>
