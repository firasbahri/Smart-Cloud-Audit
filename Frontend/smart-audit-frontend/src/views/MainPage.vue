<template>
  <div class="main-layout flex min-h-screen w-screen">
    <nav class="sidebar flex flex-column">
      <div class="sidebar-header">
        <div class="logo-container inline-flex">
          <SmartAuditLogo :size="32" />
        </div>
        <h2>Smart Audit</h2>
        <div v-if="hasAccounts" class="account-name-badge inline-flex align-items-center">
          <Cloud :size="14" />
          <span class="account-name-text" :title="selectedAccountName">
            {{ selectedAccountName }}
          </span>
        </div>
      </div>

      <ul class="nav-menu list-none p-0 m-0 flex-1">
        <li>
          <router-link to="/app/cloud-accounts" active-class="active">
            <Cloud :size="20" />
            <span>Cuentas de Nube</span>
          </router-link>
        </li>
        
        <template v-if="hasAccounts">
          <li>
            <router-link to="/app/dashboard" active-class="active">
              <LayoutDashboard :size="20" />
              <span>Panel de Control</span>
            </router-link>
          </li>
          <li>
            <router-link to="/app/inventory" active-class="active">
              <Package :size="20" />
              <span>Inventario</span>
            </router-link>
          </li>
          <li>
            <router-link to="/app/audit" active-class="active">
              <Search :size="20" />
              <span>Auditoría</span>
            </router-link>
          </li>
          <li>
            <router-link to="/app/configuration" active-class="active">
              <Settings :size="20" />
              <span>Configuración</span>
            </router-link>
          </li>
        </template>
        
        <li v-else class="menu-hint">
          <div class="hint-text">
            <span>👆 Añade una cuenta para comenzar</span>
          </div>
        </li>
      </ul>

      <div ref="userMenuRef" class="user-footer">
        <Transition name="user-menu">
          <div v-if="userMenuOpen" class="user-menu">
            <div class="user-menu-item">
              <User :size="13" /> Mi perfil
            </div>
            <div class="user-menu-divider" />
            <div class="user-menu-item danger" @click.stop="logout">
              <LogOut :size="13" /> Cerrar sesión
            </div>
          </div>
        </Transition>
        <div class="user-row" @click.stop="userMenuOpen = !userMenuOpen">
          <div class="user-avatar">{{ userInitial }}</div>
          <div class="user-info">
            <span class="user-name">{{ storedUsername }}</span>
          </div>
          <ChevronUp v-if="userMenuOpen" :size="14" class="user-chevron" />
          <ChevronDown v-else :size="14" class="user-chevron" />
        </div>
      </div>
    </nav>

    <main class="content flex-1 p-4 md:p-6 lg:p-8 overflow-y-auto relative">
      <div v-if="hasAccounts" class="content-account-corner">
        <span class="account-switcher-label">Cambiar cuenta</span>
        <Select
          v-model="selectedAccountKey"
          :options="accountOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Selecciona una cuenta"
          appendTo="self"
          :style="accountSelectStyle"
          class="account-select"
        />
      </div>
      <router-view></router-view>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useScanStore } from '../store/scanStore';
import { useAuditStore } from '@/store/auditStore';
import { useCloudAccountsStore } from '../store/cloudAccountsStore';
import Select from 'primevue/select';
import { Cloud, ChevronDown, ChevronUp, LayoutDashboard, LogOut, Package, Search, Settings, User } from 'lucide-vue-next';
import SmartAuditLogo from '../components/SmartAuditLogo.vue';

const router = useRouter();
const scanStore = useScanStore();
const auditStore = useAuditStore();
const cloudAccountsStore = useCloudAccountsStore();
let isLoggingOut = false;

const userMenuOpen = ref(false)
const userMenuRef = ref(null)
const storedUsername = computed(() => localStorage.getItem('username') || 'Usuario')
const userInitial = computed(() => storedUsername.value.charAt(0).toUpperCase())

const handleDocumentClick = (e) => {
  if (userMenuRef.value && !userMenuRef.value.contains(e.target)) {
    userMenuOpen.value = false
  }
}

const getAccountKey = (account) => String(
  account?.id ?? account?.account_id ?? account?.identifier ?? account?.name ?? ''
);

const accountOptions = computed(() =>
  cloudAccountsStore.accounts.map(account => ({
    label: account.name || 'Cuenta sin nombre',
    value: getAccountKey(account)
  }))
);

