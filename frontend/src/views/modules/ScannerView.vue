<template>
  <div class="scanner-module">
    <div class="dashboard-grid">
      <!-- Controls -->
      <section class="card">
        <div class="card-header"><h2><LucideIcon name="aperture" /> Сканирование</h2>
          <span class="badge">{{ statusText }}</span>
        </div>
        <div class="scanner-actions">
          <button class="btn btn-primary" @click="startScanning" :disabled="active">
            <LucideIcon name="camera" /> Открыть сканер
          </button>
          <label class="btn btn-secondary file-btn">
            <LucideIcon name="image" /> Скан из файла
            <input type="file" accept="image/*" @change="onFile" hidden />
          </label>
        </div>
      </section>

      <div class="sidebar-grid">
        <!-- Result -->
        <section class="card" v-if="result">
          <div class="card-header"><h2><LucideIcon name="file-text" /> Результат</h2>
            <span class="badge">{{ result.type.replace(/_/g, ' ') }}</span>
          </div>
          <textarea class="result-text" readonly :value="result.text"></textarea>
          <div class="action-grid">
            <button class="btn btn-action" @click="copy(result.text)"><LucideIcon name="copy" /> Копировать</button>
            <a v-if="isUrl(result.text)" :href="result.text" target="_blank" rel="noopener" class="btn btn-action"><LucideIcon name="external-link" /> Открыть</a>
          </div>
        </section>

        <!-- Product (1C) -->
        <section class="card" v-if="product.state">
          <div class="card-header"><h2><LucideIcon name="package" /> Товар (1С)</h2>
            <span :class="['badge', product.state === 'found' ? 'badge-success' : product.state === 'error' ? 'badge-danger' : '']">
              {{ product.state === 'loading' ? 'Запрос…' : product.state === 'found' ? 'Найден' : 'Ошибка' }}
            </span>
          </div>
          <div v-if="product.state === 'loading'" class="product-loading"><div class="spinner"></div></div>
          <div v-else-if="product.state === 'error'" class="empty-state"><LucideIcon name="alert-circle" /><p>{{ product.error }}</p></div>
          <div v-else class="product-info">
            <h3>{{ product.data.NomDescription || 'Без названия' }}</h3>
            <div class="product-details-grid">
              <div class="detail-item"><span class="detail-label">Артикул</span><span class="detail-value mono">{{ product.data.Art || '—' }}</span></div>
              <div class="detail-item"><span class="detail-label">Код 1С</span><span class="detail-value mono">{{ product.data.NomCode || '—' }}</span></div>
              <div class="detail-item"><span class="detail-label">Цена</span><span class="detail-value">{{ product.data.Price ? product.data.Price + ' ₸' : '—' }}</span></div>
              <div class="detail-item"><span class="detail-label">Ед.</span><span class="detail-value">{{ product.data.Unit || 'шт' }}</span></div>
            </div>
            <table v-if="product.data.Rests?.length" class="data-table">
              <thead><tr><th>Склад</th><th>Кол-во</th></tr></thead>
              <tbody><tr v-for="(r, i) in product.data.Rests" :key="i"><td>{{ r.Warehouse || '—' }}</td><td><strong>{{ r.Quantity || 0 }}</strong></td></tr></tbody>
            </table>
            <p v-else class="muted">Нет остатков на складах.</p>
          </div>
        </section>

        <!-- History -->
        <section class="card">
          <div class="card-header"><h2><LucideIcon name="history" /> История</h2>
            <button class="btn-icon" title="Очистить" @click="clearHistory"><LucideIcon name="trash-2" /></button>
          </div>
          <ul v-if="history.length" class="history-list">
            <li v-for="item in history" :key="item.id" class="history-item">
              <div class="history-item-main" @click="showHistory(item)">
                <span class="history-item-title">{{ item.text }}</span>
                <div class="history-item-meta"><span class="chip">{{ item.type.replace(/_/g,' ') }}</span><span>{{ item.time }}</span></div>
              </div>
              <button class="btn-icon" @click="deleteHistory(item.id)"><LucideIcon name="x" /></button>
            </li>
          </ul>
          <div v-else class="empty-state"><LucideIcon name="folder-open" /><p>История пуста</p></div>
        </section>
      </div>
    </div>

    <!-- Scanner modal -->
    <div v-if="modalOpen" class="modal-overlay">
      <div class="card modal-scanner">
        <div class="card-header"><h3><LucideIcon name="scan" /> Наведите код</h3>
          <button class="btn-icon" @click="stopScanning"><LucideIcon name="x" /></button>
        </div>
        <div id="reader" class="reader"></div>
        <div class="camera-controls">
          <select v-model="selectedCamera" class="camera-select">
            <option v-for="c in cameras" :key="c.id" :value="c.id">{{ c.label }}</option>
          </select>
          <button v-if="cameras.length > 1" class="btn-icon" @click="switchCamera"><LucideIcon name="switch-camera" /></button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount, nextTick } from 'vue';
