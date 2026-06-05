<template>
  <div class="my-audits-view">
    <div class="page-header">
      <div class="title-group">
        <div class="page-icon"><History :size="18" /></div>
        <div>
          <h2>Mis Auditorías</h2>
          <p class="subtitle">Historial de auditorías · {{ activeAccountLabel }}</p>
        </div>
      </div>
    </div>

    <div v-if="loading" class="state-box">
      <i class="pi pi-spin pi-spinner" style="font-size:1.6rem;color:#768390" />
      <span>Cargando auditorías...</span>
    </div>

    <div v-else-if="!audits.length" class="state-box">
      <FileX :size="34" style="color:#4d5566" />
      <span>No hay auditorías para esta cuenta</span>
      <p>Ejecuta una desde <strong>Auditoría</strong></p>
    </div>

    <div v-else class="layout">
      <!-- ── Master list ── -->
      <aside class="audits-list">
        <button
          v-for="audit in audits"
          :key="audit.audit_id"
          :class="['audit-item', { active: selectedAuditId === audit.audit_id }]"
          @click="selectedAuditId = audit.audit_id"
        >
          <div class="audit-item__top">
            <div class="audit-item__id">{{ shortId(audit.audit_id) }}</div>
            <div class="audit-item__actions">
              <span :class="['origin-badge', audit.origin === 'ai' ? 'origin-ai' : 'origin-static']">
                {{ audit.origin === 'ai' ? '✦ IA' : 'Estático' }}
              </span>
              <div class="kebab-wrap" @click.stop>
                <button class="kebab-btn" @click.stop="toggleMenu(audit.audit_id)">⋮</button>
                <div v-if="openMenuId === audit.audit_id" class="audit-menu">
                  <button class="menu-item disabled" @click="openMenuId = null">
                    <i class="pi pi-file-pdf" /> Exportar PDF
                  </button>
                  <div class="menu-divider" />
                  <button class="menu-item danger" @click="requestDelete(audit.audit_id)">
                    <i class="pi pi-trash" /> Eliminar
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="audit-item__date">{{ formatDate(audit.created_at) }}</div>
          <div class="severity-strip">
            <span class="sev-chip critical">C {{ audit.counts.critical }}</span>
            <span class="sev-chip high">H {{ audit.counts.high }}</span>
            <span class="sev-chip medium">M {{ audit.counts.medium }}</span>
            <span class="sev-chip low">L {{ audit.counts.low }}</span>
          </div>
        </button>
      </aside>

      <!-- ── Detail panel ── -->
      <article v-if="selectedAudit" class="audit-detail">
        <div class="detail-header">
          <div>
            <div class="detail-id">{{ shortId(selectedAudit.audit_id) }}</div>
            <div class="detail-full-id">{{ selectedAudit.audit_id }}</div>
            <div class="detail-date">{{ formatDate(selectedAudit.created_at) }}</div>
          </div>
          <div class="detail-header__right">
            <span :class="['origin-badge', 'origin-badge--lg', selectedAudit.origin === 'ai' ? 'origin-ai' : 'origin-static']">
              {{ selectedAudit.origin === 'ai' ? '✦ Análisis IA' : '⚙ Estático' }}
            </span>
            <div class="kebab-wrap" @click.stop>
              <button class="kebab-btn" @click.stop="toggleMenu('detail')">⋮</button>
              <div v-if="openMenuId === 'detail'" class="audit-menu audit-menu--left">
                <button class="menu-item disabled" @click="openMenuId = null">
                  <i class="pi pi-file-pdf" /> Exportar PDF
                </button>
                <div class="menu-divider" />
                <button class="menu-item danger" @click="requestDelete(selectedAudit.audit_id)">
                  <i class="pi pi-trash" /> Eliminar
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="summary-grid">
          <div class="summary-card">
            <span class="summary-label">Total</span>
            <strong>{{ totalVulns(selectedAudit) }}</strong>
          </div>
          <div class="summary-card danger">
            <span class="summary-label">Críticos</span>
            <strong>{{ selectedAudit.counts.critical }}</strong>
          </div>
          <div class="summary-card warn">
            <span class="summary-label">Altos</span>
            <strong>{{ selectedAudit.counts.high }}</strong>
          </div>
          <div class="summary-card info">
            <span class="summary-label">Medios</span>
            <strong>{{ selectedAudit.counts.medium }}</strong>
          </div>
          <div class="summary-card ok">
            <span class="summary-label">Bajos</span>
            <strong>{{ selectedAudit.counts.low }}</strong>
          </div>
        </div>

        <div class="findings-section">
          <div class="findings-header">
            <span class="section-label">HALLAZGOS</span>
            <span class="findings-count">{{ selectedAudit.vulnerabilities.length }}</span>
          </div>
          <div v-if="selectedAudit.vulnerabilities.length" class="finding-list">
            <div
              v-for="vuln in selectedAudit.vulnerabilities"
              :key="vuln.id"
              class="finding-item"
            >
              <span :class="['finding-sev', (vuln.severity || '').toLowerCase()]">
                {{ vuln.severity }}
              </span>
              <div class="finding-body">
                <div class="finding-name">{{ vuln.name || vuln.id }}</div>
                <div class="finding-resource">{{ vuln.resource_id }}</div>
              </div>
            </div>
          </div>
          <div v-else class="no-findings">Sin hallazgos registrados.</div>
        </div>
      </article>
    </div>

  
    <div v-if="confirmDialog.visible" class="confirm-overlay" @click.self="confirmDialog.visible = false">
      <div class="confirm-box">
        <div class="confirm-title">¿Eliminar auditoría {{ shortId(confirmDialog.auditId) }}?</div>
        <div class="confirm-body">Se borrarán todos sus hallazgos. Esta acción no se puede deshacer.</div>
        <div class="confirm-actions">
          <button class="btn-cancel" @click="confirmDialog.visible = false">Cancelar</button>
          <button class="btn-delete" @click="confirmDelete">Eliminar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useCloudAccountsStore } from '../store/cloudAccountsStore'