const selectedAccountKey = computed({
  get: () => (cloudAccountsStore.selectedAccount ? getAccountKey(cloudAccountsStore.selectedAccount) : null),
  set: (value) => {
    const selected = cloudAccountsStore.accounts.find(account => getAccountKey(account) === String(value));
    if (selected) {
      cloudAccountsStore.selectAccount(selected);
    }
  }
});

const selectedAccountName = computed(() => {
  const selected = cloudAccountsStore.selectedAccount;
  return selected?.name || 'Cuenta sin nombre';
});

const accountSelectStyle = computed(() => {
  const widthInCh = Math.min(24, Math.max(12, selectedAccountName.value.length + 3));
  return {
    width: `${widthInCh}ch`,
    maxWidth: '100%'
  };
});

watch(() => cloudAccountsStore.selectedAccount, async(account) => {
  if (!account) {
    scanStore.clearData();
    auditStore.clearData();

    if (isLoggingOut || !localStorage.getItem('token')) {
      return;
    }

    router.push('/app/cloud-accounts');
    return;
  }

  try {
    await scanStore.loadScanDataForAccount(account);
    await auditStore.loadAuditDataForAccount(account);
    
  } catch (error) {
    console.error('Error cargando datos por cuenta seleccionada:', error);
  }
}, { immediate: true });
 
onUnmounted(() => {
  document.removeEventListener('click', handleDocumentClick)
})

onMounted(async () => {
  document.addEventListener('click', handleDocumentClick)
  cloudAccountsStore.loadSelectedAccount();
  await cloudAccountsStore.loadAccounts();

  const restoredKey = cloudAccountsStore.selectedAccount
    ? getAccountKey(cloudAccountsStore.selectedAccount)
    : null;

  if (restoredKey) {
    const matchedAccount = cloudAccountsStore.accounts.find(account => getAccountKey(account) === restoredKey);
    if (matchedAccount) {
      cloudAccountsStore.selectAccount(matchedAccount);
      return;
    }
  }

  if (cloudAccountsStore.accounts.length > 0) {
    cloudAccountsStore.selectAccount(cloudAccountsStore.accounts[0]);
  }
});

const hasAccounts = computed(() => cloudAccountsStore.totalAccounts > 0);

const logout = () => {
  isLoggingOut = true;
  localStorage.removeItem('token');

  scanStore.clearData();
  auditStore.clearData();
  cloudAccountsStore.clearAccounts();

  router.replace('/login');
};
</script>

<style scoped>
.sidebar {
  width: 280px;
  background: #0d1117;
  color: white;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.4);
  position: relative;
  z-index: 100;
}

.sidebar-header {
  padding: 2rem 1.5rem 2.6rem;
  text-align: center;
  border-bottom: 1px solid rgba(34, 197, 94, 0.15);
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.logo-container {
  padding: 1rem;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 16px;
  margin-bottom: 1rem;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }
  50% { transform: scale(1.05); box-shadow: 0 0 0 10px rgba(34, 197, 94, 0); }
}

.logo-icon {
  color: white;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.sidebar-header h2 {
  color: #22c55e;
  margin: 0 0 1rem 0;
  font-size: 1.5rem;
  font-weight: 700;
}

.account-name-badge {
  gap: 0.5rem;
  padding: 0.5rem 0.85rem;
  background: rgba(34, 197, 94, 0.08);
  border: 1px solid rgba(34, 197, 94, 0.25);
  border-radius: 999px;
  color: #4ade80;
  font-size: 0.75rem;
  max-width: 100%;
  animation: slideIn 0.5s ease-out 0.2s both;
}

.account-name-text {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-20px); }
  to { opacity: 1; transform: translateX(0); }
}

.account-select {
  background: #0d1a15 !important;
  color: #c9d1d9;
  border: 1px solid rgba(34, 197, 94, 0.35);
  border-radius: 9px;
  min-height: 1.95rem;
  box-shadow: none;
}

.content-account-corner {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 25;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.35rem;
}

.account-switcher-label {
  font-size: 0.72rem;
  color: rgba(74, 222, 128, 0.85);
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.account-select :deep(.p-select:not(.p-disabled).p-focus) {
  border-color: #22c55e;
  box-shadow: 0 0 0 1px rgba(34, 197, 94, 0.35);
}

.account-select :deep(.p-select-label) {
  font-size: 0.76rem;
  color: #c9d1d9 !important;
  background: transparent !important;
  padding: 0.35rem 0.55rem;
  line-height: 1.2;
}

.account-select :deep(.p-select-dropdown) {
  background: transparent !important;
  color: #34d399;
  width: 1.8rem;
}

.account-select :deep(.p-select-overlay) {
  background: #0d1a15 !important;
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 10px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.35);
}

