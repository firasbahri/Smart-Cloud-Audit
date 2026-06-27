<template>
  <div class="cloud-accounts-view">
    <Toast />

    <div class="page-header flex align-items-center gap-3 mb-5">
      <Cloud :size="32" class="page-icon p-3 border-round-xl shadow-3" />
      <div>
        <h2 class="m-0">Cuentas de Nube</h2>
        <p class="subtitle m-0 mt-2">Gestiona tus cuentas de proveedores cloud vinculadas</p>
      </div>
    </div>

    <div class="accounts-section mb-5">
      <div class="flex justify-content-between align-items-center mb-4">
        <h3 class="m-0">Cuentas Vinculadas</h3>
        <Button
          label="Añadir Cuenta"
          icon="pi pi-plus"
          @click="showAddDialog = true"
          severity="success"
        />
      </div>

      <Card v-if="isLoadingAccounts && shouldShowLoading" class="empty-state">
        <template #content>
          <div class="flex flex-column align-items-center justify-content-center py-6 gap-3">
            <i class="pi pi-spin pi-spinner text-500" style="font-size: 2rem"></i>
            <h3 class="text-600 m-0">Cargando cuentas vinculadas...</h3>
          </div>
        </template>
      </Card>

      <div v-else-if="isLoadingAccounts" style="min-height: 12rem"></div>

      <Card v-else-if="cloudAccountsStore.accounts.length === 0" class="empty-state">
        <template #content>
          <div class="flex flex-column align-items-center justify-content-center py-6">
            <CloudOff :size="64" class="text-400 mb-3" />
            <h3 class="text-600 mb-2">No hay cuentas vinculadas</h3>
            <p class="text-500 mb-4">Añade tu primera cuenta de nube para comenzar</p>
            <Button
              label="Conectar Cuenta"
              icon="pi pi-plus"
              @click="showAddDialog = true"
            />
          </div>
        </template>
      </Card>

      <div v-else class="grid">
        <div
          v-for="account in cloudAccountsStore.accounts"
          :key="account.id"
          class="col-12 md:col-6 xl:col-4"
        >
          <Card class="account-card h-full">
            <template #content>
              <div class="flex flex-column gap-3">
                <div class="flex justify-content-between align-items-start">
                  <div class="flex align-items-center gap-3">
                    <component
                      :is="getProviderIcon(account.provider)"
                      :size="32"
                      class="provider-icon"
                      :class="'provider-' + account.provider.toLowerCase()"
                    />
                    <div class="account-detail">
                      <h4 class="m-0 mb-1">{{ account.name }}</h4>
                      <Tag
                        :value="account.provider"
                        :severity="getProviderSeverity(account.provider)"
                      />
                    </div>
                  </div>
                  <Button
                    icon="pi pi-ellipsis-v"
                    text
                    rounded
                    severity="secondary"
                    @click="toggleMenu($event, account)"
                  />
                  <Menu ref="menu" :model="menuItems" :popup="true" />
                </div>

                <Divider class="my-2" />

                <div class="account-details flex flex-column gap-2">
                  <div class="account-detail flex align-items-center gap-2 text-sm">
                    <Key :size="16" class="text-500" />
                    <span class="text-600 font-semibold">ARN:</span>
                    <span class="text-500 text-overflow-ellipsis overflow-hidden white-space-nowrap flex-1">
                      {{ account.identifier }}
                    </span>
                  </div>
                  <div class="account-detail flex align-items-center gap-2 text-sm">
                    <Calendar :size="16" class="text-500" />
                    <span class="text-600 font-semibold">Vinculada:</span>
                    <span class="text-500">{{ formatDate(account.created_at) }}</span>
                  </div>
                  <div class="account-detail flex align-items-center gap-2 text-sm">
                    <Activity :size="16" class="text-500" />
                    <span class="text-600 font-semibold">Estado:</span>
                    <Tag
                      :value="account.status"
                      :severity="getStatusSeverity(account.status)"
                      :icon="getStatusIcon(account.status)"
                    />
                  </div>
                </div>

                <Divider class="my-2" />

                <Button
                  :label="getScanButtonLabel(account.id)"
                  icon="pi pi-arrow-right"
                  severity="success"
                  class="w-full"
                  :loading="isAccountScanning(account.id)"
                  :disabled="isAccountScanning(account.id)"
                  @click="startScan(account)"
                />

                <ProgressBar
                  v-if="shouldShowProgressBar(account.id)"
                  :value="scanStore.scanProgressByAccount[account.id] || 0"
                  :showValue="true"
                  style="height: .8rem"
                />
              </div>
            </template>
          </Card>
        </div>
      </div>
    </div>

    <!-- ── Custom Add Account Modal ── -->
    <div v-if="showAddDialog" class="add-overlay" @click.self="closeDialog">
      <div class="add-stage" :class="{ 'guide-open': showGuide }">

        <!-- Form modal -->
        <div class="add-modal">
          <div class="add-modal__header">
            <div class="add-modal__title-group">
              <div class="add-modal__icon"><Cloud :size="15" /></div>
              <div>
                <div class="add-modal__title">Añadir Cuenta</div>
                <div class="add-modal__sub">Conecta una cuenta AWS</div>
              </div>
            </div>
            <button class="add-modal__close" @click="closeDialog">✕</button>
          </div>

          <div class="add-modal__body">
            <!-- Name -->
            <div class="af-field">
              <label class="af-label">Nombre de la cuenta</label>
              <input v-model="newAccount.name" class="af-input" :class="{ invalid: errors.name }" placeholder="ej. Producción AWS" />
              <span v-if="errors.name" class="af-error">{{ errors.name }}</span>
            </div>

            <!-- Provider -->
            <div class="af-field">
              <label class="af-label">Proveedor</label>
              <div class="prov-seg">
                <button :class="['prov-btn', { active: selectedProvider === 'AWS' }]" @click="selectedProvider = 'AWS'">AWS</button>
                <button class="prov-btn prov-btn--disabled" disabled title="Próximamente">Azure</button>
                <button class="prov-btn prov-btn--disabled" disabled title="Próximamente">GCP</button>
              </div>
            </div>

            <!-- Role ARN -->
            <div class="af-field">
              <div class="arn-label-row">
                <div class="arn-label-left">
                  <span class="af-label">Role ARN</span>
                  <span class="req-pill">requerido</span>
                </div>
                <button class="guide-link" @click="showGuide = !showGuide">
                  ¿Cómo lo consigo? {{ showGuide ? '←' : '→' }}
                </button>
              </div>
              <input v-model="newAccount.arn" class="af-input af-input--mono" :class="{ invalid: errors.arn }" placeholder="arn:aws:iam::..." />
              <span v-if="errors.arn" class="af-error">{{ errors.arn }}</span>
            </div>

            <!-- Regions -->
            <div class="af-field">
              <div class="region-label-row">
                <label class="af-label">Regiones AWS</label>
                <label class="auto-detect-toggle">
                  <input type="checkbox" v-model="autoDetectRegions" @change="autoDetectRegions && (newAccount.regions = [])" />
                  <span class="toggle-track"><span class="toggle-thumb" /></span>
                  <span class="toggle-label">Auto-detectar</span>
                </label>
              </div>
              <MultiSelect
                v-if="!autoDetectRegions"
                v-model="newAccount.regions"
                :options="AWS_REGIONS"
                optionLabel="label"
                optionValue="value"
                optionGroupLabel="label"
                optionGroupChildren="items"
                placeholder="Selecciona regiones..."
                display="chip"
                filter
                filterPlaceholder="Buscar región..."
                class="w-full"
                panelClass="add-account-multiselect-panel"
                :invalid="errors.regions"
              />
              <div v-if="autoDetectRegions" class="auto-detect-warn">
                <i class="pi pi-exclamation-triangle" style="font-size:0.75rem" />
                <span>Recorrerá ~30 regiones. El escaneo inicial será más lento.</span>
              </div>
              <span v-if="errors.regions && !autoDetectRegions" class="af-error">{{ errors.regions }}</span>
              <span class="af-hint">Recomendación: selecciona tus regiones manualmente — ayuda a reducir el tiempo de escaneo de EC2.</span>
            </div>

            <!-- Description -->
            <div class="af-field">
              <label class="af-label">Descripción <span class="af-optional">(opcional)</span></label>
              <textarea v-model="newAccount.description" class="af-textarea" rows="2" placeholder="Describe el propósito de esta cuenta..." />
              <div class="ai-ctx-hint-box">
                <i class="pi pi-sparkles" style="font-size:0.75rem;color:#a78bfa" />
                <span>Se usará como contexto en el <strong>Análisis IA</strong>.</span>
              </div>
            </div>
          </div>

          <div class="add-modal__footer">
            <button class="af-btn-cancel" @click="closeDialog">Cancelar</button>
            <button
              class="af-btn-primary"
              :disabled="isConnecting || !selectedProvider || !newAccount.name || !newAccount.arn"
              @click="addAccount"
            >
              <i v-if="isConnecting" class="pi pi-spin pi-spinner" style="font-size:0.8rem" />
              {{ isConnecting ? 'Conectando...' : 'Conectar cuenta' }}
            </button>
          </div>
        </div>

        <!-- ARN Guide Drawer -->
        <div class="arn-guide" :class="{ open: showGuide }">
          <div class="arn-guide__inner">
            <div class="arn-guide__header">
              <span class="arn-guide__title">Cómo obtener tu Role ARN</span>
              <button class="add-modal__close" @click="showGuide = false">✕</button>
            </div>

            <div class="guide-stepper">
              <button
                v-for="n in 5"
                :key="n"
                :class="['stepper-seg', { done: n <= guideStep }]"
                @click="guideStep = n"
                :title="`Paso ${n}`"
              />
            </div>

            <div class="guide-step">
              <div class="guide-step__head">
                <div class="step-circle">{{ guideStep }}</div>
                <span class="step-title">{{ GUIDE_STEPS[guideStep - 1].title }}</span>
                <span class="step-counter">{{ guideStep }}/5</span>
              </div>

              <p class="step-desc">{{ GUIDE_STEPS[guideStep - 1].description }}</p>

              <div class="copy-box">
                <span class="copy-value">{{ GUIDE_STEPS[guideStep - 1].copyValue }}</span>
                <button class="copy-btn" @click="copyGuideStep(guideStep)">
                  {{ copiedStep === guideStep ? '✓ Copiado' : '📋 Copiar' }}
                </button>
              </div>

              <div class="step-img-wrap">
                <img
                  v-if="!failedGuideImages[guideStep - 1]"
                  :src="`/assets/arn-guide/step-${guideStep}.png`"
                  :alt="GUIDE_STEPS[guideStep - 1].title"
                  class="step-img"
                  @error="failedGuideImages[guideStep - 1] = true"
                />
                <div v-else class="step-img-placeholder">
                  <i class="pi pi-image" style="font-size:1.4rem;color:#4d5566" />
                  <span>{{ GUIDE_STEPS[guideStep - 1].placeholder }}</span>
                </div>
              </div>
            </div>

            <div class="guide-nav">
              <button class="af-btn-ghost" :disabled="guideStep === 1" @click="guideStep--">← Anterior</button>
              <button v-if="guideStep < 5" class="af-btn-secondary" @click="guideStep++">Siguiente →</button>
              <button v-else class="af-btn-primary af-btn-primary--sm" @click="showGuide = false">✓ Ya tengo mi ARN</button>
            </div>
          </div>
        </div>

      </div>
    </div>

    <Dialog
      v-model:visible="showScanConfirmDialog"
      modal
      header="Scan reciente detectado"
      :style="{ width: '28rem' }"
    >
      <div class="flex align-items-center gap-3 mb-3">
        <i class="pi pi-exclamation-triangle text-yellow-500" style="font-size: 2rem" />
        <p class="m-0">
          Ya tienes un escaneo de menos de <strong>24 horas</strong> para esta cuenta.
          ¿Quieres lanzar uno nuevo igualmente?
        </p>
      </div>
      <template #footer>
        <Button label="Cancelar" icon="pi pi-times" text @click="cancelScan" />
        <Button label="Sí, escanear" icon="pi pi-refresh" severity="warning" @click="confirmScan" />
      </template>
    </Dialog>

    <Dialog
      v-model:visible="showDeleteDialog"
      modal
      header="Eliminar Cuenta"
      :style="{ width: '30rem' }"
    >
      <div class="flex align-items-center gap-3 mb-3">
        <AlertTriangle :size="48" class="text-orange-500" />
        <p class="m-0">
          ¿Estás seguro de que deseas eliminar la cuenta <strong>{{ selectedAccount?.name }}</strong>?
        </p>
      </div>
      <p class="text-500 text-sm">Esta acción no se puede deshacer.</p>

      <template #footer>
        <Button label="Cancelar" icon="pi pi-times" text @click="showDeleteDialog = false" />
        <Button label="Eliminar" icon="pi pi-trash" severity="danger" @click="confirmDelete" />
      </template>
    </Dialog>

    <!-- ── Custom Details Modal ── -->
    <div v-if="showDetailsDialog" class="add-overlay" @click.self="showDetailsDialog = false">
      <div class="add-modal add-modal--wide">
        <div class="add-modal__header">
          <div class="add-modal__title-group">
            <div class="add-modal__icon">
              <component :is="getProviderIcon(selectedAccount?.provider)" :size="15" />
            </div>
            <div>
              <div class="add-modal__title">{{ selectedAccount?.name }}</div>
              <div class="add-modal__sub">Detalles de la cuenta</div>
            </div>
          </div>
          <button class="add-modal__close" @click="showDetailsDialog = false">✕</button>
        </div>

        <div v-if="selectedAccount" class="add-modal__body">
          <div class="af-field">
            <div class="flex gap-2">
              <Tag :value="selectedAccount.provider" :severity="getProviderSeverity(selectedAccount.provider)" />
              <Tag
                :value="selectedAccount.status || 'Sin estado'"
                :severity="getStatusSeverity(selectedAccount.status)"
                :icon="getStatusIcon(selectedAccount.status)"
              />
            </div>
          </div>

          <div class="af-field">
            <label class="af-label">Role ARN</label>
            <div class="af-readonly af-readonly--mono">{{ selectedAccount.identifier || selectedAccount.arn || '-' }}</div>
          </div>

          <div class="af-field">
            <label class="af-label">ID de Cuenta</label>
            <div class="af-readonly">{{ selectedAccount.account_id || '-' }}</div>
          </div>

          <div class="af-field">
            <label class="af-label">Fecha de Vinculación</label>
            <div class="af-readonly">{{ selectedAccount.created_at ? formatDate(selectedAccount.created_at) : '-' }}</div>
          </div>

          <div class="af-field">
            <label class="af-label">Regiones AWS</label>
            <div class="af-readonly">
              {{ (selectedAccount.regions && selectedAccount.regions.length) ? selectedAccount.regions.join(', ') : 'Auto-detectar (todas las regiones)' }}
            </div>
          </div>

          <div class="af-field">
            <label class="af-label">Descripción</label>
            <div class="af-readonly">{{ selectedAccount.description || 'Sin descripción' }}</div>
          </div>
        </div>

        <div class="add-modal__footer">
          <button class="af-btn-cancel" @click="showDetailsDialog = false">Cerrar</button>
        </div>
      </div>
    </div>

    <!-- ── Custom Edit Modal ── -->
    <div v-if="showEditDialog" class="add-overlay" @click.self="closeEditDialog">
      <div class="add-modal add-modal--wide">
        <div class="add-modal__header">
          <div class="add-modal__title-group">
            <div class="add-modal__icon"><Cloud :size="15" /></div>
            <div>
              <div class="add-modal__title">Editar Cuenta</div>
              <div class="add-modal__sub">{{ editAccount.name || 'Cuenta de nube' }}</div>
            </div>
          </div>
          <button class="add-modal__close" @click="closeEditDialog">✕</button>
        </div>

        <div class="add-modal__body">
          <!-- Name -->
          <div class="af-field">
            <label class="af-label">Nombre de la cuenta</label>
            <input v-model="editAccount.name" class="af-input" :class="{ invalid: editErrors.name }" placeholder="Nombre de la cuenta" />
            <span v-if="editErrors.name" class="af-error">{{ editErrors.name }}</span>
          </div>

          <!-- ARN (read-only) -->
          <div class="af-field">
            <label class="af-label">Role ARN</label>
            <div class="af-readonly af-readonly--mono">{{ editAccount.arn }}</div>
            <span class="af-hint">El ARN no puede modificarse. Elimina y vuelve a conectar la cuenta si necesitas cambiarlo.</span>
          </div>

          <!-- Regions -->
          <div class="af-field">
            <div class="region-label-row">
              <label class="af-label">Regiones AWS</label>
              <label class="auto-detect-toggle">
                <input type="checkbox" v-model="editAutoDetectRegions" @change="editAutoDetectRegions && (editAccount.regions = [])" />
                <span class="toggle-track"><span class="toggle-thumb" /></span>
                <span class="toggle-label">Auto-detectar</span>
              </label>
            </div>
            <MultiSelect
              v-if="!editAutoDetectRegions"
              v-model="editAccount.regions"
              :options="AWS_REGIONS"
              optionLabel="label"
              optionValue="value"
              optionGroupLabel="label"
              optionGroupChildren="items"
              placeholder="Selecciona regiones..."
              display="chip"
              filter
              filterPlaceholder="Buscar región..."
              class="w-full"
              panelClass="add-account-multiselect-panel"
              :invalid="editErrors.regions"
            />
            <div v-if="editAutoDetectRegions" class="auto-detect-warn">
              <i class="pi pi-exclamation-triangle" style="font-size:0.75rem" />
              <span>El próximo escaneo recorrerá ~30 regiones.</span>
            </div>
            <span v-if="editErrors.regions && !editAutoDetectRegions" class="af-error">{{ editErrors.regions }}</span>
            <span class="af-hint">Recomendación: selecciona tus regiones manualmente — ayuda a reducir el tiempo de escaneo de EC2.</span>
          </div>

          <!-- Description -->
          <div class="af-field">
            <label class="af-label">Descripción <span class="af-optional">(opcional)</span></label>
            <textarea v-model="editAccount.description" class="af-textarea" rows="2" placeholder="Describe el propósito de esta cuenta..." />
            <div class="ai-ctx-hint-box">
              <i class="pi pi-sparkles" style="font-size:0.75rem;color:#a78bfa" />
              <span>Se usará como contexto en el <strong>Análisis IA</strong>.</span>
            </div>
          </div>
        </div>

        <div class="add-modal__footer">
          <button class="af-btn-cancel" @click="closeEditDialog">Cancelar</button>
          <button class="af-btn-primary" :disabled="!editAccount.name" @click="saveEdit">Guardar cambios</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useCloudAccountsStore } from '../store/cloudAccountsStore'
