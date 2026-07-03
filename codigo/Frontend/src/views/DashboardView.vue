<template>
  <div class="dashboard-view">

    <div class="dash-header mb-4">
      <div>
        <h2 class="dash-title">Panel de Control</h2>
        <p class="dash-subtitle">Postura de seguridad de la cuenta auditada</p>
      </div>
      <div v-if="selectedAccount" class="dash-account">
        <span class="acc-name">{{ selectedAccount.name }}</span>
        <span class="acc-tag">AWS</span>
        <code class="acc-arn">{{ selectedAccount.identifier }}</code>
      </div>
    </div>

    <div class="mode-bar mb-4">
      <div class="audit-mode-toggle">
        <button
          :class="['toggle-btn', 'static-btn', { active: selectedMode === 'static' }]"
          @click="selectedMode = 'static'"
        >
          <i class="pi pi-shield" /> Estático
        </button>
        <button
          :class="['toggle-btn', 'ai-btn', { active: selectedMode === 'ai' }]"
          @click="selectedMode = 'ai'"
        >
          <i class="pi pi-sparkles" /> Análisis IA
        </button>
      </div>
      <span class="mode-count">
        {{ auditCounts[selectedMode] }}
        {{ auditCounts[selectedMode] === 1 ? 'auditoría' : 'auditorías' }}
        {{ selectedMode === 'static' ? 'estáticas' : 'de IA' }}
      </span>
    </div>

    <Card class="donut-card mb-3">
      <template #content>
        <span class="section-lbl">
          Hallazgos por severidad · última auditoría {{ selectedMode === 'static' ? 'estática' : 'de IA' }}
        </span>

        <div v-if="!current" class="chart-empty">
          <i class="pi pi-chart-pie chart-empty-icon" />
          <p class="chart-empty-title">Aún no tienes auditorías {{ selectedMode === 'static' ? 'estáticas' : 'de IA' }}</p>
          <p class="chart-empty-hint">Ejecuta una auditoría {{ selectedMode === 'static' ? 'estática' : 'de IA' }} para ver los datos aquí.</p>
        </div>

        <div v-else class="donut-grid">
          <div class="donut-wrap">
            <Chart type="doughnut" :data="donutData" :options="donutOptions" class="donut-canvas" />
            <div class="donut-center">
              <span class="donut-total">{{ currentTotal }}</span>
              <span class="donut-total-lbl">hallazgos</span>
            </div>
          </div>
          <div class="donut-legend">
            <div v-for="item in donutLegend" :key="item.key" class="legend-row">
              <span class="legend-dot" :style="{ background: item.color }" />
              <span class="legend-name">{{ item.label }}</span>
              <span class="legend-n" :style="{ color: item.color }">{{ item.n }}</span>
              <span class="legend-pct">{{ item.pct }}%</span>
              <div class="legend-bar-track">
                <div class="legend-bar-fill" :style="{ width: item.pct + '%', background: item.color }" />
              </div>
            </div>
          </div>
        </div>
      </template>
    </Card>

    <Card class="trend-card mb-3">
      <template #content>
        <span class="section-lbl">
          Evolución por severidad · {{ selectedMode === 'static' ? 'auditorías estáticas' : 'auditorías de IA' }}
        </span>

        <div v-if="filtered.length < 2" class="empty-chart">
          <i class="pi pi-chart-line" style="font-size:1.8rem;color:#2d333b" />
          <p style="color:#4d5566;margin:0;font-size:12px">
            {{
              filtered.length === 0
                ? 'Aún no tienes auditorías ' + (selectedMode === 'static' ? 'estáticas' : 'de IA')
                : 'Necesitas al menos 2 auditorías ' + (selectedMode === 'static' ? 'estáticas' : 'de IA') + ' para ver la evolución'
            }}
          </p>
        </div>
        <div v-else class="line-chart-wrap">
          <Chart type="line" :data="lineData" :options="lineOptions" class="line-canvas" />
        </div>
      </template>
    </Card>

    <Card v-if="inventoryItems.some(i => i.n > 0)" class="inv-card mb-3">
      <template #content>
        <span class="section-lbl">Inventario · {{ totalInventory }} recursos escaneados</span>
        <div class="inv-strip">
          <div
            v-for="(item, i) in inventoryItems" :key="item.label"
            class="inv-item" :class="{ 'inv-sep': i < inventoryItems.length - 1 }"
          >
            <span class="inv-n">{{ item.n }}</span>
            <span class="inv-label">{{ item.label }}</span>
          </div>
        </div>
      </template>
    </Card>

    <Card v-if="selectedAccount" class="meta-card">
      <template #content>
        <div class="meta-row">
          <div class="meta-item">
            <span class="meta-key">Estado</span>
            <span class="meta-val"><span class="dot-green">●</span> Conectada</span>
          </div>
          <div class="meta-item meta-sep">
            <span class="meta-key">Último escaneo</span>
            <span class="meta-val">{{ lastScanLabel }}</span>
          </div>
          <div class="meta-item meta-sep">
            <span class="meta-key">Última auditoría</span>
            <span class="meta-val">{{ lastAuditMetaLabel }}</span>
          </div>
        </div>
      </template>
    </Card>

  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import Card from 'primevue/card'
