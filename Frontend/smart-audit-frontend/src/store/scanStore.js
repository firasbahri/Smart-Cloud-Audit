import { defineStore } from 'pinia'
import { ref } from 'vue'
import { buildApiSseUrl, buildApiUrl } from '../utils/api'

export const useScanStore = defineStore('scan', () => {

  const scanResultIdByAccount = ref({})
  const scanResultByAccount = ref({})
  const scanProgressByAccount = ref({})
  const scanningAccounts = ref({})
  const scanIdByAccount = ref({})
  const scanCreatedAtByAccount = ref({})
  const pendingNotifications = ref([])
  const resourceContextsByAccount = ref({})

  // Map no reactivo, solo gestión interna de conexiones SSE
  const eventSources = new Map()

  const setScanData = (accountId, scanId, dataResult, createdAt) => {
    scanResultIdByAccount.value[accountId] = scanId
    scanResultByAccount.value[accountId] = dataResult
    scanCreatedAtByAccount.value[accountId] = createdAt
    console.log('Datos de escaneo actualizados para la cuenta:', accountId, {
      scanId,
      createdAt: createdAt,
      result: dataResult
    })
  
  }

  const startAccountScan = (accountId, scanId) => {
    scanningAccounts.value[accountId] = true
    scanProgressByAccount.value[accountId] = 0
    scanIdByAccount.value[accountId] = scanId
  }

  const setAccountScanProgress = (accountId, progress) => {
    const normalized = Number.isFinite(progress)
      ? Math.max(0, Math.min(100, Number(progress)))
      : 0
    scanProgressByAccount.value[accountId] = normalized
  }

  const completeAccountScan = (accountId) => {
    scanProgressByAccount.value[accountId] = 100
    scanningAccounts.value[accountId] = false
  }

  const failAccountScan = (accountId) => {
    scanningAccounts.value[accountId] = false
  }

  const clearAccountScan = (accountId) => {
    delete scanProgressByAccount.value[accountId]
    delete scanningAccounts.value[accountId]
    delete scanIdByAccount.value[accountId]
  }

  const loadContextsForAccount = (accountId) => {
    if (!accountId || resourceContextsByAccount.value[accountId]) return
    try {
      const stored = localStorage.getItem(`sa_ctx_${accountId}`)
      resourceContextsByAccount.value[accountId] = stored ? JSON.parse(stored) : {}
    } catch {
      resourceContextsByAccount.value[accountId] = {}
    }
  }

  const setResourceContext = (accountId, resourceId, context) => {
    if (!accountId) return
    if (!resourceContextsByAccount.value[accountId]) resourceContextsByAccount.value[accountId] = {}
    const trimmed = context.trim()
    if (trimmed) {
      resourceContextsByAccount.value[accountId][resourceId] = trimmed
    } else {
      delete resourceContextsByAccount.value[accountId][resourceId]
    }
    localStorage.setItem(`sa_ctx_${accountId}`, JSON.stringify(resourceContextsByAccount.value[accountId]))
  }

  const clearData = () => {
    scanCreatedAtByAccount.value = {}
    scanResultIdByAccount.value = {}
    scanResultByAccount.value = {}
    scanProgressByAccount.value = {}
    scanningAccounts.value = {}
    scanIdByAccount.value = {}
    scanCreatedAtByAccount.value = {}
  }

  const pushNotification = (notification) => {
    pendingNotifications.value.push({ ...notification, _id: Date.now() + Math.random() })
  }

  const consumeNotifications = () => {
    const copy = [...pendingNotifications.value]
    pendingNotifications.value = []
    return copy
  }

  const startSSE = (scanId, accountId) => {
    if (eventSources.has(accountId)) return

    startAccountScan(accountId, scanId)

    const token = localStorage.getItem('token')
    const url = buildApiSseUrl(`/cloud/scan_progress_sse/${scanId}`, { token })
    const es = new EventSource(url)
    eventSources.set(accountId, es)

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const progress = Number(data.progress ?? 0)
        setAccountScanProgress(accountId, progress)

        if (data.results) setScanData(accountId, scanId, data.results,data.created_at)

        if (data.status === 'completed') {
          es.close()
          eventSources.delete(accountId)
          completeAccountScan(accountId)
          pushNotification({
            severity: 'success',
            summary: 'Escaneo Completo',
            detail: 'El escaneo de la cuenta ha finalizado correctamente',
            life: 4000
          })
        }

        if (data.status === 'failed') {
          es.close()
          eventSources.delete(accountId)
          failAccountScan(accountId)
          pushNotification({
            severity: 'error',
            summary: 'Escaneo fallido',
            detail: data.errors || 'Ocurrió un error durante el escaneo',
            life: 4000
          })
        }
      } catch (e) {}
    }

    es.onerror = () => {
      es.close()
      eventSources.delete(accountId)
      failAccountScan(accountId)
      pushNotification({
        severity: 'error',
        summary: 'Error de conexión',
        detail: 'Se perdió la conexión con el servidor durante el escaneo',
        life: 4000
      })
    }
  }

  const stopSSE = (accountId) => {
    const es = eventSources.get(accountId)
    if (es) {
      es.close()
      eventSources.delete(accountId)
    }
  }

  const loadScanDataForAccount = async (account) => {
    const accountId = account?.id || account?.account_id || account
    if (!accountId) { clearData(); return null }

    const token = localStorage.getItem('token')
    if (!token) { clearData(); return null }
    if (scanIdByAccount.value[accountId]) return 
    try {
      const response = await fetch(buildApiUrl(`/cloud/get_scan_result/${accountId}`), {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Error al cargar resultados')

      const scanId = data.scan_id || ''
      if (!scanId) { clearData(); return null }

      setScanData(accountId, scanId, data.results ,data.created_at)
      console.log('Datos de escaneo cargados para la cuenta:', accountId, data)
      return data
    } catch (error) {
      console.error('Error cargando datos de escaneo:', error)
      clearData()
      return null
    }
  }

  const esScanReciente=(accountId)=> {
    console.log('Verificando si el escaneo es reciente...')
    console.log('Valor de scanCreatedAt:', scanCreatedAtByAccount.value[accountId])
    if (!scanCreatedAtByAccount.value[accountId]) return false
    const hours = (new Date() - new Date(scanCreatedAtByAccount.value[accountId])) / (1000 * 60 * 60)
    console.log('Horas desde el último escaneo:', hours)
    console.log('Fecha de creación del escaneo:', scanCreatedAtByAccount.value[accountId])
    return hours < 24
  }
  

  return {
    scanResultIdByAccount,
    scanResultByAccount,
    scanCreatedAtByAccount,
    scanProgressByAccount,
    scanningAccounts,
    scanIdByAccount,
    pendingNotifications,
    resourceContextsByAccount,
    setScanData,
    startAccountScan,
    setAccountScanProgress,
    completeAccountScan,
    failAccountScan,
    clearAccountScan,
    clearData,
    startSSE,
    stopSSE,
    consumeNotifications,
    loadScanDataForAccount,
    loadContextsForAccount,
    setResourceContext,
    esScanReciente
  }
})
