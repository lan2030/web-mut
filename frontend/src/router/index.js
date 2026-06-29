import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const routes = [
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/components/AppShell.vue'),
    children: [
      { path: '', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },
      {
        path: 'modules/scanner',
        name: 'module-scanner',
        component: () => import('@/views/modules/ScannerView.vue'),
        meta: { permission: 'module:scanner' },
      },
      {
        path: 'admin',
        name: 'admin',
        component: () => import('@/views/admin/AdminView.vue'),
        meta: { anyPermission: ['admin:users', 'admin:roles'] },
      },
      {
        path: 'admin/users',
        name: 'admin-users',
        component: () => import('@/views/admin/UsersView.vue'),
        meta: { permission: 'admin:users' },
      },
      {
        path: 'admin/roles',
        name: 'admin-roles',
        component: () => import('@/views/admin/RolesView.vue'),
        meta: { permission: 'admin:roles' },
      },
      { path: 'forbidden', name: 'forbidden', component: () => import('@/views/ForbiddenView.vue') },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
];

const router = createRouter({ history: createWebHistory(), routes });

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (!auth.ready) await auth.fetchMe();

  if (to.meta.public) {
    return auth.isAuthenticated && to.name === 'login' ? { name: 'dashboard' } : true;
  }
  if (!auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } };
  }
  if (to.meta.permission && !auth.can(to.meta.permission)) {
    return { name: 'forbidden' };
  }
  if (to.meta.anyPermission && !to.meta.anyPermission.some((p) => auth.can(p))) {
    return { name: 'forbidden' };
  }
  return true;
});

export default router;
