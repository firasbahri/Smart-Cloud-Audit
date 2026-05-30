<template>
	<div class="audit-view">
		<div class="page-header flex align-items-center gap-3 mb-5">
			<i class="pi pi-shield page-icon p-3 border-round-xl shadow-3" />
			<div>
				<h2 class="m-0">Auditoria de Seguridad</h2>
				<p class="subtitle m-0 mt-2">Ejecuta auditorias estaticas o con IA sobre la cuenta escaneada</p>
			</div>
		</div>

		<Card class="account-card mb-4">
			<template #content>
				<div class="flex flex-column md:flex-row md:align-items-center md:justify-content-between gap-3">
					<div class="flex flex-column gap-2">
						<span class="account-label">Cuenta a auditar</span>
						<span class="account-value">{{ activeAccountLabel }}</span>
					</div>
					<div class="audit-controls">
						<div class="audit-mode-toggle">
							<button
								:class="['toggle-btn', 'static-btn', { active: auditMode === 'static' }]"
								@click="auditMode = 'static'"
							>
								<i class="pi pi-search" /> Estático
							</button>
							<button
								:class="['toggle-btn', 'ai-btn', { active: auditMode === 'ai' }]"
								@click="auditMode = 'ai'"
							>
								<i class="pi pi-sparkles" /> Análisis IA
							</button>
						</div>
						<Button
							:label="auditMode === 'ai' ? 'Ejecutar IA' : 'Ejecutar'"
							:icon="auditMode === 'ai' ? 'pi pi-sparkles' : 'pi pi-search'"
							:loading="isLoadingAny"
							:disabled="isLoadingAny || !canRunAudit"
							:style="auditMode === 'ai' ? { background: '#7c3aed', borderColor: '#7c3aed', color: '#fff' } : {}"
							@click="auditMode === 'ai' ? submitAiAudit() : runStaticAudit()"
						/>
					</div>
				</div>
			</template>
		</Card>

		<!-- AI context summary panel -->
		<div v-if="auditMode === 'ai'" class="ctx-panel mb-4">
			<div class="ctx-panel-header">
				<div class="ctx-panel-title">
					<i class="pi pi-sparkles" style="color:#a78bfa" />
					<span>Contexto IA activo</span>
					<span class="ctx-sections-badge">{{ filledSections }}/{{ totalSections }} secciones</span>
				</div>
				<button class="ctx-edit-link" @click="router.push('/app/inventory')">Editar contexto →</button>
			</div>
			<p v-if="cloudAccountsStore.selectedAccount?.description" class="ctx-business">
				<strong>Negocio:</strong> {{ cloudAccountsStore.selectedAccount.description }}
			</p>
			<p v-else class="ctx-business ctx-empty-hint">Sin descripción de negocio — añádela al editar la cuenta.</p>
			<div class="ctx-pills">
				<span
					v-for="g in contextGroups"
					:key="g.key"
					:class="['ctx-pill', `pill-${g.status}`]"
				>
					<span v-if="g.status === 'full'">✓ </span>{{ g.label }}
					<span v-if="g.status === 'full'"> · {{ g.filled }}</span>
					<span v-else-if="g.status === 'partial'"> · {{ g.filled }}/{{ g.total }}</span>
					<span v-else> · sin contexto</span>
				</span>
			</div>
		</div>

		<Message v-if="!hasResources" severity="warn" :closable="false" class="mb-4">
			No hay recursos para auditar en la cuenta seleccionada.
		</Message>

		<Card v-if="hasResources" class="vuln-card">
			<template #content>
				<div class="results-bar">
					<div :class="['seg-ctrl', `mode-${activeTab}`]">
						<button :class="['seg-btn', { active: activeTab === 'static' }]" @click="activeTab = 'static'">
							Estático
							<span v-if="staticVulnerabilities.length" class="seg-badge">{{ staticVulnerabilities.length }}</span>
						</button>
						<button
							v-if="aiVulnerabilities.length > 0"
							:class="['seg-btn', { active: activeTab === 'ai' }]"
							@click="activeTab = 'ai'"
						>
							<i class="pi pi-sparkles" style="font-size: 0.68rem" /> IA
							<span class="seg-badge">{{ aiVulnerabilities.length }}</span>
						</button>
					</div>
					<div class="filter-right">
						<small class="text-muted">{{ currentTotal }} hallazgos</small>
						<select v-model="selectedSeverity" class="sev-select">
							<option v-for="opt in severityOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
						</select>
					</div>
				</div>

				<div v-if="pagedVulns.length" class="vuln-list flex flex-column gap-3">
					<div
						v-for="vuln in pagedVulns"
						:key="vuln.id"
						:class="['vuln-item', { 'ai-vuln-item': activeTab === 'ai' }]"
					>
						<div class="vuln-top flex align-items-center justify-content-between gap-2">
							<strong :class="{ 'ai-vuln-id': activeTab === 'ai' }">{{ vuln.id }}</strong>
							<div class="flex gap-2">
								<Tag :value="vuln.severity" :severity="mapSeverity(vuln.severity)" rounded />
								<Tag v-if="activeTab === 'static'" :value="vuln.origin" severity="secondary" rounded />
							</div>
						</div>
						<p class="vuln-description">{{ vuln.description }}</p>
						<div :class="['vuln-meta', { 'ai-vuln-meta': activeTab === 'ai' }]">
							<span><strong>Resource ID:</strong> {{ vuln.resource_id }}</span>
						</div>
					</div>
				</div>
				<Message v-else-if="activeFiltered.length === 0 && currentTotal > 0" severity="info" :closable="false" class="mt-3">No hay vulnerabilidades para la severidad seleccionada.</Message>

				<div v-if="totalPages > 1" class="paginator">
					<button class="pag-btn" :disabled="currentPage === 1" @click="currentPage--">
						<i class="pi pi-chevron-left" style="font-size:0.75rem" />
					</button>
					<template v-for="p in pageNumbers" :key="p">
						<span v-if="p === '...'" class="pag-ellipsis">…</span>
						<button v-else :class="['pag-btn', 'pag-num', { active: currentPage === p }]" @click="currentPage = p">{{ p }}</button>
					</template>
					<button class="pag-btn" :disabled="currentPage === totalPages" @click="currentPage++">
						<i class="pi pi-chevron-right" style="font-size:0.75rem" />
					</button>
					<span class="pag-info">{{ pageInfo }}</span>
				</div>
			</template>
		</Card>

	</div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useRouter } from 'vue-router'
