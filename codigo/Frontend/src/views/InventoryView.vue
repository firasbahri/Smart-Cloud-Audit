<template>
  <div class="inventory-view">
    <Toast />
    <div class="page-header">
      <div class="title-group">
        <div class="page-icon">
          <Package :size="18" />
        </div>
        <div>
          <h2>Inventario de Recursos AWS</h2>
          <p class="subtitle">Recursos detectados en la cuenta vinculada{{ scanAge }}</p>
        </div>
      </div>
      <div v-if="resourcesWithContext.length > 0" class="ai-coverage-badge">
        <Sparkles :size="13" />
        <span><strong class="ai-count">{{ aiCoverage.with }}/{{ aiCoverage.total }}</strong> recursos con contexto IA</span>
      </div>
    </div>

    <div class="tabs-bar">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['tab-btn', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        <span>{{ tab.label }}</span>
        <span class="count-pill">{{ tab.count }}</span>
        <span v-if="tab.ctxCount > 0" class="ai-pill">
          <Sparkles :size="9" />{{ tab.ctxCount }}
        </span>
      </button>
    </div>

    <div class="toolbar">
      <div class="search-box">
        <Search :size="13" class="search-icon" />
        <input v-model="search" placeholder="Buscar recursos..." />
      </div>
      <button :class="['missing-btn', { active: onlyMissing }]" @click="onlyMissing = !onlyMissing">
        <Sparkles :size="11" /> Solo sin contexto IA
      </button>
      <span class="result-count">{{ filtered.length }} resultados</span>
    </div>

    <div class="content-wrap" :class="{ 'has-drawer': !!selectedResource }">
      <div class="table-box" :class="{ 'drawer-open': !!selectedResource }">
        <div class="table-header table-grid">
          <div>Nombre</div>
          <div>Tipo</div>
          <div>Región</div>
          <div class="ai-col-header"><Sparkles :size="11" /> Contexto IA</div>
          <div></div>
        </div>

        <div v-if="resourcesWithContext.length === 0" class="empty-state">
          <FileX :size="28" />
          <span>Sin datos de escaneo para esta cuenta</span>
        </div>
        <div v-else-if="filtered.length === 0" class="empty-state">
          <Search :size="28" />
          <span>No se encontraron recursos con estos filtros</span>
        </div>

        <div
          v-for="(r, i) in filtered"
          :key="r.id"
          :class="['table-row', 'table-grid', { selected: selectedResource?.id === r.id, 'last-row': i === filtered.length - 1 }]"
          @click="openDrawer(r)"
        >
          <div class="col-name">
            <span class="resource-name">{{ r.name }}</span>
            <span v-if="r.state === 'STOPPED'" class="status-badge stopped">STOPPED</span>
            <span v-if="r.public === true" class="status-badge public-badge">PUBLIC</span>
          </div>
          <div><span :class="['tipo-badge', `tipo-${r.service}`]">{{ r.tipo }}</span></div>
          <div class="col-region">{{ r.region }}</div>
          <div class="col-context" @click.stop>
            <div v-if="r.aiContext" class="context-filled" @click="openDrawerEdit(r)">
              <Check :size="10" class="ctx-check" />
              <span>{{ r.aiContext }}</span>
            </div>
            <button v-else class="context-add-btn" @click="openDrawerEdit(r)">
              ✏️ Añadir
            </button>
          </div>
          <div class="col-actions">
            <MoreVertical :size="14" />
          </div>
        </div>
      </div>

      <div v-if="selectedResource" class="side-drawer">
        <div class="drawer-header">
          <div class="drawer-title">
            <span :class="['tipo-badge', `tipo-${selectedResource.service}`]" style="font-size:9px;padding:1px 6px">{{ selectedResource.tipo }}</span>
            <span class="drawer-name">{{ selectedResource.name }}</span>
          </div>
          <button class="close-btn" @click="closeDrawer"><X :size="15" /></button>
        </div>

        <div class="drawer-body">
          <div class="drawer-section">
            <div class="section-label">DETALLES</div>
            <div class="detail-list">
              <div class="detail-row"><span>Región</span><span>{{ selectedResource.region }}</span></div>
              <div v-if="selectedResource.state" class="detail-row">
                <span>Estado</span>
                <span :style="{ color: selectedResource.state === 'STOPPED' ? '#f85149' : '#3fb950' }">{{ selectedResource.state }}</span>
              </div>
              <div v-if="selectedResource.public !== undefined && selectedResource.service === 's3'" class="detail-row">
                <span>Público</span>
                <span :style="{ color: selectedResource.public ? '#f85149' : '#3fb950' }">{{ selectedResource.public ? 'Sí' : 'No' }}</span>
              </div>
            </div>
          </div>

          <div class="drawer-section">
            <div class="ai-context-box">
              <div class="ai-ctx-header">
                <div class="ai-ctx-title"><Sparkles :size="12" /> Contexto IA</div>
                <span v-if="selectedResource.aiContext && drawerMode !== 'edit'" class="ctx-status">✓ Descrito</span>
              </div>
              <p class="ai-ctx-hint">Describe este recurso (qué guarda, propósito, criticidad). La IA lo usará al auditar.</p>
              <textarea
                v-if="drawerMode === 'edit'"
                ref="contextTextareaRef"
                v-model="editingContext"
                class="ctx-textarea"
                rows="4"
                placeholder="Ej: este bucket almacena facturas de clientes. Es PII y debe cumplir con PSD2..."
              />
              <div v-else-if="selectedResource.aiContext" class="ctx-preview" @click="startEdit">{{ selectedResource.aiContext }}</div>
              <div class="ctx-actions">
                <template v-if="drawerMode === 'edit'">
                  <button class="btn-cancel" @click="cancelEdit">Cancelar</button>
                  <button class="btn-save" @click="saveContext">Guardar</button>
                </template>
                <template v-else>
                  <button class="btn-edit" @click="startEdit">Editar</button>
                </template>
              </div>
            </div>
          </div>

          <div class="drawer-section">
            <div class="section-label">ÚLTIMA AUDITORÍA</div>
            <div v-if="resourceFindings.length" class="findings-list">
              <div v-for="(f, fi) in resourceFindings" :key="fi" class="finding-item">
                <span :class="['sev-badge', `sev-${(f.severity || '').toLowerCase()}`]">{{ f.severity }}</span>
                <span class="finding-name">{{ f.check_id || f.title || f.check_name }}</span>
              </div>
            </div>
            <div v-else class="no-findings">Sin hallazgos</div>
          </div>
        </div>
      </div>
    </div>

    <div class="footer-tip">
      <Sparkles :size="11" />
      <span>Click sobre cualquier fila para ver detalles y editar contexto. Los contextos guardados se usan automáticamente al ejecutar <strong>Análisis IA</strong>.</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useScanStore } from '../store/scanStore'
