<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/client'
import { useBoardStore } from '../../stores/boards'
import { useLabels } from '../../utils/labels'

const labels = useLabels()
const boardStore = useBoardStore()
const persons = ref([])
const allAccounts = ref({})
const loading = ref(false)
const search = ref('')

const view = ref('list')
const editingPerson = ref(null)
const saving = ref(false)
const savingMessage = ref('')

const form = ref({ name: '', remark: '', signature: '', location: '', avatar: '', circle_tags: [], impression_tags: [], importance: 0, notes: '', birthday: '' })
const circleInput = ref('')
const impressionInput = ref('')

const accounts = ref([])
const accForm = ref({ account_type: 'QQ', account_identifier: '', current_nickname: '', current_avatar: '' })
const accSaving = ref(false)

function addCircleTag() { const v = circleInput.value.trim(); if (v && !form.value.circle_tags.includes(v)) form.value.circle_tags.push(v); circleInput.value = '' }
function removeCircleTag(i) { form.value.circle_tags.splice(i, 1) }
function addImpressionTag() { const v = impressionInput.value.trim(); if (v && !form.value.impression_tags.includes(v)) form.value.impression_tags.push(v); impressionInput.value = '' }
function removeImpressionTag(i) { form.value.impression_tags.splice(i, 1) }

async function loadPersons() {
  loading.value = true
  await boardStore.fetchBoards()
  if (boardStore.currentBoardId) {
    persons.value = await api.listPersons(search.value, boardStore.currentBoardId)
    for (const p of persons.value) {
      if (!allAccounts.value[p.id]) allAccounts.value[p.id] = await api.listAccounts(p.id)
    }
  }
  loading.value = false
}

function goCreate() { form.value = { name: '', remark: '', signature: '', location: '', avatar: '', circle_tags: [], impression_tags: [], importance: 0, notes: '', birthday: '' }; accounts.value = []; view.value = 'create' }

async function goEdit(p) {
  form.value = { name: p.name, remark: p.remark || '', signature: p.signature || '', location: p.location || '', avatar: p.avatar || '', circle_tags: [...(p.circle_tags || [])], impression_tags: [...(p.impression_tags || [])], importance: p.importance || 0, notes: p.notes || '', birthday: p.birthday || '' }
  editingPerson.value = p
  accounts.value = await api.listAccounts(p.id)
  view.value = 'edit'
}

function goList() { view.value = 'list'; editingPerson.value = null; loadPersons() }

async function doSave() {
  if (!form.value.name.trim()) return
  saving.value = true
  try {
    if (view.value === 'create') {
      await api.createPerson({ ...form.value, board_id: boardStore.currentBoardId })
    } else {
      await api.updatePerson(editingPerson.value.id, form.value)
    }
    savingMessage.value = labels.value.saveSuccess
    setTimeout(goList, 600)
  } catch (e) { savingMessage.value = '错误: ' + e.message }
  finally { saving.value = false }
}

async function doDelete(id) { if (!confirm(labels.value.confirmDeleteCard)) return; await api.deletePerson(id); delete allAccounts.value[id]; loadPersons() }

async function doAddAccount() {
  if (!accForm.value.account_identifier.trim()) return
  accSaving.value = true
  try { await api.createAccount(editingPerson.value.id, { ...accForm.value }); accounts.value = await api.listAccounts(editingPerson.value.id); accForm.value = { account_type: 'QQ', account_identifier: '', current_nickname: '', current_avatar: '' } }
  catch (e) { alert(e.message) }
  finally { accSaving.value = false }
}
async function doDeleteAccount(accId) { if (!confirm(labels.value.confirmDeleteAccount)) return; await api.deleteAccount(editingPerson.value.id, accId); accounts.value = await api.listAccounts(editingPerson.value.id) }

onMounted(loadPersons)
</script>

