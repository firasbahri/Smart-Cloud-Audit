<template>
  <div class="my-audits-view">
    <div class="page-header">
      <div class="title-group">
        <div class="page-icon"><History :size="18" /></div>
        <div>
          <h2>My Audits</h2>
          <p class="subtitle">Audit history · {{ activeAccountLabel }}</p>
        </div>
      </div>

      <div v-if="audits.length" class="origin-filter">
        <button
          :class="['filter-btn', { active: originFilter === 'all' }]"
          @click="originFilter = 'all'"
        >
          All <span class="filter-count">{{ audits.length }}</span>
        </button>
        <button
          :class="['filter-btn', 'filter-btn--static', { active: originFilter === 'static' }]"
          @click="originFilter = 'static'"
        >
          Static <span class="filter-count">{{ originCounts.static }}</span>
        </button>
        <button
          :class="['filter-btn', 'filter-btn--ai', { active: originFilter === 'ai' }]"
          @click="originFilter = 'ai'"
        >
          ✦ IA <span class="filter-count">{{ originCounts.ai }}</span>
        </button>
      </div>
    </div>

    <div v-if="auditStore.auditsLoading" class="state-box">
      <i class="pi pi-spin pi-spinner" style="font-size:1.6rem;color:#768390" />
      <span>Loading audits...</span>
    </div>

    <div v-else-if="!audits.length" class="state-box">
      <FileX :size="34" style="color:#4d5566" />
      <span>No audits for this account</span>
      <p>Run one from <strong>Audit</strong></p>
    </div>

    <div v-else-if="!filteredAudits.length" class="state-box">
      <FileX :size="34" style="color:#4d5566" />
      <span>No {{ originFilter === 'ai' ? 'AI' : 'static' }} audits</span>
      <p>Try changing the filter or run one from <strong>Audit</strong></p>
    </div>

    <div v-else class="layout">
      <aside class="audits-list">
        <button
          v-for="audit in filteredAudits"
          :key="audit.audit_id"
          :class="['audit-item', { active: selectedAuditId === audit.audit_id }]"
          @click="selectedAuditId = audit.audit_id"
        >
          <div class="audit-item__top">
            <div class="audit-item__id">{{ shortId(audit.audit_id) }}</div>
            <div class="audit-item__actions">
              <span :class="['origin-badge', audit.origin === 'ai' ? 'origin-ai' : 'origin-static']">
                {{ audit.origin === 'ai' ? '✦ AI' : 'Static' }}
              </span>
              <div class="kebab-wrap" @click.stop>
                <button class="kebab-btn" @click.stop="toggleMenu(audit.audit_id)">⋮</button>
                <div v-if="openMenuId === audit.audit_id" class="audit-menu">
                  <button class="menu-item disabled" @click="openMenuId = null">
                    <i class="pi pi-file-pdf" /> Export PDF
                  </button>
                  <div class="menu-divider" />
                  <button class="menu-item danger" @click="requestDelete(audit.audit_id)">
                    <i class="pi pi-trash" /> Delete
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

      <article v-if="selectedAudit" class="audit-detail">
        <div class="detail-header">
          <div>
            <div class="detail-id">{{ shortId(selectedAudit.audit_id) }}</div>
            <div class="detail-full-id">{{ selectedAudit.audit_id }}</div>
            <div class="detail-date">{{ formatDate(selectedAudit.created_at) }}</div>
          </div>
          <div class="detail-header__right">
            <span :class="['origin-badge', 'origin-badge--lg', selectedAudit.origin === 'ai' ? 'origin-ai' : 'origin-static']">
              {{ selectedAudit.origin === 'ai' ? '✦ AI Analysis' : '⚙ Static' }}
            </span>
            <div class="kebab-wrap" @click.stop>
              <button class="kebab-btn" @click.stop="toggleMenu('detail')">⋮</button>
              <div v-if="openMenuId === 'detail'" class="audit-menu audit-menu--left">
                <button class="menu-item disabled" @click="openMenuId = null">
                  <i class="pi pi-file-pdf" /> Export PDF
                </button>
                <div class="menu-divider" />
                <button class="menu-item danger" @click="requestDelete(selectedAudit.audit_id)">
                  <i class="pi pi-trash" /> Delete
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
            <span class="summary-label">Critical</span>
            <strong>{{ selectedAudit.counts.critical }}</strong>
          </div>
          <div class="summary-card warn">
            <span class="summary-label">High</span>
            <strong>{{ selectedAudit.counts.high }}</strong>
          </div>
          <div class="summary-card info">
            <span class="summary-label">Medium</span>
            <strong>{{ selectedAudit.counts.medium }}</strong>
          </div>
          <div class="summary-card ok">
            <span class="summary-label">Low</span>
            <strong>{{ selectedAudit.counts.low }}</strong>
          </div>
        </div>

        <div class="findings-section">
          <div class="findings-header">
            <span class="section-label">FINDINGS</span>
            <span class="findings-count">{{ selectedAudit.vulnerabilities.length }}</span>
          </div>
          <div v-if="selectedAudit.vulnerabilities.length" class="finding-list">
            <div
              v-for="vuln in selectedAudit.vulnerabilities"
              :key="vuln.id"
              :class="['vi-item', { 'vi-item--ai': selectedAudit.origin === 'ai' }]"
            >
              <!-- Cabecera compacta -->
              <div class="vi-header">
                <div class="vi-sev" :style="sevBadgeStyle(vuln.severity)">{{ vuln.severity }}</div>
                <div class="vi-center">
                  <div class="fr-name-row">
                    <span class="vi-name" :class="{ 'vi-name--ai': selectedAudit.origin === 'ai' }">
                      <span v-if="selectedAudit.origin === 'ai'" aria-hidden="true">✦ </span>{{ vuln.name || vuln.id }}
                    </span>
                    <span :class="['vi-origin', selectedAudit.origin === 'ai' ? 'vi-origin--ai' : 'vi-origin--static']">
                      {{ selectedAudit.origin === 'ai' ? '✦ AI' : 'Static' }}
                    </span>
                  </div>
                  <div class="vi-resource">{{ vuln.resource_id }}</div>
                </div>
                <!-- pastilla verde: hay solución guardada -->
                <button
                  v-if="vuln.cli_command"
                  class="fix-pill"
                  @click="expandedVulns[vuln.id] = !expandedVulns[vuln.id]"
                >
                  ✓ Fix ready
                  <i
                    :class="['pi', expandedVulns[vuln.id] ? 'pi-chevron-up' : 'pi-chevron-down']"
                    style="font-size:0.6rem;color:#4d5566;transition:transform 0.15s"
                  />
                </button>
                <!-- loading mientras se genera -->
                <div v-else-if="loadingVulns[vuln.id]" class="gen-loading" role="status" aria-live="polite">
                  <span class="rem-spin" aria-hidden="true">✦</span> Generating command...
                </div>
                <!-- botón morado: no hay solución -->
                <button v-else class="gen-btn" @click="handleGenerate(vuln.id)">
                  <span aria-hidden="true">✦</span> Generate fix
                </button>
              </div>

              <!-- Detalle expandible: solo si hay solución y está abierta -->
              <div v-if="expandedVulns[vuln.id] && vuln.cli_command" class="row-detail">
                <div :class="['row-origin-pill', selectedAudit.origin === 'ai' ? 'row-origin-pill--ai' : 'row-origin-pill--static']">
                  {{ selectedAudit.origin === 'ai' ? '✦ AI-generated · saved' : '✓ Fix saved' }}
                </div>
                <ol v-if="parseRemediationSteps(vuln.recommendation).length" class="rem-steps">
                  <li v-for="(step, i) in parseRemediationSteps(vuln.recommendation)" :key="i" class="rem-step">
                    <span class="rem-step-num" aria-hidden="true">{{ i + 1 }}</span>
                    <span class="rem-step-text">{{ step }}</span>
                  </li>
                </ol>
                <div class="rem-code-box">
                  <div class="rem-code-header">
                    <span class="rem-cmd-label">AWS CLI · saved</span>
                    <button
                      :class="['rem-copy-btn', { 'rem-copy-btn--copied': copiedVuln[vuln.id] }]"
                      @click="copyVulnCommand(vuln.id, vuln.cli_command)"
                    >
                      {{ copiedVuln[vuln.id] ? '✓ Copied' : 'Copy' }}
                    </button>
                  </div>
                  <div class="rem-code-body">
                    <pre class="rem-code-pre">{{ vuln.cli_command }}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="no-findings">No findings recorded.</div>
        </div>
      </article>
    </div>

  
    <div v-if="confirmDialog.visible" class="confirm-overlay" @click.self="confirmDialog.visible = false">
      <div class="confirm-box">
        <div class="confirm-title">Delete audit {{ shortId(confirmDialog.auditId) }}?</div>
        <div class="confirm-body">All its findings will be deleted. This action cannot be undone.</div>
        <div class="confirm-actions">
          <button class="btn-cancel" @click="confirmDialog.visible = false">Cancel</button>
          <button class="btn-delete" @click="confirmDelete">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useCloudAccountsStore } from '../store/cloudAccountsStore'
