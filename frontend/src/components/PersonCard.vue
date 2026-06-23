<script setup>
import { computed } from 'vue'

const props = defineProps({
  person: { type: Object, required: true },
  gradient: { type: String, default: 'from-blue-500 to-cyan-500' },
})
defineEmits(['click'])

const initials = computed(() => {
  return (props.person.name || '?')[0]
})
</script>

<template>
  <div
    @click="$emit('click')"
    class="group relative bg-white rounded-2xl overflow-hidden cursor-pointer hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border border-gray-100"
  >
    <!-- 顶部渐变条 -->
    <div :class="['h-2 bg-gradient-to-r', gradient]" />

    <div class="p-6">
      <!-- 头像 + 姓名区 -->
      <div class="flex items-start gap-4 mb-4">
        <div class="relative shrink-0">
          <div v-if="person.avatar" class="w-16 h-16 rounded-2xl overflow-hidden ring-2 ring-gray-100">
            <img :src="person.avatar" class="w-full h-full object-cover" />
          </div>
          <div v-else :class="['w-16 h-16 rounded-2xl bg-gradient-to-br flex items-center justify-center text-white text-2xl font-bold', gradient]">
            {{ initials }}
          </div>
          <span v-if="person.importance" class="absolute -bottom-1 -right-1 text-xs">
            {{ '⭐'.repeat(Math.min(person.importance, 3)) }}
          </span>
        </div>

        <div class="flex-1 min-w-0 pt-1">
          <h3 class="text-base font-bold text-slate-800 truncate">{{ person.name }}</h3>
          <p v-if="person.remark" class="text-sm text-slate-400 truncate mt-0.5">{{ person.remark }}</p>
          <p v-if="person.location" class="text-xs text-slate-300 mt-0.5">📍 {{ person.location }}</p>
        </div>
      </div>

      <!-- 签名 -->
      <p v-if="person.signature" class="text-sm text-slate-500 leading-relaxed mb-3 line-clamp-2">
        {{ person.signature }}
      </p>

      <!-- 标签 -->
      <div class="flex flex-wrap gap-1.5 mb-3">
        <span
          v-for="tag in person.impression_tags?.slice(0, 3)"
          :key="tag"
          class="px-2.5 py-1 text-xs rounded-full bg-amber-50 text-amber-600 font-medium"
        >{{ tag }}</span>
        <span
          v-for="tag in person.circle_tags?.slice(0, 3)"
          :key="tag"
          class="px-2.5 py-1 text-xs rounded-full bg-blue-50 text-blue-600 font-medium"
        >{{ tag }}</span>
      </div>

      <!-- 底部信息 -->
      <div class="flex items-center justify-between text-xs text-slate-400 pt-3 border-t border-gray-50">
        <span>{{ person.account_count }} 个账号</span>
        <span v-if="person.birthday" class="text-slate-300">🎂 {{ person.birthday }}</span>
      </div>
    </div>
  </div>
</template>
