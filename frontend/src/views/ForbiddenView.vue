<template>
  <div class="empty-state card">
    <LucideIcon name="shield-alert" />
    <p>Недостаточно прав для доступа к этому разделу.</p>
    <router-link to="/" class="btn btn-secondary">На главную</router-link>
  </div>
</template>

<script setup>
import LucideIcon from '@/components/LucideIcon.vue';
</script>
