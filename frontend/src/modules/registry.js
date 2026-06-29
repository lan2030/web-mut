// Maps a module key (from the backend) to its SPA view component.
// Backend is the source of truth for *which* modules a user may access; this
// registry only wires each key to its frontend route/component.
export const MODULE_COMPONENTS = {
  scanner: () => import('@/views/modules/ScannerView.vue'),
};