import { useCloudAccountsStore } from '../store/cloudAccountsStore'
import { useAuditStore } from '../store/auditStore'
import { useToast } from 'primevue/usetoast'
import Toast from 'primevue/toast'
import { Package, Sparkles, Search, X, MoreVertical, Check, FileX } from 'lucide-vue-next'

const scanStore = useScanStore()
const cloudAccountsStore = useCloudAccountsStore()
const auditStore = useAuditStore()
const toast = useToast()

const accountId = computed(() => cloudAccountsStore.selectedAccount?.id)
const scanResult = computed(() => scanStore.scanResultByAccount[accountId.value] || {})

const scanAge = computed(() => {
  const createdAt = scanStore.scanCreatedAtByAccount[accountId.value]
  if (!createdAt) return ''
  const hours = Math.floor((new Date() - new Date(createdAt)) / (1000 * 60 * 60))
  if (hours < 1) return ' · último escaneo hace menos de 1h'
  if (hours === 1) return ' · último escaneo hace 1h'
  return ` · último escaneo hace ${hours}h`
})

const allResources = computed(() => {
  const r = scanResult.value
  const resources = []
  for (const role of r.roles || []) {
    resources.push({ id: `role:${role.name}`, name: role.name, tipo: 'IAM Role', service: 'iam', region: 'global' })
  }
  for (const user of r.users || []) {
    resources.push({ id: `user:${user.name}`, name: user.name, tipo: 'IAM User', service: 'iam', region: 'global' })
  }
  for (const group of r.groups || []) {
    resources.push({ id: `group:${group.name}`, name: group.name, tipo: 'IAM Group', service: 'iam', region: 'global' })
  }
  for (const ec2 of r.ec2 || []) {
    resources.push({
      id: `ec2:${ec2.id}`,
      name: ec2.id,
      tipo: 'EC2',
      service: 'ec2',
      region: ec2.region || 'us-east-1',
      state: ec2.state ? ec2.state.toUpperCase() : undefined
    })
  }
  for (const bucket of r.buckets || []) {
    resources.push({
      id: `bucket:${bucket.name}`,
      name: bucket.name,
      tipo: 'S3 Bucket',
      service: 's3',
      region: bucket.region || 'us-east-1',
      public: bucket.public ?? bucket.isPublic ?? false
    })
  }
  return resources
})

