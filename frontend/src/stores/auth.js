import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    username: localStorage.getItem('username') || '',
  }),
  getters: {
    isLoggedIn: (state) => !!state.username,
  },
  actions: {
    async login(username, password) {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ username, password }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: '登录失败' }))
        throw new Error(err.detail || '登录失败')
      }
      const data = await res.json()
      this.username = data.username
      localStorage.setItem('username', data.username)
    },
    async checkAuth() {
      try {
        const res = await fetch('/api/auth/me', { credentials: 'same-origin' })
        if (res.ok) {
          const data = await res.json()
          this.username = data.username
          localStorage.setItem('username', data.username)
          return true
        }
      } catch {}
      this.username = ''
      localStorage.removeItem('username')
      return false
    },
    async logout() {
      try {
        await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' })
      } catch {}
      this.username = ''
      localStorage.removeItem('username')
    },
  },
})
