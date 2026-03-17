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
      path: '/auth',
      name: 'auth',
      component: () => import('../views/AuthView.vue')
    },
    {
      path: '/app',
      name: 'layout',
      component: () => import('../views/MainPage.vue'),
      redirect: '/app/cloud-accounts',
      children: [
        { path: 'cloud-accounts', component: () => import('../views/CloudAccountsView.vue') },
        { path: 'dashboard', component: () => import('../views/DashboardView.vue') },
        { path: 'inventory', component: () => import('../views/InventoryView.vue') },
        { path: 'audit', component: () => import('../views/AuditView.vue') },
        { path: 'configuration', component: () => import('../views/ConfigurationView.vue') },
      ]
    }
  ]
})


export default  router