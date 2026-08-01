<template>
	<div class="audit-view">
		<div class="page-header flex align-items-center gap-3 mb-5">
			<i class="pi pi-shield page-icon p-3 border-round-xl shadow-3" />
			<div>
				<h2 class="m-0">Security Audit</h2>
				<p class="subtitle m-0 mt-2">Run static or AI audits on the scanned account</p>
			</div>
		</div>

		<Card class="account-card mb-4">
			<template #content>
				<div class="flex flex-column md:flex-row md:align-items-center md:justify-content-between gap-3">
					<div class="flex flex-column gap-2">
						<span class="account-label">Account to audit</span>
						<span class="account-value">{{ activeAccountLabel }}</span>
					</div>
					<div class="audit-controls">
						<div class="audit-mode-toggle">
							<button
								:class="['toggle-btn', 'static-btn', { active: auditMode === 'static' }]"
								:disabled="isLoadingAny"
								@click="auditMode = 'static'"
							>
								<i class="pi pi-search" /> Static
							</button>
							<button
								:class="['toggle-btn', 'ai-btn', { active: auditMode === 'ai' }]"
								:disabled="isLoadingAny"
								@click="auditMode = 'ai'"
							>
								<i class="pi pi-sparkles" /> AI Analysis
							</button>
						</div>
						<Button
							:label="auditMode === 'ai' ? 'Run AI' : 'Run'"
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

		<div v-if="auditMode === 'ai'" class="ctx-panel mb-4">
			<div class="ctx-panel-header">
				<div class="ctx-panel-title">
					<i class="pi pi-sparkles" style="color:#a78bfa" />
					<span>Active AI context</span>
					<span class="ctx-sections-badge">{{ filledSections }}/{{ totalSections }} sections</span>
				</div>
				<button class="ctx-edit-link" @click="router.push('/app/inventory')">Edit context →</button>
			</div>
			<p v-if="cloudAccountsStore.selectedAccount?.description" class="ctx-business">
				<strong>Business:</strong> {{ cloudAccountsStore.selectedAccount.description }}
			</p>
			<p v-else class="ctx-business ctx-empty-hint">No business description — add it when editing the account.</p>
			<div class="ctx-pills">
				<span
					v-for="g in contextGroups"
					:key="g.key"
					:class="['ctx-pill', `pill-${g.status}`]"
				>
					<span v-if="g.status === 'full'">✓ </span>{{ g.label }}
					<span v-if="g.status === 'full'"> · {{ g.filled }}</span>
					<span v-else-if="g.status === 'partial'"> · {{ g.filled }}/{{ g.total }}</span>
					<span v-else> · no context</span>
				</span>
			</div>
		</div>

		<Message v-if="!hasResources" severity="warn" :closable="false" class="mb-4">
			No resources to audit in the selected account.
		</Message>

		<Card v-if="hasResources" class="vuln-card">
			<template #content>

				<div v-if="!hasResults && !isLoadingAny" class="audit-empty">
					<div class="empty-well">
						<div class="empty-icon-box">
							<i class="pi pi-shield" style="font-size:1.25rem" />
						</div>
						<h3 class="empty-title">No findings yet</h3>
						<p class="empty-hint">
							Choose <span style="color:#3fb950;font-weight:600">Static</span> or
							<span style="color:#a78bfa;font-weight:600">AI Analysis</span>
							above and click <strong style="color:#e6edf3">Run</strong>.
							Results will appear here in real time.
						</p>
					</div>
				</div>

				<template v-else>
				<div class="results-bar">
					<div :class="['seg-ctrl', `mode-${activeTab}`]">
						<button
							:class="['seg-btn', { active: activeTab === 'static' }]"
							:disabled="isLoadingAi"
							@click="activeTab = 'static'"
						>
							Static
							<span v-if="staticVulnerabilities.length" class="seg-badge">{{ staticVulnerabilities.length }}</span>
						</button>
						<button
							:class="['seg-btn', { active: activeTab === 'ai' }]"
							:disabled="isLoadingAi"
							@click="activeTab = 'ai'"
						>
							<i class="pi pi-sparkles" style="font-size: 0.68rem" /> AI
							<span v-if="aiVulnerabilities.length" class="seg-badge">{{ aiVulnerabilities.length }}</span>
						</button>
					</div>
					<div class="filter-right">
						<small class="filter-count">
							{{ activeFiltered.length }} findings
							<span v-if="isFiltered" class="filter-dim">· of {{ currentTotal }}</span>
						</small>
						<select v-model="selectedSeverity" class="sev-select">
							<option v-for="opt in severityOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
						</select>
						<select v-model="resourceFilter" class="sev-select">
							<option value="all">All types</option>
							<option v-for="rt in resourceOptions" :key="rt" :value="rt">{{ rt }}</option>
						</select>
					</div>
				</div>

				<div v-if="activeTab === 'ai' && pagedVulns.length" class="ai-notice-banner" role="note">
					<span class="ai-notice-icon pi pi-sparkles" aria-hidden="true" />
					<p class="ai-notice-text">
						<strong class="ai-notice-lead">AI-generated findings.</strong>
						These are interpretations by a language model of your configuration and may vary between runs or contain inaccuracies (false positives/negatives).
						<strong class="ai-notice-action">Verify each finding before acting</strong>
						— unlike static analysis, they are not deterministic and do not replace the judgement of a security professional.
					</p>
				</div>

				<div v-if="pagedVulns.length" class="vuln-list flex flex-column gap-3">
					<div
						v-for="vuln in pagedVulns"
						:key="vuln.id"
						:class="['vuln-item', { 'ai-vuln-item': activeTab === 'ai' }]"
					>
						<div class="vi-header">
							<div class="vi-sev" :style="sevBadgeStyle(vuln.severity)">
								{{ vuln.severity }}
							</div>
							<div class="vi-center">
								<div class="vi-name" :class="{ 'vi-name--ai': activeTab === 'ai' }">
									<span v-if="activeTab === 'ai'" aria-hidden="true">✦ </span>{{ vuln.name }}
								</div>
								<div class="vi-resource">{{ vuln.resource_id }}</div>
							</div>
						</div>

						<div class="vi-body">
							<div class="vi-why">
								<span class="vi-label">Why this is a problem</span>
								<p class="vi-why-text">{{ vuln.description }}</p>
							</div>

							<button
								v-if="getRemState(vuln.id) === 'idle'"
								class="rem-gen-btn"
								@click="handleGenerate(vuln.id)"
							>
								<span aria-hidden="true">✦</span> Generate fix with AI
							</button>

							<div
								v-else-if="getRemState(vuln.id) === 'loading'"
								class="rem-loading"
								role="status"
								aria-live="polite"
							>
								<span class="rem-spin" aria-hidden="true">✦</span>
								<span>Generating command for your resource...</span>
							</div>

							<div v-else class="rem-done">
								<div class="rem-saved-pill">
									<span aria-hidden="true">✦</span> AI-generated · saved
								</div>

								<span class="vi-label">How to fix it</span>

								<ol class="rem-steps">
									<li v-for="(step, i) in getRemData(vuln.id).steps" :key="i" class="rem-step">
										<span class="rem-step-num" aria-hidden="true">{{ i + 1 }}</span>
										<span class="rem-step-text">{{ step }}</span>
									</li>
								</ol>

								<!-- CLI code box -->
								<div class="rem-code-box">
									<div class="rem-code-header">
										<span class="rem-cmd-label">{{ getRemData(vuln.id).cmdLabel }}</span>
										<button
											:class="['rem-copy-btn', { 'rem-copy-btn--copied': copiedVuln[vuln.id] }]"
											@click="copyVulnCommand(vuln.id)"
										>
											{{ copiedVuln[vuln.id] ? '✓ Copied' : 'Copy' }}
										</button>
									</div>
									<div class="rem-code-body">
										<pre class="rem-code-pre">{{ getRemData(vuln.id).command }}</pre>
									</div>
								</div>

								<!-- Disclaimer -->
								<div class="rem-disclaimer" role="note">
									<span class="rem-disc-icon" aria-hidden="true">⚠</span>
									<span>AI-suggested command — review it before executing. Smart Audit does not apply changes (read-only).</span>
								</div>

							</div>
						</div>
					</div>
				</div>

				<Message v-else-if="activeFiltered.length === 0 && currentTotal > 0" severity="info" :closable="false" class="mt-3">
					No findings match the selected filters.
				</Message>

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
			</template>
		</Card>

	</div>

	<div v-if="aiModeDialog" class="ai-modal-overlay" @click.self="aiModeDialog = false">
		<div class="ai-modal">
			<div class="ai-modal__header">
				<div class="ai-modal__icon"><i class="pi pi-sparkles" /></div>
				<div class="ai-modal__title">You already have a static audit for this account</div>
				<div class="ai-modal__subtitle">How do you want to run the AI analysis?</div>
			</div>
			<div class="ai-modal__options">
				<button class="ai-opt ai-opt--base" @click="executeAiAudit(auditStore.id || auditStore.auditIdByAccount[accountId])">
					<div class="ai-opt__icon"><i class="pi pi-link" /></div>
					<div class="ai-opt__content">
						<div class="ai-opt__label">Use static audit as base</div>
						<div class="ai-opt__desc">AI complements the static findings without duplicating them</div>
					</div>
					<i class="pi pi-chevron-right ai-opt__arrow" />
				</button>
				<button class="ai-opt ai-opt--scratch" @click="executeAiAudit(null)">
					<div class="ai-opt__icon"><i class="pi pi-sparkles" /></div>
					<div class="ai-opt__content">
						<div class="ai-opt__label">Analyze everything from scratch with AI</div>
						<div class="ai-opt__desc">AI analyzes resources completely independently</div>
					</div>
					<i class="pi pi-chevron-right ai-opt__arrow" />
				</button>
			</div>
			<button class="ai-modal__cancel" @click="aiModeDialog = false">Cancel</button>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch, reactive } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useRouter } from 'vue-router'
