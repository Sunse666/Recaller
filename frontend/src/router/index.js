import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/1' },
  { path: '/login', name: 'login', component: () => import('../views/admin/LoginView.vue') },
  { path: '/register', name: 'register', component: () => import('../views/admin/RegisterView.vue') },

  // admin (before :uid to avoid matching)
  {
    path: '/admin',
    component: () => import('../views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'admin-dashboard', component: () => import('../views/admin/AdminDashboardView.vue') },
      { path: 'users', name: 'admin-users', component: () => import('../views/admin/AdminUsersView.vue') },
      { path: 'users/:uid', name: 'admin-user-detail', component: () => import('../views/admin/AdminUserDetailView.vue') },
      { path: 'users/:uid/boards/:boardId', redirect: to => `/admin/users/${to.params.uid}/boards/${to.params.boardId}/persons` },
      { path: 'users/:uid/boards/:boardId/persons', name: 'admin-user-board-persons', component: () => import('../views/admin/AdminPersonsView.vue') },
      { path: 'users/:uid/boards/:boardId/settings', name: 'admin-user-board-settings', component: () => import('../views/admin/AdminSettingsView.vue') },
      { path: 'users/:uid/boards/:boardId/images', name: 'admin-user-board-images', component: () => import('../views/admin/AdminImagesView.vue') },
      { path: 'persons', name: 'admin-persons', component: () => import('../views/admin/AdminPersonsView.vue') },
      { path: 'settings', name: 'admin-settings', component: () => import('../views/admin/AdminSettingsView.vue') },
      { path: 'images', name: 'admin-images', component: () => import('../views/admin/AdminImagesView.vue') },
      { path: 'audit', name: 'admin-audit', component: () => import('../views/admin/AdminAuditView.vue') },
      { path: 'system', name: 'admin-system', component: () => import('../views/admin/AdminSystemView.vue') },
    ],
  },

  // user pages (public profile + management, same layout as admin)
  {
    path: '/:uid(\\d+)',
    component: () => import('../views/admin/AdminLayout.vue'),
    children: [
      { path: '', name: 'user-profile', component: () => import('../views/UserProfileView.vue') },
      { path: 'persons', name: 'user-persons', component: () => import('../views/admin/AdminPersonsView.vue') },
      { path: 'settings', name: 'user-settings', component: () => import('../views/admin/AdminSettingsView.vue') },
      { path: 'images', name: 'user-images', component: () => import('../views/admin/AdminImagesView.vue') },
      { path: ':boardName/:personName', name: 'user-person-detail', component: () => import('../views/PersonDetailView.vue'), props: true },
    ],
  },

  // legacy: global person detail
  { path: '/:personName', redirect: to => `/1/default/${to.params.personName}` },
]

async function verifyAuth() {
  try {
    const res = await fetch('/api/auth/me', { credentials: 'same-origin' })
    if (!res.ok) return null
    const data = await res.json()
    return data
  } catch {
    return null
  }
}

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to, from, next) => {
  if (to.meta.requiresAuth) {
    const user = await verifyAuth()
    if (!user) return next('/login')
    if (to.meta.requiresAdmin && user.role !== 'admin' && user.role !== 'superadmin') return next('/')
    next()
    return
  }
  if (to.path === '/login' || to.path === '/register') {
    const user = await verifyAuth()
    if (user) {
      if (user.role === 'admin' || user.role === 'superadmin') return next('/admin/dashboard')
      return next(`/${user.uid || ''}/persons`)
    }
  }
  next()
})

export default router
