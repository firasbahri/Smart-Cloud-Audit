import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useScanStore = defineStore('scan', () => {
  
  const id = ref('')
  const scanResult = ref(null)
  const scanProgressByAccount = ref({})
  const scanningAccounts = ref({})
  const scanIdByAccount = ref({})
  const scanCreatedAt=ref(null)
  
  const setScanData = (scanId, data) => {
    id.value = scanId
    scanResult.value = data
    scanCreatedAt.value = data.created_at || null
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

  const clearData = () => {
    id.value = ''
    scanResult.value = null
    scanProgressByAccount.value = {}
    scanningAccounts.value = {}
    scanIdByAccount.value = {}
    scanCreatedAt.value = null
  }

  const loadScanDataForAccount = async (account) => {
    const accountId = account?.id || account?.account_id || account

    if (!accountId) {
      clearData()
      return null
    }

    const token = localStorage.getItem('token')
    if (!token) {
      clearData()
      return null
    }

    const endpoint = `http://localhost:8000/cloud/get_scan_result/${accountId}`
    try {
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Error al cargar resultados de escaneo')
      }

      const scanId = data.scan_id || ''
      const result = data.results || data.resources || null
      if (!scanId) {
        clearData()
        return null
      }

      setScanData(scanId, result)
      scanIdByAccount.value[accountId] = scanId
      scanCreatedAt.value = data.created_at || null
      return data
    } catch (error) {
      console.error('Error cargando datos de escaneo:', error)
      clearData()
      return null
    }
  }


  return {
    id,
    scanResult,
    scanProgressByAccount,
    scanningAccounts,
    scanIdByAccount,
    scanCreatedAt,
    setScanData,
    startAccountScan,
    setAccountScanProgress,
    completeAccountScan,
    failAccountScan,
    clearAccountScan,
    clearData,  
    loadScanDataForAccount
  }
})