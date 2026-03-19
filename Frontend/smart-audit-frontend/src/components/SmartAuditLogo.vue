<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 100 100"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    class="smart-audit-logo"
    :aria-label="label"
    role="img"
  >
    <!-- Background rounded square (optional) -->
    <rect
      v-if="withBackground"
      x="0" y="0" width="100" height="100"
      rx="18" ry="18"
      :fill="bgColor"
    />

    <!-- Outer shield -->
    <path
      d="M50 9 C71 9 88 16 88 32 C88 63 70 81 50 92 C30 81 12 63 12 32 C12 16 29 9 50 9 Z"
      :stroke="strokeColor"
      stroke-width="3"
      stroke-linejoin="round"
      fill="none"
    />

    <!-- Inner shield -->
    <path
      d="M50 19 C68 19 78 25 78 36 C78 60 63 76 50 85 C37 76 22 60 22 36 C22 25 32 19 50 19 Z"
      :stroke="strokeColor"
      stroke-width="2.5"
      stroke-linejoin="round"
      fill="none"
    />

    <!-- Vertical dividing line -->
    <line
      x1="50" y1="19" x2="50" y2="85"
      :stroke="strokeColor"
      stroke-width="2.5"
      stroke-linecap="round"
    />

    <!-- Center ring -->
    <circle
      cx="50" cy="48" r="7"
      :stroke="strokeColor"
      stroke-width="2.5"
      fill="none"
    />

    <!-- Center dot -->
    <circle
      cx="50" cy="48" r="2.5"
      :fill="strokeColor"
    />
  </svg>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  size: {
    type: [Number, String],
    default: 48
  },
  /** Override stroke color directly. Falls back to CSS var --sa-logo-color, then teal. */
  color: {
    type: String,
    default: null
  },
  /** Show the dark rounded-square background (like the app icon). */
  withBackground: {
    type: Boolean,
    default: false
  },
  /** Override background color when withBackground is true. */
  background: {
    type: String,
    default: null
  },
  label: {
    type: String,
    default: 'SmartAudit logo'
  }
});

const strokeColor = computed(() => props.color ?? 'var(--sa-logo-color, #17c3ce)');
const bgColor     = computed(() => props.background ?? 'var(--sa-logo-bg, #2d3748)');
</script>

<style scoped>
.smart-audit-logo {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
}
</style>
