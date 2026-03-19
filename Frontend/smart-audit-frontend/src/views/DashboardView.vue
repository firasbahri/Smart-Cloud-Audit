<template>
  <div class="dashboard-view">
    <div class="page-header flex align-items-center gap-3 mb-5">
      <LayoutDashboard :size="32" class="page-icon p-3 border-round-xl shadow-3" />
      <div>
        <h2 class="m-0">Panel de Control</h2>
        <p class="subtitle m-0 mt-2">Resumen de la auditoría de infraestructura AWS</p>
      </div>
    </div>

    <div class="dashboard-stats grid">
      <Card class="stat-card card-1 col-12 md:col-6 xl:col-3 h-full">
        <template #content>
        <div class="flex align-items-center gap-3">
        <div class="stat-icon flex align-items-center justify-content-center">
          <ShieldCheck :size="32" />
        </div>
        <div class="stat-content flex-1 flex flex-column justify-content-center">
          <h3>Roles IAM</h3>
          <p class="stat-number">{{ rolesCount }}</p>
          <span class="stat-trend inline-flex align-items-center gap-1">
            <TrendingUp :size="14" />
            Detectados
          </span>
        </div>
        </div>
        </template>
      </Card>

      <Card class="stat-card card-2 col-12 md:col-6 xl:col-3 h-full">
        <template #content>
        <div class="flex align-items-center gap-3">
        <div class="stat-icon flex align-items-center justify-content-center">
          <Server :size="32" />
        </div>
        <div class="stat-content flex-1 flex flex-column justify-content-center">
          <h3>Instancias EC2</h3>
          <p class="stat-number">{{ instancesCount }}</p>
          <span class="stat-trend inline-flex align-items-center gap-1">
            <Activity :size="14" />
            Detectadas
          </span>
        </div>
        </div>
        </template>
      </Card>

      <Card class="stat-card card-3 col-12 md:col-6 xl:col-3 h-full">
        <template #content>
        <div class="flex align-items-center gap-3">
        <div class="stat-icon flex align-items-center justify-content-center">
          <Database :size="32" />
        </div>
        <div class="stat-content flex-1 flex flex-column justify-content-center">
          <h3>Almacenamiento S3</h3>
          <p class="stat-number">{{ bucketsCount }}</p>
          <span class="stat-trend inline-flex align-items-center gap-1">
            <HardDrive :size="14" />
            Detectado
          </span>
        </div>
        </div>
        </template>
      </Card>

      <Card class="stat-card card-4 col-12 md:col-6 xl:col-3 h-full">
        <template #content>
        <div class="flex align-items-center gap-3">
        <div class="stat-icon flex align-items-center justify-content-center">
          <AlertTriangle :size="32" />
        </div>
        <div class="stat-content flex-1 flex flex-column justify-content-center">
          <h3>Problemas</h3>
          <p class="stat-number">{{ issuesCount }}</p>
          <span class="stat-trend inline-flex align-items-center gap-1">
            <AlertCircle :size="14" />
            Detectados
          </span>
        </div>
        </div>
        </template>
      </Card>

      <Card class="stat-card card-5 col-12 md:col-6 xl:col-3 h-full">
        <template #content>
        <div class="flex align-items-center gap-3">
        <div class="stat-icon flex align-items-center justify-content-center">
          <Users :size="32" />
        </div>
        <div class="stat-content flex-1 flex flex-column justify-content-center">
          <h3>Usuarios IAM</h3>
          <p class="stat-number">{{ usersCount }}</p>
          <span class="stat-trend inline-flex align-items-center gap-1">
            <User :size="14" />
            Detectados
          </span>
        </div>
        </div>
        </template>
      </Card>

      <Card class="stat-card card-6 col-12 md:col-6 xl:col-3 h-full">
        <template #content>
        <div class="flex align-items-center gap-3">
        <div class="stat-icon flex align-items-center justify-content-center">
          <Users2 :size="32" />
        </div>
        <div class="stat-content flex-1 flex flex-column justify-content-center">
          <h3>Grupos IAM</h3>
          <p class="stat-number">{{ groupsCount }}</p>
          <span class="stat-trend inline-flex align-items-center gap-1">
            <Users2 :size="14" />
            Detectados
          </span>
        </div>
        </div>
        </template>
      </Card>
    </div>

    <Card class="dashboard-section mt-4">
      <template #content>
      <div class="section-header flex align-items-center gap-2 mb-3 pb-3 border-bottom-2 surface-border">
        <Clock :size="24" />
        <h3>Información del Escaneo</h3>
      </div>
      <div v-if="scanStore.awsArn" class="scan-info flex flex-column gap-3">
        <div class="info-item flex align-items-start gap-3 p-3 border-round-xl surface-50">
          <Cloud :size="20" />
          <div class="flex-1">
            <strong>ARN:</strong>
            <span>{{ scanStore.awsArn }}</span>
          </div>
        </div>
        <div class="info-item flex align-items-start gap-3 p-3 border-round-xl surface-50">
          <CheckCircle2 :size="20" />
          <div class="flex-1">
            <strong>Estado:</strong>
            <Tag class="badge-success" severity="success" value="Conectado" rounded />
          </div>
        </div>
        <div class="info-item flex align-items-start gap-3 p-3 border-round-xl surface-50">
          <Calendar :size="20" />
          <div class="flex-1">
            <strong>Fecha:</strong>
            <span>{{ new Date().toLocaleString() }}</span>
          </div>
        </div>
      </div>
      <div v-else class="scan-info empty flex flex-column align-items-center p-6 text-center">
        <FileQuestion :size="48" />
        <p class="text-muted">No hay datos de escaneo disponibles</p>
      </div>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import Card from 'primevue/card';