import { useScanStore } from '../store/scanStore'
import { useAuditStore } from '../store/auditStore'
import { useCloudAccountsStore } from '../store/cloudAccountsStore'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Message from 'primevue/message'

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
const aiVulnerabilities = computed(() =>
	Array.isArray(auditStore.aiAuditResult)
		? auditStore.aiAuditResult.map((item, i) => normalizeVulnerability(item, i, 'ai'))
		: []
)
const activeTab = ref('static')
const selectedSeverity = ref('ALL')
const resourceFilter = ref('all')
const isLoadingStatic = ref(false)
const isLoadingAi = ref(false)
const auditMode = ref('static')

const remediationStates = reactive({})
const remediationData = reactive({})
const copiedVuln = reactive({})

const getRemState = (vulnId) => remediationStates[vulnId] || 'idle'

const getRemData = (vulnId) => remediationData[vulnId] || { steps: [], command: '', cmdLabel: 'AWS CLI · AI-suggested' }

// Parses "1- Paso uno\n2- Paso dos" → ['Paso uno', 'Paso dos']
const parseRemediationSteps = (text) => {
	if (!text) return []
	return text
		.split('\n')
		.map(line => line.trim())
		.filter(line => line.length > 0)
		.map(line => line.replace(/^\d+[-.)]\s*/, '').trim())
		.filter(line => line.length > 0)
}

