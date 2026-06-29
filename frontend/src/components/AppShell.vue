<template>
  <div class="app-container">
    <header class="app-header">
      <router-link to="/" class="logo-area">
        <div class="logo-icon"><LucideIcon name="layout-grid" /></div>
        <div>
          <h1>OmniScan</h1>
          <p class="subtitle">Platform</p>
        </div>
      </router-link>

      <nav class="top-nav">
        <router-link
          v-if="auth.can('admin:users')"
          to="/admin/users"
          class="nav-link"
          active-class="active"
        ><LucideIcon name="users" /> Пользователи</router-link>
        <router-link
          v-if="auth.can('admin:roles')"
          to="/admin/roles"
          class="nav-link"
          active-class="active"
        ><LucideIcon name="shield" /> Роли</router-link>
      </nav>

      <div class="user-area">
        <span class="user-name">{{ auth.user?.full_name || auth.user?.username }}</span>
        <button class="btn-icon" title="Выйти" @click="onLogout"><LucideIcon name="log-out" /></button>
      </div>
    </header>

    <main class="shell-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import LucideIcon from './LucideIcon.vue';

const auth = useAuthStore();
const router = useRouter();

async function onLogout() {
  await auth.logout();
  router.push({ name: 'login' });
}
</script>
