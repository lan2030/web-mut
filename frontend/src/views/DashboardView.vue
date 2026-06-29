<template>
  <div class="dashboard">
    <div class="card-header">
      <h2><LucideIcon name="layout-grid" /> Модули</h2>
    </div>

    <div v-if="hasTiles" class="module-grid">
      <router-link
        v-for="m in auth.modules"
        :key="m.key"
        :to="m.route"
        class="module-tile card"
      >
        <div class="module-icon"><LucideIcon :name="m.icon" /></div>
        <span class="module-name">{{ m.name }}</span>
      </router-link>

      <router-link v-if="isAdmin" to="/admin" class="module-tile card">
        <div class="module-icon"><LucideIcon name="shield" /></div>
        <span class="module-name">Администрирование</span>
      </router-link>
    </div>

    <div v-else class="empty-state card">
      <LucideIcon name="folder-open" />
      <p>Вам не назначено ни одного модуля. Обратитесь к администратору.</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import LucideIcon from '@/components/LucideIcon.vue';

const auth = useAuthStore();
const isAdmin = computed(() => auth.can('admin:users') || auth.can('admin:roles'));
const hasTiles = computed(() => auth.modules.length > 0 || isAdmin.value);
</script>