import { useScanStore } from '../store/scanStore'
import { useAuditStore } from '../store/auditStore'
import { useCloudAccountsStore } from '../store/cloudAccountsStore'
import { buildApiUrl } from '../utils/api'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Message from 'primevue/message'
import Tag from 'primevue/tag'

const scanStore = useScanStore()
const cloudAccountsStore = useCloudAccountsStore()
const auditStore = useAuditStore()
const toast = useToast()
const router = useRouter()

const staticVulnerabilities = computed(() =>
	Array.isArray(auditStore.auditResult)
		? auditStore.auditResult.map((item, i) => normalizeVulnerability(item, i, 'static'))
		: []
)
const aiVulnerabilities = ref([])
const activeTab = ref('static')
const selectedSeverity = ref('ALL')
const isLoadingStatic = ref(false)
const isLoadingAi = ref(false)
const auditMode = ref('static')

const severityOptions = [
	{ label: 'Todas', value: 'ALL' },
	{ label: 'Critical', value: 'CRITICAL' },
	{ label: 'High', value: 'HIGH' },
	{ label: 'Medium', value: 'MEDIUM' },
	{ label: 'Low', value: 'LOW' },
]

const accountId = computed(() => cloudAccountsStore.selectedAccount?.id)
const resources = computed(() => scanStore.scanResultByAccount[accountId.value] || {})

