<script setup>
import { ref, onMounted } from 'vue'
import { useBoardStore } from '../../stores/boards'
import { useLabels, DEF, TYPE_DEFAULTS } from '../../utils/labels'

const boardStore = useBoardStore()
const labels = useLabels()

const SKIP = new Set(['name','icon','description','appTitle','is_public',
  'card_label','cards_label','group_label','groups_label',
  'homeTitlePrefix','countUnit','manageSuffix','addPrefix','searchPrefix',
  'remarkLabel','signatureLabel','locationLabel','birthdayLabel','birthdayPlaceholder',
  'avatarLabel','importanceLabel','importanceNone','circleTagsLabel','impressionTagsLabel','notesLabel','accountManageLabel'])
const EXTRA = Object.keys(DEF).filter(k => !SKIP.has(k) && !k.startsWith('settings') && !k.startsWith('images') && !k.startsWith('appName') && !k.startsWith('login') && !k.startsWith('register') && !k.startsWith('username') && !k.startsWith('password') && !k.startsWith('confirmPassword') && !k.startsWith('avatarUpload') && !k.startsWith('changeAvatar') && !k.startsWith('changeUsername'))

const form = ref({ name:'',icon:'',description:'',appTitle:'',is_public:false,random_order:false,board_type:'image',
  card_label:'',cards_label:'',group_label:'',groups_label:'',
  homeTitlePrefix:'',countUnit:'',manageSuffix:'',addPrefix:'',searchPrefix:'',
  remarkLabel:'',signatureLabel:'',locationLabel:'',birthdayLabel:'',birthdayPlaceholder:'',
  avatarLabel:'',importanceLabel:'',importanceNone:'',
  circleTagsLabel:'',impressionTagsLabel:'',notesLabel:'',accountManageLabel:'',
  ...Object.fromEntries(EXTRA.map(k => [k, ''])),
})
const saving = ref(false)
const message = ref('')
const showFrameWords = ref(false)
const showFormLabels = ref(false)
const showAll = ref(false)

function loadBoard() {
  const b = boardStore.currentBoard
  if (!b) return
  const fc = typeof b.field_config === 'object' ? b.field_config : {}
  const boardFields = ['name', 'icon', 'description', 'card_label', 'cards_label', 'group_label', 'groups_label', 'board_type']
  for (const k of boardFields) form.value[k] = (b[k] || '')
  for (const k of EXTRA) form.value[k] = fc[k] || ''
  for (const k of Object.keys(form.value)) {
    if (k !== 'is_public' && k !== 'random_order' && form.value[k] === '' && fc[k]) form.value[k] = fc[k]
  }
  form.value.is_public = b.is_public || false
  form.value.random_order = b.random_order || false
  if (!form.value.board_type) form.value.board_type = 'image'
}

function pv(key) { return form.value[key] || DEF[key] || '' }

async function doSave() {
  saving.value = true; message.value = ''
  try {
    const fc = {}
    for (const k of Object.keys(form.value)) {
      if (!['name', 'icon', 'description', 'card_label', 'cards_label', 'group_label', 'groups_label', 'is_public', 'board_type', 'random_order'].includes(k)) {
        if (form.value[k]) fc[k] = form.value[k]
      }
    }
    await boardStore.updateBoard(boardStore.currentBoardId, {
      name: form.value.name, icon: form.value.icon || null, description: form.value.description || null,
      card_label: form.value.card_label, cards_label: form.value.cards_label,
      group_label: form.value.group_label, groups_label: form.value.groups_label,
      board_type: form.value.board_type,
      field_config: fc, is_public: form.value.is_public, random_order: form.value.random_order,
    })
    message.value = labels.value.saveSuccess
    await boardStore.fetchBoards()
  } catch (e) { message.value = '错误: ' + e.message }
  finally { saving.value = false }
}

const deleting = ref(false)
async function doDeleteBoard() {
  if (!confirm(labels.value.deleteBoardConfirm)) return
  deleting.value = true
  try {
    await boardStore.deleteBoard(boardStore.currentBoardId)
    if (boardStore.boards.length > 0) boardStore.setCurrentBoard(boardStore.boards[0].id)
    message.value = '画板已删除'
    setTimeout(() => { loadBoard(); message.value = '' }, 500)
  } catch (e) { message.value = '删除失败: ' + e.message }
  finally { deleting.value = false }
}

onMounted(async () => { await boardStore.fetchBoards(); loadBoard() })
</script>

