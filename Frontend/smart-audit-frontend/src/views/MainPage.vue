<template>
  <div class="main-layout flex min-h-screen w-screen">
    <nav class="sidebar flex flex-column">
      <div class="sidebar-header">
        <div class="logo-container inline-flex">
          <SmartAuditLogo :size="32" />
        </div>
        <h2>Smart Audit</h2>
        <div v-if="cloudAccountsStore.activeAccountId" class="arn-badge inline-flex align-items-center">
          <Cloud :size="14" />
          <span class="arn-text" title="Account ID">
            {{ cloudAccountsStore.activeAccountId.substring(0, 25) }}...
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

      <Button
        class="logout-btn"
        label="Desconectar"
        icon="pi pi-sign-out"
        @click="logout"
      />
    </nav>

    <main class="content flex-1 p-4 md:p-6 lg:p-8 overflow-y-auto relative">
      <router-view></router-view>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { computed,onMounted } from 'vue';
import { useScanStore } from '../store/scanStore';
import { useCloudAccountsStore } from '../store/cloudAccountsStore';
import Button from 'primevue/button';
import { Cloud, LayoutDashboard, Package, Search, Settings } from 'lucide-vue-next';
import SmartAuditLogo from '../components/SmartAuditLogo.vue';

const router = useRouter();
const scanStore = useScanStore();
const cloudAccountsStore = useCloudAccountsStore();
onMounted(() => cloudAccountsStore.loadSelectedAccount());
const hasAccounts = computed(() => cloudAccountsStore.totalAccounts > 0);

const logout = () => {
  scanStore.clearData();
  cloudAccountsStore.clearAccounts();
  router.push('/login');
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
  padding: 2rem 1.5rem;
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

.arn-badge {
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(34, 197, 94, 0.08);
  border: 1px solid rgba(34, 197, 94, 0.25);
  border-radius: 20px;
  font-size: 0.7rem;
  color: #4ade80;
  margin-top: 0.5rem;
  animation: slideIn 0.5s ease-out 0.2s both;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-20px); }
  to { opacity: 1; transform: translateX(0); }
}

.arn-text {
  word-break: break-all;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nav-menu {
  padding: 1.5rem 0;
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

.logout-btn.p-button {
  margin: 1.5rem;
  width: calc(100% - 3rem);
  padding: 0.875rem 1.5rem;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
  animation: slideIn 0.5s ease-out 0.5s both;
}

.logout-btn.p-button:hover {
  transform: translateY(-2px);
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
}

.logout-btn.p-button:active {
  transform: translateY(0);
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
</style>
