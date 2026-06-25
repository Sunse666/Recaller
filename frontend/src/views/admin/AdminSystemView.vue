<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/client'

const config = ref({ registration_open: '1', site_name: '图片展示' })
const saving = ref(false)
const message = ref('')

onMounted(async () => {
  try {
    const data = await api.adminGetConfig()
    config.value = { ...config.value, ...data }
  } catch {}
})

async function saveConfig(key, value) {
  saving.value = true
  message.value = ''
  try {
    await api.adminUpdateConfig({ key, value })
    message.value = '保存成功'
    setTimeout(() => message.value = '', 2000)
  } catch (e) { message.value = '保存失败: ' + e.message }
  finally { saving.value = false }
}
</script>

<template>
  <div class="max-w-lg">
    <h2 class="text-lg font-bold text-gray-900 mb-6">系统设置</h2>

    <div class="bg-white rounded-xl border border-gray-100 p-6 space-y-6">
      <div>
        <label class="text-sm font-medium text-gray-700 block mb-2">站点名称</label>
        <div class="flex gap-2">
          <input v-model="config.site_name" class="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-xl outline-none focus:border-primary" />
          <button @click="saveConfig('site_name', config.site_name)" :disabled="saving"
            class="px-4 py-2 bg-primary text-white text-sm rounded-xl hover:bg-primary-dark disabled:opacity-50">保存</button>
        </div>
      </div>

      <div>
        <label class="text-sm font-medium text-gray-700 block mb-2">开放注册</label>
        <div class="flex items-center gap-3">
          <label class="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" :checked="config.registration_open === '1'"
              @change="saveConfig('registration_open', $event.target.checked ? '1' : '0')"
              class="sr-only peer" />
            <div class="w-9 h-5 bg-gray-300 peer-checked:bg-primary rounded-full transition-colors after:content-[''] after:absolute after:top-0.5 after:start-0.5 after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-4" />
          </label>
          <span class="text-sm text-gray-500">{{ config.registration_open === '1' ? '已开启，任何人可注册' : '已关闭，仅管理员可添加用户' }}</span>
        </div>
      </div>

      <p v-if="message" :class="message.includes('失败') ? 'text-red-500' : 'text-green-500'" class="text-sm">{{ message }}</p>
    </div>
  </div>
</template>
