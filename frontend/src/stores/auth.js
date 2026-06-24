import { defineStore } from 'pinia'
import { api } from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    username: localStorage.getItem('username') || '',
    role: localStorage.getItem('role') || '',
    uid: localStorage.getItem('uid') || '',
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
        localStorage.setItem('username', data.username)
        localStorage.setItem('role', data.role || '')
        localStorage.setItem('uid', data.uid || '')
        return true
      } catch {
        this.username = ''
        this.role = ''
        this.uid = ''
        localStorage.removeItem('username')
        localStorage.removeItem('role')
        localStorage.removeItem('uid')
        return false
      }
    },
    async logout() {
      try { await api.logout() } catch {}
      this.username = ''
      this.role = ''
      this.uid = ''
      localStorage.removeItem('username')
      localStorage.removeItem('role')
      localStorage.removeItem('uid')
    },
  },
})
