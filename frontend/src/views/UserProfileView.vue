<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'
import { useLabels } from '../utils/labels'
import SearchBar from '../components/SearchBar.vue'
import PersonCard from '../components/PersonCard.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const boardMap = ref({})
const labels = useLabels()

const profileUid = computed(() => route.params.uid)
const isOwner = computed(() => auth.uid === profileUid.value)
const boardGroups = ref([])
const loading = ref(true)
const search = ref('')

const imageAspects = ref({})

const COLORS = ['#f472b6','#818cf8','#34d399','#fb923c','#a78bfa','#fbbf24','#38bdf8','#e879f9']
function placeholderUrl(name) {
  const i = (name || '?').charCodeAt(0) % COLORS.length
  return 'bg:' + COLORS[i]
}

function preloadImage(src) {
  if (src.startsWith('bg:')) return Promise.resolve(1)
  return new Promise((resolve) => {
    if (imageAspects.value[src]) return resolve(imageAspects.value[src])
    const img = new Image()
    img.onload = () => { imageAspects.value[src] = img.naturalWidth / img.naturalHeight; resolve(imageAspects.value[src]) }
    img.onerror = () => resolve(1)
    img.src = src
  })
}

function pickImages(personsList, boardBanners, boardType = 'image') {
  const pool = boardBanners.length > 0 ? [...boardBanners] : []
  return personsList.map(p => {
    if (p.card_bg) return p.card_bg
    if (boardType === 'shuoshuo' && p.avatar) return p.avatar
    if (p.avatar && !p.card_bg && pool.length === 0) return p.avatar
    if (pool.length === 0) return placeholderUrl(p.name)
    const idx = Math.floor(Math.random() * pool.length)
    return pool[idx]
  })
}

const NICE_SCALES = [3 / 8, 1 / 2, 5 / 8, 2 / 3, 3 / 4, 7 / 8, 1, 8 / 7, 4 / 3, 3 / 2, 2]

function calcWidth(aspect) {
  const base = 24.25
  const raw = base * Math.sqrt(aspect)
  if (raw >= 22.5 && raw <= 26) return raw
  const ratio = 24.25 / raw
  let best = 1, bestD = Infinity
  for (const s of NICE_SCALES) { const d = Math.abs(s - ratio); if (d < bestD) { bestD = d; best = s } }
  return Math.max(22.5, Math.min(26, raw * best))
}

async function computeLayout(personsList, banners, boardType = 'image') {
  if (!personsList.length) return []
  const picks = pickImages(personsList, banners, boardType)
  await Promise.all(picks.map(src => preloadImage(src)))
  const cards = personsList.map((p, i) => {
    const src = picks[i]; const aspect = imageAspects.value[src] || 1
    const w = calcWidth(aspect); return { person: p, image: src, w, h: w / aspect }
  })
  const vw = window.innerWidth
  let COLS = 3; if (vw < 640) COLS = 1; else if (vw < 1024) COLS = 2
  const GAP = 0.15
  const colCards = Array.from({ length: COLS }, () => [])
  const colHeights = Array(COLS).fill(0)
  for (const card of cards) {
    let minCol = 0
    for (let c = 1; c < COLS; c++) { if (colHeights[c] < colHeights[minCol]) minCol = c }
    colCards[minCol].push(card); colHeights[minCol] += card.h
  }
  const colWidths = colCards.map(col => col.reduce((m, c) => Math.max(m, c.w), 0))
  const totalW = colWidths.reduce((s, w) => s + w, 0) + GAP * (COLS - 1)
  const baseX = (100 - totalW) / 2
  const colX = []; let cx = baseX
  for (let c = 0; c < COLS; c++) { colX.push(cx); cx += colWidths[c] + GAP }
  const colY = Array(COLS).fill(0); const result = []
  for (let c = 0; c < COLS; c++) {
    for (const card of colCards[c]) {
      let offset
      if (COLS === 1) offset = (colWidths[c] - card.w) / 2
      else if (c === 0) offset = colWidths[c] - card.w
      else if (c === COLS - 1) offset = 0
      else offset = (colWidths[c] - card.w) / 2
      result.push({ person: card.person, image: card.image, x: colX[c] + offset, y: colY[c], w: card.w, h: card.h })
      colY[c] += card.h
    }
  }
  return result
}

async function loadPersons() {
  loading.value = true
  try {
    const profile = await api.getUserProfile(profileUid.value)
    const boards = profile.boards || []
    const map = {}
    boards.forEach(b => { map[b.id] = b.name || 'default' })
    boardMap.value = map
    const sharedBanners = []
    for (const b of boards) {
      const fc = typeof b.field_config === 'object' ? b.field_config : {}
      if (fc.bannerImages && fc.bannerImages.length) {
        sharedBanners.push(...fc.bannerImages)
      }
    }
    const groups = []
    for (const b of boards) {
      try {
        const cards = await api.listPersons(search.value, b.id)
        if (cards.length === 0) continue
        const places = await computeLayout(cards, sharedBanners, b.board_type)
        groups.push({
          board: b,
          cards_count: cards.length,
          places,
          containerHeight: places.reduce((m, p) => Math.max(m, p.y + p.h), 0),
        })
      } catch { }
    }
    boardGroups.value = groups
  } catch {
    boardGroups.value = []
  }
  loading.value = false
}

