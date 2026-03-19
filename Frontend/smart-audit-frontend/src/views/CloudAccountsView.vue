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

    <Dialog
      v-model:visible="showAddDialog"
      modal
      header="Añadir Cuenta de Nube"
      :style="{ width: '50rem' }"
      :breakpoints="{ '1199px': '75vw', '575px': '90vw' }"
    >
      <div class="flex flex-column gap-4 py-3">
        <p class="text-600 mb-3">Selecciona el proveedor de nube y proporciona las credenciales necesarias</p>

        <div class="provider-selection grid">
          <div class="col-12 md:col-4">
            <Card
              class="provider-option"
              :class="{ selected: selectedProvider === 'AWS' }"
              @click="selectedProvider = 'AWS'"
            >
              <template #content>
                <div class="flex flex-column align-items-center gap-3 cursor-pointer">
                  <Aws :size="48" class="provider-aws" />
                  <h4 class="m-0">AWS</h4>
                  <Tag value="Disponible" severity="success" />
                </div>
              </template>
            </Card>
          </div>

          <div class="col-12 md:col-4">
            <Card class="provider-option disabled">
              <template #content>
                <div class="flex flex-column align-items-center gap-3">
                  <CloudIcon :size="48" class="provider-azure text-400" />
                  <h4 class="m-0 text-400">Azure</h4>
                  <Tag value="Próximamente" severity="secondary" />
                </div>
              </template>
            </Card>
          </div>

          <div class="col-12 md:col-4">
            <Card class="provider-option disabled">
              <template #content>
                <div class="flex flex-column align-items-center gap-3">
                  <CloudIcon :size="48" class="provider-gcp text-400" />
                  <h4 class="m-0 text-400">Google Cloud</h4>
                  <Tag value="Próximamente" severity="secondary" />
                </div>
              </template>
            </Card>
          </div>
        </div>

        <div v-if="selectedProvider === 'AWS'" class="aws-form flex flex-column gap-4 mt-3">
          <div class="flex flex-column gap-2">
            <label for="accountName" class="font-semibold">Nombre de la Cuenta</label>
            <InputText
              id="accountName"
              v-model="newAccount.name"
              placeholder="Ej: Producción AWS"
              :invalid="errors.name"
            />
            <small v-if="errors.name" class="text-red-500">{{ errors.name }}</small>
          </div>

          <div class="flex flex-column gap-2">
            <label for="arn" class="font-semibold">ARN (Amazon Resource Name)</label>
            <Textarea
              id="arn"
              v-model="newAccount.arn"
              rows="3"
              placeholder="arn:aws:iam::123456789012:role/RoleName"
              :invalid="errors.arn"
            />
            <small v-if="errors.arn" class="text-red-500">{{ errors.arn }}</small>
            <small class="text-500">
              <InfoIcon :size="14" class="mr-1" />
              El ARN debe tener permisos de lectura para los servicios que deseas auditar
            </small>
          </div>

          <div class="flex flex-column gap-2">
            <label for="description" class="font-semibold">Descripción (Opcional)</label>
            <Textarea
              id="description"
              v-model="newAccount.description"
              rows="2"
              placeholder="Describe el propósito de esta cuenta..."
            />
          </div>
        </div>
      </div>

      <template #footer>
        <Button label="Cancelar" icon="pi pi-times" text @click="closeDialog" />
        <Button
          label="Conectar Cuenta"
          icon="pi pi-check"
          @click="addAccount"
          :disabled="!selectedProvider || !newAccount.name || !newAccount.arn"
        />
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

    <Dialog
      v-model:visible="showDetailsDialog"
      modal
      header="Detalles de la Cuenta"
      :style="{ width: '42rem' }"
      :breakpoints="{ '1199px': '75vw', '575px': '90vw' }"
    >
      <div v-if="selectedAccount" class="flex flex-column gap-4 py-2">
        <div class="flex align-items-center justify-content-between gap-3">
          <div class="flex align-items-center gap-3">
            <component
              :is="getProviderIcon(selectedAccount.provider)"
              :size="28"
              class="provider-icon"
              :class="'provider-' + selectedAccount.provider.toLowerCase()"
            />
            <div>
              <h3 class="m-0 mb-1">{{ selectedAccount.name }}</h3>
              <Tag :value="selectedAccount.provider" :severity="getProviderSeverity(selectedAccount.provider)" />
            </div>
          </div>
          <Tag
            :value="selectedAccount.status || 'Sin estado'"
            :severity="getStatusSeverity(selectedAccount.status)"
            :icon="getStatusIcon(selectedAccount.status)"
          />
        </div>

        <Divider class="my-1" />

        <div class="flex flex-column gap-3 text-sm">
          <div class="flex flex-column gap-1">
            <span class="text-600 font-semibold">ARN</span>
            <span class="text-500 break-all">{{ selectedAccount.identifier || selectedAccount.arn || '-' }}</span>
          </div>

          <div class="grid">
            <div class="col-12 md:col-6 flex flex-column gap-1">
              <span class="text-600 font-semibold">ID de Cuenta</span>
              <span class="text-500">{{ selectedAccount.account_id || '-' }}</span>
            </div>
            <div class="col-12 md:col-6 flex flex-column gap-1">
              <span class="text-600 font-semibold">Fecha de Vinculación</span>
              <span class="text-500">{{ selectedAccount.created_at ? formatDate(selectedAccount.created_at) : '-' }}</span>
            </div>
          </div>

          <div class="flex flex-column gap-1">
            <span class="text-600 font-semibold">Descripción</span>
            <span class="text-500">{{ selectedAccount.description || 'Sin descripción' }}</span>
          </div>
        </div>
      </div>

      <template #footer>
        <Button label="Cerrar" icon="pi pi-times" text @click="showDetailsDialog = false" />
      </template>
    </Dialog>

    <Dialog
      v-model:visible="showEditDialog"
      modal
      header="Editar Cuenta de Nube"
      :style="{ width: '50rem' }"
      :breakpoints="{ '1199px': '75vw', '575px': '90vw' }"
    >
      <div class="flex flex-column gap-4 py-3">
        <div class="flex flex-column gap-2">
          <label class="font-semibold">Nombre de la Cuenta</label>
          <InputText v-model="editAccount.name" placeholder="Nombre de la cuenta" />
        </div>

        <div class="flex flex-column gap-2">
          <label class="font-semibold">ARN</label>
          <Textarea :modelValue="editAccount.arn" rows="3" disabled class="opacity-60" />
          <small class="text-500">El ARN no puede modificarse. Elimina y vuelve a conectar la cuenta si necesitas cambiarlo.</small>
        </div>

        <div class="flex flex-column gap-2">
          <label class="font-semibold">Descripción (Opcional)</label>
          <Textarea v-model="editAccount.description" rows="2" placeholder="Describe el propósito de esta cuenta..." />
        </div>
      </div>

      <template #footer>
        <Button label="Cancelar" icon="pi pi-times" text @click="showEditDialog = false" />
        <Button label="Guardar cambios" icon="pi pi-check" @click="saveEdit" :disabled="!editAccount.name" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
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
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'
import Divider from 'primevue/divider'
import Menu from 'primevue/menu'
import Toast from 'primevue/toast'
import ProgressBar from 'primevue/progressbar'

