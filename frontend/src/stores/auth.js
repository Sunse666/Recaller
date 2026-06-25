import { defineStore } from 'pinia'
import { api } from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    username: localStorage.getItem('username') || '',
    role: '',
    uid: '',
    avatar: '',
    verified: false,
  }),
  getters: {
    isLoggedIn: (state) => !!state.username && state.verified,
    isAdmin: (state) => state.verified && (state.role === 'admin' || state.role === 'superadmin'),
  },
  actions: {
    async login(username, password) {
      const data = await api.login(username, password)
      this.verified = true
      localStorage.setItem('username', data.username)
      await this.checkAuth()
    },
    async register(username, password) {
      await api.register(username, password)
    },
    async checkAuth() {
      try {
        const data = await api.me()
        this.username = data.username
        this.role = data.role || ''
        this.uid = data.uid || ''
        this.avatar = data.avatar || ''
        this.verified = true
        localStorage.setItem('username', data.username)
        return true
      } catch {
        this.username = ''
        this.role = ''
        this.uid = ''
        this.avatar = ''
        this.verified = false
        localStorage.removeItem('username')
        return false
      }
    },
    async logout() {
      try { await api.logout() } catch {}
      this.username = ''
      this.role = ''
      this.uid = ''
      this.avatar = ''
      this.verified = false
      localStorage.removeItem('username')
    },
    async changeUsername(newUsername) {
      const data = await api.changeUsername(newUsername)
      this.username = data.username
      localStorage.setItem('username', data.username)
      return data
    },
    async uploadAvatar(file) {
      const data = await api.uploadAvatar(file)
      this.avatar = data.url
      return data
    },
  },
})
