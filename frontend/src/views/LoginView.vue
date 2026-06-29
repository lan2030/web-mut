<template>
  <div class="login-wrap">
    <form class="card login-card" @submit.prevent="onSubmit">
      <div class="login-logo"><LucideIcon name="scan-qr-code" /></div>
      <h1>OmniScan</h1>
      <p class="login-sub">Вход в систему</p>

      <label class="field">
        <span>Логин</span>
        <input v-model="username" type="text" autocomplete="username" required autofocus />
      </label>
      <label class="field">
        <span>Пароль</span>
        <input v-model="password" type="password" autocomplete="current-password" required />
      </label>

      <p v-if="error" class="form-error">{{ error }}</p>

      <button class="btn btn-primary" type="submit" :disabled="loading">
        <LucideIcon :name="loading ? 'loader' : 'log-in'" /> {{ loading ? 'Вход…' : 'Войти' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import LucideIcon from '@/components/LucideIcon.vue';

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();

const username = ref('');
const password = ref('');
const error = ref('');
const loading = ref(false);

async function onSubmit() {
  error.value = '';
  loading.value = true;
  try {
    await auth.login(username.value, password.value);
    router.push(route.query.redirect || { name: 'dashboard' });
  } catch (e) {
    error.value = e.response?.data?.detail || 'Не удалось войти';
  } finally {
    loading.value = false;
  }
}
</script>
