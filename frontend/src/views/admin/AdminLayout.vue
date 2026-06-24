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

provide('currentBoardId', computed(() => boardStore.currentBoardId))

const basePath = computed(() => {
  const uid = route.params.uid
  return uid ? `/${uid}` : '/admin'
})

const navItems = computed(() => {
  const b = basePath.value
  return [
    { path: `${b}/persons`, label: labels.value.cardManage },
    { path: `${b}/settings`, label: labels.value.settingsTitle },
    { path: `${b}/images`, label: labels.value.imagesTitle },
  ]
})

function isActive(path) { return route.path.startsWith(path) }

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
const newBoardType = ref('image')

async function onAvatarUpload(e) {
  const file = e.target.files?.[0]; if (!file) return
  try { await auth.uploadAvatar(file) } catch (err) { alert(labels.value.avatarUploadFail + ': ' + err.message) }
  finally { e.target.value = '' }
}

const editingUser = ref(false)
const newUserName = ref('')
function doChangeUsername() {
  editingUser.value = false
  const name = newUserName.value.trim()
  if (!name || name === auth.username) return
  auth.changeUsername(name).catch(e => alert(labels.value.usernameChangeFail + ': ' + e.message))
}

const TYPE_DEFAULTS = {
  image:  { card_label:'图片', cards_label:'图片', group_label:'图组', groups_label:'图组', icon:'🖼️' },
  friend: { card_label:'群友', cards_label:'群友们', group_label:'群', groups_label:'群组', icon:'👥' },
  shuoshuo:{ card_label:'说说', cards_label:'说说', group_label:'话题', groups_label:'话题', icon:'💬' },
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

onMounted(async () => {
  if (route.name === 'user-profile' || route.name === 'user-person-detail') return
  const ok = await auth.checkAuth()
  if (!ok) {
    router.replace('/login')
    return
  }
  await boardStore.fetchBoards()
})
</script>

<template>
  <div v-if="route.name === 'user-profile' || route.name === 'user-person-detail'" class="min-h-screen">
    <RouterView />
  </div>

  <div v-else class="min-h-screen flex bg-gradient-to-br from-pink-50/50 via-white to-blue-50/50 p-4 gap-4">
    <aside class="w-56 bg-white rounded-2xl border border-pink-100 flex flex-col shrink-0 shadow-sm overflow-hidden">
      <div class="px-5 py-5 border-b border-pink-50 bg-gradient-to-r from-pink-50 to-white">
        <div class="flex items-center gap-3">
          <label class="cursor-pointer shrink-0 relative group">
            <img v-if="auth.avatar" :src="auth.avatar" class="w-8 h-8 rounded-full object-cover" />
            <div v-else class="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-blue-400 flex items-center justify-center text-white text-sm font-bold">{{ (auth.username || '?')[0].toUpperCase() }}</div>
            <div class="absolute inset-0 bg-black/30 rounded-full opacity-0 group-hover:opacity-100 transition flex items-center justify-center text-white text-[10px]">{{ labels.changeAvatar }}</div>
            <input type="file" accept="image/*" @change="onAvatarUpload" class="hidden" />
          </label>
          <div>
            <h1 class="text-base font-bold text-primary">{{ labels.appTitle }}</h1>
            <div class="flex items-center gap-1">
              <p v-if="!editingUser" class="text-xs text-gray-400" @dblclick="editingUser = true; newUserName = auth.username" :title="labels.changeUsernameHint">{{ auth.username }}</p>
              <input v-else v-model="newUserName" @keyup.enter="doChangeUsername" @blur="doChangeUsername" class="text-xs px-2 py-0.5 border border-pink-100 rounded-lg outline-none focus:border-primary w-24" ref="userInput" />
            </div>
          </div>
        </div>
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
          {{ showNewBoard ? labels.cancel : labels.newBoard }}
        </button>
        <div v-if="showNewBoard" class="mt-2 space-y-1.5">
          <div class="flex gap-1">
            <input v-model="newBoardIcon" :placeholder="labels.defaultBoardIcon" class="w-10 px-2 py-1.5 text-sm border border-pink-100 rounded-lg outline-none focus:border-primary" maxlength="2" />
            <input v-model="newBoardName" :placeholder="labels.boardNamePlaceholder" class="flex-1 px-2 py-1.5 text-sm border border-pink-100 rounded-lg outline-none focus:border-primary" @keyup.enter="createBoard" />
          </div>
          <select v-model="newBoardType" class="w-full px-2 py-1.5 text-xs border border-pink-100 rounded-lg outline-none">
            <option value="image">🖼️ 图组模式</option>
            <option value="friend">👥 群友模式</option>
            <option value="shuoshuo">💬 说说模式</option>
          </select>
          <button @click="createBoard" class="w-full py-1.5 bg-primary text-white text-xs rounded-lg hover:bg-primary-dark">{{ labels.confirm }}</button>
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
        >{{ labels.logoutButton }}</button>
      </div>
    </aside>

    <main class="flex-1 overflow-y-auto bg-white rounded-2xl border border-pink-100 shadow-sm p-6">
      <RouterView />
    </main>
  </div>
</template>
