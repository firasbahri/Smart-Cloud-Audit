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
					<Button
						label="Static Audit"
						icon="pi pi-search"
						:loading="isLoadingStatic"
						:disabled="isLoadingAny || !canRunAudit"
						@click="runStaticAudit"
					/>
				</div>
			</template>
		</Card>

		<Message v-if="!hasResources" severity="warn" :closable="false" class="mb-4">
			No hay recursos para auditar en la cuenta seleccionada.
		</Message>

		<Card v-if="hasResources" class="vuln-card">
			<template #content>
				<Tabs v-model:value="activeTab">
					<TabList>
						<Tab value="static">
							Estático
							<span v-if="staticVulnerabilities.length" class="tab-badge">{{ staticVulnerabilities.length }}</span>
						</Tab>
						<Tab v-if="aiVulnerabilities.length > 0" value="ai">
							IA
							<span class="tab-badge ai-badge">{{ aiVulnerabilities.length }}</span>
						</Tab>
					</TabList>

					<TabPanels>
						<TabPanel value="static">
							<div class="vuln-filter flex justify-content-between align-items-center mt-3 mb-3">
								<small class="text-muted">Total: {{ staticVulnerabilities.length }}</small>
								<Select v-model="selectedSeverity" :options="severityOptions" optionLabel="label" optionValue="value" class="w-14rem" />
							</div>
							<div v-if="filteredStatic.length" class="vuln-list flex flex-column gap-3">
								<div v-for="vuln in filteredStatic" :key="vuln.id" class="vuln-item">
									<div class="vuln-top flex align-items-center justify-content-between gap-2">
										<strong>{{ vuln.id }}</strong>
										<div class="flex gap-2">
											<Tag :value="vuln.severity" :severity="mapSeverity(vuln.severity)" rounded />
											<Tag :value="vuln.origin" severity="secondary" rounded />
										</div>
									</div>
									<p class="vuln-description">{{ vuln.description }}</p>
									<div class="vuln-meta"><span><strong>Resource ID:</strong> {{ vuln.resource_id }}</span></div>
								</div>
							</div>
							<Message v-else severity="info" :closable="false">No hay vulnerabilidades para la severidad seleccionada.</Message>
						</TabPanel>

						<TabPanel value="ai">
							<div class="vuln-filter flex justify-content-between align-items-center mt-3 mb-3">
								<small class="text-muted">Total: {{ aiVulnerabilities.length }}</small>
								<Select v-model="selectedSeverity" :options="severityOptions" optionLabel="label" optionValue="value" class="w-14rem" />
							</div>
							<div v-if="filteredAi.length" class="vuln-list flex flex-column gap-3">
								<div v-for="vuln in filteredAi" :key="vuln.id" class="vuln-item">
									<div class="vuln-top flex align-items-center justify-content-between gap-2">
										<strong>{{ vuln.id }}</strong>
										<div class="flex gap-2">
											<Tag :value="vuln.severity" :severity="mapSeverity(vuln.severity)" rounded />
											<Tag :value="vuln.origin" severity="secondary" rounded />
										</div>
									</div>
									<p class="vuln-description">{{ vuln.description }}</p>
									<div class="vuln-meta"><span><strong>Resource ID:</strong> {{ vuln.resource_id }}</span></div>
								</div>
							</div>
							<Message v-else severity="info" :closable="false">No hay vulnerabilidades para la severidad seleccionada.</Message>
						</TabPanel>
					</TabPanels>
				</Tabs>

				<div v-if="staticVulnerabilities.length > 0" class="ai-button-wrap mt-4">
					<Button
						label="Audit con IA"
						icon="pi pi-sparkles"
						severity="contrast"
						:disabled="isLoadingAny"
						@click="openAiDrawer"
					/>
				</div>
			</template>
		</Card>

		<!-- AI Drawer -->
		<Drawer v-model:visible="drawerOpen" position="right" :style="{ width: '460px' }">
			<template #header>
				<div class="flex align-items-center gap-2">
					<i class="pi pi-sparkles" style="color: #fb7185; font-size: 1.1rem" />
					<span class="font-bold" style="color: #e6edf3; font-size: 1rem">
						{{ drawerPhase === 'results' ? 'Resultados del Análisis IA' : 'Contexto para Análisis IA' }}
					</span>
					<span v-if="drawerPhase === 'results'" class="res-count ml-1">{{ drawerResults.length }}</span>
				</div>
			</template>

			<!-- PHASE: form -->
			<div v-if="drawerPhase === 'form'" class="flex flex-column gap-4 p-1">
				<div class="flex flex-column gap-2">
					<label class="ctx-label">Descripción de la empresa / servicio</label>
					<small class="ctx-hint">Ayuda a la IA a entender el propósito de la cuenta y priorizar riesgos.</small>
					<Textarea
						v-model="companyContext"
						:rows="4"
						placeholder="Ej: Startup fintech que procesa pagos online. Los buckets S3 almacenan facturas de clientes..."
						class="ctx-textarea"
						autoResize
					/>
				</div>

				<div class="flex flex-column gap-2">
					<label class="ctx-label">Contexto por recurso <span class="ctx-optional">(opcional)</span></label>
					<small class="ctx-hint">Describe para qué se usa cada recurso. Deja vacío si no es relevante.</small>
					<Accordion class="resource-accordion" :value="openAccordionPanels" multiple>
						<AccordionPanel v-for="group in resourceGroups" :key="group.key" :value="group.key">
							<AccordionHeader>
								<div class="flex align-items-center gap-2 w-full">
									<i :class="['pi', group.icon]" style="color: #8b949e" />
									<span>{{ group.label }}</span>
									<span class="res-count">{{ group.items.length }}</span>
								</div>
							</AccordionHeader>
							<AccordionContent>
								<div class="flex flex-column gap-2 pt-1">
									<div v-for="item in group.items" :key="item.id" class="res-row">
										<span class="res-id" :title="item.id">{{ item.label }}</span>
										<InputText
											v-model="resourceContextMap[item.id]"
											placeholder="Descripción opcional..."
											class="res-input"
											size="small"
										/>
									</div>
								</div>
							</AccordionContent>
						</AccordionPanel>
					</Accordion>
				</div>
			</div>

			<!-- PHASE: loading -->
			<div v-else-if="drawerPhase === 'loading'" class="flex flex-column align-items-center justify-content-center gap-4" style="height: 60%">
				<i class="pi pi-spin pi-spinner" style="font-size: 2.5rem; color: #fb7185" />
				<span style="color: #8b949e; font-size: 0.95rem">Analizando con IA...</span>
				<small style="color: #64748b; text-align: center; max-width: 260px">
					Gemini está revisando los recursos y el contexto proporcionado
				</small>
			</div>

			<!-- PHASE: results -->
			<div v-else-if="drawerPhase === 'results'" class="flex flex-column gap-3 p-1">
				<div class="results-summary flex gap-3">
					<div v-for="s in resultSummary" :key="s.label" class="summary-pill">
						<span class="summary-count" :style="{ color: s.color }">{{ s.count }}</span>
						<span class="summary-label">{{ s.label }}</span>
					</div>
				</div>

				<div class="flex flex-column gap-2">
					<div v-for="vuln in drawerResults" :key="vuln.id" class="drawer-vuln-item">
						<div class="flex align-items-center justify-content-between gap-2 mb-1">
							<strong style="color: #e6edf3; font-size: 0.82rem">{{ vuln.id }}</strong>
							<Tag :value="vuln.severity" :severity="mapSeverity(vuln.severity)" rounded />
						</div>
						<p class="drawer-vuln-desc">{{ vuln.description }}</p>
						<span class="drawer-vuln-res">{{ vuln.resource_id }}</span>
					</div>
				</div>
			</div>

			<template #footer>
				<!-- footer form -->
				<div v-if="drawerPhase === 'form'" class="flex justify-content-end gap-2">
					<Button label="Cancelar" severity="secondary" text @click="drawerOpen = false" />
					<Button
						label="Ejecutar Análisis IA"
						icon="pi pi-sparkles"
						@click="submitAiAudit"
					/>
				</div>

				<!-- footer results -->
				<div v-else-if="drawerPhase === 'results'" class="flex justify-content-between align-items-center">
					<Button label="Nuevo análisis" icon="pi pi-refresh" severity="secondary" text @click="drawerPhase = 'form'" />
					<Button label="Ver en pestaña IA" icon="pi pi-arrow-right" iconPos="right" @click="goToAiTab" />
				</div>
			</template>
		</Drawer>
	</div>