const handleGenerate = async (vulnId) => {
	remediationStates[vulnId] = 'loading'
	const auditId = activeTab.value === 'ai' ? auditStore.aiAuditId : auditStore.id
	try {
		const data = await auditStore.generateSolution(auditId, vulnId)
		const cmd = data?.cli_command || ''
		const steps = data?.recommendation ? parseRemediationSteps(data.recommendation) : []
		remediationData[vulnId] = {
			steps: steps.length > 0
				? steps
				: ['Check the official AWS documentation for this type of vulnerability.'],
			command: cmd,
			cmdLabel: cmd ? 'AWS CLI · generado por IA' : '',
		}
		remediationStates[vulnId] = 'done'
		auditStore.loadAuditsForAccount(cloudAccountsStore.selectedAccount, { silent: true })
	} catch (error) {
		toast.add({ severity: 'error', summary: 'Error al generar', detail: error.message, life: 3000 })
		remediationStates[vulnId] = 'idle'
	}
}

const copyVulnCommand = async (vulnId) => {
	const cmd = getRemData(vulnId).command
	try {
		await navigator.clipboard.writeText(cmd)
		copiedVuln[vulnId] = true
		setTimeout(() => { copiedVuln[vulnId] = false }, 1500)
	} catch { /* clipboard not available */ }
}

