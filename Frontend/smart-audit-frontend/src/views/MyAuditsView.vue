<template>
	<section class="my-audits-view">
		<header class="view-header">
			<h1>Mis auditorías</h1>
			<p>Selecciona una auditoría para ver su contenido.</p>
		</header>

		<div class="layout">
			<aside class="audits-list" aria-label="Listado de auditorías">
				<button
					v-for="audit in audits"
					:key="audit.id"
					class="audit-item"
					:class="{ active: selectedAudit?.id === audit.id }"
					@click="selectedAuditId = audit.id"
				>
					<div class="audit-item__title">{{ audit.title }}</div>
					<div class="audit-item__meta">
						<span>{{ audit.company }}</span>
						<span class="dot">•</span>
						<span>{{ audit.date }}</span>
					</div>
					<span class="status" :class="audit.status.toLowerCase()">{{ audit.status }}</span>
				</button>
			</aside>

			<article class="audit-content" v-if="selectedAudit">
				<h2>{{ selectedAudit.title }}</h2>
				<div class="content-meta">
					<p><strong>Empresa:</strong> {{ selectedAudit.company }}</p>
					<p><strong>Fecha:</strong> {{ selectedAudit.date }}</p>
					<p>
						<strong>Estado:</strong>
						<span class="status" :class="selectedAudit.status.toLowerCase()">{{ selectedAudit.status }}</span>
					</p>
				</div>

				<div class="content-section">
					<h3>Resumen</h3>
					<p>{{ selectedAudit.summary }}</p>
				</div>

				<div class="content-section">
					<h3>Hallazgos</h3>
					<ul>
						<li v-for="(finding, index) in selectedAudit.findings" :key="index">{{ finding }}</li>
					</ul>
				</div>
			</article>

			<article class="audit-content empty" v-else>
				<p>No hay auditorías disponibles.</p>
			</article>
		</div>
	</section>
</template>

<script setup>
import { computed, ref } from 'vue'

const audits = ref([
	{
		id: 1,
		title: 'Auditoría de Seguridad Web',
		company: 'TechNova S.L.',
		date: '12/03/2026',
		status: 'Completada',
		summary:
			'Se revisaron configuraciones críticas, autenticación y exposición de datos en aplicaciones web internas.',
		findings: [
			'Falta de cabeceras de seguridad en 2 servicios.',
			'Política de contraseñas mejorable en el portal de administración.',
			'Buenas prácticas generales en control de accesos.'
		]
	},
	{
		id: 2,
		title: 'Auditoría de Cumplimiento RGPD',
		company: 'Salamanca Data Group',
		date: '04/04/2026',
		status: 'En progreso',
		summary:
			'Evaluación de procesos de tratamiento de datos personales y mecanismos de consentimiento.',
		findings: [
			'Registro de actividades parcialmente actualizado.',
			'Falta homogeneizar textos legales entre plataformas.',
			'Plan de mejora en gestión de derechos ARSULIPO.'
		]
	},
	{
		id: 3,
		title: 'Auditoría de Infraestructura',
		company: 'InfraSys Europa',
		date: '20/04/2026',
		status: 'Pendiente',
		summary:
			'Análisis preliminar de redes, segmentación y configuración de servicios críticos.',
		findings: [
			'Pendiente validación de segmentación VLAN.',
			'Inventario de activos en actualización.',
			'Se requiere revisión de backups remotos.'
		]
	}
])

const selectedAuditId = ref(audits.value[0]?.id ?? null)

const selectedAudit = computed(() => audits.value.find((audit) => audit.id === selectedAuditId.value) ?? null)
</script>

<style scoped>
.my-audits-view {
	padding: 1.5rem;
	color: #1f2937;
}

.view-header h1 {
	margin: 0;
	font-size: 1.5rem;
	color: #0f172a;
}

.view-header p {
	margin: 0.35rem 0 1.2rem;
	color: #64748b;
}

.layout {
	display: grid;
	grid-template-columns: 320px 1fr;
	gap: 1rem;
}

.audits-list {
	background: #ffffff;
	border: 1px solid #e2e8f0;
	border-radius: 12px;
	padding: 0.6rem;
	max-height: 72vh;
	overflow: auto;
}

.audit-item {
	width: 100%;
	text-align: left;
	border: 1px solid #e2e8f0;
	border-radius: 10px;
	background: #f8fafc;
	padding: 0.75rem;
	margin-bottom: 0.6rem;
	cursor: pointer;
	transition: 0.2s ease;
}

.audit-item:hover {
	background: #eef2ff;
	border-color: #c7d2fe;
}

.audit-item.active {
	background: #e0e7ff;
	border-color: #6366f1;
}

.audit-item__title {
	font-weight: 600;
	color: #0f172a;
}

.audit-item__meta {
	margin-top: 0.3rem;
	font-size: 0.85rem;
	color: #64748b;
	display: flex;
	align-items: center;
	gap: 0.35rem;
}

.dot {
	color: #94a3b8;
}

.audit-content {
	background: #ffffff;
	border: 1px solid #e2e8f0;
	border-radius: 12px;
	padding: 1rem 1.25rem;
}

.audit-content h2 {
	margin: 0 0 0.85rem;
	color: #0f172a;
}

.content-meta p {
	margin: 0.25rem 0;
	color: #334155;
}

.content-section {
	margin-top: 1rem;
}

.content-section h3 {
	margin: 0 0 0.45rem;
	color: #1e293b;
}

.content-section p,
.content-section li {
	color: #475569;
}

.status {
	display: inline-block;
	margin-top: 0.45rem;
	font-size: 0.75rem;
	font-weight: 600;
	padding: 0.15rem 0.5rem;
	border-radius: 999px;
}

.status.completada {
	color: #166534;
	background: #dcfce7;
}

.status.en\ progreso {
	color: #854d0e;
	background: #fef3c7;
}

.status.pendiente {
	color: #1d4ed8;
	background: #dbeafe;
}

.empty {
	display: grid;
	place-items: center;
	color: #64748b;
}

@media (max-width: 900px) {
	.layout {
		grid-template-columns: 1fr;
	}
}
</style>
