<template>
  <div class="audit-view">
    <div class="page-header flex align-items-center gap-3 mb-5">
      <Search :size="32" class="page-icon p-3 border-round-xl shadow-3" />
      <div>
        <h2 class="m-0">Auditoría de Seguridad</h2>
        <p class="subtitle m-0 mt-2">Verificación de cumplimiento de políticas y mejores prácticas</p>
      </div>
    </div>

    <div class="audit-filters mb-4">
      <SelectButton v-model="activeFilter" :options="filters" />
    </div>

    <div class="audit-results flex flex-column gap-3">
      <Card v-if="filteredIssues.length === 0" class="empty-state">
        <template #content>
        <div class="flex flex-column align-items-center text-center py-6">
          <CheckCircle2 :size="48" />
          <p class="m-0 mt-3">No se encontraron problemas de seguridad</p>
        </div>
        </template>
      </Card>

      <Card v-for="(issue, idx) in filteredIssues" :key="idx" class="issue-card" :class="issue.severity">
        <template #content>
        <div class="issue-header flex align-items-center gap-3 mb-3">
          <div class="severity-icon flex align-items-center justify-content-center">
            <ShieldAlert v-if="issue.severity === 'Crítico'" :size="20" />
            <AlertTriangle v-else-if="issue.severity === 'Alto'" :size="20" />
            <AlertCircle v-else-if="issue.severity === 'Medio'" :size="20" />
            <Info v-else :size="20" />
          </div>
          <Tag class="severity-badge" :value="issue.severity" :severity="severityTag(issue.severity)" rounded />
          <h4 class="m-0 flex-1">{{ issue.title }}</h4>
        </div>
        <p class="issue-description">{{ issue.description }}</p>
        <div class="issue-details flex flex-column gap-2">
          <div class="detail-item flex align-items-start gap-2">
            <Server :size="16" />
            <strong>Recurso:</strong>
            <span>{{ issue.resource }}</span>
          </div>
          <div class="detail-item recommendation flex align-items-start gap-2">
            <Lightbulb :size="16" />
            <strong>Recomendación:</strong>
            <span>{{ issue.recommendation }}</span>
          </div>
        </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import SelectButton from 'primevue/selectbutton';
import Tag from 'primevue/tag';
import Card from 'primevue/card';
import { useAuditStore } from '../store/scanStore';
import { 
  Search, CheckCircle2, ShieldAlert, AlertTriangle, 
  AlertCircle, Info, Server, Lightbulb 
} from 'lucide-vue-next';

const auditStore = useAuditStore();
const activeFilter = ref('Todos');

const filters = ['Todos', 'Crítico', 'Alto', 'Medio', 'Bajo'];

const issues = ref([
  {
    severity: 'Crítico',
    title: 'Root Account MFA No Habilitado',
    description: 'La cuenta raíz no tiene autenticación multifactor activada',
    resource: 'AWS Account',
    recommendation: 'Habilitar MFA en la cuenta raíz inmediatamente'
  },
  {
    severity: 'Alto',
    title: 'Buckets S3 Públicos',
    description: 'Se detectaron buckets S3 con acceso público',
    resource: 'S3 Buckets',
    recommendation: 'Revisar y restringir permisos públicos en todos los buckets'
  },
  {
    severity: 'Medio',
    title: 'Grupos de Seguridad Permisivos',
    description: 'Grupos de seguridad con reglas demasiado permisivas',
    resource: 'Security Groups',
    recommendation: 'Implementar principio de menor privilegio'
  },
  {
    severity: 'Bajo',
    title: 'Instancias sin Etiquetar',
    description: 'Instances EC2 sin tags de identificación',
    resource: 'EC2 Instances',
    recommendation: 'Aplicar política de tags obligatorios'
  }
]);

const filteredIssues = computed(() => {
  if (activeFilter.value === 'Todos') {
    return issues.value;
  }
  return issues.value.filter(issue => issue.severity === activeFilter.value);
});

const severityTag = (severity) => {
  if (severity === 'Crítico') return 'danger';
  if (severity === 'Alto') return 'warn';
  if (severity === 'Medio') return 'contrast';
  return 'info';
};
</script>

<style scoped>
.audit-view {
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
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
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

.audit-filters {
  animation: slideIn 0.6s ease-out 0.2s both;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-20px); }
  to { opacity: 1; transform: translateX(0); }
}

.audit-filters :deep(.p-selectbutton .p-togglebutton) {
  border-radius: 12px;
  font-weight: 600;
}

.empty-state {
  background: rgba(34, 197, 94, 0.05);
  border-radius: 16px;
  color: #4ade80;
  font-weight: 600;
  border: 2px dashed rgba(34, 197, 94, 0.25);
  animation: slideUp 0.6s ease-out 0.3s both;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.empty-state svg {
  color: #22c55e;
  margin-bottom: 1rem;
}

.empty-state p {
  margin: 0;
  font-size: 1.125rem;
}

.issue-card {
  background: #161b22;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
  border: 1px solid rgba(255,255,255,0.06);
  border-left: 4px solid #8b949e;
  transition: all 0.3s ease;
  animation: slideUp 0.6s ease-out both;
}

.issue-card:nth-child(1) { animation-delay: 0.1s; }
.issue-card:nth-child(2) { animation-delay: 0.2s; }
.issue-card:nth-child(3) { animation-delay: 0.3s; }
.issue-card:nth-child(4) { animation-delay: 0.4s; }

.issue-card:hover {
  transform: translateX(4px);
  box-shadow: 0 8px 16px -2px rgba(0,0,0,0.1);
}

.issue-card.Crítico {
  border-left-color: #dc2626;
  background: linear-gradient(to right, rgba(220, 38, 38, 0.08) 0%, #161b22 50%);
}

.issue-card.Alto {
  border-left-color: #f59e0b;
  background: linear-gradient(to right, rgba(245, 158, 11, 0.08) 0%, #161b22 50%);
}

.issue-card.Medio {
  border-left-color: #eab308;
  background: linear-gradient(to right, rgba(234, 179, 8, 0.08) 0%, #161b22 50%);
}

.issue-card.Bajo {
  border-left-color: #3b82f6;
  background: linear-gradient(to right, rgba(59, 130, 246, 0.08) 0%, #161b22 50%);
}

.severity-icon {
  padding: 0.5rem;
  border-radius: 10px;
}

.issue-card.Crítico .severity-icon {
  background: rgba(220, 38, 38, 0.1);
  color: #dc2626;
}

.issue-card.Alto .severity-icon {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.issue-card.Medio .severity-icon {
  background: rgba(234, 179, 8, 0.1);
  color: #eab308;
}

.issue-card.Bajo .severity-icon {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.severity-badge {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.issue-card h4 {
  color: #e6edf3;
  font-size: 1.125rem;
}

.issue-description {
  margin: 0 0 1.5rem 0;
  color: #8b949e;
  font-size: 0.95rem;
  line-height: 1.6;
}

.detail-item {
  padding: 0.875rem;
  background: #21262d;
  border-radius: 10px;
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.detail-item:hover {
  background: #30363d;
}

.detail-item svg {
  color: #8b949e;
  margin-top: 0.125rem;
  flex-shrink: 0;
}

.detail-item.recommendation svg {
  color: #f59e0b;
}

.detail-item strong {
  color: #c9d1d9;
  margin-right: 0.5rem;
  font-weight: 600;
}

.detail-item span {
  color: #8b949e;
  flex: 1;
}
</style>