const SEV_COLORS = { CRITICAL: '#f85149', HIGH: '#e3b341', MEDIUM: '#388bfd', LOW: '#3fb950' }
const sevBadgeStyle = (severity) => {
	const color = SEV_COLORS[String(severity).toUpperCase()] ?? '#768390'
	return { background: color + '21', color }
}

const severityOptions = [
	{ label: 'All', value: 'ALL' },
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
	cloudAccountsStore.selectedAccount?.name || 'No account selected'
)

const resolvedScanId = computed(() => {
	if (!accountId.value) return null
	return scanStore.scanResultIdByAccount[accountId.value] || null
})

const canRunAudit = computed(() => Boolean(resolvedScanId.value) && hasResources.value)
const isLoadingAny = computed(() => isLoadingStatic.value || isLoadingAi.value)
const hasResults = computed(() =>
	staticVulnerabilities.value.length > 0 || aiVulnerabilities.value.length > 0
)
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

const resourceOptions = computed(() => {
	const source = activeTab.value === 'ai' ? aiVulnerabilities.value : staticVulnerabilities.value
	return [...new Set(source.map(v => v.resource_type).filter(Boolean))].sort()
})

const isFiltered = computed(() => selectedSeverity.value !== 'ALL' || resourceFilter.value !== 'all')

const filteredStatic = computed(() => {
	let list = staticVulnerabilities.value
	if (selectedSeverity.value !== 'ALL') list = list.filter(v => String(v.severity || '').toUpperCase() === selectedSeverity.value)
	if (resourceFilter.value !== 'all') list = list.filter(v => v.resource_type === resourceFilter.value)
	return list
})

const filteredAi = computed(() => {
	let list = aiVulnerabilities.value
	if (selectedSeverity.value !== 'ALL') list = list.filter(v => String(v.severity || '').toUpperCase() === selectedSeverity.value)
	if (resourceFilter.value !== 'all') list = list.filter(v => v.resource_type === resourceFilter.value)
	return list
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
	return `${start}–${end} of ${total}`
})

const normalizeVulnerability = (item, index, mode) => ({
	id: item?.id || item?._id || `VULN-${index + 1}`,
	name: item?.name || item?.id || `VULN-${index + 1}`,
	description: item?.description || item?.detail || 'Sin descripcion',
	severity: String(item?.severity || 'LOW').toUpperCase(),
	resource_id: item?.resource_id || item?.resourceId || 'N/A',
	resource_type: item?.resource_type || item?.resourceType || '',
	remediation: item?.remediation || item?.recommendation || item?.cli_command || '',
	origin: item?.origin || (mode === 'ai' ? 'AI Analysis' : 'Static Analysis')
})

watch(accountId, () => {
	auditStore.clearData()
	activeTab.value = 'static'
	currentPage.value = 1
	selectedSeverity.value = 'ALL'
	resourceFilter.value = 'all'
	Object.keys(remediationStates).forEach(k => delete remediationStates[k])
	Object.keys(remediationData).forEach(k => delete remediationData[k])
})

watch(activeTab, () => {
	currentPage.value = 1
	selectedSeverity.value = 'ALL'
	resourceFilter.value = 'all'
})

watch([selectedSeverity, resourceFilter], () => { currentPage.value = 1 })

// auditMode (qué voy a ejecutar) sincroniza la vista de resultados,
// pero no al revés: navegar resultados no debe cambiar qué se va a ejecutar.
watch(auditMode, (val) => { activeTab.value = val })

const runStaticAudit = async () => {
	const scanId = resolvedScanId.value
	if (!scanId) { toast.add({ severity: 'warn', summary: 'Auditoria', detail: 'No hay scan_id disponible', life: 3000 }); return }

	isLoadingStatic.value = true
	try {
		const count = await auditStore.runStaticAudit(scanId, cloudAccountsStore.selectedAccount)
		activeTab.value = 'static'
		toast.add({ severity: 'success', summary: 'Auditoria completada', detail: `${count} vulnerabilidades encontradas`, life: 3000 })
	} catch (error) {
		toast.add({ severity: 'error', summary: 'Error en auditoria', detail: error.message, life: 3500 })
	} finally {
		isLoadingStatic.value = false
	}
}

