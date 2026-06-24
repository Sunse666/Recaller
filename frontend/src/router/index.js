import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/:personName',
    name: 'person-detail',
    component: () => import('../views/PersonDetailView.vue'),
    props: true,
  },
  {
    path: '/admin/login',
    name: 'admin-login',
    component: () => import('../views/admin/LoginView.vue'),
  },
  {
    path: '/admin',
    component: () => import('../views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true },
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
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth) {
    const username = localStorage.getItem('username')
    if (!username) {
      return next('/admin/login')
    }
  }
  if (to.path === '/admin/login') {
    const username = localStorage.getItem('username')
    if (username) {
      return next('/admin/persons')
    }
  }
  next()
})

export default router