.account-select :deep(.p-select-list) {
  background: #0d1a15 !important;
  padding: 0.2rem;
}

.account-select :deep(.p-select-option) {
  background: transparent;
  color: #c9d1d9;
  border-radius: 8px;
  font-size: 0.8rem;
  padding: 0.45rem 0.55rem;
}

.account-select :deep(.p-select-option.p-select-option-selected) {
  background: rgba(34, 197, 94, 0.16);
  color: #86efac;
}

.account-select :deep(.p-select-option:not(.p-select-option-selected):not(.p-disabled):hover) {
  background: rgba(34, 197, 94, 0.08);
}

.nav-menu {
  padding: 1.1rem 0;
}

.nav-menu li {
  margin: 0.5rem 0;
  animation: slideIn 0.5s ease-out both;
}

.nav-menu li:nth-child(1) { animation-delay: 0.1s; }
.nav-menu li:nth-child(2) { animation-delay: 0.2s; }
.nav-menu li:nth-child(3) { animation-delay: 0.3s; }
.nav-menu li:nth-child(4) { animation-delay: 0.4s; }

.nav-menu li a {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  color: #8b949e;
  text-decoration: none;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
  position: relative;
  overflow: hidden;
}

.nav-menu li a::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 0;
  background: linear-gradient(90deg, rgba(34, 197, 94, 0.08) 0%, transparent 100%);
  transition: width 0.3s ease;
}

.nav-menu li a:hover::before {
  width: 100%;
}

.nav-menu li a:hover {
  color: #e6edf3;
  background-color: rgba(34, 197, 94, 0.05);
  transform: translateX(5px);
}

.nav-menu li a.active {
  background: linear-gradient(90deg, rgba(34, 197, 94, 0.12) 0%, transparent 100%);
  color: #4ade80;
  border-left-color: #22c55e;
  font-weight: 600;
}

.nav-menu li a.active::after {
  content: '';
  position: absolute;
  right: 1rem;
  width: 6px;
  height: 6px;
  background: #22c55e;
  border-radius: 50%;
  box-shadow: 0 0 10px #22c55e;
  animation: blink 2s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.user-footer {
  padding: 10px 12px;
  border-top: 1px solid rgba(34, 197, 94, 0.15);
  position: relative;
}

.user-row {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.user-row:hover {
  background: rgba(255, 255, 255, 0.05);
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(34, 197, 94, 0.12);
  border: 1.5px solid #22c55e;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: #22c55e;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 12px;
  font-weight: 500;
  color: #c9d1d9;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-chevron {
  color: #4d5566;
  flex-shrink: 0;
}

.user-menu {
  position: absolute;
  bottom: calc(100% + 4px);
  left: 12px;
  right: 12px;
  background: #1c2128;
  border: 1px solid #2d333b;
  border-radius: 9px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
  z-index: 200;
}

.user-menu-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 9px 14px;
  font-size: 12px;
  cursor: pointer;
  color: #768390;
  transition: background 0.1s;
}

.user-menu-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #e6edf3;
}

.user-menu-item.danger {
  color: #f85149;
}

.user-menu-item.danger:hover {
  background: rgba(248, 81, 73, 0.12);
}

.user-menu-divider {
  height: 1px;
  background: #2d333b;
  margin: 4px 0;
}

.user-menu-enter-active,
.user-menu-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.user-menu-enter-from,
.user-menu-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

.menu-hint {
  margin-top: 2rem;
  padding: 0 1.5rem;
}

.hint-text {
  padding: 1rem;
  background: rgba(34, 197, 94, 0.05);
  border: 1px dashed rgba(34, 197, 94, 0.25);
  border-radius: 12px;
  color: #8b949e;
  font-size: 0.85rem;
  text-align: center;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.content {
  background: #0d1117;
}

.content :deep(.p-select-label) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 300px;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.03) 0%, transparent 100%);
  pointer-events: none;
}

@media (max-width: 768px) {
  .content-account-corner {
    position: static;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    justify-content: flex-end;
    margin-bottom: 0.75rem;
  }

  .account-select {
    width: min(100%, 16rem);
  }
}
</style>
