import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomePage.vue')
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue')
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue')
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('../views/ForgotPasswordView.vue')
    },
    {
      path: '/reset-password/',
      name: 'reset-password',
      component: () => import('../views/ResetPasswordView.vue')
    },
    {
      path: '/terminos-y-condiciones',
      name: 'terminos',
      component: () => import('../views/TerminosView.vue')
    },
    {
      path: '/politica-privacidad',
      name: 'privacidad',
      component: () => import('../views/PrivacidadView.vue')
    },
    {
      path: '/app',
      name: 'layout',
      component: () => import('../views/MainPage.vue'),
      meta: { requiresAuth: true },
      redirect: '/app/cloud-accounts',
      children: [
        { path: 'cloud-accounts', component: () => import('../views/CloudAccountsView.vue') },
        { path: 'dashboard', component: () => import('../views/DashboardView.vue') },
        { path: 'inventory', component: () => import('../views/InventoryView.vue') },
        { path: 'audit', component: () => import('../views/AuditView.vue') },
        { path: 'my-audits', component: () => import('../views/MyAuditsView.vue') },
      ]
    }
  ]
})

const isTokenValid = () => {
  const token = localStorage.getItem('token')
  if (!token) return false
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp * 1000 > Date.now()
  } catch {
    return false
  }
}

router.beforeEach((to, from, next) => {
  const authRequired = to.matched.some(record => record.meta.requiresAuth);
  const loggedIn = isTokenValid();
  const publicPages = ['/', '/login', '/register', '/forgot-password'];

  if (authRequired && !loggedIn) {
    return next('/login');
  }

  if (!authRequired && loggedIn && publicPages.includes(to.path)) {
    return next('/app/cloud-accounts');
  }

  return next();
});


export default  router