function onSearch(val) { search.value = val; loadPersons() }
function goDetail(p, boardName) {
  router.push(`/${profileUid.value}/${encodeURIComponent(boardName)}/${encodeURIComponent(p.name)}`)
}

let resizeTimer
function onResize() { clearTimeout(resizeTimer); resizeTimer = setTimeout(loadPersons, 300) }

const showUserMenu = ref(false)

const showPwdDialog = ref(false)
const pwdForm = ref({ oldPassword: '', newPassword: '', confirmPassword: '' })
const pwdError = ref('')
const pwdOk = ref('')
const pwdSaving = ref(false)

function openChangePwd() {
  showUserMenu.value = false
  pwdForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
  pwdError.value = ''; pwdOk.value = ''
  showPwdDialog.value = true
}

async function doChangePwd() {
  pwdError.value = ''; pwdOk.value = ''
  if (!pwdForm.value.oldPassword || !pwdForm.value.newPassword) {
    pwdError.value = '请填写新旧密码'; return
  }
  if (pwdForm.value.newPassword.length < 8) {
    pwdError.value = '新密码长度不能少于8位'; return
  }
  if (pwdForm.value.newPassword !== pwdForm.value.confirmPassword) {
    pwdError.value = '两次输入的新密码不一致'; return
  }
  pwdSaving.value = true
  try {
    await api.changePassword(pwdForm.value.oldPassword, pwdForm.value.newPassword)
    pwdOk.value = '密码修改成功'
    setTimeout(() => { showPwdDialog.value = false }, 1500)
  } catch (e) {
    pwdError.value = e.message
  } finally {
    pwdSaving.value = false
  }
}

const headerHidden = ref(false)
const showBackTop = ref(false)
let lastScrollY = 0
function onScroll() {
  const y = window.scrollY
  if (y < 10) { headerHidden.value = false; showBackTop.value = false }
  else if (y > lastScrollY + 5) { headerHidden.value = true; showBackTop.value = true }
  else if (y < lastScrollY - 5) { headerHidden.value = false; showBackTop.value = true }
  lastScrollY = y
}
function scrollToTop() { window.scrollTo({ top: 0, behavior: 'smooth' }) }

onMounted(async () => {
  await auth.checkAuth()
  loadPersons()
  window.addEventListener('resize', onResize)
  window.addEventListener('scroll', onScroll, { passive: true })
})

watch(() => route.params.uid, () => { loadPersons() })
</script>

