<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/client'

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
  loading.value = true
  groups.value = await api.listGroups(search.value)
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
      savingMessage.value = '保存成功'
    } else {
      await api.createGroup(form.value)
      savingMessage.value = '创建成功'
    }
    setTimeout(goList, 600)
  } catch (e) {
    savingMessage.value = '错误: ' + e.message
  } finally {
    saving.value = false
  }
}

async function doDelete(id) {
  if (!confirm('确定删除此群？')) return
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
        <h2 class="text-lg font-bold">群管理</h2>
        <button @click="goCreate" class="px-4 py-2 bg-[#12b7f5] text-white text-sm rounded-lg hover:bg-[#0ea0db] transition">
          + 添加群
        </button>
      </div>

      <div class="mb-4">
        <input v-model="search" @input="loadGroups" placeholder="搜索群..." class="w-full max-w-sm px-4 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]" />
      </div>

      <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <div v-if="loading" class="text-center text-gray-400 py-10">加载中...</div>
        <table v-else-if="groups.length" class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-500 text-xs">
            <tr>
              <th class="text-left px-4 py-2.5 font-normal">群名称</th>
              <th class="text-left px-4 py-2.5 font-normal">群号</th>
              <th class="text-left px-4 py-2.5 font-normal">备注</th>
              <th class="text-left px-4 py-2.5 font-normal">标签</th>
              <th class="text-right px-4 py-2.5 font-normal">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="g in groups" :key="g.id" class="border-t border-gray-50 hover:bg-gray-50">
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
                <button @click="viewMembers(g)" class="text-gray-500 hover:underline text-xs mr-3">成员</button>
                <button @click="goEdit(g)" class="text-[#12b7f5] hover:underline text-xs mr-3">编辑</button>
                <button @click="doDelete(g.id)" class="text-red-400 hover:underline text-xs">删除</button>
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
          <h2 class="text-lg font-bold">{{ editingGroup ? '编辑群' : '添加群' }}</h2>
        </div>

        <div class="bg-white rounded-xl p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs text-gray-500 mb-1 block">群号 *</label>
              <input v-model="form.group_number" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]" />
            </div>
            <div>
              <label class="text-xs text-gray-500 mb-1 block">群名称 *</label>
              <input v-model="form.group_name" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]" />
            </div>
            <div class="col-span-2">
              <label class="text-xs text-gray-500 mb-1 block">备注</label>
              <input v-model="form.remark" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]" />
            </div>
          </div>

          <div>
            <label class="text-xs text-gray-500 mb-1 block">标签</label>
            <div class="flex gap-2 mb-2">
              <input v-model="tagInput" @keyup.enter="addTag" placeholder="输入后回车添加" class="flex-1 px-3 py-1.5 text-sm border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]" />
              <button @click="addTag" class="px-3 py-1.5 text-sm bg-gray-100 rounded-lg hover:bg-gray-200">添加</button>
            </div>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="(t, i) in form.tags" :key="i" class="px-2 py-0.5 text-xs bg-green-50 text-green-600 rounded-full flex items-center gap-1">
                {{ t }}
                <button @click="removeTag(i)" class="text-green-400 hover:text-red-500">&times;</button>
              </span>
            </div>
          </div>

          <div class="flex items-center gap-3 pt-2">
            <button @click="doSave" :disabled="saving" class="px-6 py-2 bg-[#12b7f5] text-white text-sm rounded-lg hover:bg-[#0ea0db] disabled:opacity-50 transition">
              {{ saving ? '保存中...' : '保存' }}
            </button>
            <button @click="goList" class="px-6 py-2 text-sm text-gray-500 hover:text-gray-700">取消</button>
            <span v-if="savingMessage" :class="savingMessage.includes('错误') ? 'text-red-500' : 'text-green-500'" class="text-sm">{{ savingMessage }}</span>
          </div>
        </div>
      </div>
    </template>

    <div v-if="showMembers" class="fixed inset-0 bg-black/30 z-20 flex items-center justify-center" @click.self="showMembers = false">
      <div class="bg-white rounded-xl p-6 w-full max-w-md max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold">{{ currentGroup?.group_name }} - 成员</h3>
          <button @click="showMembers = false" class="text-gray-400 hover:text-gray-600 text-lg">&times;</button>
        </div>

        <div class="flex gap-2 mb-4">
          <select v-model="memberForm.account_id" class="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none">
            <option value="">选择账号</option>
            <option v-for="a in allAccounts" :key="a.id" :value="a.id">
              {{ a.person_name }} - {{ a.current_nickname || a.account_identifier }} ({{ a.account_type }})
            </option>
          </select>
          <input v-model="memberForm.group_nickname" placeholder="群名片" class="w-28 px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none" />
          <button @click="addMember" class="px-3 py-2 bg-[#12b7f5] text-white text-sm rounded-lg hover:bg-[#0ea0db]">添加</button>
        </div>

        <div v-if="currentMembers.length === 0" class="text-center text-gray-400 text-sm py-6">暂无成员</div>
        <div v-for="m in currentMembers" :key="m.id" class="flex items-center justify-between py-2 border-b last:border-0">
          <div class="flex items-center gap-3">
            <img :src="m.current_avatar || '/default-avatar.svg'" class="w-7 h-7 rounded-full object-cover bg-gray-200" />
            <div>
              <p class="text-sm font-medium">{{ m.current_nickname || m.account_identifier }}</p>
              <p class="text-xs text-gray-400">{{ m.account_type }} · {{ m.account_identifier }}</p>
            </div>
          </div>
          <button @click="removeMember(m.id)" class="text-red-400 text-xs hover:underline">移除</button>
        </div>
      </div>
    </div>
  </div>
</template>