const totalResources = computed(() =>
	['users', 'groups', 'roles', 'buckets', 'ec2']
		.reduce((sum, key) => sum + (Array.isArray(resources.value[key]) ? resources.value[key].length : 0), 0)
)

const hasResources = computed(() => totalResources.value > 0)

const activeAccountLabel = computed(() =>
	cloudAccountsStore.selectedAccount?.name || 'Sin cuenta seleccionada'
)

const resolvedScanId = computed(() => {
	if (!accountId.value) return null
	return scanStore.scanResultIdByAccount[accountId.value] || null
})

const canRunAudit = computed(() => Boolean(resolvedScanId.value) && hasResources.value)
const isLoadingAny = computed(() => isLoadingStatic.value || isLoadingAi.value)
const currentTotal = computed(() => activeTab.value === 'ai' ? aiVulnerabilities.value.length : staticVulnerabilities.value.length)

const contextGroups = computed(() => {
	const contexts = scanStore.resourceContextsByAccount[accountId.value] || {}
	const res = resources.value
	return [
		{ key: 'user',   label: 'IAM Users', items: (res.users   || []).map(r => `user:${r.name}`) },
		{ key: 'group',  label: 'IAM Groups', items: (res.groups  || []).map(r => `group:${r.name}`) },
		{ key: 'role',   label: 'IAM Roles',  items: (res.roles   || []).map(r => `role:${r.name}`) },
		{ key: 'ec2',    label: 'EC2',        items: (res.ec2     || []).map(r => `ec2:${r.id}`) },
		{ key: 'bucket', label: 'S3',         items: (res.buckets || []).map(r => `bucket:${r.name}`) },
	]
		.filter(g => g.items.length > 0)
		.map(g => {
			const total = g.items.length
			const filled = g.items.filter(id => contexts[id]).length
			const status = filled === 0 ? 'empty' : filled === total ? 'full' : 'partial'
			return { key: g.key, label: g.label, total, filled, status }
		})
})

const filledSections = computed(() => {
	const hasCompany = !!cloudAccountsStore.selectedAccount?.description?.trim()
	return (hasCompany ? 1 : 0) + contextGroups.value.filter(g => g.filled > 0).length
})

const totalSections = computed(() => 1 + contextGroups.value.length)

const filteredStatic = computed(() => {
	if (selectedSeverity.value === 'ALL') return staticVulnerabilities.value
	return staticVulnerabilities.value.filter(v => String(v.severity || '').toUpperCase() === selectedSeverity.value)
})

const filteredAi = computed(() => {
	if (selectedSeverity.value === 'ALL') return aiVulnerabilities.value
	return aiVulnerabilities.value.filter(v => String(v.severity || '').toUpperCase() === selectedSeverity.value)
})

const PAGE_SIZE = 10
const currentPage = ref(1)

const activeFiltered = computed(() => activeTab.value === 'ai' ? filteredAi.value : filteredStatic.value)
const totalPages = computed(() => Math.max(1, Math.ceil(activeFiltered.value.length / PAGE_SIZE)))

const pagedVulns = computed(() => {
	const start = (currentPage.value - 1) * PAGE_SIZE
	return activeFiltered.value.slice(start, start + PAGE_SIZE)
})

const pageNumbers = computed(() => {
	const total = totalPages.value
	const cur = currentPage.value
	if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
	const pages = [1]
	if (cur > 3) pages.push('...')
	for (let i = Math.max(2, cur - 1); i <= Math.min(total - 1, cur + 1); i++) pages.push(i)
	if (cur < total - 2) pages.push('...')
	pages.push(total)
	return pages
})

const pageInfo = computed(() => {
	const total = activeFiltered.value.length
	if (!total) return ''
	const start = (currentPage.value - 1) * PAGE_SIZE + 1
	const end = Math.min(currentPage.value * PAGE_SIZE, total)
	return `${start}–${end} de ${total}`
})