import Chart from 'primevue/chart'
import { useScanStore } from '../store/scanStore'
import { useCloudAccountsStore } from '../store/cloudAccountsStore'
import { useAuditStore } from '../store/auditStore'

const scanStore = useScanStore()
const cloudAccountsStore = useCloudAccountsStore()
const auditStore = useAuditStore()

const selectedAccount = computed(() => cloudAccountsStore.selectedAccount)
const accountId       = computed(() => selectedAccount.value?.id)
const scanResult      = computed(() => scanStore.scanResultByAccount[accountId.value] || {})

// ── Auditorías mapeadas desde el store (datos reales, sin fetch propio: MainPage ya las carga) ──
const auditHistory = computed(() =>
  (auditStore.audits || [])
    .map(a => ({
      id:     a.audit_id,
      origin: a.origin ?? 'static',
      crit:   a.counts?.critical ?? 0,
      high:   a.counts?.high     ?? 0,
      med:    a.counts?.medium   ?? 0,
      low:    a.counts?.low      ?? 0,
      created_at: a.created_at,
    }))
    .sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0))
)


const selectedMode = ref('static')

const auditCounts = computed(() => ({
  static: auditHistory.value.filter(a => a.origin === 'static').length,
  ai:     auditHistory.value.filter(a => a.origin === 'ai').length,
}))

const filtered = computed(() =>
  auditHistory.value.filter(a => a.origin === selectedMode.value).slice(-5)
)

const SEV_DEF = [
  { key: 'crit', label: 'Críticos', color: '#f85149' },
  { key: 'high', label: 'Altos',    color: '#e3b341' },
  { key: 'med',  label: 'Medios',   color: '#388bfd' },
  { key: 'low',  label: 'Bajos',    color: '#768390' },
]

const totalOf = a => a.crit + a.high + a.med + a.low
const current      = computed(() => filtered.value.at(-1) ?? null)
const currentTotal = computed(() => current.value ? totalOf(current.value) : 0)

const shortId = (id = '') => 'AUD-' + String(id).replace(/-/g, '').slice(0, 6).toUpperCase()

const donutLegend = computed(() => {
  if (!current.value) return []
  const total = currentTotal.value
  return SEV_DEF.map(s => {
    const n = current.value[s.key]
    return { ...s, n, pct: total > 0 ? Math.round(n / total * 100) : 0 }
  })
})

const donutData = computed(() => ({
  labels: SEV_DEF.map(s => s.label),
  datasets: [{
    data: SEV_DEF.map(s => current.value?.[s.key] ?? 0),
    backgroundColor: SEV_DEF.map(s => s.color),
    borderWidth: 0,
  }],
}))

const donutOptions = {
  cutout: '68%',
  plugins: { legend: { display: false }, tooltip: { enabled: true } },
  maintainAspectRatio: false,
}

const lineData = computed(() => ({
  labels: filtered.value.map(a => shortId(a.id)),
  datasets: SEV_DEF.map(s => ({
    label: s.label,
    borderColor: s.color,
    backgroundColor: s.color,
    data: filtered.value.map(a => a[s.key]),
    tension: 0.3,
  })),
}))

const lineOptions = {
  maintainAspectRatio: false,
  plugins: { legend: { position: 'top', labels: { color: '#768390', boxWidth: 14, usePointStyle: true } } },
  scales: {
    x: { ticks: { color: '#768390' }, grid: { color: '#2d333b' } },
    y: { beginAtZero: true, ticks: { color: '#768390', precision: 0 }, grid: { color: '#2d333b' } },
  },
}

const inventoryItems = computed(() => [
  { label: 'Roles IAM',      n: scanResult.value?.roles?.length   ?? 0 },
  { label: 'Instancias EC2', n: scanResult.value?.ec2?.length     ?? 0 },
  { label: 'Almacenes S3',   n: scanResult.value?.buckets?.length ?? 0 },
  { label: 'Usuarios IAM',   n: scanResult.value?.users?.length   ?? 0 },
  { label: 'Grupos IAM',     n: scanResult.value?.groups?.length  ?? 0 },
])
const totalInventory = computed(() => inventoryItems.value.reduce((s, i) => s + i.n, 0))

const formatDate = iso => {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' })
    + ' · ' + d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
}
const lastScanLabel      = computed(() => formatDate(scanStore.scanCreatedAtByAccount[accountId.value]))
const lastAuditMetaLabel = computed(() => formatDate(current.value?.created_at))
</script>

