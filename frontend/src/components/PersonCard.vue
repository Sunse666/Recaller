<script setup>
import { computed } from 'vue'

const props = defineProps({
  person: { type: Object, required: true },
  image: { type: String, default: '' },
})
defineEmits(['click'])

const initials = computed(() => (props.person.name || '?')[0])
const isBgColor = computed(() => props.image && props.image.startsWith('bg:'))
const bgColor = computed(() => isBgColor.value ? props.image.slice(3) : null)
</script>

<template>
  <div
    @click="$emit('click')"
    class="group relative w-full overflow-hidden cursor-pointer rounded-xl shadow-md hover:shadow-xl transition-shadow duration-300"
  >
    <img
      v-if="image && !isBgColor"
      :src="image"
      class="w-full h-auto block"
    />
    <div
      v-else
      class="w-full flex items-center justify-center"
      :style="{ backgroundColor: bgColor || undefined, aspectRatio: '3/4' }"
      :class="{ 'bg-gradient-to-br from-pink-100 to-blue-50': !bgColor }"
    >
      <span class="text-6xl font-bold" :class="bgColor ? 'text-white/40' : 'text-primary/30'">{{ initials }}</span>
    </div>

    <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent opacity-90 group-hover:opacity-100 transition-opacity" />
    <div class="absolute inset-0 bg-primary/0 group-hover:bg-primary/5 transition-colors" />

    <div class="absolute bottom-0 left-0 right-0 p-3 md:p-5">
      <div class="flex items-center gap-2 mb-1">
        <h3 class="text-white font-bold text-sm md:text-lg truncate">{{ person.name }}</h3>
        <span v-if="person.importance" class="text-xs shrink-0">
          <span class="text-pink-300">{{ '★'.repeat(Math.min(person.importance, 5)) }}</span>
        </span>
      </div>
      <p v-if="person.remark" class="text-white/70 text-xs md:text-sm truncate mb-1">{{ person.remark }}</p>

      <div class="opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <p v-if="person.signature" class="text-white/60 text-xs line-clamp-2 mb-2">{{ person.signature }}</p>
        <div class="flex flex-wrap gap-1">
          <span
            v-for="tag in person.impression_tags?.slice(0, 2)"
            :key="tag"
            class="px-2 py-0.5 text-[10px] rounded-full bg-primary/30 text-white/90 backdrop-blur-sm"
          >{{ tag }}</span>
          <span
            v-for="tag in person.circle_tags?.slice(0, 2)"
            :key="tag"
            class="px-2 py-0.5 text-[10px] rounded-full bg-blue-400/30 text-white/90 backdrop-blur-sm"
          >{{ tag }}</span>
        </div>
        <p v-if="person.birthday" class="text-pink-200 text-[10px] mt-2">🎂 {{ person.birthday }}</p>
      </div>
    </div>
  </div>
</template>