</template>

<script setup>
import { computed, ref, reactive, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useScanStore } from '../store/scanStore'
import { useAuditStore } from '../store/auditStore'
import { useCloudAccountsStore } from '../store/cloudAccountsStore'
import { buildApiUrl } from '../utils/api'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Message from 'primevue/message'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import Tabs from 'primevue/tabs'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import Drawer from 'primevue/drawer'
import Textarea from 'primevue/textarea'
import InputText from 'primevue/inputtext'
import Accordion from 'primevue/accordion'
import AccordionPanel from 'primevue/accordionpanel'
import AccordionHeader from 'primevue/accordionheader'
import AccordionContent from 'primevue/accordioncontent'

const scanStore = useScanStore()
const cloudAccountsStore = useCloudAccountsStore()
const auditStore = useAuditStore()
const toast = useToast()

const staticVulnerabilities = ref([])
const aiVulnerabilities = ref([])
const activeTab = ref('static')
const selectedSeverity = ref('ALL')
const isLoadingStatic = ref(false)
const isLoadingAi = ref(false)

// Drawer state
const drawerOpen = ref(false)
const drawerPhase = ref('form') // 'form' | 'loading' | 'results'
const drawerResults = ref([])
const companyContext = ref('')
const resourceContextMap = reactive({})
const openAccordionPanels = ref([])

