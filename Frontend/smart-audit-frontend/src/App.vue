<template>
  <router-view></router-view>
  <ScanProgressToast />
</template>

<script setup>
import ScanProgressToast from './components/ScanProgressToast.vue'
</script>

<style>
:root {
  --sa-accent: #22c55e;
  --sa-accent-dark: #16a34a;
  --sa-accent-light: #4ade80;
  --sa-accent-glow: rgba(34, 197, 94, 0.3);
  --sa-bg: #0d1117;
  --sa-bg-2: #161b22;
  --sa-bg-3: #21262d;
  --sa-text: #e6edf3;
  --sa-text-muted: #8b949e;
  --sa-border: rgba(34, 197, 94, 0.15);
  --sa-logo-color: #22c55e;
  --sa-logo-bg: #0d1117;

  /* PrimeVue Aura – override primary palette to green */
  --p-primary-50: #f0fdf4;
  --p-primary-100: #dcfce7;
  --p-primary-200: #bbf7d0;
  --p-primary-300: #86efac;
  --p-primary-400: #4ade80;
  --p-primary-500: #22c55e;
  --p-primary-600: #16a34a;
  --p-primary-700: #15803d;
  --p-primary-800: #166534;
  --p-primary-900: #14532d;
  --p-primary-950: #052e16;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  background-color: var(--sa-bg);
  color: var(--sa-text);
}

.result-section {
  margin-top: 2rem;
  border-top: 2px solid var(--sa-border);
  padding-top: 1.5rem;
}

pre {
  background-color: var(--sa-bg-2);
  color: var(--sa-accent);
  padding: 1.5rem;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 0.9rem;
}
</style>