const toast = useToast()
const cloudAccountsStore = useCloudAccountsStore()
const scanStore = useScanStore()

const isLoadingAccounts = ref(true)
const shouldShowLoading = ref(false)
let loadingIndicatorTimer = null
const pollingIntervals = new Map()

const showAddDialog = ref(false)
const showEditDialog = ref(false)
const showDeleteDialog = ref(false)
const showDetailsDialog = ref(false)
const selectedProvider = ref(null)
const selectedAccount = ref(null)
const menu = ref()

const newAccount = reactive({
  name: '',
  arn: '',
  description: ''
})

const editAccount = reactive({
  id: null,
  name: '',
  arn: '',
  description: '',
  provider: ''
})

const errors = reactive({
  name: '',
  arn: ''
})

onMounted(async () => {
  loadingIndicatorTimer = setTimeout(() => {
    if (isLoadingAccounts.value) {
      shouldShowLoading.value = true
    }
  }, 250)

  try {
    await cloudAccountsStore.loadAccounts()
    restoreActivePollings()
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

  for (const intervalId of pollingIntervals.values()) {
    clearInterval(intervalId)
  }
  pollingIntervals.clear()
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
  let isValid = true

  if (!newAccount.name.trim()) {
    errors.name = 'El nombre es requerido'
    isValid = false
  }

  if (!newAccount.arn.trim()) {
    errors.arn = 'El ARN es requerido'
    isValid = false
  } else if (!newAccount.arn.startsWith('arn:aws:')) {
    errors.arn = 'El formato del ARN no es válido'
    isValid = false
  }

  return isValid
}

const closeDialog = () => {
  showAddDialog.value = false
  selectedProvider.value = null
  newAccount.name = ''
  newAccount.arn = ''
  newAccount.description = ''
  errors.name = ''
  errors.arn = ''
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

const restoreActivePollings = () => {
  Object.entries(scanStore.scanIdByAccount).forEach(([accountId, scanId]) => {
    if (scanStore.scanningAccounts[accountId] && scanId) {
      startPollingScanStatus(scanId, accountId)
    }
  })
}

const addAccount = async () => {
  if (!validateForm()) return

  try {
    const token = localStorage.getItem('token')
    const API_URL = 'http://localhost:8000/cloud/register_cloud'
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
        description: newAccount.description
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
  }

  closeDialog()
}

const startPollingScanStatus = (scanId, accountId) => {
  if (pollingIntervals.has(accountId)) {
    return
  }

  scanStore.startAccountScan(accountId, scanId)

  const interval = setInterval(async () => {
    try {
      const token = localStorage.getItem('token')
      const API_URL = `http://localhost:8000/cloud/scan_status/${scanId}`
      const response = await fetch(API_URL, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail)

      const progress = Number(data.progress ?? data.porcentage ?? 0)
      scanStore.setAccountScanProgress(accountId, progress)

      if (data.status === 'completed') {
        clearInterval(interval)
        pollingIntervals.delete(accountId)
        scanStore.completeAccountScan(accountId)
        toast.add({
          severity: 'success',
          summary: 'Escaneo Completo',
          detail: 'El escaneo de la cuenta ha finalizado',
          life: 3000
        })
        scanStore.setScanData(accountId, data.results)
      }

      if (data.status === 'error') {
        clearInterval(interval)
        pollingIntervals.delete(accountId)
        scanStore.failAccountScan(accountId)
        toast.add({
          severity: 'error',
          summary: 'Escaneo fallido',
          detail: data.errors || 'Ocurrió un error durante el escaneo',
          life: 3000
        })
      }
    } catch (error) {
      clearInterval(interval)
      pollingIntervals.delete(accountId)
      scanStore.failAccountScan(accountId)
      toast.add({
        severity: 'error',
        summary: 'Error',
        detail: error.message,
        life: 3000
      })
    }
  }, 5000)

  pollingIntervals.set(accountId, interval)
}

const startScan = async (account) => {
  if (account.provider === 'AWS') {
    const token = localStorage.getItem('token')
    try {
      const URL = 'http://localhost:8000/cloud/start_scan'
      const response = await fetch(URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          id: account.id
        })
      })

      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'No se pudo iniciar el escaneo')

      const scanId = data.scan_id
      scanStore.id = scanId
      startPollingScanStatus(scanId, String(account.id))
    } catch (error) {
      scanStore.failAccountScan(String(account.id))
      toast.add({
        severity: 'error',
        summary: 'Error',
        detail: error.message,
        life: 3000
      })
      return
    }
  }

  cloudAccountsStore.selectAccount(account)
}

const confirmDelete = () => {
  try {
    const token = localStorage.getItem('token')
    const API_URL = 'http://localhost:8000/cloud/delete_cloud_data'
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
  showEditDialog.value = true
}

const saveEdit = async () => {
  if (!editAccount.name.trim()) {
    toast.add({
      severity: 'error',
      summary: 'Error de Validación',
      detail: 'El nombre es requerido',
      life: 3000
    })
    return
  }

  try {
    const token = localStorage.getItem('token')
    const API_URL = 'http://localhost:8000/cloud/update_cloud_data'
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        id: editAccount.id,
        name: editAccount.name,
        description: editAccount.description
      })
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail)
    auditStore.setScanData(editAccount.arn, data.result)
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
    description: editAccount.description
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
</style>
