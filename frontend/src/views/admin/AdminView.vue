<template>
  <div class="dashboard">
    <div class="card-header">
      <h2><LucideIcon name="shield" /> Администрирование</h2>
      <router-link to="/" class="btn btn-secondary"><LucideIcon name="arrow-left" /> На главную</router-link>
    </div>

    <div class="module-grid">
      <router-link v-if="auth.can('admin:users')" to="/admin/users" class="module-tile card">
        <div class="module-icon"><LucideIcon name="users" /></div>
        <span class="module-name">Пользователи</span>
      </router-link>
      <router-link v-if="auth.can('admin:roles')" to="/admin/roles" class="module-tile card">
        <div class="module-icon"><LucideIcon name="key-round" /></div>
        <span class="module-name">Роли</span>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth';
import LucideIcon from '@/components/LucideIcon.vue';
const auth = useAuthStore();
</script>