<template>
  <div class="max-w-lg">
    <h2 class="text-lg font-bold text-gray-900 mb-6">{{ labels.settingsTitle }}</h2>

    <div class="bg-white rounded-xl border border-pink-100 p-6 space-y-4">
      <div>
        <label class="text-xs text-gray-500 mb-1 block">{{ labels.boardNameLabel }}</label>
        <input v-model="form.name" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="text-xs text-gray-500 mb-1 block">{{ labels.iconLabel }}</label>
          <input v-model="form.icon" placeholder="" maxlength="2" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
        </div>
        <div>
          <label class="text-xs text-gray-500 mb-1 block">{{ labels.descriptionLabel }}</label>
          <input v-model="form.description" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
        </div>
      </div>
      <div>
        <label class="text-xs text-gray-500 mb-1 block">画板类型</label>
        <select v-model="form.board_type" @change="() => { const td = TYPE_DEFAULTS[form.board_type]; if (td) { if (!form.card_label) form.card_label = td.card_label; if (!form.cards_label) form.cards_label = td.cards_label; if (!form.group_label) form.group_label = td.group_label; if (!form.groups_label) form.groups_label = td.groups_label } }" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none">
          <option value="image">图组模式</option>
          <option value="friend">群友模式</option>
          <option value="shuoshuo">说说模式</option>
        </select>
      </div>
      <div>
        <label class="text-xs text-gray-500 mb-1 block">{{ labels.appTitleLabel }}</label>
        <input v-model="form.appTitle" :placeholder="labels.appTitle" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
      </div>

      <hr class="border-pink-50" />

      <div>
        <label class="text-xs text-gray-500 mb-1 block">{{ labels.cardSingleLabel }}</label>
        <input v-model="form.card_label" :placeholder="DEF.card_label" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
      </div>
      <div>
        <label class="text-xs text-gray-500 mb-1 block">{{ labels.cardPluralLabel }}</label>
        <input v-model="form.cards_label" :placeholder="DEF.cards_label" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="text-xs text-gray-500 mb-1 block">{{ labels.groupSingleLabel }}</label>
          <input v-model="form.group_label" :placeholder="DEF.group_label" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
        </div>
        <div>
          <label class="text-xs text-gray-500 mb-1 block">{{ labels.groupPluralLabel }}</label>
          <input v-model="form.groups_label" :placeholder="DEF.groups_label" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
        </div>
      </div>

      <hr class="border-pink-50" />

      <button @click="showFrameWords = !showFrameWords" class="flex items-center gap-2 text-sm text-primary hover:underline">
        {{ showFrameWords ? '▾' : '▸' }} {{ labels.frameWordsTitle }}
      </button>
      <div v-if="showFrameWords" class="grid grid-cols-1 sm:grid-cols-2 gap-3 pl-2">
        <div v-for="item in [
          { key: 'homeTitlePrefix', d: DEF.homeTitlePrefix || '(空)' },
          { key: 'countUnit', d: DEF.countUnit },
          { key: 'manageSuffix', d: DEF.manageSuffix },
          { key: 'addPrefix', d: DEF.addPrefix },
          { key: 'searchPrefix', d: DEF.searchPrefix },
        ]" :key="item.key">
          <label class="text-xs text-gray-400 mb-1 block">"{{ item.d }}" →</label>
          <input v-model="form[item.key]" :placeholder="DEF[item.key]" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
        </div>
      </div>

      <button @click="showFormLabels = !showFormLabels" class="flex items-center gap-2 text-sm text-primary hover:underline">
        {{ showFormLabels ? '▾' : '▸' }} {{ labels.formLabelsTitle }}
      </button>
      <div v-if="showFormLabels" class="grid grid-cols-1 sm:grid-cols-2 gap-3 pl-2">
        <div v-for="item in [
          { key: 'remarkLabel', d: DEF.remarkLabel }, { key: 'signatureLabel', d: DEF.signatureLabel },
          { key: 'locationLabel', d: DEF.locationLabel }, { key: 'birthdayLabel', d: DEF.birthdayLabel },
          { key: 'birthdayPlaceholder', d: DEF.birthdayPlaceholder }, { key: 'avatarLabel', d: DEF.avatarLabel },
          { key: 'importanceLabel', d: DEF.importanceLabel }, { key: 'importanceNone', d: DEF.importanceNone },
          { key: 'circleTagsLabel', d: DEF.circleTagsLabel }, { key: 'impressionTagsLabel', d: DEF.impressionTagsLabel },
          { key: 'notesLabel', d: DEF.notesLabel }, { key: 'accountManageLabel', d: DEF.accountManageLabel },
        ]" :key="item.key">
          <label class="text-xs text-gray-400 mb-1 block">"{{ item.d }}" →</label>
          <input v-model="form[item.key]" :placeholder="DEF[item.key]" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
        </div>
      </div>

      <button @click="showAll = !showAll" class="flex items-center gap-2 text-sm text-primary hover:underline">
        {{ showAll ? '▾' : '▸' }} {{ labels.allTextTitle }}（{{ EXTRA.length }} 项）
      </button>
      <div v-if="showAll" class="grid grid-cols-1 sm:grid-cols-2 gap-3 pl-2 max-h-96 overflow-y-auto">
        <div v-for="k in EXTRA" :key="k">
          <label class="text-xs text-gray-400 mb-1 block">{{ DEF[k] ? '"' + DEF[k] + '"' : '(动态)' }} → <code class="text-[10px]">{{ k }}</code></label>
          <input v-model="form[k]" :placeholder="DEF[k] || ''" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
        </div>
      </div>

      <hr class="border-pink-50" />

      <div class="flex items-center gap-3">
        <span class="text-xs text-gray-500">{{ labels.publicBoardLabel }}</span>
        <label class="relative inline-flex items-center cursor-pointer">
          <input type="checkbox" v-model="form.is_public" class="sr-only peer" />
          <div class="w-9 h-5 bg-gray-300 peer-checked:bg-primary rounded-full transition-colors after:content-[''] after:absolute after:top-0.5 after:start-0.5 after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-4" />
        </label>
        <span class="text-xs text-gray-400">{{ form.is_public ? labels.publicVisible : labels.privateOnly }}</span>
      </div>

      <div class="flex items-center gap-3">
        <span class="text-xs text-gray-500">随机展示卡片</span>
        <label class="relative inline-flex items-center cursor-pointer">
          <input type="checkbox" v-model="form.random_order" class="sr-only peer" />
          <div class="w-9 h-5 bg-gray-300 peer-checked:bg-primary rounded-full transition-colors after:content-[''] after:absolute after:top-0.5 after:start-0.5 after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-4" />
        </label>
        <span class="text-xs text-gray-400">{{ form.random_order ? '卡片将随机排列展示' : '按默认顺序展示' }}</span>
      </div>

      <div class="bg-blue-50/50 rounded-xl p-4 text-sm">
        <p class="font-medium text-blue-700 mb-1">{{ labels.bannerImagesTitle }}</p>
        <p class="text-xs text-blue-500 mb-2">{{ labels.bannerImagesHint }}</p>
        <p class="text-xs text-gray-400">{{ labels.bannerImagesHelp }}</p>
      </div>

      <hr class="border-pink-50" />

      <div class="bg-pink-50/50 rounded-xl p-4 text-xs space-y-1 text-gray-500">
        <p class="text-gray-600 font-medium mb-2">{{ labels.previewTitle }}：</p>
        <p>首页标题：<span class="text-gray-800">{{ pv('homeTitlePrefix') }}{{ pv('cards_label') }}</span></p>
        <p>计数：<span class="text-gray-800">0 {{ pv('countUnit') }}{{ pv('card_label') }}</span></p>
        <p>导航：<span class="text-gray-800">{{ pv('card_label') }}{{ pv('manageSuffix') }}</span> / <span class="text-gray-800">{{ pv('group_label') }}{{ pv('manageSuffix') }}</span></p>
        <p>按钮：<span class="text-gray-800">{{ pv('addPrefix') }}{{ pv('card_label') }}</span> / <span class="text-gray-800">{{ pv('addPrefix') }}{{ pv('group_label') }}</span></p>
        <p>搜索：<span class="text-gray-800">{{ pv('searchPrefix') }}{{ pv('card_label') }}...</span></p>
      </div>

      <div class="flex items-center gap-3 pt-2">
        <button @click="doSave" :disabled="saving"
          class="px-6 py-2 bg-primary text-white text-sm rounded-xl hover:bg-primary-dark disabled:opacity-50 transition"
        >{{ saving ? labels.saving : labels.save }}</button>
        <button @click="doDeleteBoard" :disabled="deleting"
          class="px-6 py-2 bg-red-400 text-white text-sm rounded-xl hover:bg-red-500 disabled:opacity-50 transition ml-auto"
        >{{ deleting ? '...' : labels.deleteBoard }}</button>
        <span v-if="message" :class="message.includes('错误') || message.includes('失败') ? 'text-red-500' : 'text-green-500'" class="text-sm">{{ message }}</span>
      </div>
    </div>
  </div>
</template>
