<template>
  <div class="cloud-accounts-view">
    <Toast />

    <div class="page-header flex align-items-center gap-3 mb-5">
      <Cloud :size="32" class="page-icon p-3 border-round-xl shadow-3" />
      <div>
        <h2 class="m-0">Cloud Accounts</h2>
        <p class="subtitle m-0 mt-2">Manage your linked cloud provider accounts</p>
      </div>
    </div>

    <div class="accounts-section mb-5">
      <div class="flex justify-content-between align-items-center mb-4">
        <h3 class="m-0">Linked Accounts</h3>
        <Button
          label="Add Account"
          icon="pi pi-plus"
          @click="showAddDialog = true"
          severity="success"
        />
      </div>

      <Card v-if="isLoadingAccounts && shouldShowLoading" class="empty-state">
        <template #content>
          <div class="flex flex-column align-items-center justify-content-center py-6 gap-3">
            <i class="pi pi-spin pi-spinner text-500" style="font-size: 2rem"></i>
            <h3 class="text-600 m-0">Loading linked accounts...</h3>
          </div>
        </template>
      </Card>

      <div v-else-if="isLoadingAccounts" style="min-height: 12rem"></div>

      <Card v-else-if="cloudAccountsStore.accounts.length === 0" class="empty-state">
        <template #content>
          <div class="flex flex-column align-items-center justify-content-center py-6">
            <CloudOff :size="64" class="text-400 mb-3" />
            <h3 class="text-600 mb-2">No linked accounts</h3>
            <p class="text-500 mb-4">Add your first cloud account to get started</p>
            <Button
              label="Connect Account"
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
                    <span class="text-600 font-semibold">Linked:</span>
                    <span class="text-500">{{ formatDate(account.created_at) }}</span>
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

    <div v-if="showAddDialog" class="add-overlay" @click.self="closeDialog">
      <div class="add-stage" :class="{ 'guide-open': showGuide }">

        <!-- Form modal -->
        <div class="add-modal">
          <div class="add-modal__header">
            <div class="add-modal__title-group">
              <div class="add-modal__icon"><Cloud :size="15" /></div>
              <div>
                <div class="add-modal__title">Add Account</div>
                <div class="add-modal__sub">Connect an AWS account</div>
              </div>
            </div>
            <button class="add-modal__close" @click="closeDialog">✕</button>
          </div>

          <div class="add-modal__body">
            <!-- Name -->
            <div class="af-field">
              <label class="af-label">Account name</label>
              <input v-model="newAccount.name" class="af-input" :class="{ invalid: errors.name }" placeholder="e.g. Production AWS" />
              <span v-if="errors.name" class="af-error">{{ errors.name }}</span>
            </div>

            <!-- Provider -->
            <div class="af-field">
              <label class="af-label">Provider</label>
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
                  <span class="req-pill">required</span>
                </div>
                <button class="guide-link" @click="showGuide = !showGuide">
                  How do I get it? {{ showGuide ? '←' : '→' }}
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
                  <span class="toggle-label">Auto-detect</span>
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
                placeholder="Select regions..."
                display="chip"
                filter
                filterPlaceholder="Search region..."
                class="w-full"
                panelClass="add-account-multiselect-panel"
                :invalid="errors.regions"
              />
              <div v-if="autoDetectRegions" class="auto-detect-warn">
                <i class="pi pi-exclamation-triangle" style="font-size:0.75rem" />
                <span>Will scan ~30 regions. The initial scan will be slower.</span>
              </div>
              <span v-if="errors.regions && !autoDetectRegions" class="af-error">{{ errors.regions }}</span>
              <span class="af-hint">Recommendation: select your regions manually — it helps reduce EC2 scan time.</span>
            </div>

            <!-- Description -->
            <div class="af-field">
              <label class="af-label">Description <span class="af-optional">(optional)</span></label>
              <textarea v-model="newAccount.description" class="af-textarea" rows="2" placeholder="Describe the purpose of this account..." />
              <div class="ai-ctx-hint-box">
                <i class="pi pi-sparkles" style="font-size:0.75rem;color:#a78bfa" />
                <span>Will be used as context in <strong>AI Analysis</strong>.</span>
              </div>
            </div>
          </div>

          <div class="add-modal__footer">
            <button class="af-btn-cancel" @click="closeDialog">Cancel</button>
            <button
              class="af-btn-primary"
              :disabled="isConnecting || !selectedProvider || !newAccount.name || !newAccount.arn"
              @click="addAccount"
            >
              <i v-if="isConnecting" class="pi pi-spin pi-spinner" style="font-size:0.8rem" />
              {{ isConnecting ? 'Connecting...' : 'Connect account' }}
            </button>
          </div>
        </div>

        <!-- ARN Guide Drawer -->
        <div class="arn-guide" :class="{ open: showGuide }">
          <div class="arn-guide__inner">
            <div class="arn-guide__header">
              <span class="arn-guide__title">How to get your Role ARN</span>
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
                  {{ copiedStep === guideStep ? '✓ Copied' : '📋 Copy' }}
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
              <button class="af-btn-ghost" :disabled="guideStep === 1" @click="guideStep--">← Previous</button>
              <button v-if="guideStep < 5" class="af-btn-secondary" @click="guideStep++">Next →</button>
              <button v-else class="af-btn-primary af-btn-primary--sm" @click="showGuide = false">✓ I have my ARN</button>
            </div>
          </div>
        </div>

      </div>
    </div>

    <Dialog
      v-model:visible="showScanConfirmDialog"
      modal
      header="Recent scan detected"
      :style="{ width: '28rem' }"
    >
      <div class="flex align-items-center gap-3 mb-3">
        <i class="pi pi-exclamation-triangle text-yellow-500" style="font-size: 2rem" />
        <p class="m-0">
          You already have a scan from less than <strong>24 hours</strong> ago for this account.
          Do you want to launch a new one anyway?
        </p>
      </div>
      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="cancelScan" />
        <Button label="Yes, scan" icon="pi pi-refresh" severity="warning" @click="confirmScan" />
      </template>
    </Dialog>

    <Dialog
      v-model:visible="showDeleteDialog"
      modal
      header="Delete Account"
      :style="{ width: '30rem' }"
    >
      <div class="flex align-items-center gap-3 mb-3">
        <AlertTriangle :size="48" class="text-orange-500" />
        <p class="m-0">
          Are you sure you want to delete the account <strong>{{ selectedAccount?.name }}</strong>?
        </p>
      </div>
      <p class="text-500 text-sm">This action cannot be undone.</p>

      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="showDeleteDialog = false" />
        <Button label="Delete" icon="pi pi-trash" severity="danger" @click="confirmDelete" />
      </template>
    </Dialog>

    <div v-if="showDetailsDialog" class="add-overlay" @click.self="showDetailsDialog = false">
      <div class="add-modal add-modal--wide">
        <div class="add-modal__header">
          <div class="add-modal__title-group">
            <div class="add-modal__icon">
              <component :is="getProviderIcon(selectedAccount?.provider)" :size="15" />
            </div>
            <div>
              <div class="add-modal__title">{{ selectedAccount?.name }}</div>
              <div class="add-modal__sub">Account details</div>
            </div>
          </div>
          <button class="add-modal__close" @click="showDetailsDialog = false">✕</button>
        </div>

        <div v-if="selectedAccount" class="add-modal__body">
          <div class="af-field">
            <div class="flex gap-2">
              <Tag :value="selectedAccount.provider" :severity="getProviderSeverity(selectedAccount.provider)" />
            </div>
          </div>

          <div class="af-field">
            <label class="af-label">Role ARN</label>
            <div class="af-readonly af-readonly--mono">{{ selectedAccount.identifier || selectedAccount.arn || '-' }}</div>
          </div>

          <div class="af-field">
            <label class="af-label">Account ID</label>
            <div class="af-readonly">{{ selectedAccount.account_id || '-' }}</div>
          </div>

          <div class="af-field">
            <label class="af-label">Linked date</label>
            <div class="af-readonly">{{ selectedAccount.created_at ? formatDate(selectedAccount.created_at) : '-' }}</div>
          </div>

          <div class="af-field">
            <label class="af-label">AWS Regions</label>
            <div class="af-readonly">
              {{ (selectedAccount.regions && selectedAccount.regions.length) ? selectedAccount.regions.join(', ') : 'Auto-detect (all regions)' }}
            </div>
          </div>

          <div class="af-field">
            <label class="af-label">Description</label>
            <div class="af-readonly">{{ selectedAccount.description || 'No description' }}</div>
          </div>
        </div>

        <div class="add-modal__footer">
          <button class="af-btn-cancel" @click="showDetailsDialog = false">Close</button>
        </div>
      </div>
    </div>

    <div v-if="showEditDialog" class="add-overlay" @click.self="closeEditDialog">
      <div class="add-modal add-modal--wide">
        <div class="add-modal__header">
          <div class="add-modal__title-group">
            <div class="add-modal__icon"><Cloud :size="15" /></div>
            <div>
              <div class="add-modal__title">Edit Account</div>
              <div class="add-modal__sub">{{ editAccount.name || 'Cloud account' }}</div>
            </div>
          </div>
          <button class="add-modal__close" @click="closeEditDialog">✕</button>
        </div>

        <div class="add-modal__body">
          <!-- Name -->
          <div class="af-field">
            <label class="af-label">Account name</label>
            <input v-model="editAccount.name" class="af-input" :class="{ invalid: editErrors.name }" placeholder="Account name" />
            <span v-if="editErrors.name" class="af-error">{{ editErrors.name }}</span>
          </div>

          <!-- ARN (read-only) -->
          <div class="af-field">
            <label class="af-label">Role ARN</label>
            <div class="af-readonly af-readonly--mono">{{ editAccount.arn }}</div>
            <span class="af-hint">The ARN cannot be changed. Delete and reconnect the account if you need to change it.</span>
          </div>

          <!-- Regions -->
          <div class="af-field">
            <div class="region-label-row">
              <label class="af-label">AWS Regions</label>
              <label class="auto-detect-toggle">
                <input type="checkbox" v-model="editAutoDetectRegions" @change="editAutoDetectRegions && (editAccount.regions = [])" />
                <span class="toggle-track"><span class="toggle-thumb" /></span>
                <span class="toggle-label">Auto-detect</span>
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
              placeholder="Select regions..."
              display="chip"
              filter
              filterPlaceholder="Search region..."
              class="w-full"
              panelClass="add-account-multiselect-panel"
              :invalid="editErrors.regions"
            />
            <div v-if="editAutoDetectRegions" class="auto-detect-warn">
              <i class="pi pi-exclamation-triangle" style="font-size:0.75rem" />
              <span>The next scan will cover ~30 regions.</span>
            </div>
            <span v-if="editErrors.regions && !editAutoDetectRegions" class="af-error">{{ editErrors.regions }}</span>
            <span class="af-hint">Recommendation: select your regions manually — it helps reduce EC2 scan time.</span>
          </div>

          <!-- Description -->
          <div class="af-field">
            <label class="af-label">Description <span class="af-optional">(optional)</span></label>
            <textarea v-model="editAccount.description" class="af-textarea" rows="2" placeholder="Describe the purpose of this account..." />
            <div class="ai-ctx-hint-box">
              <i class="pi pi-sparkles" style="font-size:0.75rem;color:#a78bfa" />
              <span>Will be used as context in <strong>AI Analysis</strong>.</span>
            </div>
          </div>
        </div>

        <div class="add-modal__footer">
          <button class="af-btn-cancel" @click="closeEditDialog">Cancel</button>
          <button class="af-btn-primary" :disabled="!editAccount.name" @click="saveEdit">Save changes</button>
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