import { useScanStore } from '../store/scanStore'
import {
  Cloud,
  CloudOff,
  Key,
  Calendar,
  Activity,
  AlertTriangle,
  Info as InfoIcon,
  Cloud as CloudIcon
} from 'lucide-vue-next'
import Aws from 'lucide-vue-next/dist/esm/icons/cloud'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Dialog from 'primevue/dialog'
import Tag from 'primevue/tag'
import Divider from 'primevue/divider'
import Menu from 'primevue/menu'
import Toast from 'primevue/toast'
import ProgressBar from 'primevue/progressbar'
import MultiSelect from 'primevue/multiselect'
import { buildApiUrl } from '../utils/api'

const AWS_REGIONS = [
  {
    label: '🇺🇸 Estados Unidos',
    items: [
      { label: 'us-east-1 — N. Virginia', value: 'us-east-1' },
      { label: 'us-east-2 — Ohio', value: 'us-east-2' },
      { label: 'us-west-1 — N. California', value: 'us-west-1' },
      { label: 'us-west-2 — Oregon', value: 'us-west-2' },
    ]
  },
  {
    label: '🇪🇺 Europa',
    items: [
      { label: 'eu-west-1 — Irlanda', value: 'eu-west-1' },
      { label: 'eu-west-2 — Londres', value: 'eu-west-2' },
      { label: 'eu-west-3 — París', value: 'eu-west-3' },
      { label: 'eu-central-1 — Frankfurt', value: 'eu-central-1' },
      { label: 'eu-central-2 — Zúrich', value: 'eu-central-2' },
      { label: 'eu-north-1 — Estocolmo', value: 'eu-north-1' },
      { label: 'eu-south-1 — Milán', value: 'eu-south-1' },
      { label: 'eu-south-2 — España', value: 'eu-south-2' },
    ]
  },
  {
    label: '🌏 Asia Pacífico',
    items: [
      { label: 'ap-southeast-1 — Singapur', value: 'ap-southeast-1' },
      { label: 'ap-southeast-2 — Sídney', value: 'ap-southeast-2' },
      { label: 'ap-southeast-3 — Yakarta', value: 'ap-southeast-3' },
      { label: 'ap-southeast-4 — Melbourne', value: 'ap-southeast-4' },
      { label: 'ap-northeast-1 — Tokio', value: 'ap-northeast-1' },
      { label: 'ap-northeast-2 — Seúl', value: 'ap-northeast-2' },
      { label: 'ap-northeast-3 — Osaka', value: 'ap-northeast-3' },
      { label: 'ap-south-1 — Bombay', value: 'ap-south-1' },
      { label: 'ap-south-2 — Hyderabad', value: 'ap-south-2' },
      { label: 'ap-east-1 — Hong Kong', value: 'ap-east-1' },
    ]
  },
  {
    label: '🌎 América',
    items: [
      { label: 'ca-central-1 — Canadá Central', value: 'ca-central-1' },
      { label: 'ca-west-1 — Canadá Oeste', value: 'ca-west-1' },
      { label: 'sa-east-1 — São Paulo', value: 'sa-east-1' },
      { label: 'mx-central-1 — México', value: 'mx-central-1' },
    ]
  },
  {
    label: '🌍 Oriente Medio y África',
    items: [
      { label: 'me-south-1 — Baréin', value: 'me-south-1' },
      { label: 'me-central-1 — EAU', value: 'me-central-1' },
      { label: 'il-central-1 — Israel', value: 'il-central-1' },
      { label: 'af-south-1 — Ciudad del Cabo', value: 'af-south-1' },
    ]
  },
]

