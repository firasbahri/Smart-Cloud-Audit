<template>
  <div class="dashboard-view">

    <!-- 1. Cabecera -->
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

    <!-- 2. Toggle Estático / IA -->
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

    <!-- 3. KPI de mejora -->
    <Card class="kpi-card mb-3">
      <template #content>

        <!-- Cargando -->
        <div v-if="loading" class="kpi-empty">
          <i class="pi pi-spin pi-spinner kpi-empty-icon" />
          <p class="kpi-empty-hint">Cargando datos…</p>
        </div>

        <!-- 0 auditorías del tipo -->
        <div v-else-if="filtered.length === 0" class="kpi-empty">
          <i class="pi pi-chart-bar kpi-empty-icon" />
          <p class="kpi-empty-title">Aún no tienes auditorías {{ selectedMode === 'static' ? 'estáticas' : 'de IA' }}</p>
          <p class="kpi-empty-hint">Ejecuta una auditoría {{ selectedMode === 'static' ? 'estática' : 'de IA' }} para ver los datos aquí.</p>
        </div>

        <!-- 1 auditoría: desglose sin % -->
        <div v-else-if="filtered.length < 2" class="kpi-grid">
          <div class="kpi-left">
            <span class="section-lbl">{{ modeLabel }} · última auditoría</span>
            <div class="kpi-num" style="color:#e6edf3">{{ totalLast }}</div>
            <span class="kpi-sub">hallazgos en total</span>
            <div class="kpi-warn">
              <i class="pi pi-info-circle" style="color:#768390" />
              Ejecuta al menos 2 auditorías {{ selectedMode === 'static' ? 'estáticas' : 'de IA' }} para ver la tendencia.
            </div>
          </div>
          <div class="kpi-right">
            <span class="section-lbl">Desglose por severidad</span>
            <div class="kpi-chips">
              <div
                v-for="chip in sevBreakdown" :key="chip.key"
                class="sev-chip"
                :style="{ background: '#1c2128', border: `1px solid ${chip.color}40` }"
              >
                <span class="chip-dot" :style="{ background: chip.color }" />
                <span class="chip-label">{{ chip.label }}</span>
                <span class="chip-range">{{ chip.val }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- ≥ 2 auditorías: KPI completo -->
        <div v-else class="kpi-grid">
          <div class="kpi-left">
            <span class="section-lbl">{{ modeLabel }} (últimas {{ filtered.length }})</span>
            <div class="kpi-num" :style="{ color: improve >= 0 ? '#3fb950' : '#f85149' }">
              {{ improve >= 0 ? '↓' : '↑' }} {{ Math.abs(improve) }}%
            </div>
            <span class="kpi-sub">{{ totalFirst }} → {{ totalLast }} hallazgos · {{ improve >= 0 ? 'menos' : 'más' }}</span>
          </div>
          <div class="kpi-right">
            <span class="section-lbl">Cambio por severidad · {{ firstLabel }} → {{ lastLabel }}</span>
            <div class="kpi-chips">
              <div
                v-for="chip in severityChips" :key="chip.key"
                class="sev-chip"
                :style="{ background: '#1c2128', border: `1px solid ${chip.color}40` }"
              >
                <span class="chip-dot" :style="{ background: chip.color }" />
                <span class="chip-label">{{ chip.label }}</span>
                <span class="chip-range">{{ chip.first }}→{{ chip.last }}</span>
                <span class="chip-pct" :style="{ color: chip.pct >= 0 ? '#3fb950' : '#f85149' }">
                  {{ chip.pct >= 0 ? '−' : '+' }}{{ Math.abs(chip.pct) }}%
                </span>
              </div>
            </div>
          </div>
        </div>

      </template>
    </Card>

    <!-- 4. Gráfico de tendencia -->
    <Card class="trend-card mb-3">
      <template #content>
        <div class="trend-head">
          <span class="section-lbl" style="margin-bottom:0">
            Tendencia · {{ selectedMode === 'static' ? 'auditorías estáticas' : 'auditorías de IA' }}
          </span>
          <div v-if="filtered.length >= 2" class="chart-legend">
            <span v-for="s in SEV_DEF" :key="s.key" class="legend-item">
              <span class="legend-dot" :style="{ background: s.color }" />{{ s.label }}
            </span>
          </div>
        </div>

        <div v-if="filtered.length < 2" class="empty-chart">
          <i class="pi pi-chart-bar" style="font-size:1.8rem;color:#2d333b" />
          <p style="color:#4d5566;margin:0;font-size:12px">
            {{
              filtered.length === 0
                ? 'Sin auditorías ' + (selectedMode === 'static' ? 'estáticas' : 'de IA')
                : 'Necesitas al menos 2 auditorías para ver la tendencia'
            }}
          </p>
        </div>
        <div v-else class="css-chart">
          <div v-for="audit in filtered" :key="audit.id" class="bar-col">
            <div class="bar-stack">
              <div v-if="audit.crit" class="seg seg-crit" :style="{ height: barH(audit.crit) }" :title="`Críticos: ${audit.crit}`" />
              <div v-if="audit.high" class="seg seg-high" :style="{ height: barH(audit.high) }" :title="`Altos: ${audit.high}`" />
              <div v-if="audit.med"  class="seg seg-med"  :style="{ height: barH(audit.med) }"  :title="`Medios: ${audit.med}`" />
              <div v-if="audit.low"  class="seg seg-low"  :style="{ height: barH(audit.low) }"  :title="`Bajos: ${audit.low}`" />
            </div>
            <span class="bar-lbl">{{ shortId(audit.id) }}</span>
          </div>
        </div>
      </template>
    </Card>

    <!-- 5. Tira de inventario -->
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

    <!-- 6. Fila de metadatos -->
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
import { computed, onMounted, ref, watch } from 'vue'
import Card from 'primevue/card'
import { useScanStore } from '../store/scanStore'
import { useCloudAccountsStore } from '../store/cloudAccountsStore'
import { useAuditStore } from '../store/auditStore'

const scanStore = useScanStore()
const cloudAccountsStore = useCloudAccountsStore()
const auditStore = useAuditStore()

// ── Cuenta seleccionada ──
const selectedAccount = computed(() => cloudAccountsStore.selectedAccount)
const accountId       = computed(() => selectedAccount.value?.id)
const scanResult      = computed(() => scanStore.scanResultByAccount[accountId.value] || {})

// ── Carga de datos ──
const loading = ref(false)


// ── Auditorías mapeadas desde el store ──
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

const modeLabel = computed(() =>
  selectedMode.value === 'static' ? 'Mejora · estáticas' : 'Mejora · IA'
)

const filtered = computed(() =>
  auditHistory.value.filter(a => a.origin === selectedMode.value).slice(-5)
)


const totalOf    = a => a.crit + a.high + a.med + a.low
const firstAudit = computed(() => filtered.value[0] ?? null)
const lastAudit  = computed(() => filtered.value[filtered.value.length - 1] ?? null)
const totalFirst = computed(() => firstAudit.value ? totalOf(firstAudit.value) : 0)
const totalLast  = computed(() => lastAudit.value  ? totalOf(lastAudit.value)  : 0)

const improve = computed(() => {
  if (!firstAudit.value || totalFirst.value === 0) return 0
  return Math.round((totalFirst.value - totalLast.value) / totalFirst.value * 100)
})

const shortId = (id = '') => 'AUD-' + String(id).replace(/-/g, '').slice(0, 6).toUpperCase()
const firstLabel = computed(() => firstAudit.value ? shortId(firstAudit.value.id) : '—')
const lastLabel  = computed(() => lastAudit.value  ? shortId(lastAudit.value.id)  : '—')

const SEV_DEF = [
  { key: 'crit', label: 'Críticos', color: '#f85149' },
  { key: 'high', label: 'Altos',    color: '#e3b341' },
  { key: 'med',  label: 'Medios',   color: '#388bfd' },
  { key: 'low',  label: 'Bajos',    color: '#768390' },
]

const severityChips = computed(() => {
  if (!firstAudit.value || !lastAudit.value) return []
  return SEV_DEF.map(s => {
    const f = firstAudit.value[s.key]
    const l = lastAudit.value[s.key]
    return { ...s, first: f, last: l, pct: f > 0 ? Math.round((f - l) / f * 100) : 0 }
  })
})

const sevBreakdown = computed(() => {
  const a = lastAudit.value
  if (!a) return []
  return SEV_DEF.map(s => ({ ...s, val: a[s.key] }))
})


const maxTotal = computed(() => Math.max(...filtered.value.map(totalOf), 1))
const barH = val => `${Math.round(val / maxTotal.value * 140)}px`

// ── Inventario (desde scanStore) ──
const inventoryItems = computed(() => [
  { label: 'Roles IAM',      n: scanResult.value?.roles?.length   ?? 0 },
  { label: 'Instancias EC2', n: scanResult.value?.ec2?.length     ?? 0 },
  { label: 'Almacenes S3',   n: scanResult.value?.buckets?.length ?? 0 },
  { label: 'Usuarios IAM',   n: scanResult.value?.users?.length   ?? 0 },
  { label: 'Grupos IAM',     n: scanResult.value?.groups?.length  ?? 0 },
])
const totalInventory = computed(() => inventoryItems.value.reduce((s, i) => s + i.n, 0))

// ── Meta ──
const formatDate = iso => {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' })
    + ' · ' + d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
}
const lastScanLabel      = computed(() => formatDate(scanStore.scanCreatedAtByAccount[accountId.value]))
const lastAuditMetaLabel = computed(() => formatDate(lastAudit.value?.created_at ?? auditStore.auditCreatedAt))
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

/* ── KPI empty ── */
.kpi-empty {
  display: flex; flex-direction: column; align-items: center;
  gap: 6px; padding: 20px 0; text-align: center;
}
.kpi-empty-icon  { font-size: 1.6rem; color: #2d333b; }
.kpi-empty-title { margin: 0; font-size: 13px; color: #768390; font-weight: 500; }
.kpi-empty-hint  { margin: 0; font-size: 11px; color: #4d5566; }

/* ── KPI grid ── */
.kpi-grid {
  display: grid; grid-template-columns: 260px 1fr; gap: 28px; align-items: start;
}
.kpi-left {
  display: flex; flex-direction: column; gap: 5px;
  padding-right: 28px; border-right: 1px solid #2d333b;
}
.kpi-num  { font-size: 42px; font-weight: 700; line-height: 1.05; }
.kpi-sub  { font-size: 11px; color: #768390; }
.kpi-warn {
  margin-top: 8px; display: flex; align-items: flex-start; gap: 6px;
  font-size: 10px; color: #4d5566; line-height: 1.4;
}

.kpi-right { display: flex; flex-direction: column; gap: 10px; }
.kpi-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.sev-chip  {
  display: inline-flex; align-items: center; gap: 7px;
  border-radius: 7px; padding: 6px 11px;
}
.chip-dot   { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.chip-label { font-size: 11px; color: #768390; }
.chip-range { font-family: 'Consolas','Monaco',monospace; font-size: 11px; color: #e6edf3; }
.chip-pct   { font-size: 11px; font-weight: 600; }

/* ── Chart ── */
.trend-head   { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.chart-legend { display: flex; gap: 12px; flex-wrap: wrap; }
.legend-item  { display: flex; align-items: center; gap: 5px; font-size: 11px; color: #768390; }
.legend-dot   { width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; }

.empty-chart {
  height: 120px; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 8px;
}
.css-chart { display: flex; gap: 8px; align-items: flex-end; height: 160px; padding-top: 8px; }
.bar-col   { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 5px; }
.bar-stack {
  width: 100%; max-width: 48px;
  display: flex; flex-direction: column; justify-content: flex-end;
  gap: 1px; height: 140px;
}
.seg      { width: 100%; flex-shrink: 0; border-radius: 2px; }
.seg-crit { background: #f85149; }
.seg-high { background: #e3b341; }
.seg-med  { background: #388bfd; }
.seg-low  { background: #768390; }
.bar-lbl  { font-family: 'Consolas','Monaco',monospace; font-size: 9px; color: #4d5566; text-align: center; }

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
  .kpi-grid     { grid-template-columns: 1fr; }
  .kpi-left     { border-right: none; padding-right: 0; border-bottom: 1px solid #2d333b; padding-bottom: 14px; }
  .dash-header  { flex-direction: column; }
  .dash-account { align-items: flex-start; }
  .mode-bar     { flex-wrap: wrap; }
}
</style>
