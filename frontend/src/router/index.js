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
      { path: '', redirect: '/admin/persons' },
      { path: 'persons', name: 'admin-persons', component: () => import('../views/admin/AdminPersonsView.vue') },
      { path: 'settings', name: 'admin-settings', component: () => import('../views/admin/AdminSettingsView.vue') },
      { path: 'images', name: 'admin-images', component: () => import('../views/admin/AdminImagesView.vue') },
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
      { path: ':boardId(\\d+)/:personName', name: 'user-person-detail', component: () => import('../views/PersonDetailView.vue'), props: true },
    ],
  },

  // legacy: global person detail
  { path: '/:personName', redirect: to => `/1/0/${to.params.personName}` },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  let username = localStorage.getItem('username')
  let role = localStorage.getItem('role')
  if (username && !role) { localStorage.removeItem('username'); username = '' }
  const uid = localStorage.getItem('uid')

  if (to.meta.requiresAuth) {
    if (!username) return next('/login')
    if (to.meta.requiresAdmin && role !== 'admin') return next('/')
  }
  if (to.path === '/login' || to.path === '/register') {
    if (username) return next(role === 'admin' ? '/admin/persons' : `/${uid || ''}/persons`)
  }
  next()
})

export default router
