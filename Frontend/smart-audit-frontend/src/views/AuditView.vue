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
						<small class="account-id" v-if="activeAccountLabel !== 'Sin cuenta seleccionada'">
							Account ID: {{ activeAccountLabel }}
						</small>
					</div>
					<div class="flex gap-2 flex-wrap">
						<Button
							label="Static Audit"
							icon="pi pi-search"
							:loading="isLoadingStatic"
							:disabled="isLoadingAny || !canRunAudit"
							@click="runAudit('static')"
						/>
						<Button
							label="Audit con IA"
							icon="pi pi-sparkles"
							severity="contrast"
							:loading="isLoadingAi"
							:disabled="isLoadingAny || !canRunAudit"
							@click="runAudit('ai')"
						/>
					</div>
				</div>
			</template>
		</Card>

		<Message v-if="!hasResources" severity="warn" :closable="false" class="mb-4">
			No hay recursos para auditar en la cuenta seleccionada.
		</Message>

		<Card v-if="hasResources" class="vuln-card">
			<template #content>
				<div class="vuln-header flex flex-column md:flex-row md:align-items-center md:justify-content-between gap-3 mb-3">
					<div>
						<h3 class="m-0">Vulnerabilidades</h3>
						<small class="text-muted">Total: {{ vulnerabilities.length }}</small>
					</div>
					<div class="filter-wrap flex gap-2 align-items-center">
						<label for="severityFilter" class="filter-label">Filtrar por severidad</label>
						<Select
							inputId="severityFilter"
							v-model="selectedSeverity"
							:options="severityOptions"
							optionLabel="label"
							optionValue="value"
							class="w-full md:w-14rem"
						/>
					</div>
				</div>

				<div v-if="filteredVulnerabilities.length" class="vuln-list flex flex-column gap-3">
					<div v-for="vuln in filteredVulnerabilities" :key="vuln.id" class="vuln-item">
						<div class="vuln-top flex flex-column md:flex-row md:align-items-center md:justify-content-between gap-2">
							<strong>{{ vuln.id }}</strong>
							<div class="flex gap-2 flex-wrap">
								<Tag :value="vuln.severity" :severity="mapSeverity(vuln.severity)" rounded />
								<Tag :value="vuln.origin" severity="secondary" rounded />
							</div>
						</div>
						<p class="vuln-description">{{ vuln.description }}</p>
						<div class="vuln-meta flex flex-wrap gap-3">
							<span><strong>Resource ID:</strong> {{ vuln.resource_id }}</span>
						</div>
					</div>
				</div>

				<Message v-else severity="info" :closable="false">
					No hay vulnerabilidades para la severidad seleccionada.
				</Message>
			</template>
		</Card>
	</div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useScanStore } from '../store/scanStore'
import { useAuditStore } from '../store/auditStore'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Message from 'primevue/message'
import Select from 'primevue/select'
import Tag from 'primevue/tag'

const scanStore = useScanStore()
const auditStore = useAuditStore()
const toast = useToast()

const vulnerabilities = computed(() => {
	if (Array.isArray(auditStore.auditResult)) return auditStore.auditResult
	if (Array.isArray(auditStore.audits)) return auditStore.audits
	return []
})
const selectedSeverity = ref('ALL')
const isLoadingStatic = ref(false)
const isLoadingAi = ref(false)

const severityOptions = [
	{ label: 'Todas', value: 'ALL' },
	{ label: 'Critical', value: 'CRITICAL' },
	{ label: 'High', value: 'HIGH' },
	{ label: 'Medium', value: 'MEDIUM' },
	{ label: 'Low', value: 'LOW' },
	{ label: 'Info', value: 'INFO' }
]

const resources = computed(() => scanStore.scanResult || {})

const totalResources = computed(() => {
	const src = resources.value
	const users = Array.isArray(src.users) ? src.users.length : 0
	const groups = Array.isArray(src.groups) ? src.groups.length : 0
	const roles = Array.isArray(src.roles) ? src.roles.length : 0
	const buckets = Array.isArray(src.buckets) ? src.buckets.length : 0
	const ec2 = Array.isArray(src.ec2) ? src.ec2.length : 0

	return users + groups + roles + buckets + ec2
})

const hasResources = computed(() => totalResources.value > 0)

const activeAccountLabel = computed(() => {
	const accountFromResult = scanStore.scanResult?.cloudAccount_id
	if (accountFromResult) return String(accountFromResult)
	if (scanStore.id) return String(scanStore.id)
	return 'Sin cuenta seleccionada'
})

const resolvedScanId = computed(() => {
	if (!scanStore.id) return null
	const idValue = String(scanStore.id)

	if (scanStore.scanIdByAccount?.[idValue]) {
		return scanStore.scanIdByAccount[idValue]
	}

	const byAccountValues = Object.values(scanStore.scanIdByAccount || {})
	if (byAccountValues.length === 1) {
		return byAccountValues[0]
	}

	return idValue
})

