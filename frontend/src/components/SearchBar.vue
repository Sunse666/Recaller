<script setup>
import { ref, watch } from 'vue'

const emit = defineEmits(['search'])
const query = ref('')

let timer
watch(query, (val) => {
  clearTimeout(timer)
  timer = setTimeout(() => emit('search', val), 300)
})
</script>

<template>
  <div class="relative">
    <span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-sm">🔍</span>
    <input
      v-model="query"
      type="text"
      placeholder="搜索群友昵称、账号..."
      class="w-full pl-10 pr-4 py-2.5 text-sm rounded-xl bg-slate-100 border-0 outline-none focus:bg-white focus:ring-2 focus:ring-blue-400/30 focus:shadow-sm transition-all"
    />
  </div>
</template>
