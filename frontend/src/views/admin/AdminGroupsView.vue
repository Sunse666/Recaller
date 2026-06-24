<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/client'
import { useBoardStore } from '../../stores/boards'
import { useLabels } from '../../utils/labels'

const labels = useLabels()
const groups = ref([])
const loading = ref(false)
const search = ref('')
const view = ref('list')
const form = ref({ group_number: '', group_name: '', remark: '', tags: [], avatar: '' })
const tagInput = ref('')
const editingGroup = ref(null)
const saving = ref(false)
const savingMessage = ref('')
const showMembers = ref(false)
const currentMembers = ref([])
const currentGroup = ref(null)
const memberForm = ref({ account_id: '', group_nickname: '' })
const allAccounts = ref([])
const accountsLoaded = ref(false)

async function loadGroups() {
  const bs = useBoardStore()
  loading.value = true
  groups.value = await api.listGroups(search.value, bs.currentBoardId)
  loading.value = false
}

function goCreate() {
  form.value = { group_number: '', group_name: '', remark: '', tags: [], avatar: '' }
  editingGroup.value = null
  view.value = 'edit'
}

function goEdit(g) {
  form.value = {
    group_number: g.group_number,
    group_name: g.group_name,
    remark: g.remark || '',
    tags: [...(g.tags || [])],
    avatar: g.avatar || '',
  }
  editingGroup.value = g
  view.value = 'edit'
}

function goList() {
  view.value = 'list'
  loadGroups()
}

function addTag() {
  const v = tagInput.value.trim()
  if (v && !form.value.tags.includes(v)) form.value.tags.push(v)
  tagInput.value = ''
}
function removeTag(i) { form.value.tags.splice(i, 1) }

async function doSave() {
  if (!form.value.group_number.trim() || !form.value.group_name.trim()) return
  saving.value = true
  savingMessage.value = ''
  try {
    if (editingGroup.value) {
      await api.updateGroup(editingGroup.value.id, form.value)
      savingMessage.value = labels.value.saveSuccess
    } else {
      const b = useBoardStore()
      await api.createGroup({ ...form.value, board_id: b.currentBoardId })
      savingMessage.value = labels.value.createSuccess
    }
    setTimeout(goList, 600)
  } catch (e) {
    savingMessage.value = '错误: ' + e.message
  } finally {
    saving.value = false
  }
}

async function doDelete(id) {
  if (!confirm(labels.value.confirmDeleteGroup)) return
  await api.deleteGroup(id)
  loadGroups()
}

async function viewMembers(g) {
  currentGroup.value = g
  if (!accountsLoaded.value) {
    const persons = await api.listPersons()
    allAccounts.value = []
    for (const p of persons) {
      const accounts = await api.listAccounts(p.id)
      allAccounts.value.push(...accounts.map(a => ({ ...a, person_name: p.name })))
    }
    accountsLoaded.value = true
  }
  currentMembers.value = await api.getGroupMembers(g.id)
  showMembers.value = true
}

async function addMember() {
  if (!memberForm.value.account_id) return
  await api.addGroupMember(currentGroup.value.id, {
    account_id: Number(memberForm.value.account_id),
    group_id: currentGroup.value.id,
    group_nickname: memberForm.value.group_nickname,
  })
  memberForm.value = { account_id: '', group_nickname: '' }
  currentMembers.value = await api.getGroupMembers(currentGroup.value.id)
}

async function removeMember(membershipId) {
  await api.removeGroupMember(currentGroup.value.id, membershipId)
  currentMembers.value = await api.getGroupMembers(currentGroup.value.id)
}

onMounted(loadGroups)
</script>