const toast = useToast()
const cloudAccountsStore = useCloudAccountsStore()
const scanStore = useScanStore()

const isLoadingAccounts = ref(true)
const shouldShowLoading = ref(false)
let loadingIndicatorTimer = null

const showAddDialog = ref(false)
const showEditDialog = ref(false)
const showDeleteDialog = ref(false)
const showDetailsDialog = ref(false)
const selectedProvider = ref(null)
const selectedAccount = ref(null)
const menu = ref()


const autoDetectRegions = ref(false)
const isConnecting = ref(false)
const showGuide = ref(false)
const guideStep = ref(1)
const copiedStep = ref(null)
const failedGuideImages = ref([false, false, false, false, false])

const SMART_AUDIT_ACCOUNT_ID = import.meta.env.VITE_SMART_AUDIT_ACCOUNT_ID || '453195924129'

const GUIDE_STEPS = [
  {
    title: 'Crea un nuevo rol en IAM',
    description: "En la consola de AWS ve a IAM → Roles → 'Create role' y selecciona el tipo de entidad de confianza 'AWS account'.",
    copyValue: 'https://console.aws.amazon.com/iam/home#/roles',
    placeholder: "IAM → Roles → 'Create role' → tipo de entidad 'AWS account'",
  },
  {
    title: 'Autoriza la cuenta de Smart Audit',
    description: "Marca 'Another AWS account' e introduce nuestro ID de cuenta. Esto nos permite leer tus recursos de forma segura.",
    copyValue: SMART_AUDIT_ACCOUNT_ID,
    placeholder: "Marcar 'Another AWS account' e introducir el ID de cuenta",
  },
  {
    title: 'Asigna permisos de solo lectura',
    description: "Busca y selecciona la política gestionada 'ReadOnlyAccess'. Smart Audit nunca modifica tus recursos — solo los lee.",
    copyValue: 'ReadOnlyAccess',
    placeholder: "Buscar y seleccionar la política 'ReadOnlyAccess'",
  },
  {
    title: 'Ponle un nombre al rol',
    description: 'Dale un nombre identificable al rol para reconocerlo más tarde, y confirma la creación.',
    copyValue: 'SmartAuditRole',
    placeholder: 'Campo de nombre del rol y confirmar creación',
  },
  {
    title: 'Copia el ARN del rol',
    description: 'Abre el rol recién creado. En la parte superior verás su ARN — cópialo y pégalo en el campo del formulario.',
    copyValue: `arn:aws:iam::${SMART_AUDIT_ACCOUNT_ID}:role/SmartAuditRole`,
    placeholder: 'Pantalla del rol creado mostrando su ARN arriba',
  },
]