const mapSeverity = (severity) => {
	const s = String(severity || '').toUpperCase()
	if (s === 'CRITICAL' || s === 'HIGH') return 'danger'
	if (s === 'MEDIUM') return 'warn'
	if (s === 'LOW') return 'success'
	return 'info'
}

const normalizeVulnerability = (item, index, mode) => ({
	id: item?.id || item?._id || `VULN-${index + 1}`,
	description: item?.description || item?.detail || 'Sin descripcion',
	severity: String(item?.severity || 'LOW').toUpperCase(),
	resource_id: item?.resource_id || item?.resourceId || 'N/A',
	origin: item?.origin || (mode === 'ai' ? 'AI Analysis' : 'Static Analysis')
})

watch(accountId, () => {
	aiVulnerabilities.value = []
	activeTab.value = 'static'
	currentPage.value = 1
})

watch([activeTab, selectedSeverity], () => { currentPage.value = 1 })

const runStaticAudit = async () => {
	const token = localStorage.getItem('token')
	if (!token) { toast.add({ severity: 'error', summary: 'Sesion', detail: 'Token no encontrado', life: 3000 }); return }
	const scanId = resolvedScanId.value
	if (!scanId) { toast.add({ severity: 'warn', summary: 'Auditoria', detail: 'No hay scan_id disponible', life: 3000 }); return }

	isLoadingStatic.value = true
	try {
		const response = await fetch(buildApiUrl('/cloud/static-audit'), {
			method: 'POST',
			headers: { 'content-type': 'application/json', Authorization: `Bearer ${token}` },
			body: JSON.stringify({ scan_id: scanId })
		})
		const data = await response.json()
		if (!response.ok) throw new Error(data?.detail || 'No se pudo ejecutar la auditoria')

		const normalized = (Array.isArray(data?.vulnerabilities) ? data.vulnerabilities : [])
			.map((item, i) => normalizeVulnerability(item, i, 'static'))

		auditStore.setAudits(data?.audit_id || '', normalized)
		activeTab.value = 'static'
		toast.add({ severity: 'success', summary: 'Auditoria completada', detail: `${normalized.length} vulnerabilidades encontradas`, life: 3000 })
	} catch (error) {
		toast.add({ severity: 'error', summary: 'Error en auditoria', detail: error.message, life: 3500 })
	} finally {
		isLoadingStatic.value = false
	}
}

const submitAiAudit = async () => {
	const token = localStorage.getItem('token')
	if (!token) { toast.add({ severity: 'error', summary: 'Sesion', detail: 'Token no encontrado', life: 3000 }); return }
	const scanId = resolvedScanId.value
	const auditId = auditStore.id
	if (!scanId || !auditId) {
		toast.add({ severity: 'warn', summary: 'Auditoria IA', detail: 'Ejecuta primero el análisis estático', life: 3000 })
		return
	}

	const userContext = {
		company: cloudAccountsStore.selectedAccount?.description?.trim() || '',
		resources: scanStore.resourceContextsByAccount[accountId.value] || {}
	}

	isLoadingAi.value = true

	try {
		const response = await fetch(buildApiUrl('/cloud/ai-audit'), {
			method: 'POST',
			headers: { 'content-type': 'application/json', Authorization: `Bearer ${token}` },
			body: JSON.stringify({ scan_id: scanId, audit_id: auditId, user_context: userContext })
		})
		const data = await response.json()
		if (!response.ok) throw new Error(data?.detail || 'No se pudo ejecutar el análisis IA')

		const normalized = (Array.isArray(data?.vulnerabilities) ? data.vulnerabilities : [])
			.map((item, i) => normalizeVulnerability(item, i, 'ai'))

		aiVulnerabilities.value = normalized
		activeTab.value = 'ai'
		toast.add({ severity: 'success', summary: 'Análisis IA completado', detail: `${normalized.length} vulnerabilidades encontradas`, life: 3000 })
	} catch (error) {
		toast.add({ severity: 'error', summary: 'Error en análisis IA', detail: error.message, life: 3500 })
	} finally {
		isLoadingAi.value = false
	}
}
</script>

