import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useScanStore = defineStore('scan', () => {
  
  const id = ref('')
  const scanResult = ref(null)
  const scanProgressByAccount = ref({})
  const scanningAccounts = ref({})
  const scanIdByAccount = ref({})

  
  const setScanData = (scanId, data) => {
    id.value = scanId
    scanResult.value = data
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
  }


  return {
    id,
    scanResult,
    scanProgressByAccount,
    scanningAccounts,
    scanIdByAccount,
    setScanData,
    startAccountScan,
    setAccountScanProgress,
    completeAccountScan,
    failAccountScan,
    clearAccountScan,
    clearData
  }
})