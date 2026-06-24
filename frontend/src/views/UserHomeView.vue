<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter, RouterView } from 'vue-router'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'
import { useBoardStore } from '../stores/boards'
import { useLabels } from '../utils/labels'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const boardStore = useBoardStore()
const labels = useLabels()

const profileUid = route.params.uid
const isOwner = auth.uid === profileUid
const profileUser = ref(null)
const notFound = ref(false)
const loading = ref(true)
const persons = ref([])
const publicBoards = ref([])

async function load() {
  loading.value = true
  notFound.value = false

  if (isOwner) {
    // 自己：加载自己的画板和人脉
    profileUser.value = { uid: auth.uid, username: auth.username }
    try {
      await boardStore.fetchBoards()
      if (boardStore.currentBoardId) {
        persons.value = await api.listPersons('', boardStore.currentBoardId)
      }
    } catch { persons.value = [] }
  } else {
    // 访客：通过 API 获取用户公开信息
    try {
      const data = await api.getUserProfile(profileUid)
      profileUser.value = data
      publicBoards.value = data.boards || []
      // 加载公开画板的人
      const allPersons = []
      for (const b of publicBoards.value) {
        try {
          const cards = await api.listPersons('', b.id)
          allPersons.push(...cards)
        } catch {}
      }
      persons.value = allPersons
    } catch (e) {
      if (e.message.includes('不存在') || e.message.includes('404')) {
        notFound.value = true
      }
    }
  }
  loading.value = false
}

onMounted(() => {
  if (route.name === 'user-home') {
    load()
  } else {
    loading.value = false
    if (isOwner) {
      profileUser.value = { uid: auth.uid, username: auth.username }
    }
  }
})

