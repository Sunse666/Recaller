<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()
const person = ref(null)
const accounts = ref([])
const meetings = ref([])
const relations = ref([])

async function loadPerson() {
  // personName from URL, need to find by name
  const name = route.params.personName
  const persons = await api.listPersons(name)
  const found = persons.find(p => p.name === name || p.remark === name)
  if (!found) return router.replace('/')
  person.value = await api.getPerson(found.id)
  accounts.value = await api.listAccounts(found.id)
  meetings.value = await api.listMeetings(found.id)
  relations.value = await api.listRelations(found.id)
}

function goBack() {
  router.push('/')
}

onMounted(loadPerson)
watch(() => route.params.personName, loadPerson)
</script>

<template>
  <div class="min-h-screen bg-[#f5f5f5]" v-if="person">
    <header class="bg-white shadow-sm sticky top-0 z-10">
      <div class="max-w-3xl mx-auto px-6 py-4 flex items-center gap-4">
        <button @click="goBack" class="text-gray-500 hover:text-gray-700 text-lg">&larr;</button>
        <h1 class="text-lg font-bold">{{ person.name }}</h1>
        <span v-if="person.remark" class="text-sm text-gray-400">{{ person.remark }}</span>
      </div>
    </header>

    <main class="max-w-3xl mx-auto px-6 py-8 space-y-8">
      <div class="bg-white rounded-xl p-6 flex items-start gap-5">
        <img
          :src="person.avatar || '/default-avatar.svg'"
          class="w-20 h-20 rounded-full object-cover bg-gray-200"
        />
        <div class="space-y-2 flex-1">
          <div class="flex items-center gap-2">
            <h2 class="text-xl font-bold">{{ person.name }}</h2>
            <span v-if="person.importance" class="text-yellow-400 text-sm">
              {{ '⭐'.repeat(person.importance) }}
            </span>
          </div>
          <p v-if="person.signature" class="text-gray-500 text-sm">{{ person.signature }}</p>
          <p v-if="person.location" class="text-gray-400 text-xs">{{ person.location }}</p>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="tag in person.circle_tags"
              :key="tag"
              class="px-2 py-0.5 text-xs rounded-full bg-blue-50 text-blue-600"
            >{{ tag }}</span>
            <span
              v-for="tag in person.impression_tags"
              :key="tag"
              class="px-2 py-0.5 text-xs rounded-full bg-amber-50 text-amber-600"
            >{{ tag }}</span>
          </div>
          <p v-if="person.notes" class="text-gray-500 text-sm mt-2">{{ person.notes }}</p>
        </div>
      </div>

      <section class="bg-white rounded-xl p-6">
        <h3 class="font-bold mb-4">账号</h3>
        <div v-if="accounts.length === 0" class="text-sm text-gray-400">暂无账号</div>
        <div v-for="a in accounts" :key="a.id" class="flex items-center gap-3 py-2 border-b last:border-0">
          <img
            :src="a.current_avatar || '/default-avatar.svg'"
            class="w-9 h-9 rounded-full object-cover bg-gray-200"
          />
          <div>
            <p class="text-sm font-medium">{{ a.current_nickname || a.account_identifier }}</p>
            <p class="text-xs text-gray-400">{{ a.account_type }} · {{ a.account_identifier }}</p>
          </div>
        </div>
      </section>

      <section v-if="meetings.length > 0" class="bg-white rounded-xl p-6">
        <h3 class="font-bold mb-4">相遇记录</h3>
        <div v-for="m in meetings" :key="m.id" class="text-sm text-gray-600 py-1">
          {{ m.met_at ? `[${m.met_at}] ` : '' }}{{ m.description }}
        </div>
      </section>

      <section v-if="relations.length > 0" class="bg-white rounded-xl p-6">
        <h3 class="font-bold mb-4">关系</h3>
        <div v-for="r in relations" :key="r.id" class="text-sm text-gray-600 py-1">
          {{ r.relation_type || '关联' }}
        </div>
      </section>

    </main>
  </div>
</template>
