<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/client'

const persons = ref([])
const allAccounts = ref({}) // personId -> accounts[]
const loading = ref(false)
const search = ref('')

const view = ref('list')
const editingPerson = ref(null)
const saving = ref(false)
const savingMessage = ref('')

const emptyForm = () => ({
  name: '',
  remark: '',
  signature: '',
  location: '',
  avatar: '',
  circle_tags: [],
  impression_tags: [],
  importance: 0,
  notes: '',
  birthday: '',
})
const form = ref(emptyForm())
const circleInput = ref('')
const impressionInput = ref('')

// 账号表单
const accounts = ref([]) // 当前编辑中的人的所有账号
const accForm = ref({ account_type: 'QQ', account_identifier: '', current_nickname: '', current_avatar: '' })
const accSaving = ref(false)

function addCircleTag() {
  const v = circleInput.value.trim()
  if (v && !form.value.circle_tags.includes(v)) form.value.circle_tags.push(v)
  circleInput.value = ''
}
function removeCircleTag(i) { form.value.circle_tags.splice(i, 1) }
function addImpressionTag() {
  const v = impressionInput.value.trim()
  if (v && !form.value.impression_tags.includes(v)) form.value.impression_tags.push(v)
  impressionInput.value = ''
}
function removeImpressionTag(i) { form.value.impression_tags.splice(i, 1) }

async function loadPersons() {
  loading.value = true
  persons.value = await api.listPersons(search.value)
  // 加载所有人的账号
  for (const p of persons.value) {
    if (!allAccounts.value[p.id]) {
      allAccounts.value[p.id] = await api.listAccounts(p.id)
    }
  }
  loading.value = false
}

function goCreate() {
  form.value = emptyForm()
  accounts.value = []
  view.value = 'create'
}

async function goEdit(p) {
  form.value = {
    name: p.name,
    remark: p.remark || '',
    signature: p.signature || '',
    location: p.location || '',
    avatar: p.avatar || '',
    circle_tags: [...(p.circle_tags || [])],
    impression_tags: [...(p.impression_tags || [])],
    importance: p.importance || 0,
    notes: p.notes || '',
    birthday: p.birthday || '',
  }
  editingPerson.value = p
  accounts.value = await api.listAccounts(p.id)
  view.value = 'edit'
}

function goList() {
  view.value = 'list'
  editingPerson.value = null
  loadPersons()
}

async function doSave() {
  if (!form.value.name.trim()) return
  saving.value = true
  savingMessage.value = ''
  try {
    if (view.value === 'create') {
      await api.createPerson(form.value)
      savingMessage.value = '创建成功'
    } else {
      await api.updatePerson(editingPerson.value.id, form.value)
      savingMessage.value = '保存成功'
    }
    setTimeout(goList, 600)
  } catch (e) {
    savingMessage.value = '错误: ' + e.message
  } finally {
    saving.value = false
  }
}

async function doDelete(id) {
  if (!confirm('确定删除？这将同时删除该群友的所有账号。')) return
  await api.deletePerson(id)
  delete allAccounts.value[id]
  loadPersons()
}

// 账号 CRUD
async function doAddAccount() {
  if (!accForm.value.account_identifier.trim()) return
  accSaving.value = true
  try {
    await api.createAccount(editingPerson.value.id, { ...accForm.value })
    accounts.value = await api.listAccounts(editingPerson.value.id)
    accForm.value = { account_type: 'QQ', account_identifier: '', current_nickname: '', current_avatar: '' }
  } catch (e) {
    alert(e.message)
  } finally {
    accSaving.value = false
  }
}

async function doDeleteAccount(accId) {
  if (!confirm('确定删除此账号？')) return
  await api.deleteAccount(editingPerson.value.id, accId)
  accounts.value = await api.listAccounts(editingPerson.value.id)
}

onMounted(loadPersons)
</script>

