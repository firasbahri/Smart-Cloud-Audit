<template>
  <div class="inventory-view">
    <div class="page-header flex align-items-center gap-3 mb-5">
      <Package :size="32" class="page-icon p-3 border-round-xl shadow-3" />
      <div>
        <h2 class="m-0">Inventario de Recursos AWS</h2>
        <p class="subtitle m-0 mt-2">Recursos detectados en la cuenta vinculada</p>
      </div>
    </div>
    
    <div class="inventory-grid grid">
      <Card class="resource-card card-1 col-12 lg:col-6 xl:col-4">
        <template #content>
        <div class="card-header flex align-items-center gap-3">
          <div class="header-icon flex align-items-center justify-content-center">
            <ShieldCheck :size="24" />
          </div>
          <h3>IAM (Roles)</h3>
          <span class="count-badge ml-auto">{{ roles.length }}</span>
        </div>
        <ul class="resource-list list-none p-0 m-0">
          <li v-for="role in roles" :key="role.idss" class="flex align-items-center gap-2">
            <Key :size="16" />
            <span>{{ role.name }}</span>
          </li>
          <li v-if="!roles.length" class="empty-msg flex align-items-center gap-2 justify-content-center">
            <FileX :size="16" />
            <span>No se encontraron roles</span>
          </li>
        </ul>
        </template>
      </Card>

      <Card class="resource-card card-2 col-12 lg:col-6 xl:col-4">
        <template #content>
        <div class="card-header flex align-items-center gap-3">
          <div class="header-icon flex align-items-center justify-content-center">
            <Server :size="24" />
          </div>
          <h3>EC2 (Instancias)</h3>
          <span class="count-badge ml-auto">{{ instances.length }}</span>
        </div>
        <ul class="resource-list list-none p-0 m-0">
          <li v-for="ec2 in instances" :key="ec2.id" class="flex align-items-center gap-2">
            <Monitor :size="16" />
            <div class="instance-info flex-1 flex justify-content-between align-items-center">
              <strong>{{ ec2.id }}</strong>
              <Tag class="badge" :class="ec2.state" :value="ec2.state" :severity="ec2.state === 'running' ? 'success' : 'danger'" rounded />
            </div>
          </li>
          <li v-if="!instances.length" class="empty-msg flex align-items-center gap-2 justify-content-center">
            <FileX :size="16" />
            <span>No se encontraron instancias</span>
          </li>
        </ul>
        </template>
      </Card>

      <Card class="resource-card card-3 col-12 lg:col-6 xl:col-4">
        <template #content>
        <div class="card-header flex align-items-center gap-3">
          <div class="header-icon flex align-items-center justify-content-center">
            <Database :size="24" />
          </div>
          <h3>Almacenamiento S3</h3>
          <span class="count-badge ml-auto">{{ buckets.length }}</span>
        </div>
        <ul class="resource-list list-none p-0 m-0">
          <li v-for="bucket in buckets" :key="bucket.Name" class="flex align-items-center gap-2">
            <HardDrive :size="16" />
            <span>{{ bucket.name }}</span>
          </li>
          <li v-if="!buckets.length" class="empty-msg flex align-items-center gap-2 justify-content-center">
            <FileX :size="16" />
            <span>No se encontró almacenamiento</span>
          </li>
        </ul>
        </template>
      </Card>

      <Card class="resource-card card-4 col-12 lg:col-6 xl:col-4">
        <template #content>
        <div class="card-header flex align-items-center gap-3">
          <div class="header-icon flex align-items-center justify-content-center">
            <Users :size="24" />
          </div>
          <h3>IAM (Usuarios)</h3>
          <span class="count-badge ml-auto">{{ users.length }}</span>
        </div>
        <ul class="resource-list list-none p-0 m-0">
          <li v-for="user in users" :key="user.UserName" class="flex align-items-center gap-2">
            <User :size="16" />
            <span>{{ user.name }}</span>
          </li>
          <li v-if="!users.length" class="empty-msg flex align-items-center gap-2 justify-content-center">
            <FileX :size="16" />
            <span>No se encontraron usuarios</span>
          </li>
        </ul>
        </template>
      </Card>

      <Card class="resource-card card-5 col-12 lg:col-6 xl:col-4">
        <template #content>
        <div class="card-header flex align-items-center gap-3">
          <div class="header-icon flex align-items-center justify-content-center">
            <Users2 :size="24" />
          </div>
          <h3>IAM (Grupos)</h3>
          <span class="count-badge ml-auto">{{ groups.length }}</span>
        </div>
        <ul class="resource-list list-none p-0 m-0">
          <li v-for="group in groups" :key="group.GroupName" class="flex align-items-center gap-2">
            <Users2 :size="16" />
            <span>{{ group.name }}</span>
          </li>
          <li v-if="!groups.length" class="empty-msg flex align-items-center gap-2 justify-content-center">
            <FileX :size="16" />
            <span>No se encontraron grupos</span>
          </li>
        </ul>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useScanStore } from '../store/scanStore';