import api from '@/api';
import LucideIcon from '@/components/LucideIcon.vue';

const HKEY = 'omniscan_history';
const history = ref(JSON.parse(localStorage.getItem(HKEY) || '[]'));
const result = ref(null);
const product = ref({ state: null });
const statusText = ref('Готов');

const modalOpen = ref(false);
const active = ref(false);
const cameras = ref([{ id: 'environment', label: 'Задняя камера (авто)' }, { id: 'user', label: 'Фронтальная (авто)' }]);
const selectedCamera = ref('environment');
let qr = null;

function ensureQr() {
  if (!qr && window.Html5Qrcode) qr = new window.Html5Qrcode('reader');
  return qr;
}

async function refreshCameras() {
  try {
    const devices = await window.Html5Qrcode.getCameras();
    if (devices?.length) {
      cameras.value = devices.map((d, i) => ({ id: d.id, label: d.label || `Камера ${i + 1}` }));
      const rear = devices.find((d) => /back|rear|environment|задн|основ/i.test(d.label || ''));
      selectedCamera.value = rear?.id || devices[devices.length - 1].id;
    }
  } catch { /* permission not granted yet — keep defaults */ }
}

async function startScanning() {
  if (!window.Html5Qrcode) { statusText.value = 'Нет библиотеки'; return; }
  modalOpen.value = true;
  await nextTick(); // wait for #reader to be rendered before html5-qrcode binds to it
  ensureQr();
  const cam = selectedCamera.value;
  const config = (!cam || cam === 'environment' || cam === 'user') ? { facingMode: cam || 'environment' } : cam;
  try {
    await qr.start(config, { fps: 15, qrbox: (w, h) => { const s = Math.min(w, h) * 0.75; return { width: s, height: s }; } }, onScan, () => {});
    active.value = true;
    statusText.value = 'Сканирование';
    if (cameras.value.length <= 2) await refreshCameras();
  } catch {
    statusText.value = 'Ошибка камеры';
    modalOpen.value = false;
  }
}

async function stopScanning() {
  if (qr && active.value) { try { await qr.stop(); } catch { /* */ } }
  active.value = false;
  modalOpen.value = false;
  statusText.value = 'Готов';
}

async function switchCamera() {
  const idx = cameras.value.findIndex((c) => c.id === selectedCamera.value);
  selectedCamera.value = cameras.value[(idx + 1) % cameras.value.length].id;
  if (active.value) { await stopScanning(); await startScanning(); }
}

function onScan(text, res) {
  if (navigator.vibrate) navigator.vibrate(100);
  const fmt = res?.result?.format?.formatName || 'QR_CODE';
  stopScanning().then(() => handleDecoded(text, fmt));
}

async function onFile(e) {
  const file = e.target.files[0];
  if (!file || !ensureQr()) return;
  try {
    statusText.value = 'Декодирование…';
    const text = await qr.scanFile(file, true);
    handleDecoded(text, 'FILE_SCAN');
  } catch { statusText.value = 'Код не найден'; }
  e.target.value = '';
}

function handleDecoded(text, type) {
  result.value = { text, type };
  addHistory(text, type);
  if (isUrl(text)) { product.value = { state: null }; } else { lookup(text); }
}

async function lookup(barcode) {
  product.value = { state: 'loading' };
  try {
    const { data } = await api.get('/modules/scanner/lookup', { params: { barcode } });
    if (!data || !data.NomCode) { product.value = { state: 'error', error: 'Товар не найден в 1С.' }; return; }
    product.value = { state: 'found', data };
  } catch (e) {
    product.value = { state: 'error', error: e.response?.data?.detail || 'Ошибка запроса к 1С' };
  }
}

function addHistory(text, type) {
  if (history.value[0]?.text === text && Date.now() - history.value[0].id < 5000) return;
  history.value.unshift({ id: Date.now(), text, type, time: new Date().toLocaleString() });
  persist();
}
function showHistory(item) { handleDecoded(item.text, item.type); }
function deleteHistory(id) { history.value = history.value.filter((i) => i.id !== id); persist(); }
function clearHistory() { if (confirm('Очистить историю?')) { history.value = []; persist(); } }
function persist() { localStorage.setItem(HKEY, JSON.stringify(history.value)); }

function isUrl(s) { try { const u = new URL(s.trim()); return u.protocol === 'http:' || u.protocol === 'https:'; } catch { return false; } }
function copy(text) { navigator.clipboard?.writeText(text); }

onBeforeUnmount(stopScanning);
</script>
