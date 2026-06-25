<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import { useLabels } from '../utils/labels'

const route = useRoute()
const router = useRouter()
const labels = useLabels()
const person = ref(null)
const accounts = ref([])
const meetings = ref([])
const relations = ref([])

const ownerUid = computed(() => route.params.uid)
const personBoardName = computed(() => route.params.boardName || '')
const boardType = ref('image')

const notFound = ref(false)
const loading = ref(true)
const CONTENT_IMG_RE = /!\[([^\]]*)\]\(([^,\s)]+)(?:\s*,\s*(?:x\s*[=:]\s*)?(\d+)(?:\s*,\s*(?:y\s*[=:]\s*)?(\d+))?\s*)?\)/g

function parseContent(raw) {
  if (!raw) return []
  const blocks = []
  let lastIdx = 0
  let match
  while ((match = CONTENT_IMG_RE.exec(raw)) !== null) {
    const textBefore = raw.slice(lastIdx, match.index).trim()
    if (textBefore) blocks.push({ type: 'text', value: textBefore })
    blocks.push({
      type: 'image',
      alt: match[1],
      url: match[2],
      w: match[3] ? parseInt(match[3]) || null : null,
      h: match[4] ? parseInt(match[4]) || null : null,
    })
    lastIdx = match.index + match[0].length
  }
  const textAfter = raw.slice(lastIdx).trim()
  if (textAfter) blocks.push({ type: 'text', value: textAfter })
  return blocks
}

const contentBlocks = computed(() => person.value ? parseContent(person.value.notes) : [])
const lightbox = ref({ show: false, url: '', alt: '' })
function openLightbox(blk) { lightbox.value = { show: true, url: blk.url, alt: blk.alt } }
function closeLightbox() { lightbox.value.show = false }

async function loadPerson() {
  const name = route.params.personName
  loading.value = true
  notFound.value = false
  let boardIds = null
  let boardMap = {}
  if (ownerUid.value) {
    try {
      const profile = await api.getUserProfile(ownerUid.value)
      const boards = profile.boards || []
      boardIds = boards.map(b => b.id)
      boards.forEach(b => { boardMap[b.id] = b.board_type || 'image' })
    } catch { }
  }
  const all = await api.listPersons(name)
  const found = all.find(p => {
    if (!(p.name === name || p.remark === name)) return false
    if (boardIds) return boardIds.includes(p.board_id)
    return true
  })
  if (!found) {
    notFound.value = true
    loading.value = false
    return
  }
  person.value = await api.getPerson(found.id)
  boardType.value = boardMap[found.board_id] || 'image'
  accounts.value = await api.listAccounts(found.id)
  meetings.value = await api.listMeetings(found.id)
  relations.value = await api.listRelations(found.id)
  loading.value = false
}

function goBack() {
  router.push(ownerUid.value ? `/${ownerUid.value}` : '/')
}

const headerHidden = ref(false)
let lastScrollY = 0
function onScroll() {
  const y = window.scrollY
  if (y < 10) headerHidden.value = false
  else if (y > lastScrollY + 5) headerHidden.value = true
  else if (y < lastScrollY - 5) headerHidden.value = false
  lastScrollY = y
}

onMounted(() => {
  loadPerson()
  window.addEventListener('scroll', onScroll, { passive: true })
})
onUnmounted(() => window.removeEventListener('scroll', onScroll))
watch(() => route.params.personName, loadPerson)
</script>