<template>
  <div>
    <template v-if="view === 'list'">
      <div class="flex items-center justify-between mb-5">
        <h2 class="text-lg font-bold">群友管理</h2>
        <button @click="goCreate" class="px-4 py-2 bg-[#12b7f5] text-white text-sm rounded-lg hover:bg-[#0ea0db] transition">
          + 添加群友
        </button>
      </div>

      <div class="mb-4">
        <input
          v-model="search"
          @input="loadPersons"
          placeholder="搜索群友..."
          class="w-full max-w-sm px-4 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]"
        />
      </div>

      <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <div v-if="loading" class="text-center text-gray-400 py-10">加载中...</div>
        <div v-else-if="persons.length === 0" class="text-center text-gray-400 py-10">暂无数据</div>
        <table v-else class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-500 text-xs">
            <tr>
              <th class="text-left px-4 py-2.5 font-normal">群友</th>
              <th class="text-left px-4 py-2.5 font-normal">账号</th>
              <th class="text-left px-4 py-2.5 font-normal">圈子标签</th>
              <th class="text-left px-4 py-2.5 font-normal">重要度</th>
              <th class="text-right px-4 py-2.5 font-normal">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in persons" :key="p.id" class="border-t border-gray-50 hover:bg-gray-50 transition">
              <td class="px-4 py-3">
                <div class="flex items-center gap-3">
                  <img :src="p.avatar || '/default-avatar.svg'" class="w-8 h-8 rounded-full object-cover bg-gray-200" />
                  <div>
                    <p class="font-medium">{{ p.name }}</p>
                    <p v-if="p.remark" class="text-xs text-gray-400">{{ p.remark }}</p>
                  </div>
                </div>
              </td>
              <td class="px-4 py-3">
                <div v-if="allAccounts[p.id]?.length" class="flex flex-wrap gap-1">
                  <span
                    v-for="a in allAccounts[p.id]"
                    :key="a.id"
                    :title="a.account_identifier"
                    class="px-1.5 py-0.5 text-xs rounded"
                    :class="{
                      'bg-blue-50 text-blue-600': a.account_type === 'QQ',
                      'bg-green-50 text-green-600': a.account_type === '微信',
                      'bg-purple-50 text-purple-600': a.account_type !== 'QQ' && a.account_type !== '微信',
                    }"
                  >
                    {{ a.account_type }}{{ a.current_nickname ? ': ' + a.current_nickname : '' }}
                  </span>
                </div>
                <span v-else class="text-gray-300">-</span>
              </td>
              <td class="px-4 py-3">
                <span v-if="p.circle_tags.length" class="flex flex-wrap gap-1">
                  <span v-for="t in p.circle_tags" :key="t" class="px-2 py-0.5 text-xs bg-blue-50 text-blue-600 rounded-full">{{ t }}</span>
                </span>
                <span v-else class="text-gray-300">-</span>
              </td>
              <td class="px-4 py-3">
                <span class="text-yellow-400">{{ '⭐'.repeat(Math.min(p.importance, 5)) || '-' }}</span>
              </td>
              <td class="px-4 py-3 text-right">
                <button @click="goEdit(p)" class="text-[#12b7f5] hover:underline text-xs mr-3">编辑</button>
                <button @click="doDelete(p.id)" class="text-red-400 hover:underline text-xs">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <template v-else>
      <div class="max-w-2xl">
        <div class="flex items-center gap-3 mb-5">
          <button @click="goList" class="text-gray-400 hover:text-gray-600">&larr;</button>
          <h2 class="text-lg font-bold">{{ view === 'create' ? '添加群友' : '编辑群友' }}</h2>
        </div>

        <div class="bg-white rounded-xl p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs text-gray-500 mb-1 block">姓名 *</label>
              <input v-model="form.name" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]" />
            </div>
            <div>
              <label class="text-xs text-gray-500 mb-1 block">备注名</label>
              <input v-model="form.remark" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]" />
            </div>
            <div class="col-span-2">
              <label class="text-xs text-gray-500 mb-1 block">签名</label>
              <input v-model="form.signature" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]" />
            </div>
            <div>
              <label class="text-xs text-gray-500 mb-1 block">所在地</label>
              <input v-model="form.location" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]" />
            </div>
            <div>
              <label class="text-xs text-gray-500 mb-1 block">生日</label>
              <input v-model="form.birthday" placeholder="如 01-15" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]" />
            </div>
            <div class="col-span-2">
              <label class="text-xs text-gray-500 mb-1 block">头像 URL</label>
              <input v-model="form.avatar" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]" />
            </div>
            <div>
              <label class="text-xs text-gray-500 mb-1 block">重要度 (1-5)</label>
              <select v-model.number="form.importance" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none">
                <option :value="0">未设置</option>
                <option :value="1">⭐</option>
                <option :value="2">⭐⭐</option>
                <option :value="3">⭐⭐⭐</option>
                <option :value="4">⭐⭐⭐⭐</option>
                <option :value="5">⭐⭐⭐⭐⭐</option>
              </select>
            </div>
          </div>

          <div>
            <label class="text-xs text-gray-500 mb-1 block">圈子标签</label>
            <div class="flex gap-2 mb-2">
              <input v-model="circleInput" @keyup.enter="addCircleTag" placeholder="输入后回车添加" class="flex-1 px-3 py-1.5 text-sm border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]" />
              <button @click="addCircleTag" class="px-3 py-1.5 text-sm bg-gray-100 rounded-lg hover:bg-gray-200">添加</button>
            </div>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="(t, i) in form.circle_tags" :key="i" class="px-2 py-0.5 text-xs bg-blue-50 text-blue-600 rounded-full flex items-center gap-1">
                {{ t }}
                <button @click="removeCircleTag(i)" class="text-blue-400 hover:text-red-500">&times;</button>
              </span>
            </div>
          </div>

          <div>
            <label class="text-xs text-gray-500 mb-1 block">印象标签</label>
            <div class="flex gap-2 mb-2">
              <input v-model="impressionInput" @keyup.enter="addImpressionTag" placeholder="输入后回车添加" class="flex-1 px-3 py-1.5 text-sm border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]" />
              <button @click="addImpressionTag" class="px-3 py-1.5 text-sm bg-gray-100 rounded-lg hover:bg-gray-200">添加</button>
            </div>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="(t, i) in form.impression_tags" :key="i" class="px-2 py-0.5 text-xs bg-amber-50 text-amber-600 rounded-full flex items-center gap-1">
                {{ t }}
                <button @click="removeImpressionTag(i)" class="text-amber-400 hover:text-red-500">&times;</button>
              </span>
            </div>
          </div>

          <div>
            <label class="text-xs text-gray-500 mb-1 block">印象笔记</label>
            <textarea v-model="form.notes" rows="3" class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5] resize-none"></textarea>
          </div>

          <div v-if="view === 'edit'" class="border-t border-gray-100 pt-4 mt-4">
            <h3 class="font-bold text-sm mb-3">账号管理</h3>

            <div v-if="accounts.length > 0" class="space-y-2 mb-4">
              <div v-for="a in accounts" :key="a.id" class="flex items-center gap-3 px-3 py-2 bg-gray-50 rounded-lg">
                <img :src="a.current_avatar || '/default-avatar.svg'" class="w-7 h-7 rounded-full object-cover bg-gray-200 shrink-0" />
                <div class="flex-1 min-w-0">
                  <p class="text-sm">
                    <span
                      :class="{
                        'text-blue-600': a.account_type === 'QQ',
                        'text-green-600': a.account_type === '微信',
                        'text-purple-600': a.account_type !== 'QQ' && a.account_type !== '微信',
                      }"
                      class="font-medium"
                    >{{ a.account_type }}</span>
                    <span class="text-gray-400 ml-1">{{ a.account_identifier }}</span>
                    <span v-if="a.current_nickname" class="text-gray-500 ml-1">· {{ a.current_nickname }}</span>
                  </p>
                </div>
                <button @click="doDeleteAccount(a.id)" class="text-red-400 text-xs hover:underline shrink-0">删除</button>
              </div>
            </div>
            <div v-else class="text-sm text-gray-400 mb-3">暂无账号</div>

            <div class="grid grid-cols-4 gap-2">
              <select v-model="accForm.account_type" class="px-2 py-1.5 text-xs border border-gray-200 rounded-lg outline-none">
                <option value="QQ">QQ</option>
                <option value="微信">微信</option>
                <option value="游戏ID">游戏ID</option>
                <option value="其他">其他</option>
              </select>
              <input v-model="accForm.account_identifier" placeholder="账号 *" class="px-2 py-1.5 text-xs border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]" />
              <input v-model="accForm.current_nickname" placeholder="昵称" class="px-2 py-1.5 text-xs border border-gray-200 rounded-lg outline-none focus:border-[#12b7f5]" />
              <button @click="doAddAccount" :disabled="accSaving" class="px-3 py-1.5 text-xs bg-[#12b7f5] text-white rounded-lg hover:bg-[#0ea0db] disabled:opacity-50">
                {{ accSaving ? '...' : '+ 添加' }}
              </button>
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
  </div>
</template>
