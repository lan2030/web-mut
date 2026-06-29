import { defineStore } from 'pinia';
import api, { setCsrfToken } from '@/api';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null, // { id, username, full_name, roles, permissions, modules, csrf_token }
    ready: false, // initial /me check finished
  }),
  getters: {
    isAuthenticated: (s) => !!s.user,
    permissions: (s) => new Set(s.user?.permissions || []),
    modules: (s) => s.user?.modules || [],
    can: (s) => (perm) => (s.user?.permissions || []).includes(perm),
  },
  actions: {
    _apply(data) {
      this.user = data;
      setCsrfToken(data?.csrf_token || null);
    },
    async fetchMe() {
      try {
        const { data } = await api.get('/auth/me');
        this._apply(data);
      } catch {
        this._apply(null);
        this.user = null;
      } finally {
        this.ready = true;
      }
    },
    async login(username, password) {
      const { data } = await api.post('/auth/login', { username, password });
      this._apply(data);
      return data;
    },
    async logout() {
      try {
        await api.post('/auth/logout');
      } finally {
        this.user = null;
        setCsrfToken(null);
      }
    },
  },
});
