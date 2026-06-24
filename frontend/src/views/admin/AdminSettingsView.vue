<script setup>
import { ref, onMounted } from 'vue'
import { useBoardStore } from '../../stores/boards'
import { useLabels } from '../../utils/labels'

const boardStore = useBoardStore()
const labels = useLabels()

const form = ref({
  name: '',
  icon: '',
  description: '',
  card_label: '',
  cards_label: '',
  group_label: '',
  groups_label: '',
  appTitle: '',
  is_public: false,
})
const saving = ref(false)
const message = ref('')

function loadBoard() {
  const b = boardStore.currentBoard
  if (!b) return
  const fc = typeof b.field_config === 'object' ? b.field_config : {}
  form.value = {
    name: b.name || '',
    icon: b.icon || '',
    description: b.description || '',
    card_label: b.card_label || '群友',
    cards_label: b.cards_label || '群友们',
    group_label: b.group_label || '群',
    groups_label: b.groups_label || '群组',
    appTitle: fc.appTitle || '',
    is_public: b.is_public || false,
  }
}

async function doSave() {
  saving.value = true
  message.value = ''
  try {
    await boardStore.updateBoard(boardStore.currentBoardId, {
      name: form.value.name,
      icon: form.value.icon || null,
      description: form.value.description || null,
      card_label: form.value.card_label,
      cards_label: form.value.cards_label,
      group_label: form.value.group_label,
      groups_label: form.value.groups_label,
      field_config: { appTitle: form.value.appTitle || undefined },
      is_public: form.value.is_public,
    })
    message.value = labels.value.saveSuccess
    // Refresh labels by refetching
    await boardStore.fetchBoards()
  } catch (e) {
    message.value = '错误: ' + e.message
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await boardStore.fetchBoards()
  loadBoard()
})
</script>

<template>
  <div class="max-w-lg">
    <h2 class="text-lg font-bold text-gray-900 mb-6">画板设置</h2>

    <div class="bg-white rounded-xl border border-pink-100 p-6 space-y-4">
      <div>
        <label class="text-xs text-gray-500 mb-1 block">画板名称</label>
        <input v-model="form.name" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="text-xs text-gray-500 mb-1 block">图标 (emoji)</label>
          <input v-model="form.icon" placeholder="👥" maxlength="2" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
        </div>
        <div>
          <label class="text-xs text-gray-500 mb-1 block">描述</label>
          <input v-model="form.description" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
        </div>
      </div>

      <div>
        <label class="text-xs text-gray-500 mb-1 block">应用标题</label>
        <input v-model="form.appTitle" :placeholder="labels.appTitle" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
        <p class="text-xs text-gray-400 mt-1">显示在首页顶部，留空则使用默认「{{ labels.appTitle }}」</p>
      </div>

      <hr class="border-pink-50" />

      <div>
        <label class="text-xs text-gray-500 mb-1 block">卡片单数标签</label>
        <input v-model="form.card_label" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
        <p class="text-xs text-gray-400 mt-1">默认"群友"，修改后所有「群友管理」「添加群友」等文字同步变化</p>
      </div>

      <div>
        <label class="text-xs text-gray-500 mb-1 block">卡片复数标签</label>
        <input v-model="form.cards_label" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
        <p class="text-xs text-gray-400 mt-1">默认"群友们"，如「我认识的群友们」「3位群友」</p>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="text-xs text-gray-500 mb-1 block">群单数标签</label>
          <input v-model="form.group_label" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
          <p class="text-xs text-gray-400 mt-1">默认"群"</p>
        </div>
        <div>
          <label class="text-xs text-gray-500 mb-1 block">群复数标签</label>
          <input v-model="form.groups_label" class="w-full px-3 py-2 text-sm border border-pink-100 rounded-xl outline-none focus:border-primary" />
          <p class="text-xs text-gray-400 mt-1">默认"群组"</p>
        </div>
      </div>

      <hr class="border-pink-50" />

      <div class="flex items-center gap-3">
        <label class="text-xs text-gray-500">公开画板</label>
        <button
          type="button"
          @click="form.is_public = !form.is_public"
          :class="form.is_public ? 'bg-primary' : 'bg-gray-300'"
          class="relative w-10 h-5 rounded-full transition-colors duration-200"
        >
          <span
            :class="form.is_public ? 'translate-x-5' : 'translate-x-0.5'"
            class="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform duration-200"
          />
        </button>
        <span class="text-xs text-gray-400">{{ form.is_public ? '任何人可见' : '仅自己可见' }}</span>
      </div>

      <div class="bg-pink-50/50 rounded-xl p-4 text-xs space-y-1 text-gray-500">
        <p class="text-gray-600 font-medium mb-2">预览效果：</p>
        <p>首页标题：<span class="text-gray-800">我认识的{{ form.cards_label || '...' }}</span></p>
        <p>计数：<span class="text-gray-800">0 位{{ form.card_label || '...' }}</span></p>
        <p>管理导航：<span class="text-gray-800">{{ form.card_label || '...' }}管理</span> / <span class="text-gray-800">{{ form.group_label || '...' }}管理</span></p>
        <p>添加按钮：<span class="text-gray-800">+ 添加{{ form.card_label || '...' }}</span> / <span class="text-gray-800">+ 添加{{ form.group_label || '...' }}</span></p>
        <p>搜索：<span class="text-gray-800">搜索{{ form.card_label || '...' }}...</span> / <span class="text-gray-800">搜索{{ form.group_label || '...' }}...</span></p>
        <p>确认删除：<span class="text-gray-800">确定删除？这将同时删除该{{ form.card_label || '...' }}的所有账号。</span></p>
      </div>

      <div class="flex items-center gap-3 pt-2">
        <button
          @click="doSave"
          :disabled="saving"
          class="px-6 py-2 bg-primary text-white text-sm rounded-xl hover:bg-primary-dark disabled:opacity-50 transition"
        >{{ saving ? labels.saving : labels.save }}</button>
        <span v-if="message" :class="message.includes('错误') ? 'text-red-500' : 'text-green-500'" class="text-sm">{{ message }}</span>
      </div>
    </div>
  </div>
</template>