import Tag from 'primevue/tag';
import { useScanStore } from '../store/scanStore';
import { 
  LayoutDashboard, ShieldCheck, Server, Database, AlertTriangle, 
  TrendingUp, Activity, HardDrive, AlertCircle, Clock, Cloud, 
  CheckCircle2, Calendar, FileQuestion, Users, User, Users2 
} from 'lucide-vue-next';

const scanStore = useScanStore();

const rolesCount = computed(() => scanStore.scanResult?.roles?.length || 0);
const instancesCount = computed(() => scanStore.scanResult?.ec2?.length || 0);
const bucketsCount = computed(() => scanStore.scanResult?.buckets?.length || 0);
const usersCount = computed(() => scanStore.scanResult?.users?.length || 0);
const groupsCount = computed(() => scanStore.scanResult?.groups?.length || 0);
const issuesCount = computed(() => 0);
</script>

<style scoped>
.dashboard-view {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.page-header { animation: slideDown 0.6s ease-out; }

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}

.page-icon {
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #22c55e;
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

.dashboard-stats {
  margin-bottom: 2.5rem;
}

.stat-card {
  background: #161b22;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
  border: 1px solid rgba(34, 197, 94, 0.1);
  transition: all 0.3s ease;
  animation: slideUp 0.6s ease-out both;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, transparent, var(--accent-color), transparent);
  transform: translateX(-100%);
  transition: transform 0.6s ease;
}

.stat-card:hover::before {
  transform: translateX(100%);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px -4px rgba(0,0,0,0.1);
}

.card-1 { --accent-color: #22c55e; animation-delay: 0.1s; }
.card-2 { --accent-color: #f59e0b; animation-delay: 0.2s; }
.card-3 { --accent-color: #10b981; animation-delay: 0.3s; }
.card-4 { --accent-color: #ef4444; animation-delay: 0.4s; }

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.stat-icon {
  padding: 1rem;
  border-radius: 12px;
}

.card-1 .stat-icon {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.2));
  color: #22c55e;
}

.card-2 .stat-icon {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(245, 158, 11, 0.2));
  color: #f59e0b;
}

.card-3 .stat-icon {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(16, 185, 129, 0.2));
  color: #10b981;
}

.card-4 .stat-icon {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.2));
  color: #ef4444;
}

.stat-content h3 {
  margin: 0;
  color: #8b949e;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-number {
  margin: 0.5rem 0;
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--accent-color);
}

.stat-trend {
  font-size: 0.75rem;
  color: #8b949e;
  font-weight: 500;
}

.dashboard-section {
  background: #161b22;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
  border: 1px solid rgba(34, 197, 94, 0.1);
  animation: slideUp 0.6s ease-out 0.5s both;
}

.section-header h3 {
  margin: 0;
  color: #e6edf3;
  font-size: 1.25rem;
  font-weight: 600;
}

.section-header svg {
  color: #22c55e;
}

.scan-info.empty svg {
  color: #cbd5e1;
  margin-bottom: 1rem;
}

.info-item {
  transition: all 0.2s ease;
}

.info-item:hover {
  transform: translateX(4px);
}

.info-item svg {
  color: #22c55e;
  margin-top: 0.25rem;
  flex-shrink: 0;
}

.info-item strong {
  display: block;
  color: #8b949e;
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}

.info-item span {
  color: #e6edf3;
  font-size: 0.95rem;
}

.badge-success {
  font-size: 0.875rem;
  font-weight: 600;
}

.text-muted {
  color: #94a3b8;
  font-style: italic;
  margin: 0;
}
</style>