const aiModeDialog = ref(false)

const submitAiAudit = () => {
	const scanId = resolvedScanId.value
	if (!scanId) {
		toast.add({ severity: 'warn', summary: 'Auditoria IA', detail: 'No hay escaneo disponible', life: 3000 })
		return
	}
	const existingAuditId = auditStore.id || auditStore.auditIdByAccount[accountId.value] || null
	if (existingAuditId) {
		aiModeDialog.value = true
		return
	}
	executeAiAudit(null)
}

const executeAiAudit = async (auditId) => {
	aiModeDialog.value = false
	const scanId = resolvedScanId.value
	const userContext = {
		company: cloudAccountsStore.selectedAccount?.description?.trim() || '',
		resources: scanStore.resourceContextsByAccount[accountId.value] || {}
	}
	isLoadingAi.value = true
	try {
		const count = await auditStore.runAiAudit(scanId, auditId, userContext, cloudAccountsStore.selectedAccount)
		activeTab.value = 'ai'
		toast.add({ severity: 'success', summary: 'Análisis IA completado', detail: `${count} vulnerabilidades encontradas`, life: 3000 })
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
.seg-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.seg-btn:hover:not(.active):not(:disabled) { background: rgba(255,255,255,0.03); color: #e6edf3; }
.seg-ctrl.mode-static .seg-btn.active { background: rgba(34, 197, 94, 0.1); color: #22c55e; }
.seg-ctrl.mode-ai .seg-btn.active { background: rgba(167, 139, 250, 0.12); color: #a78bfa; }

.seg-badge {
	display: inline-flex; align-items: center; justify-content: center;
	background: rgba(255,255,255,0.07); color: inherit;
	border-radius: 999px; font-size: 0.65rem; font-weight: 700;
	padding: 0.05rem 0.4rem; min-width: 18px;
}

.filter-right { display: flex; align-items: center; gap: 8px; }
.filter-count { color: #94a3b8; white-space: nowrap; }
.filter-dim   { color: #4d5566; }

.sev-select {
	background: #1c2128; border: 1px solid #2d333b; color: #e6edf3;
	border-radius: 7px; padding: 5px 10px; font-size: 12px; font-family: inherit;
	cursor: pointer; outline: none; appearance: auto;
}
.sev-select option { background: #1c2128; color: #e6edf3; }
.sev-select:hover { border-color: #4d5566; }

.audit-controls { display: flex; align-items: center; gap: 0.5rem; }
.audit-mode-toggle { display: flex; border: 1px solid #2d333b; border-radius: 8px; overflow: hidden; background: #161b22; }

.toggle-btn {
	flex: 1; padding: 9px 14px; background: transparent; border: none;
	color: #768390; cursor: pointer; font-size: 12px; font-weight: 500;
	display: flex; align-items: center; gap: 6px;
	transition: all 0.15s; border-right: 1px solid #2d333b; white-space: nowrap;
}
.toggle-btn:last-child { border-right: none; }
.toggle-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.toggle-btn:hover:not(:disabled) { background: #1c2128; color: #e6edf3; }
.toggle-btn.static-btn.active { background: #1c2128; color: #22c55e; }
.toggle-btn.ai-btn.active { background: #1c2128; color: #a78bfa; }

.text-muted { color: #94a3b8; }
.vuln-list { margin-top: 0.5rem; }

/* ── Vulnerability item (card) ── */
.vuln-item {
	background: #161b22;
	border: 1px solid #2d333b;
	border-radius: 10px;
	overflow: hidden;
}
.ai-vuln-item { border-color: rgba(167, 139, 250, 0.25); }

/* Header */
.vi-header {
	display: flex;
	align-items: center;
	gap: 12px;
	padding: 12px 14px;
	border-bottom: 1px solid #2d333b;
}

.vi-sev {
	flex-shrink: 0;
	width: 62px;
	text-align: center;
	font-size: 9px;
	font-weight: 700;
	padding: 3px 0;
	border-radius: 4px;
	letter-spacing: 0.04em;
}

.vi-center {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	gap: 3px;
}

.vi-name {
	font-family: 'Consolas', 'Monaco', monospace;
	font-size: 13px;
	font-weight: 600;
	color: #e6edf3;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}
.vi-name--ai { color: #a78bfa; }

.vi-resource {
	font-family: 'Consolas', 'Monaco', monospace;
	font-size: 11px;
	color: #4d5566;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}


/* Body */
.vi-body {
	padding: 14px;
	display: flex;
	flex-direction: column;
	gap: 12px;
}

.vi-why { display: flex; flex-direction: column; gap: 5px; }

.vi-label {
	display: block;
	font-size: 10px;
	font-weight: 700;
	color: #4d5566;
	text-transform: uppercase;
	letter-spacing: 0.05em;
}

.vi-why-text {
	margin: 0;
	font-size: 12px;
	color: #768390;
	line-height: 1.6;
}

/* idle: generate button */
.rem-gen-btn {
	align-self: flex-start;
	background: rgba(167,139,250,0.1);
	border: 1px solid rgba(167,139,250,0.35);
	color: #a78bfa;
	border-radius: 7px;
	padding: 6px 12px;
	font-size: 12px;
	font-weight: 600;
	font-family: inherit;
	cursor: pointer;
	transition: background 0.15s, border-color 0.15s;
	display: inline-flex;
	align-items: center;
	gap: 7px;
}
.rem-gen-btn:hover {
	background: rgba(167,139,250,0.16);
	border-color: rgba(167,139,250,0.55);
}

/* loading */
.rem-loading {
	align-self: flex-start;
	background: rgba(167,139,250,0.06);
	border: 1px solid rgba(167,139,250,0.2);
	color: #a78bfa;
	border-radius: 7px;
	padding: 6px 12px;
	font-size: 12px;
	font-weight: 500;
	display: inline-flex;
	align-items: center;
	gap: 9px;
	opacity: 0.85;
}

.rem-spin {
	display: inline-block;
	animation: rem-rotate 1s linear infinite;
}

@keyframes rem-rotate {
	from { transform: rotate(0deg); }
	to   { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
	.rem-spin { animation: none; opacity: 0.6; }
}

/* done */
.rem-done {
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.rem-saved-pill {
	display: inline-flex;
	align-items: center;
	gap: 5px;
	background: rgba(167,139,250,0.1);
	border: 1px solid rgba(167,139,250,0.3);
	color: #a78bfa;
	font-size: 10px;
	font-weight: 600;
	padding: 4px 10px;
	border-radius: 20px;
	align-self: flex-start;
}

/* Steps */
.rem-steps { margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 7px; }
.rem-step  { display: flex; gap: 10px; align-items: flex-start; }
.rem-step-num  { flex-shrink: 0; color: #a78bfa; font-weight: 700; font-size: 12px; min-width: 14px; margin-top: 1px; }
.rem-step-text { font-size: 12px; color: #768390; line-height: 1.5; }

/* CLI code box */
.rem-code-box { background: #0a0e14; border: 1px solid #2d333b; border-radius: 8px; overflow: hidden; }

.rem-code-header {
	background: #1c2128;
	border-bottom: 1px solid #2d333b;
	padding: 6px 12px;
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.rem-cmd-label { font-family: 'Consolas','Monaco',monospace; font-size: 10px; color: #4d5566; }

.rem-copy-btn {
	background: transparent;
	border: 1px solid #2d333b;
	color: #c9d1d9;
	font-size: 10px;
	font-family: inherit;
	padding: 3px 10px;
	border-radius: 5px;
	cursor: pointer;
	transition: background 0.12s, color 0.12s;
}
.rem-copy-btn:hover { background: rgba(255,255,255,0.05); }
.rem-copy-btn--copied { color: #3fb950; border-color: rgba(63,185,80,0.3); }

.rem-code-body { padding: 10px 12px; overflow-x: auto; }
.rem-code-pre {
	margin: 0;
	font-family: 'Consolas','Monaco',monospace;
	font-size: 11px;
	color: #c9d1d9;
	line-height: 1.6;
	white-space: pre;
}

/* Disclaimer */
.rem-disclaimer {
	display: flex;
	align-items: flex-start;
	gap: 8px;
	background: rgba(227,179,65,0.06);
	border: 1px solid rgba(227,179,65,0.25);
	border-radius: 7px;
	padding: 9px 12px;
	font-size: 11px;
	color: #f0d28a;
	line-height: 1.5;
}
.rem-disc-icon { color: #e3b341; flex-shrink: 0; margin-top: 1px; }


/* ── Empty state ── */
.audit-empty {
	padding: 4px 0;
}

.empty-well {
	border: 1px dashed #2d333b;
	border-radius: 12px;
	padding: 30px 20px;
	display: flex;
	flex-direction: column;
	align-items: center;
	text-align: center;
}

.empty-icon-box {
	width: 48px;
	height: 48px;
	border-radius: 14px;
	background: #1c2128;
	border: 1px solid #2d333b;
	color: #768390;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 16px;
}

.empty-title {
	margin: 0 0 6px;
	font-size: 15px;
	font-weight: 600;
	color: #e6edf3;
}

.empty-hint {
	margin: 0;
	font-size: 12.5px;
	color: #768390;
	max-width: 360px;
	line-height: 1.55;
}

/* ── Context summary panel ── */
.ctx-panel {
	background: #161b22; border: 1px solid rgba(167,139,250,0.2);
	border-radius: 14px; padding: 0.9rem 1rem;
	display: flex; flex-direction: column; gap: 0.55rem;
}
.ctx-panel-header { display: flex; align-items: center; justify-content: space-between; }
.ctx-panel-title  { display: flex; align-items: center; gap: 7px; font-size: 0.875rem; font-weight: 600; color: #c4b5fd; }
.ctx-sections-badge { background: rgba(167,139,250,0.15); color: #a78bfa; border-radius: 999px; font-size: 0.7rem; font-weight: 700; padding: 0.1rem 0.5rem; }
.ctx-edit-link { background: transparent; border: none; color: #768390; font-size: 0.8rem; cursor: pointer; font-family: inherit; transition: color 0.15s; padding: 0; }
.ctx-edit-link:hover { color: #a78bfa; }
.ctx-business { margin: 0; font-size: 0.82rem; color: #c9d1d9; line-height: 1.5; }
.ctx-empty-hint { color: #4d5566; font-style: italic; }
.ctx-pills { display: flex; flex-wrap: wrap; gap: 6px; }
.ctx-pill { display: inline-flex; align-items: center; font-size: 0.75rem; font-weight: 500; padding: 3px 10px; border-radius: 999px; border: 1px solid; white-space: nowrap; }
.pill-full    { background: rgba(63,185,80,0.1);  border-color: rgba(63,185,80,0.35);  color: #3fb950; }
.pill-partial { background: rgba(227,179,65,0.1); border-color: rgba(227,179,65,0.35); color: #e3b341; }
.pill-empty   { background: rgba(255,255,255,0.03); border-color: #2d333b; color: #4d5566; }

/* ── Paginator ── */
.paginator { display: flex; align-items: center; justify-content: center; gap: 4px; padding: 1rem 0 0.25rem; }
.pag-btn { display: inline-flex; align-items: center; justify-content: center; min-width: 30px; height: 30px; padding: 0 6px; background: transparent; border: 1px solid #2d333b; border-radius: 7px; color: #768390; font-size: 12px; font-family: inherit; cursor: pointer; transition: all 0.15s; }
.pag-btn:hover:not(:disabled):not(.active) { background: #1c2128; color: #e6edf3; border-color: #4d5566; }
.pag-btn:disabled { opacity: 0.3; cursor: default; }
.pag-btn.active { background: #1c2128; border-color: #4d5566; color: #e6edf3; font-weight: 600; }
.pag-ellipsis { color: #4d5566; font-size: 12px; padding: 0 4px; line-height: 30px; }
.pag-info { margin-left: 8px; font-size: 11px; color: #4d5566; white-space: nowrap; }

/* ── Modal de modo IA ── */
.ai-modal-overlay {
	position: fixed; inset: 0; z-index: 300;
	background: rgba(0, 0, 0, 0.6);
	display: flex; align-items: center; justify-content: center;
	padding: 1rem;
}

.ai-modal {
	background: #161b22;
	border: 1px solid rgba(167, 139, 250, 0.3);
	border-radius: 16px;
	padding: 24px;
	width: 100%;
	max-width: 440px;
	display: flex;
	flex-direction: column;
	gap: 20px;
	box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(167, 139, 250, 0.1);
	animation: modalIn 0.18s ease-out;
}

@keyframes modalIn {
	from { opacity: 0; transform: translateY(-8px) scale(0.98); }
	to   { opacity: 1; transform: translateY(0) scale(1); }
}

.ai-modal__header { display: flex; flex-direction: column; align-items: center; gap: 10px; text-align: center; }

.ai-modal__icon {
	width: 44px; height: 44px; border-radius: 12px;
	background: rgba(167, 139, 250, 0.12);
	border: 1px solid rgba(167, 139, 250, 0.3);
	display: flex; align-items: center; justify-content: center;
	color: #a78bfa; font-size: 1.1rem;
}

.ai-modal__title {
	font-size: 15px; font-weight: 700; color: #e6edf3; line-height: 1.35;
}

.ai-modal__subtitle {
	font-size: 12.5px; color: #768390;
}

.ai-modal__options { display: flex; flex-direction: column; gap: 10px; }

.ai-opt {
	display: flex; align-items: center; gap: 13px;
	width: 100%; text-align: left;
	background: #0f141a;
	border: 1px solid #2d333b;
	border-radius: 11px;
	padding: 14px 14px;
	cursor: pointer; font-family: inherit;
	transition: border-color 0.15s, background 0.15s;
}

.ai-opt:hover { background: #131920; }

.ai-opt__icon {
	flex-shrink: 0;
	width: 34px; height: 34px; border-radius: 9px;
	display: flex; align-items: center; justify-content: center;
	font-size: 0.9rem;
}

.ai-opt--base .ai-opt__icon {
	background: rgba(34, 197, 94, 0.1);
	border: 1px solid rgba(34, 197, 94, 0.3);
	color: #22c55e;
}
.ai-opt--base:hover { border-color: rgba(34, 197, 94, 0.4); }

.ai-opt--scratch .ai-opt__icon {
	background: rgba(167, 139, 250, 0.1);
	border: 1px solid rgba(167, 139, 250, 0.3);
	color: #a78bfa;
}
.ai-opt--scratch:hover { border-color: rgba(167, 139, 250, 0.45); }

.ai-opt__content { flex: 1; min-width: 0; }

.ai-opt__label {
	font-size: 13px; font-weight: 600; color: #e6edf3; margin-bottom: 3px;
}

.ai-opt__desc {
	font-size: 11.5px; color: #4d5566; line-height: 1.45;
}

.ai-opt--base .ai-opt__label  { color: #4ade80; }
.ai-opt--scratch .ai-opt__label { color: #c4b5fd; }

.ai-opt__arrow { color: #2d333b; font-size: 0.7rem; flex-shrink: 0; }
.ai-opt:hover .ai-opt__arrow { color: #4d5566; }

.ai-modal__cancel {
	align-self: center;
	background: transparent; border: none;
	color: #4d5566; font-size: 12px; font-family: inherit;
	cursor: pointer; padding: 4px 12px; border-radius: 6px;
	transition: color 0.12s, background 0.12s;
}
.ai-modal__cancel:hover { color: #768390; background: rgba(255, 255, 255, 0.04); }

/* ── Banner aviso IA ── */
.ai-notice-banner {
	display: flex;
	gap: 10px;
	align-items: flex-start;
	margin-bottom: 10px;
	background: rgba(167, 139, 250, 0.07);
	border: 1px solid rgba(167, 139, 250, 0.3);
	border-radius: 8px;
	padding: 10px 14px;
}

.ai-notice-icon {
	flex-shrink: 0;
	color: #a78bfa;
	font-size: 0.85rem;
	margin-top: 2px;
}

.ai-notice-text {
	margin: 0;
	font-size: 11.5px;
	color: #768390;
	line-height: 1.5;
}

.ai-notice-lead   { color: #a78bfa; font-weight: 600; }
.ai-notice-action { color: #e6edf3; font-weight: 600; }

</style>
