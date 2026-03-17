import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useCloudAccountsStore = defineStore('cloudAccounts', () => {
  
  const accounts = ref([])
  const selectedAccount = ref(null)

  const activeAccountId = computed(() =>
    selectedAccount.value?.account_id || selectedAccount.value?.id || null
  )

  const awsAccounts = computed(() => 
    accounts.value.filter(acc => acc.provider === 'AWS')
  )

  const azureAccounts = computed(() => 
    accounts.value.filter(acc => acc.provider === 'Azure')
  )

  const gcpAccounts = computed(() => 
    accounts.value.filter(acc => acc.provider === 'GCP')
  )

  const activeAccounts = computed(() => 
    accounts.value.filter(acc => acc.status === 'Activa')
  )

  const totalAccounts = computed(() => accounts.value.length)

  
  const addAccount = (account) => {
    const newAccount = {
      ...account,
      status: 'Activa',
    }
    accounts.value.push(newAccount)

    
    return newAccount
  }

  const updateAccount = (id, updates) => {
    const index = accounts.value.findIndex(acc => acc.id === id)
    if (index !== -1) {
      accounts.value[index] = { ...accounts.value[index], ...updates }
      

      console.log('Cuenta actualizada:', accounts.value[index])
    }
  }

  const deleteAccount = (id) => {
    accounts.value = accounts.value.filter(acc => acc.id !== id)
    
    if (selectedAccount.value?.id === id) {
      selectedAccount.value = null
    }
    
    // TODO: Llamar al backend para eliminar
    console.log('Cuenta eliminada del store:', id)
  }

  const selectAccount = (account) => {
    selectedAccount.value = account
    localStorage.setItem('selectedCloudAccount', JSON.stringify(account))
  }

  const loadSelectedAccount = () => {
    const raw = localStorage.getItem('selectedCloudAccount')
    selectedAccount.value = raw ? JSON.parse(raw) : null
  }

  const clearSelection = () => {
    selectedAccount.value = null
    localStorage.removeItem('selectedCloudAccount')
  }

  const loadAccounts = async () => {
    // TODO: Cargar cuentas desde el backend
    try {
      const token= localStorage.getItem('token')
      const URL= 'http://localhost:8000/cloud/get_cloud_data'
      const response = await fetch(URL,{
        method : 'GET',
        headers :{
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
      )

      const data= await response.json()
      if(!response.ok){
        throw new Error(data.detail || 'Error al cargar cuentas')
      } 
      
      if(data.length === 0){
        console.log('No se encontraron cuentas para el usuario.')
        accounts.value = []
      }
      else{
        accounts.value = data
      }
    } catch (error) {
      console.error('Error cargando cuentas:', error)
    }
  }

  const clearAccounts = () => {
    accounts.value = []
    selectedAccount.value = null
  }

  return { 
    // State
    accounts,
    selectedAccount,
    activeAccountId,
    // Computed
    awsAccounts,
    azureAccounts,
    gcpAccounts,
    activeAccounts,
    totalAccounts,
    // Actions
    addAccount,
    updateAccount,
    deleteAccount,
    selectAccount,
    loadSelectedAccount,
    clearSelection,
    loadAccounts,
    clearAccounts
  }
})