import { useAuditStore } from '../store/auditStore'
import { FileX, History } from 'lucide-vue-next'

const cloudAccountsStore = useCloudAccountsStore()
const auditStore = useAuditStore()
const toast = useToast()

const audits = computed(() => auditStore.audits)
const selectedAuditId = ref(null)
const openMenuId = ref(null)
const confirmDialog = ref({ visible: false, auditId: null })
const originFilter = ref('all') // 'all' | 'static' | 'ai'

const copiedVuln    = reactive({})
const expandedVulns = reactive({})
const loadingVulns  = reactive({})

const activeAccountLabel = computed(() => cloudAccountsStore.selectedAccount?.name || 'No account selected')
const selectedAudit = computed(() => audits.value.find(a => a.audit_id === selectedAuditId.value) ?? null)

const originCounts = computed(() => ({
  static: audits.value.filter(a => a.origin === 'static').length,
  ai:     audits.value.filter(a => a.origin === 'ai').length,
}))

const filteredAudits = computed(() => {
  if (originFilter.value === 'all') return audits.value
  return audits.value.filter(a => a.origin === originFilter.value)
})

watch(originFilter, () => {
  if (!filteredAudits.value.some(a => a.audit_id === selectedAuditId.value)) {
    selectedAuditId.value = filteredAudits.value[0]?.audit_id ?? null
  }
})