<style scoped>
.audit-view { animation: fadeIn 0.35s ease-out; }

@keyframes fadeIn {
	from { opacity: 0; transform: translateY(6px); }
	to { opacity: 1; transform: translateY(0); }
}

.page-icon { background: rgba(34, 197, 94, 0.12); border: 1px solid rgba(34, 197, 94, 0.3); color: #22c55e; }
.page-header h2 { color: #e6edf3; font-size: 2rem; font-weight: 700; }
.subtitle { color: #8b949e; }

.account-card, .vuln-card { background: #161b22; border: 1px solid rgba(34, 197, 94, 0.12); border-radius: 14px; }

:deep(.p-card .p-card-content) { padding: 0.85rem; }

.account-label { color: #8b949e; font-size: 0.875rem; }
.account-value { color: #e6edf3; font-weight: 600; font-size: 1.1rem; }

/* ── Results bar ── */
.results-bar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0.5rem 0 0.75rem;
	gap: 1rem;
}

.seg-ctrl {
	display: inline-flex;
	border: 1px solid #2d333b;
	border-radius: 8px;
	overflow: hidden;
	background: #0d1117;
}

.seg-btn {
	display: inline-flex;
	align-items: center;
	gap: 6px;
	padding: 6px 14px;
	background: transparent;
	border: none;
	border-right: 1px solid #2d333b;
	color: #768390;
	font-size: 12px;
	font-weight: 500;
	cursor: pointer;
	white-space: nowrap;
	transition: color 0.15s, background 0.15s;
	font-family: inherit;
}
.seg-btn:last-child { border-right: none; }
.seg-btn:hover:not(.active) { background: rgba(255,255,255,0.03); color: #e6edf3; }

/* green when static mode is active */
.seg-ctrl.mode-static .seg-btn.active {
	background: rgba(34, 197, 94, 0.1);
	color: #22c55e;
}
/* purple when ai mode is active */
.seg-ctrl.mode-ai .seg-btn.active {
	background: rgba(167, 139, 250, 0.12);
	color: #a78bfa;
}

.seg-badge {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	background: rgba(255,255,255,0.07);
	color: inherit;
	border-radius: 999px;
	font-size: 0.65rem;
	font-weight: 700;
	padding: 0.05rem 0.4rem;
	min-width: 18px;
}

/* ── Filter right ── */
.filter-right {
	display: flex;
	align-items: center;
	gap: 10px;
}

.sev-select {
	background: #1c2128;
	border: 1px solid #2d333b;
	color: #e6edf3;
	border-radius: 7px;
	padding: 5px 10px;
	font-size: 12px;
	font-family: inherit;
	cursor: pointer;
	outline: none;
	appearance: auto;
}
.sev-select option {
	background: #1c2128;
	color: #e6edf3;
}
.sev-select:hover { border-color: #4d5566; }

.audit-controls { display: flex; align-items: center; gap: 0.5rem; }

.audit-mode-toggle {
	display: flex;
	border: 1px solid #2d333b;
	border-radius: 8px;
	overflow: hidden;
	background: #161b22;
}

.toggle-btn {
	flex: 1;
	padding: 9px 14px;
	background: transparent;
	border: none;
	color: #768390;
	cursor: pointer;
	font-size: 12px;
	font-weight: 500;
	display: flex;
	align-items: center;
	gap: 6px;
	transition: all 0.15s;
	border-right: 1px solid #2d333b;
	white-space: nowrap;
}

.toggle-btn:last-child { border-right: none; }
.toggle-btn:hover { background: #1c2128; color: #e6edf3; }
.toggle-btn.static-btn.active { background: #1c2128; color: #22c55e; }
.toggle-btn.ai-btn.active { background: #1c2128; color: #a78bfa; }

.text-muted { color: #94a3b8; }
.vuln-list { margin-top: 0.5rem; }
.vuln-item { border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 10px; padding: 0.7rem; background: rgba(2, 6, 23, 0.45); }
.vuln-description { margin: 0.65rem 0; color: #cbd5e1; }
.vuln-meta { color: #94a3b8; font-size: 0.9rem; }

.ai-vuln-item { border-color: rgba(167, 139, 250, 0.25); background: rgba(88, 28, 135, 0.08); }
.ai-vuln-id { color: #c4b5fd; }
.ai-vuln-meta { color: #a78bfa; }

/* ── Context summary panel ── */
.ctx-panel {
	background: #161b22;
	border: 1px solid rgba(167, 139, 250, 0.2);
	border-radius: 14px;
	padding: 0.9rem 1rem;
	display: flex;
	flex-direction: column;
	gap: 0.55rem;
}

.ctx-panel-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.ctx-panel-title {
	display: flex;
	align-items: center;
	gap: 7px;
	font-size: 0.875rem;
	font-weight: 600;
	color: #c4b5fd;
}

.ctx-sections-badge {
	background: rgba(167, 139, 250, 0.15);
	color: #a78bfa;
	border-radius: 999px;
	font-size: 0.7rem;
	font-weight: 700;
	padding: 0.1rem 0.5rem;
}

.ctx-edit-link {
	background: transparent;
	border: none;
	color: #768390;
	font-size: 0.8rem;
	cursor: pointer;
	font-family: inherit;
	transition: color 0.15s;
	padding: 0;
}
.ctx-edit-link:hover { color: #a78bfa; }

.ctx-business {
	margin: 0;
	font-size: 0.82rem;
	color: #c9d1d9;
	line-height: 1.5;
}
.ctx-empty-hint { color: #4d5566; font-style: italic; }

.ctx-pills {
	display: flex;
	flex-wrap: wrap;
	gap: 6px;
}

.ctx-pill {
	display: inline-flex;
	align-items: center;
	font-size: 0.75rem;
	font-weight: 500;
	padding: 3px 10px;
	border-radius: 999px;
	border: 1px solid;
	white-space: nowrap;
}

.pill-full    { background: rgba(63, 185, 80, 0.1);  border-color: rgba(63, 185, 80, 0.35);  color: #3fb950; }
.pill-partial { background: rgba(227, 179, 65, 0.1); border-color: rgba(227, 179, 65, 0.35); color: #e3b341; }
.pill-empty   { background: rgba(255,255,255,0.03);  border-color: #2d333b;                  color: #4d5566; }

/* ── Paginator ── */
.paginator {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 4px;
	padding: 1rem 0 0.25rem;
}

.pag-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	min-width: 30px;
	height: 30px;
	padding: 0 6px;
	background: transparent;
	border: 1px solid #2d333b;
	border-radius: 7px;
	color: #768390;
	font-size: 12px;
	font-family: inherit;
	cursor: pointer;
	transition: all 0.15s;
}
.pag-btn:hover:not(:disabled):not(.active) { background: #1c2128; color: #e6edf3; border-color: #4d5566; }
.pag-btn:disabled { opacity: 0.3; cursor: default; }
.pag-btn.active { background: #1c2128; border-color: #4d5566; color: #e6edf3; font-weight: 600; }

.seg-ctrl.mode-static ~ * .pag-btn.active,
.pag-btn.pag-num.active { border-color: #4d5566; }

.pag-ellipsis { color: #4d5566; font-size: 12px; padding: 0 4px; line-height: 30px; }

.pag-info {
	margin-left: 8px;
	font-size: 11px;
	color: #4d5566;
	white-space: nowrap;
}
</style>