const severityOptions = [
	{ label: 'Todas', value: 'ALL' },
	{ label: 'Critical', value: 'CRITICAL' },
	{ label: 'High', value: 'HIGH' },
	{ label: 'Medium', value: 'MEDIUM' },
	{ label: 'Low', value: 'LOW' },
]

const resources = computed(() => scanStore.scanResult || {})

const totalResources = computed(() =>
	['users', 'groups', 'roles', 'buckets', 'ec2']
		.reduce((sum, key) => sum + (Array.isArray(resources.value[key]) ? resources.value[key].length : 0), 0)
)

const hasResources = computed(() => totalResources.value > 0)

const activeAccountLabel = computed(() =>
	cloudAccountsStore.selectedAccount?.name || scanStore.id || 'Sin cuenta seleccionada'
)

const resolvedScanId = computed(() => {
	if (!scanStore.id) return null
	const idValue = String(scanStore.id)
	if (scanStore.scanIdByAccount?.[idValue]) return scanStore.scanIdByAccount[idValue]
	const values = Object.values(scanStore.scanIdByAccount || {})
	if (values.length === 1) return values[0]
	return idValue
})

const canRunAudit = computed(() => Boolean(resolvedScanId.value) && hasResources.value)
const isLoadingAny = computed(() => isLoadingStatic.value || isLoadingAi.value)

const filteredStatic = computed(() => {
	if (selectedSeverity.value === 'ALL') return staticVulnerabilities.value
	return staticVulnerabilities.value.filter(v => String(v.severity || '').toUpperCase() === selectedSeverity.value)
})

const filteredAi = computed(() => {
	if (selectedSeverity.value === 'ALL') return aiVulnerabilities.value
	return aiVulnerabilities.value.filter(v => String(v.severity || '').toUpperCase() === selectedSeverity.value)
})

const resourceGroups = computed(() => {
	const res = resources.value
	return [
		{ key: 'users', label: 'IAM Users', icon: 'pi-users', items: (res.users || []).map(r => ({ id: r.arn || r.username || r.name || String(r), label: r.username || r.name || r.arn || 'User' })) },
		{ key: 'groups', label: 'IAM Groups', icon: 'pi-sitemap', items: (res.groups || []).map(r => ({ id: r.arn || r.group_name || r.name || String(r), label: r.group_name || r.name || r.arn || 'Group' })) },
		{ key: 'roles', label: 'IAM Roles', icon: 'pi-id-card', items: (res.roles || []).map(r => ({ id: r.arn || r.role_name || r.name || String(r), label: r.role_name || r.name || r.arn || 'Role' })) },
		{ key: 'ec2', label: 'EC2 Instances', icon: 'pi-server', items: (res.ec2 || []).map(r => ({ id: r.instance_id || r.id || String(r), label: r.instance_id || r.id || 'Instance' })) },
		{ key: 'buckets', label: 'S3 Buckets', icon: 'pi-database', items: (res.buckets || []).map(r => ({ id: r.name || r.bucket_name || String(r), label: r.name || r.bucket_name || 'Bucket' })) },
	].filter(g => g.items.length > 0)
})

