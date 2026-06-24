import { defineStore } from 'pinia'
import { api } from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    username: localStorage.getItem('username') || '',
    role: localStorage.getItem('role') || '',
    uid: localStorage.getItem('uid') || '',
    avatar: localStorage.getItem('avatar') || '',
  }),
  getters: {
    isLoggedIn: (state) => !!state.username,
    isAdmin: (state) => state.role === 'admin',
  },
  actions: {
    async login(username, password) {
      const data = await api.login(username, password)
      this.username = data.username
      this.role = data.role || ''
      this.uid = data.uid || ''
      localStorage.setItem('username', data.username)
      localStorage.setItem('role', data.role || '')
      localStorage.setItem('uid', data.uid || '')
      await this.checkAuth()  // get avatar
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
        localStorage.setItem('username', data.username)
        localStorage.setItem('role', data.role || '')
        localStorage.setItem('uid', data.uid || '')
        localStorage.setItem('avatar', data.avatar || '')
        return true
      } catch {
        this.username = ''
        this.role = ''
        this.uid = ''
        this.avatar = ''
        localStorage.removeItem('username')
        localStorage.removeItem('role')
        localStorage.removeItem('uid')
        localStorage.removeItem('avatar')
        return false
      }
    },
    async logout() {
      try { await api.logout() } catch {}
      this.username = ''
      this.role = ''
      this.uid = ''
      this.avatar = ''
      localStorage.removeItem('username')
      localStorage.removeItem('role')
      localStorage.removeItem('uid')
      localStorage.removeItem('avatar')
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
      localStorage.setItem('avatar', data.url)
      return data
    },
  },
})