const activeTab = ref('all')
const search = ref('')
const onlyMissing = ref(false)
const selectedResource = ref(null)
const drawerMode = ref('view')
const editingContext = ref('')
const contextTextareaRef = ref(null)

const resourcesWithContext = computed(() =>
  allResources.value.map(r => ({
    ...r,
    aiContext: (scanStore.resourceContextsByAccount[accountId.value] || {})[r.id] || ''
  }))
)

const filtered = computed(() =>
  resourcesWithContext.value.filter(r => {
    if (activeTab.value !== 'all' && r.service !== activeTab.value) return false
    if (onlyMissing.value && r.aiContext) return false
    if (search.value && !r.name.toLowerCase().includes(search.value.toLowerCase())) return false
    return true
  })
)

const tabs = computed(() => {
  const rs = resourcesWithContext.value
  const cnt = (svc) => svc === 'all' ? rs.length : rs.filter(r => r.service === svc).length
  const ctx = (svc) => svc === 'all' ? rs.filter(r => r.aiContext).length : rs.filter(r => r.service === svc && r.aiContext).length
  return [
    { id: 'all', label: 'Todos', count: cnt('all'), ctxCount: ctx('all') },
    { id: 'iam', label: 'IAM', count: cnt('iam'), ctxCount: ctx('iam') },
    { id: 'ec2', label: 'EC2', count: cnt('ec2'), ctxCount: ctx('ec2') },
    { id: 's3', label: 'S3', count: cnt('s3'), ctxCount: ctx('s3') },
  ]
})

const aiCoverage = computed(() => ({
  with: resourcesWithContext.value.filter(r => r.aiContext).length,
  total: resourcesWithContext.value.length
}))

watch(accountId, (id) => {
  selectedResource.value = null
  search.value = ''
  onlyMissing.value = false
}, { immediate: true })

const openDrawer = (resource) => {
  const full = resourcesWithContext.value.find(r => r.id === resource.id) || resource
  selectedResource.value = { ...full }
  editingContext.value = full.aiContext || ''
  drawerMode.value = full.aiContext ? 'view' : 'edit'
  if (!full.aiContext) {
    nextTick(() => contextTextareaRef.value?.focus())
  }
}

const openDrawerEdit = (resource) => {
  const full = resourcesWithContext.value.find(r => r.id === resource.id) || resource
  selectedResource.value = { ...full }
  editingContext.value = full.aiContext || ''
  drawerMode.value = 'edit'
  nextTick(() => contextTextareaRef.value?.focus())
}

