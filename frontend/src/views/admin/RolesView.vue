<template>
  <div class="admin-page">
    <div class="card-header">
      <div class="header-left">
        <router-link to="/admin" class="btn-icon" title="К администрированию"><LucideIcon name="arrow-left" /></router-link>
        <h2><LucideIcon name="shield" /> Роли</h2>
      </div>
      <button class="btn btn-primary" @click="openCreate"><LucideIcon name="plus" /> Добавить</button>
    </div>

    <div class="card table-card">
      <table class="data-table">
        <thead>
          <tr><th>Ключ</th><th>Название</th><th>Права</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="r in roles" :key="r.id">
            <td class="mono">{{ r.key }} <span v-if="r.is_system" class="badge">система</span></td>
            <td>{{ r.name }}</td>
            <td>
              <span v-for="p in r.permissions" :key="p" class="chip">{{ p }}</span>
              <span v-if="!r.permissions.length" class="muted">—</span>
            </td>
            <td class="row-actions">
              <button class="btn-icon" title="Редактировать" @click="openEdit(r)"><LucideIcon name="pencil" /></button>
              <button
                v-if="!r.is_system"
                class="btn-icon"
                title="Удалить"
                @click="remove(r)"
              ><LucideIcon name="trash-2" /></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="modal" class="modal-overlay" @click.self="modal = null">
      <form class="card modal-form" @submit.prevent="save">
        <h3>{{ modal.id ? 'Редактирование роли' : 'Новая роль' }}</h3>
        <label class="field">
          <span>Ключ</span>
          <input v-model="form.key" :disabled="!!modal.id" required pattern="[a-z0-9_:-]+" />
        </label>
        <label class="field">
          <span>Название</span>
          <input v-model="form.name" required />
        </label>
        <label class="field">
          <span>Описание</span>
          <input v-model="form.description" />
        </label>
        <div class="field">
          <span>Права</span>
          <div class="checkbox-list">
            <label v-for="p in permissions" :key="p.key" class="check" :class="{ disabled: modal.is_system }">
              <input type="checkbox" :value="p.key" v-model="form.permissions" :disabled="modal.is_system" />
              <span>{{ p.description }} <code>{{ p.key }}</code></span>
            </label>
          </div>
          <p v-if="modal.is_system" class="muted">Права системной роли изменять нельзя.</p>
        </div>
        <p v-if="error" class="form-error">{{ error }}</p>
        <div class="modal-actions">
          <button type="button" class="btn btn-secondary" @click="modal = null">Отмена</button>
          <button type="submit" class="btn btn-primary" :disabled="saving">Сохранить</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '@/api';
import LucideIcon from '@/components/LucideIcon.vue';

const roles = ref([]);
const permissions = ref([]);
const modal = ref(null);
const form = ref({});
const error = ref('');
const saving = ref(false);

async function load() {
  const [r, p] = await Promise.all([api.get('/admin/roles'), api.get('/admin/permissions')]);
  roles.value = r.data;
  permissions.value = p.data;
}
onMounted(load);

function openCreate() {
  error.value = '';
  form.value = { key: '', name: '', description: '', permissions: [] };
  modal.value = {};
}
function openEdit(r) {
  error.value = '';
  form.value = { key: r.key, name: r.name, description: r.description, permissions: [...r.permissions] };
  modal.value = { id: r.id, is_system: r.is_system };
}

async function save() {
  saving.value = true;
  error.value = '';
  try {
    if (modal.value.id) {
      await api.patch(`/admin/roles/${modal.value.id}`, {
        name: form.value.name,
        description: form.value.description,
        permissions: modal.value.is_system ? undefined : form.value.permissions,
      });
    } else {
      await api.post('/admin/roles', form.value);
    }
    modal.value = null;
    await load();
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка сохранения';
  } finally {
    saving.value = false;
  }
}

async function remove(r) {
  if (!confirm(`Удалить роль «${r.name}»?`)) return;
  try {
    await api.delete(`/admin/roles/${r.id}`);
    await load();
  } catch (e) {
    alert(e.response?.data?.detail || 'Ошибка удаления');
  }
}
</script>
