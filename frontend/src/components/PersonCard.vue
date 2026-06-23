<script setup>
import { computed } from 'vue'

const props = defineProps({
  person: { type: Object, required: true },
  image: { type: String, default: '' },
})
defineEmits(['click'])

const initials = computed(() => (props.person.name || '?')[0])
</script>

<template>
  <div
    @click="$emit('click')"
    class="group relative w-full overflow-hidden cursor-pointer"
  >
    <img
      v-if="image"
      :src="image"
      class="w-full h-auto block"
    />
    <div
      v-else
      class="w-full bg-gradient-to-br from-zinc-700 to-zinc-800 flex items-center justify-center"
      style="aspect-ratio: 3/4"
    >
      <span class="text-6xl font-bold text-zinc-600">{{ initials }}</span>
    </div>

    <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-90 group-hover:opacity-100 transition-opacity" />
    <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />

    <div class="absolute bottom-0 left-0 right-0 p-3 md:p-5">
      <div class="flex items-center gap-2 mb-1">
        <h3 class="text-white font-bold text-sm md:text-lg truncate">{{ person.name }}</h3>
        <span v-if="person.importance" class="text-xs shrink-0">
          {{ '⭐'.repeat(Math.min(person.importance, 5)) }}
        </span>
      </div>
      <p v-if="person.remark" class="text-white/70 text-xs md:text-sm truncate mb-1">{{ person.remark }}</p>

      <div class="opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <p v-if="person.signature" class="text-white/60 text-xs line-clamp-2 mb-2">{{ person.signature }}</p>
        <div class="flex flex-wrap gap-1">
          <span
            v-for="tag in person.impression_tags?.slice(0, 2)"
            :key="tag"
            class="px-2 py-0.5 text-[10px] rounded-full bg-white/20 text-white/90 backdrop-blur-sm"
          >{{ tag }}</span>
          <span
            v-for="tag in person.circle_tags?.slice(0, 2)"
            :key="tag"
            class="px-2 py-0.5 text-[10px] rounded-full bg-white/15 text-white/80 backdrop-blur-sm"
          >{{ tag }}</span>
        </div>
        <p v-if="person.birthday" class="text-white/50 text-[10px] mt-2">🎂 {{ person.birthday }}</p>
      </div>
    </div>
  </div>
</template>