const canRunAudit = computed(() => Boolean(resolvedScanId.value) && hasResources.value)

const isLoadingAny = computed(() => isLoadingStatic.value || isLoadingAi.value)

const filteredVulnerabilities = computed(() => {
	if (selectedSeverity.value === 'ALL') return vulnerabilities.value
	return vulnerabilities.value.filter(
		(v) => String(v.severity || '').toUpperCase() === selectedSeverity.value
	)
})

const normalizeOrigin = (origin, mode) => {
	if (origin) return String(origin)
	return mode === 'ai' ? 'IA' : 'Static'
}

const normalizeVulnerability = (item, index, mode) => {
	const id = item?.id || item?._id || `VULN-${index + 1}`
	const description = item?.description || item?.detail || 'Sin descripcion'
	const severity = String(item?.severity || 'LOW').toUpperCase()
	const resourceId = item?.resource_id || item?.resourceId || 'N/A'
	const origin = normalizeOrigin(item?.origin, mode)

	return {
		id,
		description,
		severity,
		resource_id: resourceId,
		origin
	}
}

const mapSeverity = (severity) => {
	const normalized = String(severity || '').toUpperCase()
	if (normalized === 'CRITICAL' || normalized === 'HIGH') return 'danger'
	if (normalized === 'MEDIUM') return 'warn'
	if (normalized === 'LOW') return 'success'
	return 'info'
}

const runAudit = async (mode) => {
	const token = localStorage.getItem('token')
	if (!token) {
		toast.add({ severity: 'error', summary: 'Sesion', detail: 'Token no encontrado', life: 3000 })
		return
	}

	const scanId = resolvedScanId.value
	if (!scanId) {
		toast.add({ severity: 'warn', summary: 'Auditoria', detail: 'No hay scan_id disponible', life: 3000 })
		return
	}

	if (mode === 'static') {
		isLoadingStatic.value = true
	} else {
		isLoadingAi.value = true
	}

	try {
		const endpoint = mode === 'static'
			? "http://localhost:8000/cloud/static-audit"
      : "http://localhost:8000/cloud/ai-audit"
  

		const response = await fetch(endpoint, {
			method: 'POST',
			headers: {
        'content-type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify({ scan_id: scanId })
		})

		const data = await response.json()
		if (!response.ok) {
			throw new Error(data?.detail || 'No se pudo ejecutar la auditoria')
		}

		const incoming = Array.isArray(data?.vulnerabilities) ? data.vulnerabilities : []
		const normalized = incoming.map((item, index) => normalizeVulnerability(item, index, mode))
		auditStore.setAudits(data?.audit_id || '', normalized)

		toast.add({
			severity: 'success',
			summary: 'Auditoria completada',
			detail: `Se encontraron ${normalized.length} vulnerabilidades`,
			life: 3000
		})
	} catch (error) {
		auditStore.clearData()
		toast.add({
			severity: 'error',
			summary: 'Error en auditoria',
			detail: error.message,
			life: 3500
		})
	} finally {
		isLoadingStatic.value = false
		isLoadingAi.value = false
	}
}
</script>

<style scoped>
.audit-view {
	animation: fadeIn 0.35s ease-out;
}

@keyframes fadeIn {
	from { opacity: 0; transform: translateY(6px); }
	to { opacity: 1; transform: translateY(0); }
}

.page-icon {
	background: rgba(34, 197, 94, 0.12);
	border: 1px solid rgba(34, 197, 94, 0.3);
	color: #22c55e;
}

.page-header h2 {
	color: #e6edf3;
	font-size: 2rem;
	font-weight: 700;
}

.subtitle {
	color: #8b949e;
}

.account-card,
.vuln-card {
	background: #161b22;
	border: 1px solid rgba(34, 197, 94, 0.12);
	border-radius: 14px;
}

:deep(.p-card .p-card-content) {
	padding: 0.85rem;
}

.account-label {
	color: #8b949e;
	font-size: 0.875rem;
}

.account-value {
	color: #e6edf3;
	font-weight: 600;
	font-size: 1.1rem;
}

.account-id {
	color: #94a3b8;
}

.vuln-header h3 {
	color: #e6edf3;
}

.filter-label {
	color: #94a3b8;
	font-size: 0.9rem;
}

.text-muted {
	color: #94a3b8;
}

.vuln-item {
	border: 1px solid rgba(148, 163, 184, 0.2);
	border-radius: 10px;
	padding: 0.7rem;
	background: rgba(2, 6, 23, 0.45);
}

.vuln-description {
	margin: 0.65rem 0;
	color: #cbd5e1;
}

.vuln-meta {
	color: #94a3b8;
	font-size: 0.9rem;
}
</style>