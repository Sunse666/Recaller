<script setup>
import { ref, watch } from 'vue'

const props = defineProps({ placeholder: { type: String, default: '搜索...' } })
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
    <span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 text-sm">🔍</span>
    <input
      v-model="query"
      type="text"
      :placeholder="props.placeholder"
      class="w-full pl-10 pr-4 py-2.5 text-sm rounded-xl bg-pink-50 text-gray-900 placeholder-gray-400 border border-pink-100 outline-none focus:border-primary focus:bg-pink-50/50 transition-all"
    />
  </div>
</template>
