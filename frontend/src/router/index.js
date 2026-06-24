import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/admin/LoginView.vue'),
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/admin/RegisterView.vue'),
  },
  // user profile + management
  {
    path: '/:uid(\\d+)',
    component: () => import('../views/UserHomeView.vue'),
    children: [
      {
        path: '',
        name: 'user-home',
      },
      {
        path: 'persons',
        name: 'user-persons',
        component: () => import('../views/admin/UserPersonsView.vue'),
      },
      {
        path: 'groups',
        name: 'user-groups',
        component: () => import('../views/admin/AdminGroupsView.vue'),
      },
      {
        path: 'settings',
        name: 'user-settings',
        component: () => import('../views/admin/AdminSettingsView.vue'),
      },
    ],
  },
  // person detail
  {
    path: '/:personName',
    name: 'person-detail',
    component: () => import('../views/PersonDetailView.vue'),
    props: true,
  },
  // admin superuser
  {
    path: '/admin',
    component: () => import('../views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        redirect: '/admin/persons',
      },
      {
        path: 'persons',
        name: 'admin-persons',
        component: () => import('../views/admin/AdminPersonsView.vue'),
      },
      {
        path: 'groups',
        name: 'admin-groups',
        component: () => import('../views/admin/AdminGroupsView.vue'),
      },
      {
        path: 'settings',
        name: 'admin-settings',
        component: () => import('../views/admin/AdminSettingsView.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  let username = localStorage.getItem('username')
  let role = localStorage.getItem('role')

  if (username && !role) {
    localStorage.removeItem('username')
    username = ''
  }

  const uid = localStorage.getItem('uid')

  if (to.meta.requiresAuth) {
    if (!username) return next('/login')
    if (to.meta.requiresAdmin && role !== 'admin') return next('/')
  }

  if (to.path === '/login' || to.path === '/register') {
    if (username) {
      return next(role === 'admin' ? '/admin/persons' : `/${uid || ''}`)
    }
  }

  next()
})

export default router
