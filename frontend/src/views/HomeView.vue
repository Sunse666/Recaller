<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'
import { useLabels } from '../utils/labels'
import SearchBar from '../components/SearchBar.vue'
import PersonCard from '../components/PersonCard.vue'

const router = useRouter()
const auth = useAuthStore()
const labels = useLabels()
const persons = ref([])
const loading = ref(true)
const search = ref('')

const imageModules = import.meta.glob('../assets/*.{jpg,png}', { eager: true })
const allImages = Object.values(imageModules).map(m => m.default)
const imageAspects = ref({})

function preloadImage(src) {
  return new Promise((resolve) => {
    if (imageAspects.value[src]) return resolve(imageAspects.value[src])
    const img = new Image()
    img.onload = () => {
      imageAspects.value[src] = img.naturalWidth / img.naturalHeight
      resolve(imageAspects.value[src])
    }
    img.onerror = () => resolve(1)
    img.src = src
  })
}

function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

const NICE_SCALES = [3/8, 1/2, 5/8, 2/3, 3/4, 7/8, 1, 8/7, 4/3, 3/2, 2]

function calcWidth(aspect) {
  const base = 24.25
  const raw = base * Math.sqrt(aspect)
  if (raw >= 22.5 && raw <= 26) return raw
  const ratio = 24.25 / raw
  let best = 1, bestD = Infinity
  for (const s of NICE_SCALES) {
    const d = Math.abs(s - ratio)
    if (d < bestD) { bestD = d; best = s }
  }
  return Math.max(22.5, Math.min(26, raw * best))
}

const places = ref([])

async function computeLayout(personsList) {
  if (!personsList.length) { places.value = []; return }

  const shuffled = shuffle(allImages)
  const picks = personsList.map((_, i) => shuffled[i % shuffled.length])
  await Promise.all(picks.map(src => preloadImage(src)))

  const cards = personsList.map((p, i) => {
    const src = picks[i]
    const aspect = imageAspects.value[src] || 1
    const w = calcWidth(aspect)
    return { person: p, image: src, w, h: w / aspect }
  })

  const vw = window.innerWidth
  let COLS = 3
  if (vw < 640) COLS = 1
  else if (vw < 1024) COLS = 2

  const GAP = 0.15

  const colCards = Array.from({ length: COLS }, () => [])
  const colHeights = Array(COLS).fill(0)

  for (const card of cards) {
    let minCol = 0
    for (let c = 1; c < COLS; c++) {
      if (colHeights[c] < colHeights[minCol]) minCol = c
    }
    colCards[minCol].push(card)
    colHeights[minCol] += card.h
  }

  const colWidths = colCards.map(col => col.reduce((m, c) => Math.max(m, c.w), 0))
  const totalW = colWidths.reduce((s, w) => s + w, 0) + GAP * (COLS - 1)
  const baseX = (100 - totalW) / 2

  const colX = []
  let cx = baseX
  for (let c = 0; c < COLS; c++) {
    colX.push(cx)
    cx += colWidths[c] + GAP
  }

  const colY = Array(COLS).fill(0)
  const result = []

  for (let c = 0; c < COLS; c++) {
    for (const card of colCards[c]) {
      let offset
      if (COLS === 1) {
        offset = (colWidths[c] - card.w) / 2
      } else if (c === 0) {
        offset = colWidths[c] - card.w
      } else if (c === COLS - 1) {
        offset = 0
      } else {
        offset = (colWidths[c] - card.w) / 2
      }
      result.push({
        person: card.person,
        image: card.image,
        x: colX[c] + offset,
        y: colY[c],
        w: card.w,
        h: card.h,
      })
      colY[c] += card.h
    }
  }

  places.value = result
}

async function loadPersons() {
  loading.value = true
  persons.value = await api.listPersons(search.value)
  await computeLayout(persons.value)
  loading.value = false
}

function onSearch(val) {
  search.value = val
  loadPersons()
}