const copyGuideStep = async (step) => {
  try {
    await navigator.clipboard.writeText(GUIDE_STEPS[step - 1].copyValue)
    copiedStep.value = step
    setTimeout(() => { copiedStep.value = null }, 2000)
  } catch { /* clipboard not available */ }
}

const newAccount = reactive({
  name: '',
  arn: '',
  description: '',
  regions: []
})

const editAccount = reactive({
  id: null,
  name: '',
  arn: '',
  description: '',
  provider: '',
  regions: []
})

const editAutoDetectRegions = ref(false)

const errors = reactive({
  name: '',
  arn: '',
  regions: ''
})

const editErrors = reactive({
  name: '',
  regions: ''
})

onMounted(async () => {
  loadingIndicatorTimer = setTimeout(() => {
    if (isLoadingAccounts.value) {
      shouldShowLoading.value = true
    }
  }, 250)

  try {
    await cloudAccountsStore.loadAccounts()
  } finally {
    isLoadingAccounts.value = false
    shouldShowLoading.value = false
    if (loadingIndicatorTimer) {
      clearTimeout(loadingIndicatorTimer)
      loadingIndicatorTimer = null
    }
  }
})

onUnmounted(() => {
  if (loadingIndicatorTimer) {
    clearTimeout(loadingIndicatorTimer)
    loadingIndicatorTimer = null
  }
})