const closeDrawer = () => {
  selectedResource.value = null
  drawerMode.value = 'view'
}

const startEdit = () => {
  editingContext.value = selectedResource.value?.aiContext || ''
  drawerMode.value = 'edit'
  nextTick(() => contextTextareaRef.value?.focus())
}

const cancelEdit = () => {
  editingContext.value = selectedResource.value?.aiContext || ''
  drawerMode.value = selectedResource.value?.aiContext ? 'view' : 'view'
}

const saveContext = () => {
  if (!selectedResource.value) return
  const ctx = editingContext.value.trim()
  scanStore.setResourceContext(accountId.value, selectedResource.value.id, ctx)
  selectedResource.value = { ...selectedResource.value, aiContext: ctx }
  drawerMode.value = 'view'
  toast.add({ severity: 'success', summary: 'Contexto guardado', life: 2000 })
}

const resourceFindings = computed(() => {
  if (!selectedResource.value || !Array.isArray(auditStore.auditResult)) return []
  const name = selectedResource.value.name.toLowerCase()
  return auditStore.auditResult.filter(f => {
    const res = (f.resource || f.resource_id || f.resource_name || '').toLowerCase()
    return res.includes(name) || (name.length > 4 && res.includes(name.slice(0, 12)))
  }).slice(0, 5)
})

const onKeydown = (e) => { if (e.key === 'Escape') closeDrawer() }
onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.inventory-view {
  animation: fadeIn 0.4s ease-out;
  display: flex;
  flex-direction: column;
  gap: 0;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* ─── Header ─── */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
  animation: slideDown 0.5s ease-out;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-16px); }
  to { opacity: 1; transform: translateY(0); }
}

.title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(63, 185, 80, 0.12);
  border: 1px solid rgba(63, 185, 80, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3fb950;
  flex-shrink: 0;
}

.page-header h2 {
  font-size: 22px;
  font-weight: 700;
  color: #e6edf3;
  margin: 0 0 2px;
  letter-spacing: -0.4px;
}

.subtitle {
  font-size: 12px;
  color: #768390;
  margin: 0;
}

.ai-coverage-badge {
  display: flex;
  align-items: center;
  gap: 7px;
  background: rgba(167, 139, 250, 0.06);
  border: 1px solid rgba(167, 139, 250, 0.2);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 11px;
  color: #c4b5fd;
  flex-shrink: 0;
}

.ai-count {
  color: #a78bfa;
  font-weight: 700;
}

/* ─── Tabs ─── */
.tabs-bar {
  display: flex;
  border-bottom: 1px solid #2d333b;
  margin-bottom: 14px;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  background: transparent;
  border: none;
  color: #768390;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s;
}

.tab-btn:hover { color: #e6edf3; }

.tab-btn.active {
  color: #e6edf3;
  font-weight: 600;
  border-bottom-color: #3fb950;
}

.count-pill {
  font-size: 10px;
  background: #1c2128;
  color: #4d5566;
  border-radius: 10px;
  padding: 1px 7px;
  font-weight: 600;
}

.ai-pill {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 10px;
  background: rgba(167, 139, 250, 0.15);
  color: #a78bfa;
  border-radius: 10px;
  padding: 1px 6px;
  font-weight: 600;
}

/* ─── Toolbar ─── */
.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  max-width: 340px;
  background: #161b22;
  border: 1px solid #2d333b;
  border-radius: 7px;
  padding: 7px 12px;
}

.search-icon { color: #4d5566; flex-shrink: 0; }

.search-box input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #e6edf3;
  font-size: 12px;
  font-family: inherit;
}

.search-box input::placeholder { color: #4d5566; }

.missing-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  border-radius: 7px;
  font-size: 11px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
  background: #161b22;
  border: 1px solid #2d333b;
  color: #768390;
}

.missing-btn.active {
  background: rgba(167, 139, 250, 0.12);
  border-color: rgba(167, 139, 250, 0.4);
  color: #a78bfa;
}