import { buildApiUrl } from '../utils/api'
import { FileX, History } from 'lucide-vue-next'

const cloudAccountsStore = useCloudAccountsStore()
const toast = useToast()

const audits = ref([])
const selectedAuditId = ref(null)
const loading = ref(false)
const openMenuId = ref(null)
const confirmDialog = ref({ visible: false, auditId: null })

const accountId = computed(() => cloudAccountsStore.selectedAccount?.id)
const activeAccountLabel = computed(() => cloudAccountsStore.selectedAccount?.name || 'Sin cuenta seleccionada')
const selectedAudit = computed(() => audits.value.find(a => a.audit_id === selectedAuditId.value) ?? null)

const computeCounts = (vulnerabilities = []) => {
  const c = { critical: 0, high: 0, medium: 0, low: 0 }
  for (const v of vulnerabilities) {
    const s = (v.severity || '').toLowerCase()
    if (s === 'critical') c.critical++
    else if (s === 'high') c.high++
    else if (s === 'medium') c.medium++
    else if (s === 'low') c.low++
  }
  return c
}

const totalVulns = (audit) => Object.values(audit.counts).reduce((s, v) => s + v, 0)

const shortId = (id = '') => {
  if (!id) return '—'
  return '#' + id.replace(/-/g, '').slice(0, 8).toUpperCase()
}

const formatDate = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' })
    + ' · ' + d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
}

const loadAudits = async () => {
  if (!accountId.value) { audits.value = []; return }
  const token = localStorage.getItem('token')
  if (!token) return

  loading.value = true
  try {
    const res = await fetch(buildApiUrl(`/cloud/my-audits/${accountId.value}`), {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (res.status === 404) { audits.value = []; return }
    if (!res.ok) throw new Error('Error cargando auditorías')

    const data = await res.json()
    console.log('Raw audits data:', data) 
    audits.value = (Array.isArray(data) ? data : []).map(a => ({
      ...a,
      vulnerabilities: a.vulnerabilities || [],
      counts: a.counts || computeCounts(a.vulnerabilities),
      origin: a.origin || 'static'
    }))

    selectedAuditId.value = audits.value[0]?.audit_id ?? null
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message, life: 3000 })
    audits.value = []
  } finally {
    loading.value = false
  }
}