import Card from 'primevue/card';
import Tag from 'primevue/tag';
import { Package, ShieldCheck, Server, Database, Key, Monitor, HardDrive, FileX, Users, User, Users2 } from 'lucide-vue-next';

const router = useRouter();
const scanStore = useScanStore();



const roles = computed(() => scanStore.scanResult?.roles || []);
const instances = computed(() => scanStore.scanResult?.ec2 || []);
const buckets = computed(() => scanStore.scanResult?.buckets || []);
const users = computed(() => scanStore.scanResult?.users || []);
const groups = computed(() => scanStore.scanResult?.groups || []);
</script>

<style scoped>
.inventory-view {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.page-header {
  animation: slideDown 0.6s ease-out;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}

.page-icon {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.page-header h2 {
  margin: 0;
  color: #e6edf3;
  font-size: 2rem;
  font-weight: 700;
}

.subtitle {
  color: #8b949e;
  font-size: 1rem;
}

.inventory-grid {
  row-gap: 2rem;
}

.resource-card {
  background: #161b22;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
  border: 1px solid rgba(34, 197, 94, 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
  animation: slideUp 0.6s ease-out both;
}

.card-1 { animation-delay: 0.1s; }
.card-2 { animation-delay: 0.2s; }
.card-3 { animation-delay: 0.3s; }
.card-4 { animation-delay: 0.4s; }
.card-5 { animation-delay: 0.5s; }

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.resource-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px -4px rgba(0,0,0,0.1);
}

.card-header {
  padding: 1.5rem;
  background: #21262d;
  border-bottom: 1px solid rgba(34, 197, 94, 0.1);
}

.header-icon {
  padding: 0.75rem;
  border-radius: 12px;
}

.card-1 .header-icon {
  background: rgba(34, 197, 94, 0.12);
  color: #22c55e;
}

.card-2 .header-icon {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(245, 158, 11, 0.2));
  color: #f59e0b;
}

.card-3 .header-icon {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(16, 185, 129, 0.2));
  color: #10b981;
}

.card-4 .header-icon {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(59, 130, 246, 0.2));
  color: #3b82f6;
}

.card-5 .header-icon {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(168, 85, 247, 0.2));
  color: #a855f7;
}

.card-header h3 {
  margin: 0;
  color: #e6edf3;
  font-size: 1.125rem;
  font-weight: 600;
}

.count-badge {
  background: #22c55e;
  color: white;
  font-size: 0.875rem;
  font-weight: 700;
  padding: 0.375rem 0.875rem;
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3);
}

.resource-list {
  max-height: 400px;
  overflow-y: auto;
}

.resource-list li {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  font-size: 0.95rem;
  color: #c9d1d9;
  transition: all 0.2s ease;
}

.resource-list li:hover {
  background: rgba(34, 197, 94, 0.05);
  padding-left: 2rem;
}

.resource-list li svg {
  color: #94a3b8;
  flex-shrink: 0;
}

.resource-list li span {
  flex: 1;
}

.empty-msg {
  color: #94a3b8;
  font-style: italic;
}

.empty-msg svg {
  color: #cbd5e1;
}

.badge {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.resource-list::-webkit-scrollbar {
  width: 6px;
}

.resource-list::-webkit-scrollbar-track {
  background: #21262d;
}

.resource-list::-webkit-scrollbar-thumb {
  background: rgba(34, 197, 94, 0.3);
  border-radius: 3px;
}

.resource-list::-webkit-scrollbar-thumb:hover {
  background: rgba(34, 197, 94, 0.5);
}
</style>