const totalVulns = (audit) => Object.values(audit.counts).reduce((s, v) => s + v, 0)

const shortId = (id = '') => {
  if (!id) return '—'
  return '#' + id.replace(/-/g, '').slice(0, 8).toUpperCase()
}

const formatDate = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', { day: '2-digit', month: '2-digit', year: 'numeric' })
    + ' · ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

const SEV_COLORS = { CRITICAL: '#f85149', HIGH: '#e3b341', MEDIUM: '#388bfd', LOW: '#3fb950' }
const sevBadgeStyle = (severity) => {
  const color = SEV_COLORS[String(severity).toUpperCase()] ?? '#768390'
  return { background: color + '21', color }
}

const parseRemediationSteps = (text) => {
  if (!text) return []
  return text.split('\n').map(l => l.trim()).filter(l => l.length > 0)
    .map(l => l.replace(/^\d+[-.)]\s*/, '').trim()).filter(l => l.length > 0)
}

const copyVulnCommand = async (vulnId, command) => {
  try {
    await navigator.clipboard.writeText(command)
    copiedVuln[vulnId] = true
    setTimeout(() => { copiedVuln[vulnId] = false }, 1500)
  } catch { /* clipboard not available */ }
}

const handleGenerate = async (vulnId) => {
  const auditId = selectedAudit.value?.audit_id
  if (!auditId) return

  loadingVulns[vulnId] = true
  try {
    const data = await auditStore.generateSolution(auditId, vulnId)
    const audit = audits.value.find(a => a.audit_id === auditId)
    const vuln = audit?.vulnerabilities.find(v => v.id === vulnId)
    if (vuln) {
      vuln.cli_command = data?.cli_command || ''
      vuln.recommendation = data?.recommendation || ''
    }
    expandedVulns[vulnId] = true
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message, life: 3000 })
  } finally {
    loadingVulns[vulnId] = false
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
  try {
    await auditStore.deleteAuditById(auditId)
    if (selectedAuditId.value === auditId) {
      selectedAuditId.value = audits.value[0]?.audit_id ?? null
    }
    toast.add({ severity: 'success', summary: 'Deleted', life: 2000 })
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message, life: 3000 })
  }
}