const menuItems = ref([
  {
    label: 'Ver detalles',
    icon: 'pi pi-eye',
    command: () => openDetails(selectedAccount.value)
  },
  {
    label: 'Editar',
    icon: 'pi pi-pencil',
    command: () => openEdit(selectedAccount.value)
  },
  {
    separator: true
  },
  {
    label: 'Eliminar',
    icon: 'pi pi-trash',
    command: () => {
      showDeleteDialog.value = true
    }
  }
])

const getProviderIcon = (provider) => {
  const icons = {
    AWS: Aws,
    Azure: CloudIcon,
    GCP: CloudIcon
  }
  return icons[provider] || CloudIcon
}

const getProviderSeverity = (provider) => {
  const severities = {
    AWS: 'warning',
    Azure: 'info',
    GCP: 'danger'
  }
  return severities[provider] || 'secondary'
}

const getStatusSeverity = (status) => {
  if (status === 'Activa') return 'success'
  if (status === 'Inactiva') return 'secondary'
  return 'info'
}

const getStatusIcon = (status) => {
  if (status === 'Activa') return 'pi pi-check'
  if (status === 'Inactiva') return 'pi pi-pause-circle'
  return 'pi pi-info-circle'
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('es-ES', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const toggleMenu = (event, account) => {
  selectedAccount.value = account
  menu.value[0].toggle(event)
}

const openDetails = (account) => {
  if (!account) return
  selectedAccount.value = account
  showDetailsDialog.value = true
}

const validateForm = () => {
  errors.name = ''
  errors.arn = ''
  errors.regions = ''
  let isValid = true

  if (!newAccount.name.trim()) {
    errors.name = 'El nombre es requerido'
    isValid = false
  }

  if (!newAccount.arn.trim()) {
    errors.arn = 'El ARN es requerido'
    isValid = false
  } else if (!/^arn:aws:iam::\d{12}:role\/.+$/.test(newAccount.arn.trim())) {
    errors.arn = 'Formato: arn:aws:iam::<ID_cuenta>:role/<nombre>'
    isValid = false
  }

  if (!autoDetectRegions.value && !newAccount.regions.length) {
    errors.regions = 'Selecciona al menos una región'
    isValid = false
  }

  return isValid
}

const closeDialog = () => {
  showAddDialog.value = false
  showGuide.value = false
  guideStep.value = 1
  selectedProvider.value = null
  newAccount.name = ''
  newAccount.arn = ''
  newAccount.description = ''
  newAccount.regions = []
  autoDetectRegions.value = false
  errors.name = ''
  errors.arn = ''
  errors.regions = ''
}

const isAccountScanning = (accountId) => {
  return Boolean(scanStore.scanningAccounts[accountId])
}

const getScanButtonLabel = (accountId) => {
  const progress = Number(scanStore.scanProgressByAccount[accountId] ?? 0)
  if (isAccountScanning(accountId)) return 'Escaneando...'
  if (progress === 100) return 'Escaneo completado'
  return 'Escanear'
}

const shouldShowProgressBar = (accountId) => {
  const progress = Number(scanStore.scanProgressByAccount[accountId] ?? 0)
  return progress > 0 && progress <= 100
}


const addAccount = async () => {
  if (!validateForm()) return

  isConnecting.value = true
  try {
    const token = localStorage.getItem('token')
    const API_URL = buildApiUrl('/cloud/register_cloud')
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        name: newAccount.name,
        provider: selectedProvider.value,
        arn: newAccount.arn,
        description: newAccount.description,
        regions: newAccount.regions
      })
    })

    const data = await response.json()
    if (!response.ok) throw new Error(data.detail)

    const accountData = {
      id: data.id,
      name: newAccount.name,
      provider: selectedProvider.value,
      identifier: newAccount.arn,
      description: newAccount.description,
      created_at: new Date().toISOString()
    }

    cloudAccountsStore.addAccount(accountData)
    toast.add({
      severity: 'success',
      summary: 'Cuenta Añadida',
      detail: `La cuenta ${accountData.name} se ha vinculado exitosamente`,
      life: 3000
    })

  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.message,
      life: 3000
    })
    return
  } finally {
    isConnecting.value = false
  }

  closeDialog()
}


const showScanConfirmDialog = ref(false)
const pendingScanAccount = ref(null)

const startScan = (account) => {
  cloudAccountsStore.selectAccount(account)
  if (scanStore.esScanReciente(account.id)) {
    pendingScanAccount.value = account
    showScanConfirmDialog.value = true
    return
  }
  executeScan(account)
}

const confirmScan = () => {
  showScanConfirmDialog.value = false
  executeScan(pendingScanAccount.value)
  pendingScanAccount.value = null
}

const cancelScan = () => {
  showScanConfirmDialog.value = false
  pendingScanAccount.value = null
}

const executeScan = async (account) => {
  if (account.provider === 'AWS') {
    
    const token = localStorage.getItem('token')
    try {
      const URL = buildApiUrl('/cloud/start_scan')
      const response = await fetch(URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ id: account.id })
      })

      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'No se pudo iniciar el escaneo')

      const scanId = data.scan_id
      scanStore.startSSE(scanId, String(account.id))
    } catch (error) {
      scanStore.failAccountScan(String(account.id))
      toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 })
    }
  }
}

const confirmDelete = () => {
  try {
    const token = localStorage.getItem('token')
    const API_URL = buildApiUrl('/cloud/delete_cloud_data')
    fetch(API_URL, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        id: selectedAccount.value.id
      })
    })
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.message,
      life: 3000
    })
    return
  }

  cloudAccountsStore.deleteAccount(selectedAccount.value.id)
  showDeleteDialog.value = false
  selectedAccount.value = null

  toast.add({
    severity: 'info',
    summary: 'Cuenta Eliminada',
    detail: 'La cuenta ha sido eliminada correctamente',
    life: 3000
  })
}

const openEdit = (account) => {
  editAccount.id = account.id
  editAccount.name = account.name
  editAccount.provider = account.provider
  editAccount.arn = account.arn || account.identifier
  editAccount.description = account.description || ''
  editAccount.regions = [...(account.regions || [])]
  editAutoDetectRegions.value = !account.regions || account.regions.length === 0
  editErrors.name = ''
  editErrors.regions = ''
  showEditDialog.value = true
}