.result-count {
  margin-left: auto;
  font-size: 11px;
  color: #4d5566;
}

/* ─── Content layout ─── */
.content-wrap {
  display: flex;
  align-items: flex-start;
  gap: 0;
  margin-bottom: 0;
}

.table-box {
  flex: 1;
  min-width: 0;
  background: #161b22;
  border: 1px solid #2d333b;
  border-radius: 10px;
  overflow: hidden;
}

.table-box.drawer-open {
  border-radius: 10px 0 0 10px;
  border-right: none;
}

/* ─── Table ─── */
.table-grid {
  display: grid;
  grid-template-columns: 1.6fr 110px 90px 1.4fr 40px;
  gap: 12px;
  padding: 10px 16px;
  align-items: center;
}

.table-header {
  background: #1c2128;
  border-bottom: 1px solid #2d333b;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #4d5566;
}

.ai-col-header {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #a78bfa;
}

.table-row {
  border-bottom: 1px solid #2d333b;
  cursor: pointer;
  transition: background 0.1s;
  font-size: 12px;
}

.table-row:hover { background: rgba(255, 255, 255, 0.02); }
.table-row.selected { background: rgba(167, 139, 250, 0.05); }
.table-row.last-row { border-bottom: none; }

.col-name {
  display: flex;
  align-items: center;
  gap: 7px;
  min-width: 0;
}

.resource-name {
  font-family: 'Consolas', 'Monaco', monospace;
  color: #e6edf3;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
}

.status-badge {
  font-size: 9px;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 600;
  flex-shrink: 0;
}

