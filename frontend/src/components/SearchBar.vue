<script setup>
import { ref, watch } from 'vue'

const props = defineProps({ placeholder: { type: String, default: '搜索...' } })
const emit = defineEmits(['search'])
const query = ref('')
const focused = ref(false)

let timer
watch(query, (val) => {
  clearTimeout(timer)
  timer = setTimeout(() => emit('search', val), 300)
})
</script>

<template>
  <div class="relative group">
    <span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 text-sm transition-transform duration-300"
      :class="{ 'scale-125 text-primary': focused || query }"
    ></span>
    <input
      v-model="query"
      type="text"
      :placeholder="props.placeholder"
      @focus="focused = true"
      @blur="focused = false"
      class="w-full min-w-[100px] pl-10 pr-4 py-2.5 text-sm rounded-xl bg-pink-50 text-gray-900 placeholder-gray-400 border border-pink-100 outline-none transition-all duration-300 ease-out focus:scale-[1.02] focus:bg-pink-50/80 focus:border-primary focus:shadow-[0_0_0_4px_rgba(236,72,153,0.1)]"
    />
  </div>
</template>