<template>
  <div v-if="notFound" class="min-h-screen bg-pink-50/30 flex items-center justify-center">
    <div class="text-center">
      <div class="text-6xl mb-4"></div>
      <p class="text-xl font-bold text-gray-600 mb-2">{{ labels.personDetailNotFound }}</p>
      <p class="text-gray-400 mb-6">{{ labels.personDetailNotFoundHint(route.params.personName) }}</p>
      <router-link to="/" class="px-6 py-2.5 bg-primary text-white rounded-xl hover:bg-primary-dark transition">{{ labels.backHome }}</router-link>
    </div>
  </div>

  <div v-else-if="loading" class="min-h-screen bg-pink-50/30 flex items-center justify-center">
    <div class="w-8 h-8 rounded-full border-2 border-pink-100 border-t-primary animate-spin" />
  </div>

  <div class="min-h-screen bg-pink-50/30" v-else-if="person">
    <header
      class="bg-white/95 backdrop-blur sticky top-3 z-10 mx-4 rounded-2xl border border-pink-100 shadow-sm transition-all duration-300"
      :class="{ '-translate-y-[calc(100%+1rem)] opacity-0': headerHidden }"
    >
      <div class="max-w-3xl mx-auto px-6 py-4 flex items-center gap-4">
        <button @click="goBack" class="w-8 h-8 flex items-center justify-center rounded-full bg-pink-50 text-primary hover:bg-primary hover:text-white transition text-lg">&larr;</button>
        <h1 class="text-lg font-bold text-gray-900">{{ person.name }}</h1>
        <span v-if="person.remark" class="text-sm text-gray-400">{{ person.remark }}</span>
      </div>
    </header>

    <main class="max-w-3xl mx-auto px-6 py-8 space-y-8">
      <div class="bg-white rounded-xl p-6 flex items-start gap-5 shadow-sm border border-pink-50">
        <img
          :src="person.avatar || '/default-avatar.svg'"
          class="w-20 h-20 rounded-full object-cover bg-pink-50"
        />
        <div class="space-y-2 flex-1">
          <div class="flex items-center gap-2">
            <h2 class="text-xl font-bold text-gray-900">{{ person.name }}</h2>
            <span v-if="person.importance" class="text-primary text-sm">
              {{ '★'.repeat(person.importance) }}
            </span>
          </div>
          <p v-if="person.signature" class="text-gray-500 text-sm">{{ person.signature }}</p>
          <p v-if="person.location" class="text-gray-400 text-xs">{{ person.location }}</p>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="tag in person.circle_tags"
              :key="tag"
              class="px-2 py-0.5 text-xs rounded-full bg-pink-50 text-primary"
            >{{ tag }}</span>
            <span
              v-for="tag in person.impression_tags"
              :key="tag"
              class="px-2 py-0.5 text-xs rounded-full bg-blue-50 text-blue-600"
            >{{ tag }}</span>
          </div>
        </div>
      </div>

      <section v-if="contentBlocks.length > 0" class="bg-white rounded-xl p-6 shadow-sm border border-pink-50">
        <h3 class="font-bold mb-4 text-gray-800">内容</h3>
        <div class="space-y-5">
          <template v-for="(blk, i) in contentBlocks" :key="i">
            <p v-if="blk.type === 'text'" class="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">{{ blk.value }}</p>
            <div v-else-if="blk.type === 'image'" class="relative">
              <img
                :src="blk.url"
                :alt="blk.alt"
                :style="{ maxWidth: blk.w ? blk.w + 'px' : '100%', height: blk.h ? blk.h + 'px' : 'auto' }"
                class="rounded-xl cursor-pointer hover:shadow-lg transition max-h-[70vh] object-contain"
                @click="openLightbox(blk)"
                @error="e => e.target.style.display = 'none'"
              />
            </div>
          </template>
        </div>
      </section>

      <Teleport to="body">
        <div v-if="lightbox.show" class="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-8" @click="closeLightbox">
          <img :src="lightbox.url" :alt="lightbox.alt" class="max-w-full max-h-full object-contain rounded-xl" @click.stop />
          <button @click="closeLightbox" class="absolute top-4 right-4 text-white text-3xl hover:text-gray-300">&times;</button>
          <p v-if="lightbox.alt" class="absolute bottom-4 text-white/70 text-sm">{{ lightbox.alt }}</p>
        </div>
      </Teleport>

      <section v-if="boardType === 'friend'" class="bg-white rounded-xl p-6 shadow-sm border border-pink-50">
        <h3 class="font-bold mb-4 text-primary">{{ labels.personDetailAccounts }}</h3>
        <div v-if="accounts.length === 0" class="text-sm text-gray-400">{{ labels.noAccounts }}</div>
        <div v-for="a in accounts" :key="a.id" class="flex items-center gap-3 py-2 border-b border-pink-50 last:border-0">
          <img
            :src="a.current_avatar || '/default-avatar.svg'"
            class="w-9 h-9 rounded-full object-cover bg-pink-50"
          />
          <div>
            <p class="text-sm font-medium text-gray-900">{{ a.current_nickname || a.account_identifier }}</p>
            <p class="text-xs text-gray-400">{{ a.account_type }} · {{ a.account_identifier }}</p>
          </div>
        </div>
      </section>

      <section v-if="meetings.length > 0" class="bg-white rounded-xl p-6 shadow-sm border border-pink-50">
        <h3 class="font-bold mb-4 text-primary">{{ labels.personDetailMeetings }}</h3>
        <div v-for="m in meetings" :key="m.id" class="text-sm text-gray-600 py-1">
          {{ m.met_at ? `[${m.met_at}] ` : '' }}{{ m.description }}
        </div>
      </section>

      <section v-if="relations.length > 0" class="bg-white rounded-xl p-6 shadow-sm border border-pink-50">
        <h3 class="font-bold mb-4 text-primary">{{ labels.personDetailRelations }}</h3>
        <div v-for="r in relations" :key="r.id" class="text-sm text-gray-600 py-1">
          {{ r.relation_type || labels.personDetailRelationFallback }}
        </div>
      </section>

    </main>
  </div>
</template>