const resultSummary = computed(() => {
	const counts = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 }
	drawerResults.value.forEach(v => { counts[v.severity] = (counts[v.severity] || 0) + 1 })
	return [
		{ label: 'Critical', count: counts.CRITICAL, color: '#ef4444' },
		{ label: 'High', count: counts.HIGH, color: '#f97316' },
		{ label: 'Medium', count: counts.MEDIUM, color: '#eab308' },
		{ label: 'Low', count: counts.LOW, color: '#22c55e' },
	].filter(s => s.count > 0)
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

onMounted(() => {
	const existing = Array.isArray(auditStore.auditResult) ? auditStore.auditResult : []
	if (existing.length > 0) {
		staticVulnerabilities.value = existing.map((item, i) => normalizeVulnerability(item, i, 'static'))
	}
})

const openAiDrawer = () => {
	drawerPhase.value = 'form'
	drawerResults.value = []
	openAccordionPanels.value = resourceGroups.value.map(g => g.key)
	drawerOpen.value = true
}

const goToAiTab = () => {
	activeTab.value = 'ai'
	drawerOpen.value = false
}

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

		staticVulnerabilities.value = normalized
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
		company: companyContext.value.trim(),
		resources: Object.fromEntries(Object.entries(resourceContextMap).filter(([, v]) => v && v.trim()))
	}

	drawerPhase.value = 'loading'
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
		drawerResults.value = normalized
		drawerPhase.value = 'results'
	} catch (error) {
		drawerPhase.value = 'form'
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
:deep(.p-tabs) { background: transparent; }
:deep(.p-tablist) { background: #0d1117 !important; border-bottom: 1px solid rgba(34, 197, 94, 0.12); }
:deep(.p-tab) { background: transparent !important; color: #8b949e !important; border: none !important; }
:deep(.p-tab:hover) { color: #e6edf3 !important; background: rgba(255,255,255,0.04) !important; }
:deep(.p-tab[aria-selected="true"]) { color: #22c55e !important; border-bottom: 2px solid #22c55e !important; }
:deep(.p-tabpanels) { background: transparent !important; padding: 0; }
:deep(.p-tabpanel) { background: transparent !important; padding: 0; }

.account-label { color: #8b949e; font-size: 0.875rem; }
.account-value { color: #e6edf3; font-weight: 600; font-size: 1.1rem; }

.tab-badge {
	display: inline-flex; align-items: center; justify-content: center;
	background: rgba(34, 197, 94, 0.15); color: #22c55e;
	border-radius: 999px; font-size: 0.7rem; font-weight: 700; padding: 0.1rem 0.45rem; margin-left: 0.4rem;
}
.ai-badge { background: rgba(139, 92, 246, 0.15); color: #a78bfa; }

.ai-button-wrap { display: flex; justify-content: flex-end; border-top: 1px solid rgba(34, 197, 94, 0.1); padding-top: 1rem; }

.vuln-filter { gap: 0.75rem; }
.text-muted { color: #94a3b8; }
.vuln-item { border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 10px; padding: 0.7rem; background: rgba(2, 6, 23, 0.45); }
.vuln-description { margin: 0.65rem 0; color: #cbd5e1; }
.vuln-meta { color: #94a3b8; font-size: 0.9rem; }

/* Drawer - background via global.css */
.ctx-label { color: #c9d1d9; font-size: 0.875rem; font-weight: 600; }
.ctx-hint { color: #64748b; font-size: 0.78rem; margin-top: -0.25rem; }
.ctx-optional { color: #475569; font-weight: 400; }

.ctx-textarea {
	width: 100%;
	background: #2a0f18;
	border-color: rgba(244, 63, 94, 0.25);
	color: #e6edf3;
	border-radius: 8px;
	font-size: 0.875rem;
	resize: none;
}
.ctx-textarea:focus { border-color: #f43f5e; box-shadow: 0 0 0 2px rgba(244, 63, 94, 0.15); }

:deep(.resource-accordion .p-accordionpanel) { border: 1px solid rgba(244, 63, 94, 0.12); border-radius: 8px; margin-bottom: 0.5rem; overflow: hidden; }
:deep(.resource-accordion .p-accordionheader) { background: #220d14; color: #c9d1d9; padding: 0.6rem 0.85rem; font-size: 0.875rem; border: none; }
:deep(.resource-accordion .p-accordionheader:hover) { background: #2a0f18; }
:deep(.resource-accordion .p-accordioncontent-content) { background: #1a0a10; padding: 0.5rem 0.85rem 0.75rem; }

.res-count { margin-left: auto; background: rgba(244, 63, 94, 0.15); color: #fb7185; border-radius: 999px; font-size: 0.7rem; font-weight: 700; padding: 0.05rem 0.4rem; }
.res-row { display: flex; flex-direction: column; gap: 0.3rem; }
.res-id { color: #8b949e; font-size: 0.78rem; font-family: monospace; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.res-input { width: 100%; background: #161b22 !important; border-color: rgba(148, 163, 184, 0.15) !important; color: #e6edf3 !important; font-size: 0.8rem; }

/* Results phase */
.results-summary { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.25rem; }
.summary-pill { display: flex; flex-direction: column; align-items: center; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 0.4rem 0.9rem; min-width: 60px; }
.summary-count { font-size: 1.3rem; font-weight: 700; line-height: 1; }
.summary-label { font-size: 0.7rem; color: #64748b; margin-top: 0.2rem; }

.drawer-vuln-item { border: 1px solid rgba(244, 63, 94, 0.12); border-radius: 8px; padding: 0.65rem 0.8rem; background: rgba(42, 15, 24, 0.5); }
.drawer-vuln-desc { margin: 0.35rem 0 0.3rem; color: #cbd5e1; font-size: 0.83rem; line-height: 1.45; }
.drawer-vuln-res { color: #64748b; font-size: 0.75rem; font-family: monospace; }
</style>
