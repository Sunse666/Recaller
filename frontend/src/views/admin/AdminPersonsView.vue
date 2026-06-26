<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from '../../api/client'
import { useBoardStore } from '../../stores/boards'
import { useLabels } from '../../utils/labels'
import { getThumbUrl } from '../../utils/images'

const boardStoreLocal = useBoardStore()
const labels = useLabels()
const boardType = computed(() => boardStoreLocal.currentBoard?.board_type || 'image')
const isImage = computed(() => boardType.value === 'image')
const isFriend = computed(() => boardType.value === 'friend')
const isShuoshuo = computed(() => boardType.value === 'shuoshuo')

const T = computed(() => {
  if (isImage.value) return {
    remarkLabel: '来源', signatureLabel: '原图地址', locationLabel: '原作者',
    notesLabel: '图片描述', cardNameLabel: '图片名称',
    importanceLabel: '评分', accountManageLabel: '',
  }
  if (isShuoshuo.value) return {
    cardNameLabel: '标题', notesLabel: '内容',
    importanceLabel: '评分',
    remarkLabel: '', signatureLabel: '', locationLabel: '', accountManageLabel: '',
  }
  return {}
})
const tl = (key) => key in T.value ? T.value[key] : labels[key]

const persons = ref([])
const allAccounts = ref({})
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
  card_bg: '',
  circle_tags: [],
  impression_tags: [],
  importance: 0,
  notes: '',
  birthday: '',
  allow_download: false,
})
const form = ref(emptyForm())
const circleInput = ref('')
const impressionInput = ref('')

const accounts = ref([])
const accForm = ref({ account_type: 'QQ', account_identifier: '', current_nickname: '', current_avatar: '' })
const accSaving = ref(false)

const sharedBanners = ref([])
const bannerPage = ref(1)
const bannerTotal = ref(0)
const bannerPageSize = 12
const notesEl = ref(null)

async function loadSharedBanners() {
  try {
    const data = await api.listImages(bannerPage.value, bannerPageSize)
    sharedBanners.value = (data.items || []).map(f => f.url)
    bannerTotal.value = data.total || 0
  } catch {}
}

function nextBannerPage() {
  if (bannerPage.value * bannerPageSize < bannerTotal.value) {
    bannerPage.value++
    loadSharedBanners()
  }
}
function prevBannerPage() {
  if (bannerPage.value > 1) {
    bannerPage.value--
    loadSharedBanners()
  }
}

function insertImageToNotes(url) {
  const el = notesEl.value
  if (!el) return
  const alt = url.split('/').pop()?.split('.').shift() || '图片'
  const tag = `![${alt}](${url})`
  const start = el.selectionStart; const end = el.selectionEnd
  const before = (form.value.notes || '').slice(0, start)
  const after = (form.value.notes || '').slice(end)
  form.value.notes = before + tag + after
  requestAnimationFrame(() => { el.focus(); el.selectionStart = el.selectionEnd = start + tag.length })
}

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
  const boardStore = useBoardStore()
  loading.value = true
  persons.value = await api.listPersons(search.value, boardStore.currentBoardId)
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
  loadSharedBanners()
}

async function goEdit(p) {
  form.value = {
    name: p.name,
    remark: p.remark || '',
    signature: p.signature || '',
    location: p.location || '',
    avatar: p.avatar || '',
    card_bg: p.card_bg || '',
    circle_tags: [...(p.circle_tags || [])],
    impression_tags: [...(p.impression_tags || [])],
    importance: p.importance || 0,
    notes: p.notes || '',
    birthday: p.birthday || '',
    allow_download: p.allow_download || false,
  }
  editingPerson.value = p
  accounts.value = await api.listAccounts(p.id)
  view.value = 'edit'
  loadSharedBanners()
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
      await api.createPerson({ ...form.value, board_id: useBoardStore().currentBoardId })
      savingMessage.value = labels.value.createSuccess
    } else {
      await api.updatePerson(editingPerson.value.id, form.value)
      savingMessage.value = labels.value.saveSuccess
    }
    setTimeout(goList, 600)
  } catch (e) {
    savingMessage.value = '错误: ' + e.message
  } finally {
    saving.value = false
  }
}

