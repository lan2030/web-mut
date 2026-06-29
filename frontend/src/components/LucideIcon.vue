<template>
  <i :data-lucide="name" ref="el"></i>
</template>

<script setup>
import { onMounted, watch, ref, nextTick } from 'vue';

const props = defineProps({ name: { type: String, required: true } });
const el = ref(null);

function render() {
  if (window.lucide?.createIcons) {
    window.lucide.createIcons({ nameAttr: 'data-lucide' });
  }
}
onMounted(render);
watch(() => props.name, () => nextTick(render));
</script>