const toggleMenu = (id) => {
  openMenuId.value = openMenuId.value === id ? null : id
}

const requestDelete = (auditId) => {
  openMenuId.value = null
  confirmDialog.value = { visible: true, auditId }
}

const confirmDelete = async () => {
  const id = confirmDialog.value.auditId
  confirmDialog.value.visible = false
  await deleteAudit(id)
}

const handleOutsideClick = () => { openMenuId.value = null }
onMounted(() => document.addEventListener('click', handleOutsideClick))
onUnmounted(() => document.removeEventListener('click', handleOutsideClick))

const deleteAudit = async (auditId) => {
  const token = localStorage.getItem('token')
  if (!token) return
  try {
    const res = await fetch(buildApiUrl(`/cloud/delete-audit/${auditId}`), {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` }
    })
    if (!res.ok) throw new Error('Error al eliminar')
    audits.value = audits.value.filter(a => a.audit_id !== auditId)
    if (selectedAuditId.value === auditId) {
      selectedAuditId.value = audits.value[0]?.audit_id ?? null
    }
    toast.add({ severity: 'success', summary: 'Eliminada', life: 2000 })
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message, life: 3000 })
  }
}

watch(accountId, () => {
  audits.value = []
  selectedAuditId.value = null
  loadAudits()
}, { immediate: true })
</script>

<style scoped>
.my-audits-view {
  animation: fadeIn 0.35s ease-out;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── Header ── */
.page-header { display: flex; align-items: center; justify-content: space-between; }
.title-group  { display: flex; align-items: center; gap: 12px; }

.page-icon {
  width: 36px; height: 36px; border-radius: 10px;
  background: rgba(167, 139, 250, 0.1);
  border: 1px solid rgba(167, 139, 250, 0.25);
  display: flex; align-items: center; justify-content: center;
  color: #a78bfa; flex-shrink: 0;
}

.page-header h2 { font-size: 22px; font-weight: 700; color: #e6edf3; margin: 0 0 2px; letter-spacing: -0.4px; }
.subtitle       { font-size: 12px; color: #768390; margin: 0; }

/* ── State boxes ── */
.state-box {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; padding: 64px 24px; color: #4d5566; font-size: 13px;
  background: #161b22; border: 1px solid #2d333b; border-radius: 14px;
}
.state-box p  { margin: 0; font-size: 11px; color: #4d5566; }
.state-box strong { color: #c4b5fd; }

/* ── Layout ── */
.layout {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
}

/* ── Audit list ── */
.audits-list {
  background: #161b22;
  border: 1px solid #2d333b;
  border-radius: 14px;
  padding: 8px;
  max-height: calc(100vh - 160px);
  overflow-y: auto;
}

.audits-list::-webkit-scrollbar { width: 4px; }
.audits-list::-webkit-scrollbar-track { background: transparent; }
.audits-list::-webkit-scrollbar-thumb { background: #2d333b; border-radius: 2px; }

.audit-item {
  width: 100%; text-align: left;
  background: #0f141a; border: 1px solid #2d333b; border-radius: 10px;
  padding: 10px 12px; margin-bottom: 6px; cursor: pointer; color: inherit;
  transition: border-color 0.15s, background 0.15s, transform 0.12s;
}
.audit-item:last-child { margin-bottom: 0; }
.audit-item:hover { background: #111827; border-color: rgba(167,139,250,0.3); transform: translateY(-1px); }
.audit-item.active { background: rgba(167,139,250,0.07); border-color: rgba(167,139,250,0.45); }

.audit-item__top {
  display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 3px;
}
.audit-item__id   { font-family: 'Consolas','Monaco',monospace; font-size: 13px; font-weight: 700; color: #e6edf3; }
.audit-item__date { font-size: 11px; color: #768390; margin-bottom: 8px; }

/* ── Origin badge ── */
.origin-badge {
  display: inline-flex; align-items: center;
  font-size: 10px; font-weight: 700; padding: 2px 8px;
  border-radius: 999px; border: 1px solid; white-space: nowrap;
}
.origin-badge--lg { font-size: 12px; padding: 4px 12px; }
.origin-static { background: rgba(63,185,80,0.1);  border-color: rgba(63,185,80,0.3);  color: #3fb950; }
.origin-ai     { background: rgba(167,139,250,0.1); border-color: rgba(167,139,250,0.3); color: #a78bfa; }

/* ── Severity strip ── */
.severity-strip { display: flex; gap: 5px; flex-wrap: wrap; }
.sev-chip {
  font-size: 10px; font-weight: 700; padding: 2px 7px;
  border-radius: 999px; border: 1px solid transparent;
}
.sev-chip.critical { background: rgba(248,81,73,0.12);  color: #f85149; border-color: rgba(248,81,73,0.25); }
.sev-chip.high     { background: rgba(227,179,65,0.12); color: #e3b341; border-color: rgba(227,179,65,0.25); }
.sev-chip.medium   { background: rgba(56,139,253,0.12); color: #388bfd; border-color: rgba(56,139,253,0.25); }
.sev-chip.low      { background: rgba(63,185,80,0.12);  color: #3fb950; border-color: rgba(63,185,80,0.25); }

/* ── Detail panel ── */
.audit-detail {
  background: #161b22; border: 1px solid #2d333b; border-radius: 14px;
  padding: 18px 20px; display: flex; flex-direction: column; gap: 16px;
  max-height: calc(100vh - 160px); overflow-y: auto;
}

.audit-detail::-webkit-scrollbar { width: 4px; }
.audit-detail::-webkit-scrollbar-track { background: transparent; }
.audit-detail::-webkit-scrollbar-thumb { background: #2d333b; border-radius: 2px; }

.detail-header {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 12px;
}
.detail-id      { font-family: 'Consolas','Monaco',monospace; font-size: 20px; font-weight: 700; color: #e6edf3; }
.detail-full-id { font-family: 'Consolas','Monaco',monospace; font-size: 10px; color: #4d5566; margin: 2px 0 4px; }
.detail-date    { font-size: 12px; color: #768390; }

/* ── Summary grid ── */
.summary-grid {
  display: grid; grid-template-columns: repeat(5, minmax(0,1fr)); gap: 10px;
}
.summary-card {
  background: #0f141a; border: 1px solid #2d333b; border-radius: 10px;
  padding: 10px 12px; display: flex; flex-direction: column; gap: 4px;
}
.summary-card strong { font-size: 1.4rem; font-weight: 700; color: #e6edf3; }
.summary-label       { font-size: 10px; color: #768390; text-transform: uppercase; letter-spacing: 0.04em; }
.summary-card.danger { border-color: rgba(248,81,73,0.2); }
.summary-card.warn   { border-color: rgba(227,179,65,0.2); }
.summary-card.info   { border-color: rgba(56,139,253,0.2); }
.summary-card.ok     { border-color: rgba(63,185,80,0.2); }

/* ── Findings ── */
.findings-section {
  background: #0f141a; border: 1px solid #2d333b; border-radius: 12px; padding: 14px;
  display: flex; flex-direction: column; gap: 10px;
}
.findings-header {
  display: flex; align-items: center; justify-content: space-between;
}
.section-label  { font-size: 10px; font-weight: 600; letter-spacing: 0.06em; color: #4d5566; }
.findings-count {
  font-size: 11px; font-weight: 700; background: #1c2128;
  border: 1px solid #2d333b; border-radius: 999px; padding: 1px 8px; color: #768390;
}
.finding-list { display: flex; flex-direction: column; gap: 7px; }
.finding-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 9px 10px; border-radius: 9px;
  background: #161b22; border: 1px solid #2d333b;
}
.finding-sev {
  font-size: 10px; font-weight: 700; padding: 2px 7px;
  border-radius: 999px; min-width: 52px; text-align: center; flex-shrink: 0;
}
.finding-sev.critical { background: rgba(248,81,73,0.12);  color: #f85149; }
.finding-sev.high     { background: rgba(227,179,65,0.12); color: #e3b341; }
.finding-sev.medium   { background: rgba(56,139,253,0.12); color: #388bfd; }
.finding-sev.low      { background: rgba(63,185,80,0.12);  color: #3fb950; }
.finding-body    { min-width: 0; flex: 1; }
.finding-name    { font-size: 12px; font-weight: 600; color: #e6edf3; margin-bottom: 2px; }
.finding-resource { font-size: 11px; color: #768390; font-family: 'Consolas','Monaco',monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.no-findings     { font-size: 12px; color: #4d5566; }

/* ── Kebab menu ── */
.audit-item__actions { display: flex; align-items: center; gap: 6px; }
.detail-header__right { display: flex; align-items: center; gap: 8px; }

.kebab-wrap { position: relative; }

.kebab-btn {
  background: transparent; border: none; color: #4d5566;
  font-size: 16px; line-height: 1; cursor: pointer; padding: 2px 5px;
  border-radius: 5px; transition: background 0.12s, color 0.12s;
  font-family: inherit;
}
.kebab-btn:hover { background: rgba(255,255,255,0.06); color: #e6edf3; }

.audit-menu {
  position: absolute; top: calc(100% + 4px); right: 0; z-index: 100;
  background: #1c2128; border: 1px solid #2d333b; border-radius: 9px;
  padding: 4px; min-width: 160px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.35);
  animation: menuIn 0.1s ease-out;
}
.audit-menu--left { right: auto; left: 0; }

@keyframes menuIn {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: translateY(0); }
}

.menu-item {
  display: flex; align-items: center; gap: 8px; width: 100%;
  padding: 7px 10px; border: none; background: transparent;
  color: #c9d1d9; font-size: 12px; font-family: inherit;
  border-radius: 6px; cursor: pointer; text-align: left;
  transition: background 0.1s, color 0.1s;
}
.menu-item:hover         { background: rgba(255,255,255,0.05); color: #e6edf3; }
.menu-item.danger        { color: #f85149; }
.menu-item.danger:hover  { background: rgba(248,81,73,0.1); }
.menu-item.disabled      { color: #4d5566; cursor: default; }
.menu-item.disabled:hover { background: transparent; color: #4d5566; }

.menu-divider { height: 1px; background: #2d333b; margin: 3px 4px; }

/* ── Confirm dialog ── */
.confirm-overlay {
  position: fixed; inset: 0; z-index: 200;
  background: rgba(0,0,0,0.55);
  display: flex; align-items: center; justify-content: center;
}
.confirm-box {
  background: #161b22; border: 1px solid #2d333b; border-radius: 14px;
  padding: 24px; width: 360px; display: flex; flex-direction: column; gap: 12px;
  box-shadow: 0 20px 50px rgba(0,0,0,0.5);
  animation: menuIn 0.15s ease-out;
}
.confirm-title { font-size: 15px; font-weight: 700; color: #e6edf3; }
.confirm-body  { font-size: 13px; color: #8b949e; line-height: 1.5; }
.confirm-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 4px; }

.btn-cancel {
  background: transparent; border: 1px solid #2d333b; color: #768390;
  padding: 7px 16px; border-radius: 7px; font-size: 13px;
  font-family: inherit; cursor: pointer; transition: border-color 0.12s, color 0.12s;
}
.btn-cancel:hover { border-color: #4d5566; color: #e6edf3; }

.btn-delete {
  background: #f85149; border: none; color: #fff;
  padding: 7px 16px; border-radius: 7px; font-size: 13px;
  font-family: inherit; font-weight: 600; cursor: pointer;
  transition: background 0.12s;
}
.btn-delete:hover { background: #da3633; }

@media (max-width: 900px) {
  .layout         { grid-template-columns: 1fr; }
  .summary-grid   { grid-template-columns: repeat(3, minmax(0,1fr)); }
}
</style>