const closeEditDialog = () => {
  showEditDialog.value = false
}

const validateEditForm = () => {
  editErrors.name = ''
  editErrors.regions = ''
  let isValid = true

  if (!editAccount.name.trim()) {
    editErrors.name = 'El nombre es requerido'
    isValid = false
  }

  if (!editAutoDetectRegions.value && !editAccount.regions.length) {
    editErrors.regions = 'Selecciona al menos una región'
    isValid = false
  }

  return isValid
}

const saveEdit = async () => {
  if (!validateEditForm()) return

  const regionsToSave = editAutoDetectRegions.value ? [] : editAccount.regions

  try {
    const token = localStorage.getItem('token')
    const API_URL = buildApiUrl('/cloud/update_cloud_data')
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        id: editAccount.id,
        name: editAccount.name,
        description: editAccount.description,
        regions: regionsToSave
      })
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail)
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.message,
      life: 3000
    })
    return
  }

  const accountData = {
    name: editAccount.name,
    provider: editAccount.provider,
    arn: editAccount.arn,
    description: editAccount.description,
    regions: regionsToSave
  }

  cloudAccountsStore.updateAccount(editAccount.id, accountData)

  toast.add({
    severity: 'success',
    summary: 'Cuenta Actualizada',
    detail: `La cuenta ${accountData.name} se ha actualizado exitosamente`,
    life: 3000
  })

  showEditDialog.value = false
}


</script>

<style scoped>
.cloud-accounts-view {
  padding: 1.5rem;
}

.page-header {
  animation: fadeIn 0.5s ease-in;
}

.page-icon {
  background: linear-gradient(135deg, var(--p-primary-500), var(--p-primary-600));
  color: white;
}

.subtitle {
  color: var(--p-text-muted-color);
  font-size: 0.95rem;
}

.account-detail {
  margin: 0;
  color: #8b949e;
  font-size: 0.875rem;
  font-weight: 600;
  letter-spacing: 0.05em;
}

.account-card {
  background: #161b22;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(34, 197, 94, 0.1);
  transition: all 0.3s ease;
  animation: slideUp 0.6s ease-out both;
  position: relative;
  overflow: hidden;
}

.account-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, transparent, #22c55e, transparent);
  transform: translateX(-100%);
  transition: transform 0.6s ease;
}

.account-card:hover::before {
  transform: translateX(100%);
}

.account-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px -4px rgba(0, 0, 0, 0.4);
  border-color: rgba(34, 197, 94, 0.3);
}

.empty-state {
  background: #161b22;
  border-radius: 16px;
  border: 2px dashed rgba(34, 197, 94, 0.2);
}