<template>
  <div class="min-h-screen bg-white relative">
    <div class="absolute top-0 left-0 w-full overflow-hidden pointer-events-none z-0">
      <div class="absolute -top-40 -left-20 w-80 h-80 rounded-full bg-pink-200/20 blur-3xl" />
      <div class="absolute -top-20 right-10 w-64 h-64 rounded-full bg-blue-200/20 blur-3xl" />
      <div class="absolute top-20 left-1/2 -translate-x-1/2 w-96 h-40 rounded-full bg-pink-100/30 blur-3xl" />
    </div>

    <header
      class="sticky top-3 z-20 mx-4 rounded-2xl backdrop-blur-xl bg-white/95 border border-pink-100 shadow-sm transition-all duration-300"
      :class="{ '-translate-y-[calc(100%+1rem)] opacity-0': headerHidden }"
    >
      <div class="px-5 py-3.5 flex items-center">
        <h1 class="text-lg font-bold text-primary shrink-0">{{ labels.appTitle }}</h1>
        <div class="flex-1 flex justify-center px-4">
          <SearchBar @search="onSearch" :placeholder="labels.searchCard" class="w-full max-w-md" />
        </div>
        <template v-if="auth.isLoggedIn">
          <div class="relative shrink-0" @mouseenter="showUserMenu = true" @mouseleave="showUserMenu = false">
            <img v-if="auth.avatar" :src="auth.avatar" class="w-8 h-8 rounded-full object-cover shadow-sm cursor-pointer" />
            <div v-else class="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-blue-400 flex items-center justify-center text-white text-sm font-bold shadow-sm cursor-pointer">
              {{ (auth.username || '?')[0].toUpperCase() }}
            </div>
            <Transition name="menu-fade">
              <div v-if="showUserMenu" class="absolute right-0 top-full mt-2 w-48 bg-white rounded-xl border border-gray-100 shadow-lg py-2 z-30">
                <div class="px-4 py-2 border-b border-gray-50">
                  <p class="text-sm font-medium text-gray-800">{{ auth.username }}</p>
                  <p class="text-xs text-gray-400">UID: {{ auth.uid }}</p>
                </div>
                <router-link :to="`/${auth.uid}`" class="block px-4 py-2 text-sm text-gray-600 hover:bg-pink-50 transition">我的主页</router-link>
                <router-link :to="`/${auth.uid}/persons`" class="block px-4 py-2 text-sm text-gray-600 hover:bg-pink-50 transition">管理</router-link>
                <router-link v-if="auth.role === 'admin'" to="/admin/dashboard" class="block px-4 py-2 text-sm text-gray-600 hover:bg-pink-50 transition">后台</router-link>
                <hr class="border-gray-50 my-1" />
                <button @click="openChangePwd" class="w-full text-left px-4 py-2 text-sm text-gray-600 hover:bg-pink-50 transition">修改密码</button>
                <button @click="auth.logout(); router.replace('/login')" class="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-red-50 transition">退出登录</button>
              </div>
            </Transition>
          </div>
        </template>
        <router-link v-else to="/login" class="shrink-0 text-sm text-gray-400 hover:text-primary transition">{{ labels.homeLogin }}</router-link>
      </div>
    </header>

    <main class="relative z-10 px-0 py-8">
      <div v-if="loading" class="px-2">
        <div class="flex gap-2">
          <div v-for="col in 3" :key="col" class="flex-1 space-y-2" :class="{ 'hidden md:block': col > 1, 'hidden lg:block': col > 2 }">
            <div v-for="i in 4" :key="i" class="rounded-xl bg-gradient-to-br from-pink-100 to-blue-50 animate-pulse" :style="{ height: (140 + Math.random() * 120) + 'px' }" />
          </div>
        </div>
      </div>

      <div v-else-if="!boardGroups.length" class="text-center text-gray-400 py-20">
        <p class="text-lg text-gray-500">{{ labels.emptyHome }}</p>
        <p class="text-sm mt-1">{{ labels.emptyHomeHint }}</p>
      </div>

      <div v-else>
        <section v-for="group in boardGroups" :key="group.board.id" class="mb-12">
          <div class="mb-4 px-2">
            <div class="flex items-center gap-2">
              <span class="text-xl font-bold text-gray-400">{{ group.board.icon || '' }}</span>
              <h2 class="text-xl font-bold text-gray-900">{{ group.board.name }}</h2>
            </div>
            <p class="text-gray-400 text-sm mt-1">{{ group.cards_count }} {{ group.board.cards_label || '图片' }}</p>
          </div>

          <div class="relative w-full" :style="{ height: group.containerHeight + 'vw' }">
            <div
              v-for="item in group.places"
              :key="item.person.id"
              class="absolute transition-transform duration-300 hover:scale-[1.02] hover:z-10"
              :style="{ left: item.x + 'vw', top: item.y + 'vw', width: item.w + 'vw' }"
            >
              <PersonCard :person="item.person" :image="item.image" @click="goDetail(item.person, group.board.name)" />
            </div>
          </div>
        </section>
      </div>
    </main>

    <Transition name="fab">
      <button v-if="showBackTop" @click="scrollToTop"
        class="fixed bottom-6 right-6 z-30 w-11 h-11 rounded-full bg-primary text-white shadow-lg hover:bg-primary-dark hover:shadow-xl transition-all duration-300 flex items-center justify-center text-lg"
      >↑</button>
    </Transition>

    <div v-if="showPwdDialog" class="fixed inset-0 bg-black/30 flex items-center justify-center z-50" @click.self="showPwdDialog = false">
      <div class="bg-white rounded-2xl p-6 w-full max-w-sm shadow-xl">
        <h3 class="text-lg font-bold text-gray-900 mb-4">修改密码</h3>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-gray-500 block mb-1">原密码</label>
            <input v-model="pwdForm.oldPassword" type="password" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl outline-none focus:border-primary" />
          </div>
          <div>
            <label class="text-xs text-gray-500 block mb-1">新密码</label>
            <input v-model="pwdForm.newPassword" type="password" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl outline-none focus:border-primary" />
          </div>
          <div>
            <label class="text-xs text-gray-500 block mb-1">确认新密码</label>
            <input v-model="pwdForm.confirmPassword" type="password" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl outline-none focus:border-primary" @keyup.enter="doChangePwd" />
          </div>
          <p v-if="pwdError" class="text-red-500 text-sm">{{ pwdError }}</p>
          <p v-if="pwdOk" class="text-green-500 text-sm">{{ pwdOk }}</p>
        </div>
        <div class="flex justify-end gap-3 mt-5">
          <button @click="showPwdDialog = false" class="px-4 py-2 text-sm text-gray-500 hover:text-gray-700">取消</button>
          <button @click="doChangePwd" :disabled="pwdSaving" class="px-4 py-2 bg-primary text-white text-sm rounded-xl hover:bg-primary-dark disabled:opacity-50">
            {{ pwdSaving ? '修改中...' : '确定' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.menu-fade-enter-active, .menu-fade-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.menu-fade-enter-from, .menu-fade-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