<template>
  <div class="max-w-5xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-lg font-bold text-gray-900">{{ labels.cardManage }}</h2>
        <p class="text-xs text-gray-400 mt-1">画板: {{ boardStore.currentBoard?.name || '加载中...' }}</p>
      </div>
      <select
        v-if="boardStore.boards.length > 1"
        :value="boardStore.currentBoardId"
        @change="boardStore.setCurrentBoard(Number($event.target.value)); loadPersons()"
        class="text-sm px-3 py-2 border border-pink-100 rounded-xl outline-none"
      >
        <option v-for="b in boardStore.boards" :key="b.id" :value="b.id">{{ b.icon }} {{ b.name }}</option>
      </select>
    </div>

    <template v-if="view === 'list'">
      <div class="flex items-center justify-between mb-4">
        <button @click="goCreate" class="px-4 py-2 bg-primary text-white text-sm rounded-xl hover:bg-primary-dark transition shadow-sm">{{ labels.addCard }}</button>
        <input v-model="search" @input="loadPersons" :placeholder="labels.searchCard" class="w-full max-w-xs px-4 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary transition ml-4" />
      </div>

      <div v-if="loading" class="text-center text-gray-400 py-10">{{ labels.loading }}</div>
      <div v-else-if="persons.length === 0" class="text-center text-gray-400 py-10">{{ labels.noData }}</div>
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <div v-for="p in persons" :key="p.id" class="bg-white rounded-xl border border-pink-50 p-4 hover:shadow-md transition">
          <div class="flex items-center gap-3 mb-2">
            <img :src="p.avatar || '/default-avatar.svg'" class="w-10 h-10 rounded-full object-cover bg-pink-100" />
            <div class="flex-1 min-w-0">
              <p class="font-medium text-gray-900 truncate">{{ p.name }}</p>
              <p v-if="p.remark" class="text-xs text-gray-400 truncate">{{ p.remark }}</p>
            </div>
            <span class="text-primary text-xs">{{ '★'.repeat(p.importance) }}</span>
          </div>
          <div class="flex gap-1 mb-2">
            <span v-for="t in p.circle_tags" :key="t" class="px-1.5 py-0.5 text-[10px] bg-blue-50 text-blue-600 rounded-full">{{ t }}</span>
          </div>
          <div class="flex gap-2 text-xs">
            <button @click="goEdit(p)" class="text-primary hover:underline">{{ labels.edit }}</button>
            <button @click="doDelete(p.id)" class="text-red-400 hover:underline">{{ labels.delete }}</button>
          </div>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="bg-white rounded-xl border border-pink-100 p-6 max-w-lg">
        <div class="flex items-center gap-3 mb-5">
          <button @click="goList" class="text-gray-400 hover:text-gray-600">&larr; 返回</button>
          <h3 class="font-bold">{{ view === 'create' ? labels.addCardTitle : labels.editCardTitle }}</h3>
        </div>

        <div class="space-y-3">
          <input v-model="form.name" :placeholder="labels.cardNameLabel" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
          <input v-model="form.remark" placeholder="备注" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
          <input v-model="form.signature" placeholder="签名" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
          <input v-model="form.location" placeholder="地区" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
          <input v-model="form.birthday" placeholder="生日 如 01-15" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
          <textarea v-model="form.notes" rows="2" placeholder="备注" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary resize-none"></textarea>

          <div>
            <label class="text-xs text-gray-400 mb-1 block">圈子标签</label>
            <div class="flex gap-1 mb-1">
              <input v-model="circleInput" @keyup.enter="addCircleTag" :placeholder="labels.tagPlaceholder" class="flex-1 px-3 py-1.5 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
              <button @click="addCircleTag" class="px-3 py-1.5 text-sm bg-pink-50 rounded-xl">{{ labels.addTag }}</button>
            </div>
            <div class="flex flex-wrap gap-1">
              <span v-for="(t, i) in form.circle_tags" :key="i" class="px-2 py-0.5 text-xs bg-blue-50 text-blue-600 rounded-full">{{ t }} <button @click="removeCircleTag(i)" class="ml-1">&times;</button></span>
            </div>
          </div>
        </div>

        <div class="flex gap-2 mt-5">
          <button @click="doSave" :disabled="saving" class="px-6 py-2 bg-primary text-white text-sm rounded-xl hover:bg-primary-dark disabled:opacity-50 transition">{{ labels.save }}</button>
          <button @click="goList" class="px-6 py-2 text-sm border border-pink-100 rounded-xl text-gray-500 hover:bg-pink-50">{{ labels.cancel }}</button>
        </div>
        <p v-if="savingMessage" class="text-xs mt-2" :class="savingMessage.includes('错误') ? 'text-red-500' : 'text-green-500'">{{ savingMessage }}</p>
      </div>
    </template>
  </div>
</template>
