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

async function loadPersons() {
  loading.value = true
  persons.value = await api.listPersons(search.value)
  loading.value = false
}

function onSearch(val) {
  search.value = val
  loadPersons()
}

function goDetail(name) {
  router.push(`/${encodeURIComponent(name)}`)
}

const gradients = [
  'from-indigo-500 via-purple-500 to-pink-500',
  'from-emerald-500 to-teal-500',
  'from-amber-500 to-orange-500',
  'from-sky-500 to-cyan-500',
  'from-rose-500 to-red-500',
  'from-violet-500 to-purple-500',
  'from-lime-500 to-green-500',
  'from-fuchsia-500 to-pink-500',
]

onMounted(() => loadPersons())
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
    <!-- 顶栏 -->
    <header class="sticky top-0 z-10 backdrop-blur-xl bg-white/70 border-b border-gray-100">
      <div class="max-w-5xl mx-auto px-6 py-4 flex items-center gap-6">
        <div class="flex items-center gap-3 shrink-0">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-white font-bold text-sm">
            群
          </div>
          <h1 class="text-lg font-bold text-slate-800">群友记忆助手</h1>
        </div>
        <SearchBar @search="onSearch" class="flex-1 max-w-md" />
      </div>
    </header>

    <main class="max-w-5xl mx-auto px-6 py-10">
      <!-- 标题区 -->
      <div class="mb-8">
        <h2 class="text-2xl font-bold text-slate-800">
          {{ search ? `搜索「${search}」` : '我认识的群友们' }}
        </h2>
        <p class="text-slate-400 mt-1 text-sm">
          {{ persons.length }} 位群友
        </p>
      </div>

      <!-- 加载/空状态 -->
      <div v-if="loading" class="text-center text-slate-400 py-20">
        <div class="w-10 h-10 mx-auto mb-4 rounded-full border-2 border-blue-200 border-t-blue-500 animate-spin" />
        加载中...
      </div>
      <div v-else-if="persons.length === 0" class="text-center text-slate-400 py-20">
        <div class="text-5xl mb-4">🫥</div>
        <p class="text-lg">还没有添加群友</p>
        <p class="text-sm mt-1">去后台管理页面添加第一位群友吧</p>
      </div>

      <!-- 卡片网格 -->
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        <PersonCard
          v-for="(p, i) in persons"
          :key="p.id"
          :person="p"
          :gradient="gradients[i % gradients.length]"
          @click="goDetail(p.name)"
        />
      </div>
    </main>
  </div>
</template>