<template>
  <div>
    <template v-if="view === 'list'">
      <div class="flex items-center justify-between mb-5">
        <h2 class="text-lg font-bold">{{ labels.groupManage }}</h2>
        <button @click="goCreate" class="px-4 py-2 bg-primary text-white text-sm rounded-xl hover:bg-primary-dark transition shadow-sm">
          {{ labels.addGroup }}
        </button>
      </div>

      <div class="mb-4">
        <input v-model="search" @input="loadGroups" :placeholder="labels.searchGroup" class="w-full max-w-sm px-4 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary focus:bg-pink-50/30 transition" />
      </div>

      <div class="bg-white rounded-xl border border-pink-100 overflow-hidden">
        <div v-if="loading" class="text-center text-gray-400 py-10">加载中...</div>
        <table v-else-if="groups.length" class="w-full text-sm">
          <thead class="bg-pink-50/30 text-gray-500 text-xs">
            <tr>
              <th class="text-left px-4 py-2.5 font-normal">{{ labels.tableGroupName }}</th>
              <th class="text-left px-4 py-2.5 font-normal">{{ labels.tableGroupNumber }}</th>
              <th class="text-left px-4 py-2.5 font-normal">{{ labels.tableGroupRemark }}</th>
              <th class="text-left px-4 py-2.5 font-normal">{{ labels.tableGroupTags }}</th>
              <th class="text-right px-4 py-2.5 font-normal">{{ labels.tableActions }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="g in groups" :key="g.id" class="border-t border-pink-50 hover:bg-pink-50/30">
              <td class="px-4 py-3 font-medium">{{ g.group_name }}</td>
              <td class="px-4 py-3 text-gray-500">{{ g.group_number }}</td>
              <td class="px-4 py-3 text-gray-500">{{ g.remark || '-' }}</td>
              <td class="px-4 py-3">
                <span v-if="g.tags.length" class="flex gap-1">
                  <span v-for="t in g.tags" :key="t" class="px-2 py-0.5 text-xs bg-green-50 text-green-600 rounded-full">{{ t }}</span>
                </span>
                <span v-else class="text-gray-300">-</span>
              </td>
              <td class="px-4 py-3 text-right">
                <button @click="viewMembers(g)" class="text-gray-500 hover:underline text-xs mr-3">{{ labels.memberTitle }}</button>
                <button @click="goEdit(g)" class="text-primary hover:underline text-xs mr-3">{{ labels.edit }}</button>
                <button @click="doDelete(g.id)" class="text-red-400 hover:underline text-xs">{{ labels.delete }}</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="text-center text-gray-400 py-10">暂无数据</div>
      </div>
    </template>

    <template v-else>
      <div class="max-w-2xl">
        <div class="flex items-center gap-3 mb-5">
          <button @click="goList" class="text-gray-400 hover:text-gray-600">&larr;</button>
          <h2 class="text-lg font-bold">{{ editingGroup ? labels.editGroupTitle : labels.addGroupTitle }}</h2>
        </div>

        <div class="bg-white rounded-xl p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs text-gray-500 mb-1 block">{{ labels.tableGroupNumber }} *</label>
              <input v-model="form.group_number" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
            </div>
            <div>
              <label class="text-xs text-gray-500 mb-1 block">{{ labels.tableGroupName }} *</label>
              <input v-model="form.group_name" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
            </div>
            <div class="col-span-2">
              <label class="text-xs text-gray-500 mb-1 block">备注</label>
              <input v-model="form.remark" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
            </div>
          </div>

          <div>
            <label class="text-xs text-gray-500 mb-1 block">标签</label>
            <div class="flex gap-2 mb-2">
              <input v-model="tagInput" @keyup.enter="addTag" :placeholder="labels.tagPlaceholder" class="flex-1 px-3 py-1.5 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
              <button @click="addTag" class="px-3 py-1.5 text-sm bg-pink-50/50 rounded-xl hover:bg-pink-100">{{ labels.addTag }}</button>
            </div>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="(t, i) in form.tags" :key="i" class="px-2 py-0.5 text-xs bg-green-50 text-green-600 rounded-full flex items-center gap-1">
                {{ t }}
                <button @click="removeTag(i)" class="text-green-400 hover:text-red-500">&times;</button>
              </span>
            </div>
          </div>

          <div class="flex items-center gap-3 pt-2">
            <button @click="doSave" :disabled="saving" class="px-6 py-2 bg-primary text-white text-sm rounded-xl hover:bg-primary-dark disabled:opacity-50 transition">
              {{ saving ? labels.saving : labels.save }}
            </button>
            <button @click="goList" class="px-6 py-2 text-sm text-gray-500 hover:text-gray-700">{{ labels.cancel }}</button>
            <span v-if="savingMessage" :class="savingMessage.includes('错误') ? 'text-red-500' : 'text-green-500'" class="text-sm">{{ savingMessage }}</span>
          </div>
        </div>
      </div>
    </template>

    <div v-if="showMembers" class="fixed inset-0 bg-black/30 z-20 flex items-center justify-center" @click.self="showMembers = false">
      <div class="bg-white rounded-xl p-6 w-full max-w-md max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold">{{ currentGroup?.group_name }} - {{ labels.memberTitle }}</h3>
          <button @click="showMembers = false" class="text-gray-400 hover:text-gray-600 text-lg">&times;</button>
        </div>

        <div class="flex gap-2 mb-4">
          <select v-model="memberForm.account_id" class="flex-1 px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none">
            <option value="">{{ labels.selectAccount }}</option>
            <option v-for="a in allAccounts" :key="a.id" :value="a.id">
              {{ a.person_name }} - {{ a.current_nickname || a.account_identifier }} ({{ a.account_type }})
            </option>
          </select>
          <input v-model="memberForm.group_nickname" :placeholder="labels.groupNickname" class="w-28 px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none" />
          <button @click="addMember" class="px-3 py-2 bg-primary text-white text-sm rounded-xl hover:bg-primary-dark">{{ labels.addTag }}</button>
        </div>

        <div v-if="currentMembers.length === 0" class="text-center text-gray-400 text-sm py-6">{{ labels.noMembers }}</div>
        <div v-for="m in currentMembers" :key="m.id" class="flex items-center justify-between py-2 border-b last:border-0">
          <div class="flex items-center gap-3">
            <img :src="m.current_avatar || '/default-avatar.svg'" class="w-7 h-7 rounded-full object-cover bg-pink-100" />
            <div>
              <p class="text-sm font-medium">{{ m.current_nickname || m.account_identifier }}</p>
              <p class="text-xs text-gray-400">{{ m.account_type }} · {{ m.account_identifier }}</p>
            </div>
          </div>
          <button @click="removeMember(m.id)" class="text-red-400 text-xs hover:underline">{{ labels.remove }}</button>
        </div>
      </div>
    </div>
  </div>
</template>
