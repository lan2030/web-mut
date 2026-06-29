<template>
  <div class="admin-page">
    <div class="card-header">
      <h2><LucideIcon name="users" /> Пользователи</h2>
      <button class="btn btn-primary" @click="openCreate"><LucideIcon name="user-plus" /> Добавить</button>
    </div>

    <div class="card table-card">
      <table class="data-table">
        <thead>
          <tr><th>Логин</th><th>ФИО</th><th>Роли</th><th>Статус</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" :class="{ inactive: !u.is_active }">
            <td class="mono">{{ u.username }}</td>
            <td>{{ u.full_name || '—' }}</td>
            <td>
              <span v-for="r in u.roles" :key="r" class="chip">{{ r }}</span>
              <span v-if="!u.roles.length" class="muted">—</span>
            </td>
            <td>
              <span :class="['badge', u.is_active ? 'badge-success' : 'badge-danger']">
                {{ u.is_active ? 'активен' : 'отключён' }}
              </span>
            </td>
            <td class="row-actions">
              <button class="btn-icon" title="Редактировать" @click="openEdit(u)"><LucideIcon name="pencil" /></button>
              <button class="btn-icon" title="Сбросить пароль" @click="openReset(u)"><LucideIcon name="key-round" /></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create / edit modal -->
    <div v-if="modal" class="modal-overlay" @click.self="modal = null">
      <form class="card modal-form" @submit.prevent="save">
        <h3>{{ modal.id ? 'Редактирование' : 'Новый пользователь' }}</h3>
        <label class="field">
          <span>Логин</span>
          <input v-model="form.username" :disabled="!!modal.id" required />
        </label>
        <label class="field">
          <span>ФИО</span>
          <input v-model="form.full_name" />
        </label>
        <label v-if="!modal.id" class="field">
          <span>Пароль</span>
          <input v-model="form.password" type="text" required minlength="6" />
        </label>
        <label v-if="modal.id" class="field check">
          <input v-model="form.is_active" type="checkbox" /> <span>Активен</span>
        </label>
        <div class="field">
          <span>Роли</span>
          <div class="checkbox-list">
            <label v-for="r in roles" :key="r.id" class="check">
              <input type="checkbox" :value="r.id" v-model="form.role_ids" /> <span>{{ r.name }}</span>
            </label>
          </div>
        </div>
        <p v-if="error" class="form-error">{{ error }}</p>
        <div class="modal-actions">
          <button type="button" class="btn btn-secondary" @click="modal = null">Отмена</button>
          <button type="submit" class="btn btn-primary" :disabled="saving">Сохранить</button>
        </div>
      </form>
    </div>

    <!-- Reset password modal -->
    <div v-if="resetUser" class="modal-overlay" @click.self="resetUser = null">
      <form class="card modal-form" @submit.prevent="doReset">
        <h3>Сброс пароля: {{ resetUser.username }}</h3>
        <label class="field">
          <span>Новый пароль</span>
          <input v-model="newPassword" type="text" required minlength="6" />
        </label>
        <p v-if="error" class="form-error">{{ error }}</p>
        <div class="modal-actions">
          <button type="button" class="btn btn-secondary" @click="resetUser = null">Отмена</button>
          <button type="submit" class="btn btn-primary">Применить</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '@/api';
import LucideIcon from '@/components/LucideIcon.vue';

const users = ref([]);
const roles = ref([]);
const modal = ref(null);
const resetUser = ref(null);
const form = ref({});
const newPassword = ref('');
const error = ref('');
const saving = ref(false);

async function load() {
  const [u, r] = await Promise.all([api.get('/admin/users'), api.get('/admin/roles')]);
  users.value = u.data;
  roles.value = r.data;
}
onMounted(load);

function openCreate() {
  error.value = '';
  form.value = { username: '', full_name: '', password: '', role_ids: [] };
  modal.value = {};
}
function openEdit(u) {
  error.value = '';
  form.value = {
    full_name: u.full_name,
    is_active: u.is_active,
    role_ids: roles.value.filter((r) => u.roles.includes(r.key)).map((r) => r.id),
  };
  modal.value = { id: u.id };
}
function openReset(u) {
  error.value = '';
  newPassword.value = '';
  resetUser.value = u;
}

async function save() {
  saving.value = true;
  error.value = '';
  try {
    if (modal.value.id) {
      await api.patch(`/admin/users/${modal.value.id}`, {
        full_name: form.value.full_name,
        is_active: form.value.is_active,
        role_ids: form.value.role_ids,
      });
    } else {
      await api.post('/admin/users', form.value);
    }
    modal.value = null;
    await load();
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка сохранения';
  } finally {
    saving.value = false;
  }
}

async function doReset() {
  error.value = '';
  try {
    await api.post(`/admin/users/${resetUser.value.id}/reset-password`, { password: newPassword.value });
    resetUser.value = null;
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка';
  }
}
</script>