async function doDelete(id) {
  if (!confirm(labels.value.confirmDeleteCard)) return
  await api.deletePerson(id)
  delete allAccounts.value[id]
  loadPersons()
}

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
  if (!confirm(labels.value.confirmDeleteAccount)) return
  await api.deleteAccount(editingPerson.value.id, accId)
  accounts.value = await api.listAccounts(editingPerson.value.id)
}

import { watch } from 'vue'

onMounted(loadPersons)
watch(() => boardStoreLocal.currentBoardId, () => {
  if (view.value === 'list') loadPersons()
})
</script>

<template>
  <div>
    <template v-if="view === 'list'">
      <div class="flex items-center justify-between mb-5 animate-fade-in-down">
        <h2 class="text-lg font-bold">{{ labels.cardManage }}</h2>
        <button @click="goCreate" class="px-4 py-2 bg-primary text-white text-sm rounded-xl transition-all duration-300 hover:bg-primary-dark hover:shadow-lg hover:shadow-primary/25 active:scale-95">
          {{ labels.addCard }}
        </button>
      </div>

      <div class="mb-4 animate-fade-in-up">
        <input
          v-model="search"
          @input="loadPersons"
          :placeholder="labels.searchCard"
          class="w-full max-w-sm px-4 py-2 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:bg-pink-50/30 focus:scale-[1.02] focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]"
        />
      </div>

      <div class="bg-white rounded-xl border border-pink-100 overflow-hidden animate-fade-in-up">
        <div v-if="loading" class="text-center text-gray-400 py-10">
          <div class="inline-block w-6 h-6 rounded-full border-2 border-pink-100 border-t-primary animate-spin" />
        </div>
        <div v-else-if="persons.length === 0" class="text-center text-gray-400 py-10 animate-fade-in-up">{{ labels.noData }}</div>
        <div v-else class="overflow-x-auto -mx-1">
        <table class="w-full text-sm min-w-[580px]">
          <thead class="bg-pink-50/30 text-gray-500 text-xs">
            <tr>
              <th class="text-left px-4 py-2.5 font-normal">{{ labels.tableCard }}</th>
              <th class="text-left px-4 py-2.5 font-normal">{{ labels.tableAccounts }}</th>
              <th class="text-left px-4 py-2.5 font-normal">{{ labels.tableTags }}</th>
              <th class="text-left px-4 py-2.5 font-normal">{{ labels.tableImportance }}</th>
              <th class="text-right px-4 py-2.5 font-normal">{{ labels.tableActions }}</th>
            </tr>
          </thead>
          <tbody class="animate-stagger">
            <tr v-for="p in persons" :key="p.id" class="border-t border-pink-50 transition-all duration-300 hover:bg-pink-50/40 hover:scale-[1.002]">
              <td class="px-4 py-3">
                <div class="flex items-center gap-3">
                  <img :src="getThumbUrl(p.avatar) || '/default-avatar.svg'" loading="lazy" class="w-8 h-8 rounded-full object-cover bg-pink-100 shrink-0 transition-transform duration-300 hover:scale-125" @error="e => { if (p.avatar && e.target.src !== p.avatar) e.target.src = p.avatar }" />
                  <div class="min-w-0">
                    <p class="font-medium truncate">{{ p.name }}</p>
                    <p v-if="p.remark" class="text-xs text-gray-400 truncate">{{ p.remark }}</p>
                    <p v-if="isShuoshuo && p.notes" class="text-xs text-gray-400 truncate mt-0.5">{{ p.notes.slice(0, 40) }}{{ p.notes.length > 40 ? '...' : '' }}</p>
                  </div>
                </div>
              </td>
              <td class="px-4 py-3">
                <div v-if="allAccounts[p.id]?.length" class="flex flex-wrap gap-1">
                  <span
                    v-for="a in allAccounts[p.id]"
                    :key="a.id"
                    :title="a.account_identifier"
                    class="px-1.5 py-0.5 text-xs rounded transition-all duration-200 hover:scale-110"
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
                  <span v-for="t in p.circle_tags" :key="t" class="px-2 py-0.5 text-xs bg-blue-50 text-blue-600 rounded-full transition-all duration-200 hover:scale-110">{{ t }}</span>
                </span>
                <span v-else class="text-gray-300">-</span>
              </td>
              <td class="px-4 py-3">
                <span class="text-yellow-400 transition-all duration-300 hover:scale-110 inline-block">{{ '★'.repeat(Math.min(p.importance, 5)) || '-' }}</span>
              </td>
              <td class="px-4 py-3 text-right">
                <button @click="goEdit(p)" class="text-primary hover:underline text-xs mr-3 transition-all duration-200 hover:scale-110 inline-block">{{ labels.edit }}</button>
                <button @click="doDelete(p.id)" class="text-red-400 hover:underline text-xs transition-all duration-200 hover:scale-110 inline-block">{{ labels.delete }}</button>
              </td>
            </tr>
          </tbody>
        </table>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="max-w-2xl animate-scale-in">
        <div class="flex items-center gap-3 mb-5">
          <button @click="goList" class="text-gray-400 hover:text-gray-600 transition-all duration-300 hover:scale-110">&larr;</button>
          <h2 class="text-lg font-bold">{{ view === 'create' ? labels.addCardTitle : labels.editCardTitle }}</h2>
        </div>

        <div class="bg-white rounded-xl p-6 space-y-4 shadow-sm border border-pink-50">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div :class="{ 'col-span-2': !isShuoshuo }">
              <label class="text-xs text-gray-500 mb-1 block">{{ tl('cardNameLabel') || labels.cardNameLabel }}</label>
              <input v-model="form.name" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]" />
            </div>
            <div v-if="!isShuoshuo" :class="{ 'col-span-2': !isFriend }">
              <label class="text-xs text-gray-500 mb-1 block">{{ tl('remarkLabel') || labels.remarkLabel }}</label>
              <input v-model="form.remark" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]" />
            </div>
            <div v-if="!isShuoshuo" class="col-span-2">
              <label class="text-xs text-gray-500 mb-1 block">{{ tl('signatureLabel') || labels.signatureLabel }}</label>
              <input v-model="form.signature" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]" />
            </div>
            <div v-if="!isShuoshuo && !isFriend" class="col-span-2">
              <label class="text-xs text-gray-500 mb-1 block">{{ tl('locationLabel') || labels.locationLabel }}</label>
              <input v-model="form.location" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]" />
            </div>
            <template v-if="isFriend">
              <div>
                <label class="text-xs text-gray-500 mb-1 block">{{ tl('locationLabel') || labels.locationLabel }}</label>
                <input v-model="form.location" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]" />
              </div>
              <div>
                <label class="text-xs text-gray-500 mb-1 block">{{ labels.birthdayLabel }}</label>
                <input v-model="form.birthday" :placeholder="labels.birthdayPlaceholder" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]" />
              </div>
            </template>
            <div class="col-span-2">
              <label class="text-xs text-gray-500 mb-1 block">{{ labels.avatarLabel }}</label>
              <input v-model="form.avatar" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]" />
            </div>
            <div v-if="!isShuoshuo" class="col-span-2">
              <label class="text-xs text-gray-500 mb-1 block">卡片背景 URL</label>
              <input v-model="form.card_bg" placeholder="卡片背景图片链接" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]" />
            </div>
            <div>
              <label class="text-xs text-gray-500 mb-1 block">{{ tl('importanceLabel') || labels.importanceLabel }}</label>
              <select v-model.number="form.importance" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary">
                <option :value="0">{{ labels.importanceNone }}</option>
                <option :value="1">★ 1 星</option>
                <option :value="2">★ 2 星</option>
                <option :value="3">★ 3 星</option>
                <option :value="4">★ 4 星</option>
                <option :value="5">★ 5 星</option>
              </select>
            </div>
          </div>

          <div v-if="isImage" class="flex items-center gap-3 py-1">
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="form.allow_download" class="sr-only peer" />
              <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary transition-colors"></div>
              <span class="ml-3 text-sm text-gray-600">允许下载原图</span>
            </label>
          </div>

          <div>
            <label class="text-xs text-gray-500 mb-1 block">{{ labels.circleTagsLabel }}</label>
            <div class="flex gap-2 mb-2">
              <input v-model="circleInput" @keyup.enter="addCircleTag" :placeholder="labels.tagPlaceholder" class="flex-1 px-3 py-1.5 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]" />
              <button @click="addCircleTag" class="px-4 py-2 text-sm bg-pink-50/50 rounded-xl transition-all duration-300 hover:bg-pink-100 active:scale-95 shrink-0">{{ labels.addTag }}</button>
            </div>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="(t, i) in form.circle_tags" :key="i" class="tag-item px-2 py-0.5 text-xs bg-blue-50 text-blue-600 rounded-full flex items-center gap-1">
                {{ t }}
                <button @click="removeCircleTag(i)" class="text-blue-400 hover:text-red-500 transition-colors duration-200">&times;</button>
              </span>
            </div>
          </div>

          <div v-if="isFriend">
            <label class="text-xs text-gray-500 mb-1 block">{{ labels.impressionTagsLabel }}</label>
            <div class="flex gap-2 mb-2">
              <input v-model="impressionInput" @keyup.enter="addImpressionTag" :placeholder="labels.tagPlaceholder" class="flex-1 px-3 py-1.5 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]" />
              <button @click="addImpressionTag" class="px-4 py-2 text-sm bg-pink-50/50 rounded-xl transition-all duration-300 hover:bg-pink-100 active:scale-95 shrink-0">{{ labels.addTag }}</button>
            </div>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="(t, i) in form.impression_tags" :key="i" class="tag-item px-2 py-0.5 text-xs bg-amber-50 text-amber-600 rounded-full flex items-center gap-1">
                {{ t }}
                <button @click="removeImpressionTag(i)" class="text-amber-400 hover:text-red-500 transition-colors duration-200">&times;</button>
              </span>
            </div>
          </div>

          <div>
            <label class="text-xs text-gray-500 mb-1 block">{{ tl('notesLabel') || labels.notesLabel }}</label>
            <textarea ref="notesEl" v-model="form.notes" rows="4" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)] resize-none"></textarea>
            <p class="text-xs text-gray-400 mt-1">支持图片：<code class="bg-gray-100 px-1 rounded">![描述](URL)</code> 或 <code class="bg-gray-100 px-1 rounded">![描述](URL,x=宽,y=高)</code> 或 <code class="bg-gray-100 px-1 rounded">![描述](URL,宽,高)</code></p>
          </div>
          <div class="border border-dashed border-pink-100 rounded-xl p-3 animate-fade-in-up">
            <div class="flex items-center justify-between mb-2">
              <p class="text-xs text-gray-400">点击图床图片插入到内容：</p>
              <div v-if="bannerTotal > bannerPageSize" class="flex items-center gap-1">
                <button @click="prevBannerPage" :disabled="bannerPage <= 1" class="px-2 py-0.5 text-xs text-primary hover:bg-pink-50 rounded disabled:opacity-30 disabled:cursor-not-allowed transition">&larr;</button>
                <span class="text-xs text-gray-400">{{ bannerPage }} / {{ Math.ceil(bannerTotal / bannerPageSize) }}</span>
                <button @click="nextBannerPage" :disabled="bannerPage * bannerPageSize >= bannerTotal" class="px-2 py-0.5 text-xs text-primary hover:bg-pink-50 rounded disabled:opacity-30 disabled:cursor-not-allowed transition">&rarr;</button>
              </div>
            </div>
            <div v-if="sharedBanners.length > 0" class="flex flex-wrap gap-2">
              <img
                v-for="(url, i) in sharedBanners"
                :key="(bannerPage - 1) * bannerPageSize + i"
                :src="getThumbUrl(url)"
                loading="lazy"
                class="w-14 h-14 object-cover rounded-lg cursor-pointer border-2 border-transparent transition-all duration-300 hover:border-primary hover:scale-110 hover:shadow-md"
                @error="e => { if (url && e.target.src !== url) e.target.src = url }"
                @click="insertImageToNotes(url)"
                title="点击插入到内容"
              />
            </div>
            <p v-else class="text-xs text-gray-300">暂无图片，请先在图片管理中上传</p>
          </div>

          <div v-if="view === 'edit' && isFriend" class="border-t border-pink-100 pt-4 mt-4 animate-fade-in-up">
            <h3 class="font-bold text-sm mb-3">{{ labels.tableAccounts }}{{ labels.cardManage }}</h3>

            <div v-if="accounts.length > 0" class="space-y-2 mb-4">
              <div v-for="a in accounts" :key="a.id" class="flex items-center gap-3 px-3 py-2 bg-pink-50/30 rounded-xl transition-all duration-300 hover:bg-pink-50">
                <img :src="getThumbUrl(a.current_avatar) || '/default-avatar.svg'" loading="lazy" class="w-7 h-7 rounded-full object-cover bg-pink-100 shrink-0" @error="e => { if (a.current_avatar && e.target.src !== a.current_avatar) e.target.src = a.current_avatar }" />
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
                <button @click="doDeleteAccount(a.id)" class="text-red-400 text-xs hover:underline shrink-0 transition-all duration-200 hover:scale-110">{{ labels.delete }}</button>
              </div>
            </div>
            <div v-else class="text-sm text-gray-400 mb-3">{{ labels.noAccounts }}</div>

            <div class="grid grid-cols-1 sm:grid-cols-4 gap-2">
              <select v-model="accForm.account_type" class="px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary">
                <option value="QQ">QQ</option>
                <option value="微信">微信</option>
                <option value="游戏ID">游戏ID</option>
                <option value="其他">其他</option>
              </select>
              <input v-model="accForm.account_identifier" placeholder="账号 *" class="px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]" />
              <input v-model="accForm.current_nickname" placeholder="昵称" class="px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none transition-all duration-300 focus:border-primary focus:shadow-[0_0_0_4px_rgba(236,72,153,0.08)]" />
              <button @click="doAddAccount" :disabled="accSaving" class="px-4 py-2 text-sm bg-primary text-white rounded-xl transition-all duration-300 hover:bg-primary-dark hover:shadow-lg active:scale-95 disabled:opacity-50">
                {{ accSaving ? '...' : '添加' }}
              </button>
            </div>
          </div>

          <div class="flex items-center gap-3 pt-2">
            <button @click="doSave" :disabled="saving" class="px-6 py-2 bg-primary text-white text-sm rounded-xl transition-all duration-300 hover:bg-primary-dark hover:shadow-lg hover:shadow-primary/25 active:scale-95 disabled:opacity-50">
              {{ saving ? labels.saving : labels.save }}
            </button>
            <button @click="goList" class="px-6 py-2 text-sm text-gray-500 hover:text-gray-700 transition-all duration-300">{{ labels.cancel }}</button>
            <Transition name="msg-bounce">
              <span v-if="savingMessage" :class="savingMessage.includes('错误') ? 'text-red-500' : 'text-green-500'" class="text-sm font-medium">{{ savingMessage }}</span>
            </Transition>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.tag-item {
  animation: scaleIn 0.25s cubic-bezier(0.68, -0.55, 0.265, 1.55) both;
}
.msg-bounce-enter-active {
  animation: bounceIn 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}
.msg-bounce-leave-active {
  transition: all 0.2s ease;
}
.msg-bounce-leave-to {
  opacity: 0;
}
</style>
