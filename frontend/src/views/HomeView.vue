<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import SearchBar from '../components/SearchBar.vue'
import PersonCard from '../components/PersonCard.vue'

const router = useRouter()
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

// ── 三固定列 + 列内最矮优先堆叠 ──
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

  // 贪心分配到各列（最短列优先），记录每列卡片
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

  // 列宽 = 列内最宽卡片
  const colWidths = colCards.map(col => col.reduce((m, c) => Math.max(m, c.w), 0))
  const totalW = colWidths.reduce((s, w) => s + w, 0) + GAP * (COLS - 1)
  const baseX = (100 - totalW) / 2

  const colX = []
  let cx = baseX
  for (let c = 0; c < COLS; c++) {
    colX.push(cx)
    cx += colWidths[c] + GAP
  }

  // 逐列放置，列内竖直堆叠，卡片左对齐
  const colY = Array(COLS).fill(0)
  const result = []

  for (let c = 0; c < COLS; c++) {
    for (const card of colCards[c]) {
      result.push({
        person: card.person,
        image: card.image,
        x: colX[c],
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

function goDetail(name) {
  router.push(`/${encodeURIComponent(name)}`)
}

let resizeTimer
function onResize() {
  clearTimeout(resizeTimer)
  resizeTimer = setTimeout(() => {
    if (persons.value.length) computeLayout(persons.value)
  }, 300)
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
})
</script>

<template>
  <div class="min-h-screen bg-zinc-900">
    <header class="sticky top-0 z-20 backdrop-blur-xl bg-zinc-900/80 border-b border-zinc-800">
      <div class="px-4 py-4 flex items-center gap-6">
        <div class="flex items-center gap-3 shrink-0">
          <h1 class="text-lg font-bold text-white">群友记忆助手</h1>
        </div>
        <SearchBar @search="onSearch" class="flex-1 max-w-md" />
      </div>
    </header>

    <main class="px-0 py-8">
      <div class="mb-8 px-2">
        <h2 class="text-2xl font-bold text-white">
          {{ search ? `搜索「${search}」` : '我认识的群友们' }}
        </h2>
        <p class="text-zinc-500 mt-1 text-sm">{{ persons.length }} 位群友</p>
      </div>

      <div v-if="loading" class="text-center text-zinc-500 py-20">
        <div class="w-10 h-10 mx-auto mb-4 rounded-full border-2 border-zinc-700 border-t-white animate-spin" />
        加载中...
      </div>
      <div v-else-if="!places.length" class="text-center text-zinc-500 py-20">
        <div class="text-5xl mb-4">🫥</div>
        <p class="text-lg text-zinc-400">还没有添加群友</p>
        <p class="text-sm mt-1">去后台管理页面添加第一位群友吧</p>
      </div>

      <div v-else class="relative w-full" :style="{ height: containerHeight() }">
        <div
          v-for="item in places"
          :key="item.person.id"
          class="absolute"
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
  </div>
</template>