<style scoped>
.dashboard-view {
  animation: fadeIn 0.35s ease-out;
  display: flex;
  flex-direction: column;
  width: 100%;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── Cabecera ── */
.dash-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 16px; padding-bottom: 18px; border-bottom: 1px solid #2d333b;
}
.dash-title    { margin: 0 0 4px; font-size: 20px; font-weight: 700; color: #e6edf3; }
.dash-subtitle { margin: 0; font-size: 12px; color: #768390; }
.dash-account  { display: flex; flex-direction: column; align-items: flex-end; gap: 5px; }
.acc-name { font-size: 14px; font-weight: 600; color: #e6edf3; }
.acc-tag  {
  display: inline-flex; align-items: center;
  background: rgba(255,153,0,0.15); border: 1px solid rgba(255,153,0,0.3);
  color: #ff9900; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 999px;
}
.acc-arn { font-family: 'Consolas','Monaco',monospace; font-size: 10px; color: #4d5566; }

/* ── Toggle (patrón AuditView) ── */
.mode-bar { display: flex; align-items: center; gap: 14px; }
.audit-mode-toggle {
  display: flex; border: 1px solid #2d333b; border-radius: 8px;
  overflow: hidden; background: #161b22;
}
.toggle-btn {
  flex: 1; padding: 9px 16px; background: transparent; border: none;
  color: #768390; cursor: pointer; font-size: 12px; font-weight: 500;
  display: flex; align-items: center; gap: 6px;
  transition: all 0.15s; border-right: 1px solid #2d333b; white-space: nowrap;
  font-family: inherit;
}
.toggle-btn:last-child { border-right: none; }
.toggle-btn:hover { background: #1c2128; color: #e6edf3; }
.toggle-btn.static-btn.active { background: #1c2128; color: #3fb950; }
.toggle-btn.ai-btn.active     { background: #1c2128; color: #a78bfa; }
.mode-count { font-size: 11px; color: #4d5566; }

/* ── Cards ── */
:deep(.p-card)                 { background: #161b22; border: 1px solid #2d333b; border-radius: 12px; }
:deep(.p-card .p-card-content) { padding: 14px 16px; }

.section-lbl {
  display: block; font-size: 10px; font-weight: 700; color: #4d5566;
  text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;
}

/* ── Estado vacío (donut / líneas) ── */
.chart-empty {
  display: flex; flex-direction: column; align-items: center;
  gap: 6px; padding: 20px 0; text-align: center;
}
.chart-empty-icon  { font-size: 1.6rem; color: #2d333b; }
.chart-empty-title { margin: 0; font-size: 13px; color: #768390; font-weight: 500; }
.chart-empty-hint  { margin: 0; font-size: 11px; color: #4d5566; }

/* ── Donut ── */
.donut-grid { display: flex; align-items: center; gap: 28px; }
.donut-wrap {
  position: relative; width: 150px; height: 150px; flex-shrink: 0;
}
.donut-canvas { width: 100%; height: 100%; }
.donut-center {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; pointer-events: none;
}
.donut-total     { font-size: 28px; font-weight: 700; color: #e6edf3; line-height: 1; }
.donut-total-lbl { font-size: 10px; color: #768390; margin-top: 2px; }

.donut-legend { flex: 1; display: flex; flex-direction: column; gap: 10px; min-width: 0; }
.legend-row {
  display: grid; grid-template-columns: 10px 76px 38px 38px 1fr;
  align-items: center; gap: 10px;
}
.legend-dot  { width: 9px; height: 9px; border-radius: 50%; }
.legend-name { font-size: 12px; color: #768390; }
.legend-n    { font-family: 'Consolas','Monaco',monospace; font-size: 14px; font-weight: 700; text-align: right; }
.legend-pct  { font-size: 11px; color: #4d5566; }
.legend-bar-track {
  height: 5px; border-radius: 4px; background: #1c2128; overflow: hidden;
}
.legend-bar-fill { height: 100%; border-radius: 4px; }

/* ── Líneas ── */
.empty-chart {
  height: 120px; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 8px;
}
.line-chart-wrap { height: 200px; }
.line-canvas     { width: 100%; height: 100%; }

/* ── Inventario ── */
.inv-strip { display: flex; align-items: center; flex-wrap: wrap; }
.inv-item  { display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 4px 20px; }
.inv-sep   { border-right: 1px solid #2d333b; }
.inv-n     { font-family: 'Consolas','Monaco',monospace; font-size: 18px; font-weight: 700; color: #e6edf3; }
.inv-label { font-size: 10px; color: #768390; white-space: nowrap; }

/* ── Meta ── */
.meta-row  { display: flex; align-items: center; flex-wrap: wrap; }
.meta-item { display: flex; flex-direction: column; gap: 3px; padding: 4px 20px; }
.meta-sep  { border-left: 1px solid #2d333b; }
.meta-key  { font-size: 10px; color: #4d5566; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700; }
.meta-val  { font-size: 12px; color: #e6edf3; display: flex; align-items: center; gap: 5px; }
.dot-green { color: #3fb950; font-size: 10px; }

@media (max-width: 700px) {
  .donut-grid   { flex-direction: column; align-items: stretch; }
  .legend-row   { grid-template-columns: 10px 70px 34px 34px 1fr; }
  .dash-header  { flex-direction: column; }
  .dash-account { align-items: flex-start; }
  .mode-bar     { flex-wrap: wrap; }
}
</style>
