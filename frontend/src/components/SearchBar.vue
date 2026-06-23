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
    <span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500 text-sm">🔍</span>
    <input
      v-model="query"
      type="text"
      placeholder="搜索群友昵称、账号..."
      class="w-full pl-10 pr-4 py-2.5 text-sm rounded-xl bg-zinc-800 text-white placeholder-zinc-500 border border-zinc-700 outline-none focus:border-zinc-500 focus:bg-zinc-700/50 transition-all"
    />
  </div>
</template>