const AWS_REGIONS = [
  {
    label: '🇺🇸 United States',
    items: [
      { label: 'us-east-1 — N. Virginia', value: 'us-east-1' },
      { label: 'us-east-2 — Ohio', value: 'us-east-2' },
      { label: 'us-west-1 — N. California', value: 'us-west-1' },
      { label: 'us-west-2 — Oregon', value: 'us-west-2' },
    ]
  },
  {
    label: '🇪🇺 Europe',
    items: [
      { label: 'eu-west-1 — Ireland', value: 'eu-west-1' },
      { label: 'eu-west-2 — London', value: 'eu-west-2' },
      { label: 'eu-west-3 — Paris', value: 'eu-west-3' },
      { label: 'eu-central-1 — Frankfurt', value: 'eu-central-1' },
      { label: 'eu-central-2 — Zurich', value: 'eu-central-2' },
      { label: 'eu-north-1 — Stockholm', value: 'eu-north-1' },
      { label: 'eu-south-1 — Milan', value: 'eu-south-1' },
      { label: 'eu-south-2 — Spain', value: 'eu-south-2' },
    ]
  },
  {
    label: '🌏 Asia Pacific',
    items: [
      { label: 'ap-southeast-1 — Singapore', value: 'ap-southeast-1' },
      { label: 'ap-southeast-2 — Sydney', value: 'ap-southeast-2' },
      { label: 'ap-southeast-3 — Jakarta', value: 'ap-southeast-3' },
      { label: 'ap-southeast-4 — Melbourne', value: 'ap-southeast-4' },
      { label: 'ap-northeast-1 — Tokyo', value: 'ap-northeast-1' },
      { label: 'ap-northeast-2 — Seoul', value: 'ap-northeast-2' },
      { label: 'ap-northeast-3 — Osaka', value: 'ap-northeast-3' },
      { label: 'ap-south-1 — Mumbai', value: 'ap-south-1' },
      { label: 'ap-south-2 — Hyderabad', value: 'ap-south-2' },
      { label: 'ap-east-1 — Hong Kong', value: 'ap-east-1' },
    ]
  },
  {
    label: '🌎 Americas',
    items: [
      { label: 'ca-central-1 — Canada Central', value: 'ca-central-1' },
      { label: 'ca-west-1 — Canada West', value: 'ca-west-1' },
      { label: 'sa-east-1 — São Paulo', value: 'sa-east-1' },
      { label: 'mx-central-1 — Mexico', value: 'mx-central-1' },
    ]
  },
  {
    label: '🌍 Middle East & Africa',
    items: [
      { label: 'me-south-1 — Bahrain', value: 'me-south-1' },
      { label: 'me-central-1 — UAE', value: 'me-central-1' },
      { label: 'il-central-1 — Israel', value: 'il-central-1' },
      { label: 'af-south-1 — Cape Town', value: 'af-south-1' },
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
    title: 'Create a new role in IAM',
    description: "In the AWS console go to IAM → Roles → 'Create role' and select 'AWS account' as the trusted entity type.",
    copyValue: 'https://console.aws.amazon.com/iam/home#/roles',
    placeholder: "IAM → Roles → 'Create role' → entity type 'AWS account'",
  },
  {
    title: 'Authorize the Smart Audit account',
    description: "Select 'Another AWS account' and enter our account ID. This allows us to read your resources securely.",
    copyValue: SMART_AUDIT_ACCOUNT_ID,
    placeholder: "Select 'Another AWS account' and enter the account ID",
  },
  {
    title: 'Assign read-only permissions',
    description: "Search for and select the managed policy 'ReadOnlyAccess'. Smart Audit never modifies your resources — it only reads them.",
    copyValue: 'ReadOnlyAccess',
    placeholder: "Search and select the 'ReadOnlyAccess' policy",
  },
  {
    title: 'Name the role',
    description: 'Give the role an identifiable name so you can recognize it later, then confirm the creation.',
    copyValue: 'SmartAuditRole',
    placeholder: 'Role name field and confirm creation',
  },
  {
    title: 'Copy the role ARN',
    description: 'Open the newly created role. At the top you will see its ARN — copy it and paste it into the form field.',
    copyValue: `arn:aws:iam::${SMART_AUDIT_ACCOUNT_ID}:role/SmartAuditRole`,
    placeholder: 'Newly created role screen showing its ARN at the top',
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
    label: 'View details',
    icon: 'pi pi-eye',
    command: () => openDetails(selectedAccount.value)
  },
  {
    label: 'Edit',
    icon: 'pi pi-pencil',
    command: () => openEdit(selectedAccount.value)
  },
  {
    separator: true
  },
  {
    label: 'Delete',
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


const formatDate = (date) => {
  return new Date(date).toLocaleDateString('en-US', {
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
    errors.name = 'Name is required'
    isValid = false
  }

  if (!newAccount.arn.trim()) {
    errors.arn = 'ARN is required'
    isValid = false
  } else if (!/^arn:aws:iam::\d{12}:role\/.+$/.test(newAccount.arn.trim())) {
    errors.arn = 'Format: arn:aws:iam::<account_id>:role/<name>'
    isValid = false
  }

  if (!autoDetectRegions.value && !newAccount.regions.length) {
    errors.regions = 'Select at least one region'
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
  if (isAccountScanning(accountId)) return 'Scanning...'
  if (progress === 100) return 'Scan completed'
  return 'Scan'
}

const shouldShowProgressBar = (accountId) => {
  const progress = Number(scanStore.scanProgressByAccount[accountId] ?? 0)
  return progress > 0 && progress <= 100
}


const addAccount = async () => {
  if (!validateForm()) return

  isConnecting.value = true
  try {
    const accountData = await cloudAccountsStore.registerAccount({
      name: newAccount.name,
      provider: selectedProvider.value,
      arn: newAccount.arn,
      description: newAccount.description,
      regions: newAccount.regions
    })
    toast.add({
      severity: 'success',
      summary: 'Account Added',
      detail: `The account ${accountData.name} has been linked successfully`,
      life: 3000
    })
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 })
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
  try {
    await scanStore.executeScan(account)
  } catch (error) {
    scanStore.failAccountScan(String(account.id))
    toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 })
  }
}

const confirmDelete = async () => {
  const id = selectedAccount.value.id
  try {
    await cloudAccountsStore.removeCloudAccount(id)
    showDeleteDialog.value = false
    selectedAccount.value = null
    toast.add({ severity: 'info', summary: 'Account Deleted', detail: 'The account has been deleted successfully', life: 3000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 })
  }
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
    editErrors.name = 'Name is required'
    isValid = false
  }

  if (!editAutoDetectRegions.value && !editAccount.regions.length) {
    editErrors.regions = 'Select at least one region'
    isValid = false
  }

  return isValid
}

const saveEdit = async () => {
  if (!validateEditForm()) return

  const regionsToSave = editAutoDetectRegions.value ? [] : editAccount.regions

  try {
    await cloudAccountsStore.updateCloudAccount({
      id: editAccount.id,
      name: editAccount.name,
      provider: editAccount.provider,
      arn: editAccount.arn,
      description: editAccount.description,
      regions: regionsToSave
    })
    toast.add({
      severity: 'success',
      summary: 'Account Updated',
      detail: `The account ${editAccount.name} has been updated successfully`,
      life: 3000
    })
    showEditDialog.value = false
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 })
  }
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