.stopped { background: rgba(248, 81, 73, 0.12); color: #f85149; }
.public-badge { background: rgba(248, 81, 73, 0.12); color: #f85149; }

.tipo-badge {
  display: inline-block;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
  white-space: nowrap;
}

.tipo-iam { background: rgba(63, 185, 80, 0.12); color: #3fb950; border: 1px solid rgba(63, 185, 80, 0.3); }
.tipo-ec2 { background: rgba(227, 179, 65, 0.12); color: #e3b341; border: 1px solid rgba(227, 179, 65, 0.3); }
.tipo-s3  { background: rgba(56, 139, 253, 0.12); color: #388bfd; border: 1px solid rgba(56, 139, 253, 0.3); }

.col-region {
  color: #768390;
  font-size: 11px;
}

.col-context { overflow: hidden; }

.context-filled {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 6px;
  background: rgba(167, 139, 250, 0.06);
  border: 1px solid rgba(167, 139, 250, 0.2);
  font-size: 10px;
  color: #c4b5fd;
  cursor: pointer;
  overflow: hidden;
}

.ctx-check { color: #a78bfa; flex-shrink: 0; }

.context-filled span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.context-add-btn {
  background: transparent;
  border: 1px dashed #2d333b;
  color: #4d5566;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 10px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-family: inherit;
  transition: border-color 0.15s, color 0.15s;
}

.context-add-btn:hover { border-color: #a78bfa; color: #a78bfa; }

.col-actions { color: #4d5566; cursor: pointer; display: flex; justify-content: center; }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 48px 24px;
  color: #4d5566;
  font-size: 13px;
}

/* ─── Side Drawer ─── */
.side-drawer {
  width: 320px;
  flex-shrink: 0;
  background: #161b22;
  border: 1px solid #2d333b;
  border-radius: 0 10px 10px 0;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 20px;
  max-height: calc(100vh - 120px);
  overflow: hidden;
  animation: slideInRight 0.2s ease-out;
}

@keyframes slideInRight {
  from { opacity: 0; transform: translateX(16px); }
  to { opacity: 1; transform: translateX(0); }
}

.drawer-header {
  padding: 12px 14px;
  border-bottom: 1px solid #2d333b;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-shrink: 0;
}

.drawer-title {
  display: flex;
  align-items: center;
  gap: 7px;
  min-width: 0;
}

.drawer-name {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 11px;
  color: #e6edf3;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.close-btn {
  background: transparent;
  border: none;
  color: #4d5566;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  border-radius: 5px;
  transition: background 0.12s, color 0.12s;
  flex-shrink: 0;
}

.close-btn:hover { background: rgba(255, 255, 255, 0.06); color: #e6edf3; }

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.drawer-body::-webkit-scrollbar { width: 4px; }
.drawer-body::-webkit-scrollbar-track { background: transparent; }
.drawer-body::-webkit-scrollbar-thumb { background: #2d333b; border-radius: 2px; }

.drawer-section { display: flex; flex-direction: column; gap: 8px; }

.section-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #4d5566;
}

.detail-list { display: flex; flex-direction: column; gap: 4px; }

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  line-height: 1.7;
}

.detail-row :first-child { color: #768390; }
.detail-row :last-child { color: #c9d1d9; }

/* ─── AI Context Box ─── */
.ai-context-box {
  background: rgba(167, 139, 250, 0.06);
  border: 1px solid rgba(167, 139, 250, 0.2);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ai-ctx-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ai-ctx-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #c4b5fd;
}

.ctx-status {
  font-size: 10px;
  color: #a78bfa;
}

.ai-ctx-hint {
  font-size: 10px;
  color: #4d5566;
  line-height: 1.5;
  margin: 0;
}

.ctx-textarea {
  width: 100%;
  background: #1c2128;
  border: 1px solid #2d333b;
  color: #e6edf3;
  border-radius: 7px;
  padding: 10px 12px;
  font-size: 11px;
  resize: none;
  line-height: 1.5;
  font-family: inherit;
  box-sizing: border-box;
  transition: border-color 0.15s;
}

.ctx-textarea:focus {
  outline: none;
  border-color: #a78bfa;
}

.ctx-textarea::placeholder { color: #4d5566; }

.ctx-preview {
  font-size: 11px;
  color: #c4b5fd;
  line-height: 1.5;
  cursor: pointer;
  padding: 4px 0;
}

.ctx-actions {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}

.btn-cancel {
  background: transparent;
  border: 1px solid #2d333b;
  color: #768390;
  font-size: 10px;
  padding: 5px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.12s, color 0.12s;
}

.btn-cancel:hover { border-color: #768390; color: #e6edf3; }

.btn-save {
  background: #7c3aed;
  border: none;
  color: #fff;
  font-size: 10px;
  padding: 5px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-family: inherit;
  font-weight: 600;
  transition: background 0.12s;
}

.btn-save:hover { background: #6d28d9; }

.btn-edit {
  background: transparent;
  border: 1px solid rgba(167, 139, 250, 0.3);
  color: #a78bfa;
  font-size: 10px;
  padding: 5px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.12s;
}

.btn-edit:hover { background: rgba(167, 139, 250, 0.08); }

/* ─── Findings ─── */
.findings-list { display: flex; flex-direction: column; gap: 6px; }

.finding-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
}

.sev-badge {
  font-size: 9px;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 600;
  flex-shrink: 0;
}

.sev-critical { background: rgba(248, 81, 73, 0.15); color: #f85149; }
.sev-high     { background: rgba(227, 179, 65, 0.15); color: #e3b341; }
.sev-medium   { background: rgba(56, 139, 253, 0.15); color: #388bfd; }
.sev-low      { background: rgba(63, 185, 80, 0.15);  color: #3fb950; }

.finding-name {
  color: #768390;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 10px;
}

.no-findings { font-size: 11px; color: #4d5566; }

/* ─── Footer ─── */
.footer-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 1px solid #2d333b;
  border-radius: 8px;
  background: #161b22;
  font-size: 11px;
  color: #768390;
  margin-top: 12px;
}

.footer-tip strong { color: #c4b5fd; }
</style>
