<template>
  <div class="bg-blur bg-blur-1"></div>
  <div class="bg-blur bg-blur-2"></div>
  <router-view v-if="auth.ready" />
  <div v-else class="boot-screen">Загрузка…</div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth';
const auth = useAuthStore();
</script>