function goDetail(p) {
  router.push(`/1/default/${encodeURIComponent(p.name)}`)
}

let resizeTimer
function onResize() {
  clearTimeout(resizeTimer)
  resizeTimer = setTimeout(() => {
    if (persons.value.length) computeLayout(persons.value)
  }, 300)
}

const headerHidden = ref(false)
const showBackTop = ref(false)
let lastScrollY = 0
function onScroll() {
  const y = window.scrollY
  if (y < 10) {
    headerHidden.value = false
    showBackTop.value = false
  } else if (y > lastScrollY + 5) {
    headerHidden.value = true
    showBackTop.value = true
  } else if (y < lastScrollY - 5) {
    headerHidden.value = false
    showBackTop.value = true
  }
  lastScrollY = y
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function containerHeight() {
  let maxBtm = 0
  for (const p of places.value) {
    if (p.y + p.h > maxBtm) maxBtm = p.y + p.h
  }
  return maxBtm + 'vw'
}

onMounted(() => {
  loadPersons()
  window.addEventListener('resize', onResize)
  window.addEventListener('scroll', onScroll, { passive: true })
})
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
        <router-link v-if="auth.isLoggedIn" :to="`/${auth.uid}`" class="shrink-0">
          <img v-if="auth.avatar" :src="auth.avatar" class="w-8 h-8 rounded-full object-cover shadow-sm hover:shadow-md transition" />
          <div v-else class="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-blue-400 flex items-center justify-center text-white text-sm font-bold shadow-sm hover:shadow-md transition">
            {{ auth.username[0].toUpperCase() }}
          </div>
        </router-link>
        <router-link v-else to="/login" class="shrink-0 text-sm text-gray-400 hover:text-primary transition">{{ labels.homeLogin }}</router-link>
      </div>
    </header>

    <main class="relative z-10 px-0 py-8">
      <div class="mb-8 px-2">
        <h2 class="text-2xl font-bold text-gray-900">
          {{ search ? labels.searchPrefix + '「' + search + '」' : labels.homeTitle }}
        </h2>
        <p class="text-primary/70 mt-1 text-sm">{{ labels.homeCount(persons.length) }}</p>
      </div>

      <div v-if="loading" class="px-2">
        <div class="flex gap-2">
          <div v-for="col in 3" :key="col" class="flex-1 space-y-2" :class="{ 'hidden md:block': col > 1, 'hidden lg:block': col > 2 }">
            <div v-for="i in 4" :key="i" class="rounded-xl bg-gradient-to-br from-pink-100 to-blue-50 animate-pulse" :style="{ height: (140 + Math.random() * 120) + 'px' }" />
          </div>
        </div>
      </div>

      <div v-else-if="!places.length" class="text-center text-gray-400 py-20">
        <div class="text-5xl mb-4">🫥</div>
        <p class="text-lg text-gray-500">{{ labels.emptyHome }}</p>
        <p class="text-sm mt-1">{{ labels.emptyHomeHint }}</p>
      </div>

      <div v-else class="relative w-full" :style="{ height: containerHeight() }">
        <div
          v-for="item in places"
          :key="item.person.id"
          class="absolute transition-transform duration-300 hover:scale-[1.02] hover:z-10"
          :style="{
            left: item.x + 'vw',
            top: item.y + 'vw',
            width: item.w + 'vw',
          }"
        >
          <PersonCard
            :person="item.person"
            :image="item.image"
            @click="goDetail(item.person.name)"
          />
        </div>
      </div>
    </main>

    <Transition name="fab">
      <button
        v-if="showBackTop"
        @click="scrollToTop"
        class="fixed bottom-6 right-6 z-30 w-11 h-11 rounded-full bg-primary text-white shadow-lg hover:bg-primary-dark hover:shadow-xl transition-all duration-300 flex items-center justify-center text-lg"
      >
        ↑
      </button>
    </Transition>
  </div>
</template>
