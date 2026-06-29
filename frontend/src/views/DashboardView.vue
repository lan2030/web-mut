<template>
  <div class="dashboard">
    <div class="card-header">
      <h2><LucideIcon name="layout-grid" /> Модули</h2>
    </div>

    <div v-if="auth.modules.length" class="module-grid">
      <router-link
        v-for="m in auth.modules"
        :key="m.key"
        :to="m.route"
        class="module-tile card"
      >
        <div class="module-icon"><LucideIcon :name="m.icon" /></div>
        <span class="module-name">{{ m.name }}</span>
      </router-link>
    </div>

    <div v-else class="empty-state card">
      <LucideIcon name="folder-open" />
      <p>Вам не назначено ни одного модуля. Обратитесь к администратору.</p>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth';
import LucideIcon from '@/components/LucideIcon.vue';
const auth = useAuthStore();
</script>
