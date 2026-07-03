<template>
  <div v-if="activeScans.length > 0" class="scan-progress-toast">
    <div class="toast-header">
      <i class="pi pi-spin pi-spinner" style="font-size: 0.85rem"></i>
      <span>Escaneando...</span>
    </div>
    <div v-for="scan in activeScans" :key="scan.accountId" class="scan-item">
      <div class="scan-item-header">
        <span class="account-name">{{ scan.name }}</span>
        <span class="progress-label">{{ scan.progress }}%</span>
      </div>
      <ProgressBar :value="scan.progress" :showValue="false" style="height: 0.4rem" />
    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useScanStore } from '../store/scanStore'
import { useCloudAccountsStore } from '../store/cloudAccountsStore'
import ProgressBar from 'primevue/progressbar'

const toast = useToast()
const scanStore = useScanStore()
const cloudAccountsStore = useCloudAccountsStore()

const activeScans = computed(() => {
  return Object.entries(scanStore.scanningAccounts)
    .filter(([, isScanning]) => isScanning)
    .map(([accountId]) => {
      const account = cloudAccountsStore.accounts.find(a => String(a.id) === String(accountId))
      return {
        accountId,
        name: account?.name || `Cuenta ${accountId}`,
        progress: scanStore.scanProgressByAccount[accountId] || 0
      }
    })
})

// Consume notificaciones del store y las muestra como toast
watch(
  () => scanStore.pendingNotifications.length,
  () => {
    if (scanStore.pendingNotifications.length === 0) return
    const notifications = scanStore.consumeNotifications()
    notifications.forEach(({ _id, ...n }) => toast.add(n))
  }
)
</script>

<style scoped>
.scan-progress-toast {
  position: fixed;
  top: 1.5rem;
  right: 1.5rem;
  z-index: 9999;
  background: #1c2128;
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 12px;
  padding: 1rem 1.2rem;
  min-width: 260px;
  max-width: 320px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  animation: slideIn 0.3s ease;
}

.toast-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #22c55e;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.scan-item {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.scan-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.account-name {
  font-size: 0.85rem;
  color: #e6edf3;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.progress-label {
  font-size: 0.75rem;
  color: #8b949e;
  font-weight: 600;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>