watch(() => route.name, (name) => {
  if (name === 'user-home' && !persons.value.length && !publicBoards.value.length) load()
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-pink-50/30 to-white">
    <div v-if="notFound" class="flex items-center justify-center py-40">
      <div class="text-center">
        <div class="text-5xl mb-4">🔍</div>
        <p class="text-xl font-bold text-gray-600 mb-2">{{ labels.userNotFound }}</p>
        <p class="text-gray-400 mb-6">{{ labels.userNotFoundHint(profileUid) }}</p>
        <router-link to="/" class="px-6 py-2.5 bg-primary text-white rounded-xl hover:bg-primary-dark transition">{{ labels.backHome }}</router-link>
      </div>
    </div>

    <div v-else-if="loading && route.name === 'user-home'" class="flex items-center justify-center py-40">
      <div class="w-8 h-8 rounded-full border-2 border-pink-100 border-t-primary animate-spin" />
    </div>

    <template v-else-if="route.name && route.name !== 'user-home'">
      <div class="bg-white border-b border-pink-50">
        <div class="max-w-4xl mx-auto px-6 py-12 flex items-center gap-6">
          <div class="w-20 h-20 rounded-full bg-gradient-to-br from-primary to-blue-400 flex items-center justify-center text-white text-3xl font-bold shadow-lg">
            {{ (profileUser?.username || '?')[0].toUpperCase() }}
          </div>
          <div>
            <h1 class="text-2xl font-bold text-gray-900">{{ profileUser?.username }}</h1>
            <p class="text-gray-400 text-sm mt-1">UID: {{ profileUid }}</p>
            <div class="flex gap-3 mt-3">
              <router-link
                v-if="isOwner"
                :to="`/${profileUid}/user/persons`"
                class="px-4 py-1.5 text-sm bg-primary text-white rounded-xl hover:bg-primary-dark transition"
              >{{ labels.adminButton }}</router-link>
              <router-link
                v-if="isOwner"
                :to="`/${profileUid}/user/groups`"
                class="px-4 py-1.5 text-sm border border-pink-100 text-gray-500 rounded-xl hover:bg-pink-50 transition"
              >{{ labels.groupManage }}</router-link>
              <router-link
                v-if="isOwner"
                :to="`/${profileUid}/user/settings`"
                class="px-4 py-1.5 text-sm border border-pink-100 text-gray-500 rounded-xl hover:bg-pink-50 transition"
              >画板设置</router-link>
              <button
                v-if="isOwner"
                @click="auth.logout(); router.push('/')"
                class="px-4 py-1.5 text-sm border border-pink-100 text-gray-500 rounded-xl hover:bg-pink-50 transition"
              >{{ labels.logoutButton }}</button>
            </div>
          </div>
        </div>
      </div>
      <RouterView />
    </template>

    <div v-else>
      <div class="bg-white border-b border-pink-50">
        <div class="max-w-4xl mx-auto px-6 py-12 flex items-center gap-6">
          <div class="w-20 h-20 rounded-full bg-gradient-to-br from-primary to-blue-400 flex items-center justify-center text-white text-3xl font-bold shadow-lg">
            {{ (profileUser?.username || '?')[0].toUpperCase() }}
          </div>
          <div>
            <h1 class="text-2xl font-bold text-gray-900">{{ profileUser?.username }}</h1>
            <p class="text-gray-400 text-sm mt-1">UID: {{ profileUid }}</p>
            <div class="flex gap-3 mt-3">
              <router-link
                v-if="isOwner"
                :to="`/${profileUid}/user/persons`"
                class="px-4 py-1.5 text-sm bg-primary text-white rounded-xl hover:bg-primary-dark transition"
              >{{ labels.adminButton }}</router-link>
              <router-link
                v-if="isOwner"
                :to="`/${profileUid}/user/groups`"
                class="px-4 py-1.5 text-sm border border-pink-100 text-gray-500 rounded-xl hover:bg-pink-50 transition"
              >{{ labels.groupManage }}</router-link>
              <router-link
                v-if="isOwner"
                :to="`/${profileUid}/user/settings`"
                class="px-4 py-1.5 text-sm border border-pink-100 text-gray-500 rounded-xl hover:bg-pink-50 transition"
              >画板设置</router-link>
              <button
                v-if="isOwner"
                @click="auth.logout(); router.push('/')"
                class="px-4 py-1.5 text-sm border border-pink-100 text-gray-500 rounded-xl hover:bg-pink-50 transition"
              >{{ labels.logoutButton }}</button>
            </div>
          </div>
        </div>
      </div>

      <div class="max-w-4xl mx-auto px-6 py-10">
        <template v-if="isOwner">
          <h2 class="text-lg font-bold text-gray-900 mb-6">{{ labels.myBoards }}</h2>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-10">
            <div v-for="board in boardStore.boards" :key="board.id"
              class="bg-white rounded-xl border border-pink-100 p-5 hover:shadow-md transition">
              <div class="flex items-center gap-3 mb-3">
                <span class="text-2xl">{{ board.icon || '📋' }}</span>
                <h3 class="font-bold text-gray-900">{{ board.name }}</h3>
              </div>
              <p v-if="board.description" class="text-sm text-gray-400 mb-2">{{ board.description }}</p>
              <p class="text-xs text-gray-400">{{ labels.boardCardStatus(board) }}</p>
            </div>
          </div>
        </template>

        <template v-else>
          <h2 class="text-lg font-bold text-gray-900 mb-6">{{ labels.publicBoards }}</h2>
          <div v-if="publicBoards.length === 0" class="text-center py-20 text-gray-400">
            <div class="text-5xl mb-4">🔒</div>
            <p>{{ labels.noPublicBoards }}</p>
          </div>
          <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-10">
            <div v-for="board in publicBoards" :key="board.id"
              class="bg-white rounded-xl border border-pink-100 p-5 hover:shadow-md transition">
              <div class="flex items-center gap-3 mb-3">
                <span class="text-2xl">{{ board.icon || '📋' }}</span>
                <h3 class="font-bold text-gray-900">{{ board.name }}</h3>
              </div>
              <p v-if="board.description" class="text-sm text-gray-400 mb-2">{{ board.description }}</p>
              <p class="text-xs text-gray-400">{{ labels.boardCardCount(board) }}</p>
            </div>
          </div>
        </template>

        <h2 v-if="persons.length" class="text-lg font-bold text-gray-900 mb-4">{{ isOwner ? labels.recentCards : labels.publicCards }}</h2>
        <div v-if="persons.length" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          <div v-for="p in persons" :key="p.id"
            @click="router.push(`/${encodeURIComponent(p.name)}`)"
            class="bg-white rounded-xl border border-pink-50 p-3 hover:shadow-md transition cursor-pointer">
            <img v-if="p.avatar" :src="p.avatar" class="w-full aspect-square object-cover rounded-lg mb-2" />
            <div v-else class="w-full aspect-square rounded-lg bg-gradient-to-br from-pink-100 to-blue-50 flex items-center justify-center mb-2">
              <span class="text-2xl font-bold text-primary/30">{{ p.name[0] }}</span>
            </div>
            <p class="text-sm font-medium text-gray-900 truncate">{{ p.name }}</p>
            <p v-if="p.signature" class="text-xs text-gray-400 truncate">{{ p.signature }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
