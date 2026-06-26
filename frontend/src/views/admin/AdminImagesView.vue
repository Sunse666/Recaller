<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from '../../api/client'
import { useBoardStore } from '../../stores/boards'
import { useLabels } from '../../utils/labels'
import { getThumbUrl } from '../../utils/images'

const boardStore = useBoardStore()
const labels = useLabels()

const images = ref([])
const uploading = ref(false)
const loading = ref(true)
const copied = ref('')
const page = ref(1)
const pageSize = 24
const total = ref(0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

async function loadImages() {
  loading.value = true
  await boardStore.fetchBoards()

  try {
    const data = await api.listImages(page.value, pageSize)
    const result = (data.items || []).map(f => ({
      url: f.url, type: '图池', size: f.size, mtime: f.mtime,
    }))
    total.value = data.total || result.length

    const seen = new Set(result.map(r => r.url))
    for (const b of boardStore.boards) {
      const fc = typeof b.field_config === 'object' ? b.field_config : {}
      for (const url of (fc.bannerImages || [])) {
        const existing = result.find(r => r.url === url)
        if (existing) existing.board = b.name
      }
    }

    for (const b of boardStore.boards) {
      try {
        const persons = await api.listPersons('', b.id)
        for (const p of persons) {
          if (p.avatar && seen.has(p.avatar)) {
            const r = result.find(r => r.url === p.avatar)
            if (r && !r.person) { r.person = p.name; r.type = '头像' }
          }
          if (p.card_bg && seen.has(p.card_bg)) {
            const r = result.find(r => r.url === p.card_bg)
            if (r && !r.person) { r.person = p.name; r.type = '卡片背景' }
          }
        }
      } catch { }
    }

    images.value = result
  } catch { images.value = []; total.value = 0 }
  loading.value = false
}

function goPage(p) {
  if (p < 1 || p > totalPages.value) return
  page.value = p
  loadImages()
}

async function doUpload(e) {
  const file = e.target.files?.[0]; if (!file) return
  if (file.size > 10 * 1024 * 1024) { alert(labels.value.uploadFail + ': 文件过大，最大 10MB'); return }
  uploading.value = true
  try {
    const data = await api.upload(file)
    const b = boardStore.currentBoard
    const fc = (b && typeof b.field_config === 'object') ? { ...b.field_config } : {}
    fc.bannerImages = [...(fc.bannerImages || []), data.url]
    await boardStore.updateBoard(boardStore.currentBoardId, { field_config: fc })
    loadImages()
  } catch (err) {
    alert(labels.value.uploadFail + ': ' + (err.message || ''))
  }
  finally { uploading.value = false; e.target.value = '' }
}

async function doDelete(url) {
  if (!confirm(labels.value.deleteImageConfirm)) return
  const b = boardStore.currentBoard
  const fc = (b && typeof b.field_config === 'object') ? { ...b.field_config } : {}
  fc.bannerImages = (fc.bannerImages || []).filter(u => u !== url)
  await boardStore.updateBoard(boardStore.currentBoardId, { field_config: fc })
  images.value = images.value.filter(img => !(img.url === url && img.type === '图池'))
}

async function copyUrl(url) {
  try {
    await navigator.clipboard.writeText(url)
    copied.value = url
    setTimeout(() => { copied.value = '' }, 1500)
  } catch {
    const el = document.createElement('textarea'); el.value = url; document.body.appendChild(el)
    el.select(); document.execCommand('copy'); document.body.removeChild(el)
    copied.value = url
    setTimeout(() => { copied.value = '' }, 1500)
  }
}

onMounted(loadImages)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-5">
      <h2 class="text-lg font-bold text-gray-900">{{ labels.imagesTitle }}</h2>
      <label class="px-4 py-2 bg-primary text-white text-sm rounded-xl hover:bg-primary-dark transition shadow-sm cursor-pointer">
        {{ uploading ? labels.uploading : labels.uploadImage }}
        <input type="file" accept="image/*" @change="doUpload" class="hidden" />
      </label>
    </div>

    <p class="text-xs text-gray-400 mb-4">{{ labels.imagesHint }}</p>

    <div v-if="loading" class="text-center text-gray-400 py-10">{{ labels.loading }}</div>

    <div v-else-if="images.length === 0" class="text-center text-gray-400 py-20">
      <p class="text-lg">{{ labels.noImages }}</p>
      <p class="text-sm mt-1">{{ labels.noImagesHint }}</p>
    </div>

    <template v-else>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
        <div v-for="(img, i) in images" :key="i"
          class="bg-white rounded-xl border border-pink-50 overflow-hidden hover:shadow-md transition group relative animate-fade-in-up"
          :style="{ animationDelay: (i % pageSize) * 0.03 + 's' }"
        >
          <img :src="getThumbUrl(img.url)" loading="lazy" class="w-full aspect-square object-cover" @error="e => { if (img.url && e.target.src !== img.url) e.target.src = img.url }" />
          <div class="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100">
            <button @click="copyUrl(img.url)"
              class="px-3 py-1.5 bg-white text-gray-800 text-xs rounded-lg hover:bg-gray-100 transition"
            >{{ copied === img.url ? labels.copied : labels.copyUrl }}</button>
            <button v-if="img.type === '图池'" @click="doDelete(img.url)"
              class="px-3 py-1.5 bg-red-400 text-white text-xs rounded-lg hover:bg-red-500 transition"
            >{{ labels.deleteImage }}</button>
          </div>
          <div class="p-2">
            <span class="text-[10px] px-1.5 py-0.5 rounded-full"
              :class="{
                'bg-blue-50 text-blue-600': img.type === '图池',
                'bg-pink-50 text-pink-600': img.type === '头像',
                'bg-green-50 text-green-600': img.type === '卡片背景',
              }"
            >{{ img.type }}</span>
            <span v-if="img.person" class="text-xs text-gray-400 ml-1">{{ img.person }}</span>
            <span v-if="img.board" class="text-xs text-gray-300 ml-1">{{ img.board }}</span>
          </div>
        </div>
      </div>

      <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 mt-6">
        <button @click="goPage(page - 1)" :disabled="page <= 1"
          class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 hover:bg-pink-50 disabled:opacity-30 disabled:cursor-not-allowed transition"
        >上一页</button>
        <template v-for="p in totalPages" :key="p">
          <button v-if="p === 1 || p === totalPages || Math.abs(p - page) <= 2"
            @click="goPage(p)"
            :class="[
              'w-8 h-8 text-sm rounded-lg transition',
              p === page ? 'bg-primary text-white font-medium' : 'hover:bg-pink-50 text-gray-600'
            ]"
          >{{ p }}</button>
          <span v-else-if="p === page - 3 || p === page + 3" class="text-gray-300">...</span>
        </template>
        <button @click="goPage(page + 1)" :disabled="page >= totalPages"
          class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 hover:bg-pink-50 disabled:opacity-30 disabled:cursor-not-allowed transition"
        >下一页</button>
        <span class="text-xs text-gray-400 ml-2">共 {{ total }} 张</span>
      </div>
    </template>
  </div>
</template>
