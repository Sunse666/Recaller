<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import { useLabels } from '../utils/labels'
import { getThumbUrl, getMediumUrl } from '../utils/images'

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
const lightbox = ref({ show: false, url: '', alt: '', original: false })
function openLightbox(blk) { lightbox.value = { show: true, url: blk.url, alt: blk.alt, original: false } }
function closeLightbox() { lightbox.value = { show: false, url: '', alt: '', original: false } }
const originalImages = computed(() => contentBlocks.value.filter(b => b.type === 'image'))
function openOriginalLightbox() {
  if (originalImages.value.length > 0) {
    lightbox.value = { show: true, url: originalImages.value[0].url, alt: originalImages.value[0].alt, original: true }
  }
}

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
    <div class="text-center animate-bounce-in">
      <div class="text-6xl mb-4"></div>
      <p class="text-xl font-bold text-gray-600 mb-2">{{ labels.personDetailNotFound }}</p>
      <p class="text-gray-400 mb-6">{{ labels.personDetailNotFoundHint(route.params.personName) }}</p>
      <router-link to="/" class="px-6 py-2.5 bg-primary text-white rounded-xl transition-all duration-300 hover:bg-primary-dark hover:shadow-lg inline-block">{{ labels.backHome }}</router-link>
    </div>
  </div>

  <div v-else-if="loading" class="min-h-screen bg-pink-50/30 flex items-center justify-center">
    <div class="w-8 h-8 rounded-full border-2 border-pink-100 border-t-primary animate-spin" />
  </div>

  <div class="min-h-screen bg-pink-50/30" v-else-if="person">
    <header
      class="bg-white/95 backdrop-blur sticky top-3 z-10 mx-4 rounded-2xl border border-pink-100 shadow-sm transition-all duration-400 ease-out"
      :class="{ '-translate-y-[calc(100%+1rem)] opacity-0': headerHidden }"
    >
      <div class="max-w-3xl mx-auto px-3 sm:px-6 py-4 flex flex-wrap items-center gap-2 sm:gap-4">
        <button @click="goBack" class="w-8 h-8 shrink-0 flex items-center justify-center rounded-full bg-pink-50 text-primary transition-all duration-300 hover:bg-primary hover:text-white hover:scale-110 active:scale-95 text-lg">&larr;</button>
        <h1 class="text-base sm:text-lg font-bold text-gray-900 truncate max-w-[60%]">{{ person.name }}</h1>
        <span v-if="person.remark" class="text-xs sm:text-sm text-gray-400 truncate max-w-[40%]">{{ person.remark }}</span>
      </div>
    </header>

    <main class="max-w-3xl mx-auto px-6 py-8 space-y-8">
      <div class="bg-white rounded-xl p-6 flex items-start gap-5 shadow-sm border border-pink-50 animate-fade-in-up">
        <img
          :src="getThumbUrl(person.avatar) || '/default-avatar.svg'"
          class="w-20 h-20 rounded-full object-cover bg-pink-50 transition-transform duration-400 hover:scale-110 hover:shadow-lg hover:rotate-3"
          @error="e => { if (person.avatar && e.target.src !== person.avatar) e.target.src = person.avatar }"
        />
        <div class="space-y-2 flex-1">
          <div class="flex items-center gap-2">
            <h2 class="text-xl font-bold text-gray-900">{{ person.name }}</h2>
            <span v-if="person.importance" class="text-primary text-sm animate-float" style="animation-delay: -1s">
              {{ '★'.repeat(person.importance) }}
            </span>
          </div>
          <p v-if="person.signature" class="text-gray-500 text-sm">{{ person.signature }}</p>
          <p v-if="person.location" class="text-gray-400 text-xs">{{ person.location }}</p>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="tag in person.circle_tags"
              :key="tag"
              class="px-2 py-0.5 text-xs rounded-full bg-pink-50 text-primary transition-all duration-200 hover:scale-110 hover:bg-primary hover:text-white cursor-default"
            >{{ tag }}</span>
            <span
              v-for="tag in person.impression_tags"
              :key="tag"
              class="px-2 py-0.5 text-xs rounded-full bg-blue-50 text-blue-600 transition-all duration-200 hover:scale-110 hover:bg-blue-400 hover:text-white cursor-default"
            >{{ tag }}</span>
          </div>
        </div>
      </div>

      <section v-if="boardType === 'image' && person.avatar" class="bg-white rounded-xl overflow-hidden shadow-sm border border-pink-50 animate-fade-in-up" style="animation-delay: 0.1s">
        <div class="relative group">
          <img
            :src="getMediumUrl(person.avatar)"
            :alt="person.name"
            class="w-full block"
            @error="e => { if (person.avatar && e.target.src !== person.avatar) e.target.src = person.avatar }"
          />
          <a
            v-if="person.allow_download"
            :href="person.avatar"
            :download="person.name"
            class="absolute bottom-3 right-3 flex items-center gap-1.5 px-3 py-2 bg-black/50 hover:bg-black/70 text-white text-xs rounded-xl backdrop-blur-sm transition-all duration-300 hover:scale-105 active:scale-95 opacity-0 group-hover:opacity-100"
            title="下载原图"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5 5-5M12 15V3"/></svg>
            下载原图
          </a>
        </div>
      </section>

      <section v-if="contentBlocks.length > 0" class="bg-white rounded-xl p-6 shadow-sm border border-pink-50 animate-fade-in-up" style="animation-delay: 0.1s">
        <h3 class="font-bold mb-4 text-gray-800">内容</h3>
        <div class="space-y-5">
          <template v-for="(blk, i) in contentBlocks" :key="i">
            <p v-if="blk.type === 'text'" class="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">{{ blk.value }}</p>
            <div v-else-if="blk.type === 'image'" class="relative group">
              <img
                :src="getMediumUrl(blk.url)"
                :alt="blk.alt"
                :style="{ maxWidth: blk.w ? blk.w + 'px' : '100%', height: blk.h ? blk.h + 'px' : 'auto' }"
                class="rounded-xl cursor-pointer transition-all duration-400 hover:shadow-xl hover:scale-[1.02] max-h-[70vh] object-contain"
                @click="openLightbox({ url: getMediumUrl(blk.url), alt: blk.alt })"
                @error="e => { if (blk.url && e.target.src !== blk.url) e.target.src = blk.url; else e.target.style.display = 'none' }"
              />
            </div>
          </template>
        </div>
        <div v-if="originalImages.length > 0" class="mt-5 text-center animate-fade-in-up" style="animation-delay: 0.2s">
          <button
            @click="openOriginalLightbox"
            class="px-4 py-2 text-sm text-primary border border-primary/30 rounded-lg transition-all duration-300 hover:bg-primary hover:text-white hover:shadow-lg active:scale-95"
          >查看原图 ({{ originalImages.length }}张)</button>
        </div>
      </section>

      <Teleport to="body">
        <Transition name="lightbox">
          <div v-if="lightbox.show" class="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-8 backdrop-blur-sm" @click="closeLightbox">
            <img :src="lightbox.url" :alt="lightbox.alt" class="max-w-full max-h-full object-contain rounded-xl animate-scale-in" @click.stop />
            <button @click="closeLightbox" class="absolute top-4 right-4 text-white text-3xl transition-all duration-300 hover:text-gray-300 hover:scale-110 active:scale-90">&times;</button>
            <p v-if="lightbox.alt" class="absolute bottom-4 text-white/70 text-sm">{{ lightbox.alt }}</p>
          </div>
        </Transition>
      </Teleport>

      <section v-if="boardType === 'friend'" class="bg-white rounded-xl p-6 shadow-sm border border-pink-50 animate-fade-in-up" style="animation-delay: 0.2s">
        <h3 class="font-bold mb-4 text-primary">{{ labels.personDetailAccounts }}</h3>
        <div v-if="accounts.length === 0" class="text-sm text-gray-400">{{ labels.noAccounts }}</div>
        <div v-for="a in accounts" :key="a.id" class="flex items-center gap-3 py-2 border-b border-pink-50 last:border-0 transition-all duration-300 hover:bg-pink-50/30 px-2 rounded-lg">
          <img
            :src="getThumbUrl(a.current_avatar) || '/default-avatar.svg'"
            class="w-9 h-9 rounded-full object-cover bg-pink-50 transition-transform duration-300 hover:scale-125"
            @error="e => { if (a.current_avatar && e.target.src !== a.current_avatar) e.target.src = a.current_avatar }"
          />
          <div>
            <p class="text-sm font-medium text-gray-900">{{ a.current_nickname || a.account_identifier }}</p>
            <p class="text-xs text-gray-400">{{ a.account_type }} · {{ a.account_identifier }}</p>
          </div>
        </div>
      </section>

      <section v-if="meetings.length > 0" class="bg-white rounded-xl p-6 shadow-sm border border-pink-50 animate-fade-in-up" style="animation-delay: 0.3s">
        <h3 class="font-bold mb-4 text-primary">{{ labels.personDetailMeetings }}</h3>
        <div v-for="m in meetings" :key="m.id" class="text-sm text-gray-600 py-1 transition-all duration-200 hover:translate-x-1">
          {{ m.met_at ? `[${m.met_at}] ` : '' }}{{ m.description }}
        </div>
      </section>

      <section v-if="relations.length > 0" class="bg-white rounded-xl p-6 shadow-sm border border-pink-50 animate-fade-in-up" style="animation-delay: 0.4s">
        <h3 class="font-bold mb-4 text-primary">{{ labels.personDetailRelations }}</h3>
        <div v-for="r in relations" :key="r.id" class="text-sm text-gray-600 py-1 transition-all duration-200 hover:translate-x-1">
          {{ r.relation_type || labels.personDetailRelationFallback }}
        </div>
      </section>

    </main>
  </div>
</template>

<style scoped>
.lightbox-enter-active {
  transition: opacity 0.3s ease;
}
.lightbox-enter-active img {
  animation: scaleIn 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}
.lightbox-leave-active {
  transition: opacity 0.25s ease;
}
.lightbox-enter-from, .lightbox-leave-to {
  opacity: 0;
}
</style>