.provider-selection .provider-option {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.provider-selection .provider-option:not(.disabled):hover {
  border-color: var(--p-primary-color);
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.provider-selection .provider-option.selected {
  border-color: var(--p-primary-color);
  background: var(--p-primary-50);
}

.provider-selection .provider-option.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.ai-ctx-hint-box {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  background: rgba(167, 139, 250, 0.06);
  border: 1px solid rgba(167, 139, 250, 0.2);
  border-radius: 7px;
  padding: 8px 10px;
  font-size: 0.78rem;
  color: #c4b5fd;
  line-height: 1.45;
}

.ai-ctx-hint-box strong { color: #a78bfa; }

/* ════════════════════════════════════════
   ADD ACCOUNT MODAL — custom overlay
   ════════════════════════════════════════ */
.add-overlay {
  position: fixed; inset: 0; z-index: 1100;
  background: rgba(0,0,0,0.55);
  display: flex; align-items: center; justify-content: center;
}

.add-stage {
  display: flex;
  align-items: stretch;
  max-height: 90vh;
  box-shadow: 0 20px 60px rgba(0,0,0,0.6);
  border-radius: 14px;
}

/* Form modal */
.add-modal {
  width: 460px;
  background: #161b22;
  border: 1px solid #2d333b;
  border-radius: 14px;
  display: flex; flex-direction: column;
  overflow: hidden;
  transition: border-radius 0.3s ease;
  flex-shrink: 0;
}
.add-stage.guide-open .add-modal {
  border-radius: 14px 0 0 14px;
  border-right: none;
}

.add-modal--wide { width: 560px; }

.add-modal__header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #2d333b;
  flex-shrink: 0;
}
.add-modal__title-group { display: flex; align-items: center; gap: 10px; }
.add-modal__icon {
  width: 30px; height: 30px; border-radius: 8px;
  background: rgba(63,185,80,0.12); border: 1px solid rgba(63,185,80,0.25);
  display: flex; align-items: center; justify-content: center;
  color: #3fb950; flex-shrink: 0;
}
.add-modal__title { font-size: 14px; font-weight: 600; color: #e6edf3; }
.add-modal__sub   { font-size: 11px; color: #768390; margin-top: 1px; }
.add-modal__close {
  background: transparent; border: none; color: #4d5566;
  font-size: 14px; cursor: pointer; padding: 4px 6px; border-radius: 5px;
  transition: background 0.1s, color 0.1s; font-family: inherit; line-height: 1;
}
.add-modal__close:hover { background: rgba(255,255,255,0.06); color: #e6edf3; }

.add-modal__body {
  flex: 1; overflow-y: auto; padding: 16px;
  display: flex; flex-direction: column; gap: 14px;
}
.add-modal__body::-webkit-scrollbar { width: 4px; }
.add-modal__body::-webkit-scrollbar-thumb { background: #2d333b; border-radius: 2px; }

.add-modal__footer {
  padding: 12px 16px; border-top: 1px solid #2d333b;
  display: flex; gap: 8px; justify-content: flex-end; flex-shrink: 0;
}

/* Form fields */
.af-field  { display: flex; flex-direction: column; gap: 5px; }
.af-label  { font-size: 11px; font-weight: 600; color: #8b949e; text-transform: uppercase; letter-spacing: 0.04em; }
.af-optional { color: #4d5566; font-weight: 400; text-transform: none; letter-spacing: 0; }
.af-error  { font-size: 11px; color: #f85149; }
.af-hint   { font-size: 11px; color: #4d5566; }

.af-readonly {
  background: #0d1117; border: 1px solid #2d333b; border-radius: 6px;
  padding: 8px 10px; font-size: 12px; color: #8b949e;
  word-break: break-all;
}
.af-readonly--mono { font-family: 'Consolas','Monaco',monospace; font-size: 11px; }

.af-input {
  background: #1c2128; border: 1px solid #2d333b; color: #e6edf3;
  border-radius: 7px; padding: 8px 11px; font-size: 12px; font-family: inherit;
  outline: none; transition: border-color 0.15s;
}
.af-input:focus         { border-color: #3fb950; }
.af-input.invalid       { border-color: #f85149; }
.af-input--mono         { font-family: 'Consolas','Monaco',monospace; font-size: 11px; }

.af-textarea {
  background: #1c2128; border: 1px solid #2d333b; color: #e6edf3;
  border-radius: 7px; padding: 8px 11px; font-size: 12px; font-family: inherit;
  outline: none; resize: none; transition: border-color 0.15s; line-height: 1.5;
}
.af-textarea:focus { border-color: #3fb950; }

/* Provider segmented buttons */
.prov-seg {
  display: flex; border: 1px solid #2d333b; border-radius: 8px; overflow: hidden;
  background: #1c2128;
}
.prov-btn {
  flex: 1; padding: 7px 0; background: transparent; border: none;
  border-right: 1px solid #2d333b; color: #768390; font-size: 12px;
  font-weight: 500; font-family: inherit; cursor: pointer; transition: all 0.15s;
}
.prov-btn:last-child { border-right: none; }
.prov-btn.active { background: rgba(63,185,80,0.12); border-color: rgba(63,185,80,0.3) !important; color: #3fb950; font-weight: 600; }
.prov-btn--disabled { opacity: 0.4; cursor: not-allowed; }

/* ARN label row */
.arn-label-row  { display: flex; align-items: center; justify-content: space-between; }
.arn-label-left { display: flex; align-items: center; gap: 7px; }
.req-pill {
  font-size: 9px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;
  background: #1c2128; border: 1px solid #2d333b; color: #4d5566;
  padding: 1px 6px; border-radius: 999px;
}
.guide-link {
  background: transparent; border: none; padding: 0; cursor: pointer;
  color: #3fb950; font-size: 11px; font-weight: 600; font-family: inherit;
  transition: opacity 0.15s;
}
.guide-link:hover { opacity: 0.75; }

/* Footer buttons */
.af-btn-cancel {
  background: transparent; border: 1px solid #2d333b; color: #768390;
  padding: 7px 14px; border-radius: 7px; font-size: 12px; font-family: inherit;
  cursor: pointer; transition: border-color 0.12s, color 0.12s;
}
.af-btn-cancel:hover { border-color: #4d5566; color: #e6edf3; }

.af-btn-primary {
  display: inline-flex; align-items: center; gap: 6px;
  background: #3fb950; border: none; color: #0d1117;
  padding: 7px 16px; border-radius: 7px; font-size: 12px; font-weight: 600;
  font-family: inherit; cursor: pointer; transition: background 0.12s;
}
.af-btn-primary:hover:not(:disabled) { background: #3da847; }
.af-btn-primary:disabled { opacity: 0.45; cursor: not-allowed; }
.af-btn-primary--sm { padding: 6px 14px; }

.af-btn-secondary {
  background: #1c2128; border: 1px solid #2d333b; color: #c9d1d9;
  padding: 6px 14px; border-radius: 7px; font-size: 12px; font-family: inherit;
  cursor: pointer; transition: background 0.12s;
}
.af-btn-secondary:hover { background: #2d333b; }

.af-btn-ghost {
  background: transparent; border: none; color: #768390;
  padding: 6px 10px; font-size: 12px; font-family: inherit; cursor: pointer;
  transition: color 0.12s;
}
.af-btn-ghost:hover:not(:disabled) { color: #e6edf3; }
.af-btn-ghost:disabled { opacity: 0.3; cursor: default; }

/* ── ARN Guide Drawer ── */
.arn-guide {
  width: 0; overflow: hidden;
  background: #161b22; border: 1px solid #2d333b; border-left: none;
  border-radius: 0 14px 14px 0;
  transition: width 0.3s ease;
  flex-shrink: 0;
}
.arn-guide.open { width: 380px; }

.arn-guide__inner {
  width: 380px; height: 100%;
  display: flex; flex-direction: column; overflow: hidden;
}

.arn-guide__header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; border-bottom: 1px solid #2d333b; flex-shrink: 0;
}
.arn-guide__title { font-size: 13px; font-weight: 600; color: #e6edf3; }

/* Stepper */
.guide-stepper {
  display: flex; gap: 4px; padding: 12px 16px 8px; flex-shrink: 0;
}
.stepper-seg {
  flex: 1; height: 4px; background: #2d333b; border: none; border-radius: 999px;
  cursor: pointer; transition: background 0.2s; padding: 0;
}
.stepper-seg.done { background: #3fb950; }

/* Step content */
.guide-step {
  flex: 1; overflow-y: auto; padding: 12px 16px;
  display: flex; flex-direction: column; gap: 12px;
}
.guide-step::-webkit-scrollbar { width: 4px; }
.guide-step::-webkit-scrollbar-thumb { background: #2d333b; border-radius: 2px; }

.guide-step__head {
  display: flex; align-items: center; gap: 10px;
}
.step-circle {
  width: 24px; height: 24px; border-radius: 50%; flex-shrink: 0;
  border: 1.5px solid #3fb950; color: #3fb950; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.step-title   { font-size: 13px; font-weight: 600; color: #e6edf3; flex: 1; }
.step-counter { font-size: 11px; color: #4d5566; flex-shrink: 0; }

.step-desc {
  margin: 0; font-size: 12px; color: #768390; line-height: 1.6;
}

/* Copy box */
.copy-box {
  display: flex; align-items: center; gap: 8px;
  background: #1c2128; border: 1px solid #2d333b; border-radius: 7px;
  padding: 8px 10px;
}
.copy-value {
  flex: 1; font-family: 'Consolas','Monaco',monospace; font-size: 11px;
  color: #a78bfa; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.copy-btn {
  background: transparent; border: 1px solid #2d333b; color: #c9d1d9;
  padding: 3px 10px; border-radius: 5px; font-size: 11px; font-family: inherit;
  cursor: pointer; white-space: nowrap; flex-shrink: 0; transition: background 0.12s;
}
.copy-btn:hover { background: rgba(255,255,255,0.05); }

/* Step image */
.step-img-wrap {
  border-radius: 8px; overflow: hidden; background: #1c2128;
  border: 1px solid #2d333b; min-height: 130px;
  display: flex; align-items: center; justify-content: center;
}
.step-img { width: 100%; display: block; border-radius: 7px; }
.step-img-placeholder {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 8px; padding: 24px; text-align: center;
  font-size: 11px; color: #4d5566; line-height: 1.5;
}

/* Guide nav */
.guide-nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; border-top: 1px solid #2d333b; flex-shrink: 0; gap: 8px;
}

/* ── Region toggle ── */
.region-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.auto-detect-toggle {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  cursor: pointer;
  user-select: none;
}

.auto-detect-toggle input { display: none; }

.toggle-track {
  width: 32px;
  height: 18px;
  background: #2d333b;
  border-radius: 999px;
  position: relative;
  transition: background 0.2s;
  flex-shrink: 0;
}

.auto-detect-toggle input:checked ~ .toggle-track { background: #22c55e; }

.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 14px;
  height: 14px;
  background: #fff;
  border-radius: 50%;
  transition: transform 0.2s;
}

.auto-detect-toggle input:checked ~ .toggle-track .toggle-thumb { transform: translateX(14px); }

.toggle-label { font-size: 0.8rem; color: #768390; font-weight: 400; }

.auto-detect-warn {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  background: rgba(227, 179, 65, 0.07);
  border: 1px solid rgba(227, 179, 65, 0.3);
  border-radius: 7px;
  padding: 8px 10px;
  font-size: 0.78rem;
  color: #e3b341;
  line-height: 1.45;
}

/* ── MultiSelect dark theme inside add modal ── */
.add-modal :deep(.p-multiselect) {
  background: #1c2128 !important;
  border: 1px solid #2d333b !important;
  border-radius: 7px;
}
.add-modal :deep(.p-multiselect:hover),
.add-modal :deep(.p-multiselect.p-focus) {
  border-color: #3fb950 !important;
  box-shadow: none !important;
}
.add-modal :deep(.p-multiselect-label) {
  color: #e6edf3 !important;
  font-size: 12px;
}
.add-modal :deep(.p-multiselect-label.p-placeholder) {
  color: #4d5566 !important;
}
.add-modal :deep(.p-multiselect-dropdown) {
  color: #768390 !important;
}
.add-modal :deep(.p-chip) {
  background: rgba(63,185,80,0.12) !important;
  color: #3fb950 !important;
  border: 1px solid rgba(63,185,80,0.25) !important;
  font-size: 11px;
}
.add-modal :deep(.p-chip-remove-icon) {
  color: #3fb950 !important;
}
</style>

<style>
/* ── MultiSelect teleported panel — dark theme + size cap ── */
.add-account-multiselect-panel.p-multiselect-overlay,
.add-account-multiselect-panel.p-multiselect-panel {
  z-index: 1200 !important;
  background: #1c2128 !important;
  border: 1px solid #2d333b !important;
  border-radius: 8px !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important;
  min-width: 0 !important;
}

/* Header row (Select All + filter) */
.add-account-multiselect-panel .p-multiselect-header {
  background: #161b22 !important;
  border-bottom: 1px solid #2d333b !important;
  padding: 7px 10px !important;
  gap: 8px;
}

/* Filter input */
.add-account-multiselect-panel .p-multiselect-filter,
.add-account-multiselect-panel .p-multiselect-filter-container input {
  background: #1c2128 !important;
  border: 1px solid #2d333b !important;
  color: #e6edf3 !important;
  border-radius: 6px !important;
  font-size: 12px !important;
  padding: 5px 8px !important;
}
.add-account-multiselect-panel .p-multiselect-filter:focus,
.add-account-multiselect-panel .p-multiselect-filter-container input:focus {
  border-color: #3fb950 !important;
  box-shadow: none !important;
  outline: none !important;
}
.add-account-multiselect-panel .p-multiselect-filter::placeholder,
.add-account-multiselect-panel .p-multiselect-filter-container input::placeholder {
  color: #4d5566 !important;
}

/* Scrollable list — cap height so it doesn't overflow */
.add-account-multiselect-panel .p-multiselect-list-container,
.add-account-multiselect-panel .p-multiselect-items-wrapper {
  max-height: 220px !important;
  overflow-y: auto !important;
}
.add-account-multiselect-panel .p-multiselect-list-container::-webkit-scrollbar,
.add-account-multiselect-panel .p-multiselect-items-wrapper::-webkit-scrollbar { width: 4px; }
.add-account-multiselect-panel .p-multiselect-list-container::-webkit-scrollbar-thumb,
.add-account-multiselect-panel .p-multiselect-items-wrapper::-webkit-scrollbar-thumb {
  background: #2d333b; border-radius: 2px;
}

/* Group headers */
.add-account-multiselect-panel .p-multiselect-option-group,
.add-account-multiselect-panel .p-multiselect-item-group {
  background: #161b22 !important;
  color: #4d5566 !important;
  font-size: 10px !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 6px 10px 4px !important;
}

/* Individual options */
.add-account-multiselect-panel .p-multiselect-option,
.add-account-multiselect-panel .p-multiselect-item {
  background: transparent !important;
  color: #c9d1d9 !important;
  font-size: 12px !important;
  padding: 6px 10px !important;
  border-radius: 0 !important;
}
.add-account-multiselect-panel .p-multiselect-option:hover,
.add-account-multiselect-panel .p-multiselect-option.p-focus,
.add-account-multiselect-panel .p-multiselect-item:hover,
.add-account-multiselect-panel .p-multiselect-item:focus {
  background: rgba(63,185,80,0.09) !important;
  color: #e6edf3 !important;
}
.add-account-multiselect-panel .p-multiselect-option.p-selected,
.add-account-multiselect-panel .p-multiselect-item.p-highlight {
  background: rgba(63,185,80,0.14) !important;
  color: #3fb950 !important;
}

/* Checkboxes */
.add-account-multiselect-panel .p-checkbox-box,
.add-account-multiselect-panel .p-checkbox .p-checkbox-box {
  background: #1c2128 !important;
  border: 1px solid #3d444d !important;
  border-radius: 4px !important;
}
.add-account-multiselect-panel .p-checkbox.p-checked .p-checkbox-box,
.add-account-multiselect-panel .p-checkbox-checked .p-checkbox-box {
  background: #3fb950 !important;
  border-color: #3fb950 !important;
}
.add-account-multiselect-panel .p-checkbox-box .p-icon,
.add-account-multiselect-panel .p-checkbox .p-checkbox-box .p-icon {
  color: #0d1117 !important;
}

/* Select-all label in header */
.add-account-multiselect-panel .p-multiselect-select-all-label,
.add-account-multiselect-panel .p-multiselect-header .p-checkbox + span {
  color: #768390 !important;
  font-size: 12px !important;
}
</style>