watch(() => auditStore.audits, (list) => {
  if (!list.some(a => a.audit_id === selectedAuditId.value)) {
    selectedAuditId.value = list[0]?.audit_id ?? null
  }
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
.page-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.title-group  { display: flex; align-items: center; gap: 12px; }

/* ── Origin filter toggle ── */
.origin-filter {
  display: flex; border: 1px solid #2d333b; border-radius: 9px;
  overflow: hidden; background: #161b22;
}
.filter-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 14px; background: transparent; border: none;
  border-right: 1px solid #2d333b; color: #768390;
  font-size: 12px; font-weight: 500; font-family: inherit;
  cursor: pointer; transition: background 0.15s, color 0.15s; white-space: nowrap;
}
.filter-btn:last-child { border-right: none; }
.filter-btn:hover { background: #1c2128; color: #e6edf3; }
.filter-btn.active { background: #1c2128; color: #e6edf3; }
.filter-btn.filter-btn--static.active { color: #3fb950; }
.filter-btn.filter-btn--ai.active     { color: #a78bfa; }
.filter-count {
  font-size: 10px; font-weight: 700; padding: 1px 6px;
  border-radius: 999px; background: rgba(255,255,255,0.06); color: inherit;
}

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
.finding-list { display: flex; flex-direction: column; gap: 8px; }
.no-findings  { font-size: 12px; color: #4d5566; }

/* ── Finding row ── */
.vi-item     { background: #161b22; border: 1px solid #2d333b; border-radius: 10px; overflow: hidden; }
.vi-item--ai { border-color: rgba(167, 139, 250, 0.25); }

.vi-header { display: flex; align-items: center; gap: 12px; padding: 12px 14px; }

.vi-sev { flex-shrink: 0; width: 62px; text-align: center; font-size: 9px; font-weight: 700; padding: 3px 0; border-radius: 4px; letter-spacing: 0.04em; }

.vi-center { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; }

.fr-name-row { display: flex; align-items: center; gap: 6px; min-width: 0; }

.vi-name { font-family: 'Consolas','Monaco',monospace; font-size: 12.5px; font-weight: 600; color: #e6edf3; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0; }
.vi-name--ai { color: #a78bfa; }

.vi-origin { flex-shrink: 0; font-size: 9px; font-weight: 600; padding: 3px 8px; border-radius: 10px; white-space: nowrap; }
.vi-origin--ai     { background: rgba(167,139,250,0.15); color: #a78bfa; }
.vi-origin--static { background: rgba(63,185,80,0.12);  color: #3fb950; }

.vi-resource { font-family: 'Consolas','Monaco',monospace; font-size: 10.5px; color: #4d5566; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Pastilla verde — hay solución guardada */
.fix-pill {
  flex-shrink: 0;
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(63,185,80,0.1); border: 1px solid rgba(63,185,80,0.3);
  color: #3fb950; border-radius: 7px; padding: 5px 11px;
  font-size: 11px; font-weight: 600; font-family: inherit; cursor: pointer;
  transition: background 0.15s;
}
.fix-pill:hover { background: rgba(63,185,80,0.16); }

/* Botón morado — sin solución */
.gen-btn {
  flex-shrink: 0;
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(167,139,250,0.1); border: 1px solid rgba(167,139,250,0.35);
  color: #a78bfa; border-radius: 7px; padding: 5px 11px;
  font-size: 11px; font-weight: 600; font-family: inherit; cursor: pointer;
  transition: background 0.15s;
}
.gen-btn:hover { background: rgba(167,139,250,0.16); }

/* Detalle expandible */
.row-detail {
  padding: 12px 14px 14px;
  border-top: 1px solid #2d333b;
  background: #0d1117;
  display: flex; flex-direction: column; gap: 10px;
}

.row-origin-pill {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 10px; font-weight: 600; padding: 4px 10px;
  border-radius: 20px; align-self: flex-start;
}
.row-origin-pill--ai     { background: rgba(167,139,250,0.1); border: 1px solid rgba(167,139,250,0.3); color: #a78bfa; }
.row-origin-pill--static { background: rgba(63,185,80,0.1);  border: 1px solid rgba(63,185,80,0.3);  color: #3fb950; }

/* Loading state en el botón generar */
.gen-loading {
  flex-shrink: 0;
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(167,139,250,0.06); border: 1px solid rgba(167,139,250,0.2);
  color: #a78bfa; border-radius: 7px; padding: 5px 11px;
  font-size: 11px; font-weight: 500; opacity: 0.85;
}
.rem-spin { display: inline-block; animation: rem-rotate 1s linear infinite; }
@keyframes rem-rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .rem-spin { animation: none; opacity: 0.6; } }

/* Pasos de remediación */
.rem-steps { margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 6px; }
.rem-step  { display: flex; gap: 9px; align-items: flex-start; }
.rem-step-num  { flex-shrink: 0; color: #a78bfa; font-weight: 700; font-size: 12px; min-width: 14px; margin-top: 1px; }
.rem-step-text { font-size: 12px; color: #768390; line-height: 1.5; }

/* Caja de código */
.rem-code-box    { background: #0a0e14; border: 1px solid #2d333b; border-radius: 8px; overflow: hidden; }
.rem-code-header { background: #1c2128; border-bottom: 1px solid #2d333b; padding: 6px 12px; display: flex; align-items: center; justify-content: space-between; }
.rem-cmd-label   { font-family: 'Consolas','Monaco',monospace; font-size: 10px; color: #4d5566; }
.rem-copy-btn    { background: transparent; border: 1px solid #2d333b; color: #c9d1d9; font-size: 10px; font-family: inherit; padding: 3px 10px; border-radius: 5px; cursor: pointer; transition: background 0.12s, color 0.12s; }
.rem-copy-btn:hover        { background: rgba(255,255,255,0.05); }
.rem-copy-btn--copied      { color: #3fb950; border-color: rgba(63,185,80,0.3); }
.rem-code-body { padding: 10px 12px; overflow-x: auto; }
.rem-code-pre  { margin: 0; font-family: 'Consolas','Monaco',monospace; font-size: 11px; color: #c9d1d9; line-height: 1.6; white-space: pre; }

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
