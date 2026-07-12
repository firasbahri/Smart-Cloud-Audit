/**
 * @module cloudAccountsStore
 * @description Store de Pinia para la gestión de cuentas cloud vinculadas por el usuario.
 * Mantiene la lista de cuentas, la cuenta actualmente seleccionada y las operaciones
 * CRUD correspondientes contra el backend.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { buildApiUrl } from '../utils/api'

export const useCloudAccountsStore = defineStore('cloudAccounts', () => {

  /** @type {Array} Lista de cuentas cloud del usuario autenticado. */
  const accounts = ref([])

  /** @type {string|null} Id de la cuenta actualmente seleccionada. */
  const selectedAccountId = ref(null)

  /** @type {Object|null} Cuenta actualmente seleccionada, derivada en tiempo real de accounts. */
  const selectedAccount = computed(() =>
    accounts.value.find(acc => acc.id === selectedAccountId.value) ?? null
  )

  /** @type {number} Total de cuentas vinculadas. */
  const totalAccounts = computed(() => accounts.value.length)

  /**
   * Añade una cuenta nueva al store con estado inicial 'Activa'.
   * Se llama después de que el backend confirme el registro exitoso.
   * @param {Object} account - Datos de la cuenta devueltos por el backend (id, name, provider, identifier…).
   * @returns {Object} La misma cuenta con el campo status añadido.
   */
  const addAccount = (account) => {
    const newAccount = { ...account, status: 'Activa' }
    accounts.value.push(newAccount)
    return newAccount
  }

  /**
   * Aplica una actualización parcial sobre una cuenta existente en el store.
   * @param {string} id - id de la cuenta a actualizar.
   * @param {Object} updates - Campos a sobreescribir (name, description, regions…).
   */
  const updateAccount = (id, updates) => {
    const index = accounts.value.findIndex(acc => acc.id === id)
    console.log('Actualizando cuenta con id:', id, 'con cambios:', updates)
    if (index !== -1) {
      accounts.value[index] = { ...accounts.value[index], ...updates }
      console.log('Cuenta actualizada:', accounts.value[index])
    }
  }

  /**
   * Elimina una cuenta del store y limpia selectedAccount si era la cuenta borrada.
   * @param {string} id - id de la cuenta a eliminar.
   */
  const deleteAccount = (id) => {
    accounts.value = accounts.value.filter(acc => acc.id !== id)
    if (selectedAccountId.value === id) {
      selectedAccountId.value = null
      localStorage.removeItem('selectedCloudAccountId')
    }
  }

  /**
   * Establece la cuenta activa y la persiste en localStorage para sobrevivir recargas.
   * @param {Object} account - Cuenta a seleccionar.
   */
  const selectAccount = (account) => {
    selectedAccountId.value = account?.id ?? null
    localStorage.setItem('selectedCloudAccountId', account?.id ?? '')
  }

  /**
   * Restaura selectedAccountId desde localStorage al montar la app (llamado en MainPage.vue onMounted).
   */
  const loadSelectedAccount = () => {
    const id = localStorage.getItem('selectedCloudAccountId')
    selectedAccountId.value = id || null
  }

  /**
   * Carga desde el backend todas las cuentas cloud del usuario autenticado
   * y rellena el array accounts.
   * @returns {Promise<void>}
   */
  const loadAccounts = async () => {
    try {
      const token = localStorage.getItem('token')
      const URL = buildApiUrl('/cloud/get_cloud_data')
      const response = await fetch(URL, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Error al cargar cuentas')
      accounts.value = data.length === 0 ? [] : data
    } catch (error) {
      console.error('Error cargando cuentas:', error)
    }
  }

  /**
   * Vacía completamente el store (cuentas y cuenta seleccionada).
   * Se usa al cerrar sesión.
   */
  const clearAccounts = () => {
    accounts.value = []
    selectedAccountId.value = null
    localStorage.removeItem('selectedCloudAccountId')
  }

  /**
   * Registra una nueva cuenta cloud en el backend y la añade al store.
   * @param {{name, provider, arn, description, regions}} payload - Datos del formulario.
   * @returns {Promise<Object>} Cuenta añadida al store (con status 'Activa').
   */
  const registerAccount = async ({ name, provider, arn, description, regions }) => {
    const token = localStorage.getItem('token')
    const response = await fetch(buildApiUrl('/cloud/register_cloud'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ name, provider, arn, description, regions })
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data?.detail || 'Error al registrar la cuenta')
    return addAccount({
      id: data.id,
      name,
      provider,
      identifier: arn,
      description,
      created_at: new Date().toISOString()
    })
  }

  /**
   * Actualiza los datos de una cuenta cloud en el backend y en el store.
   * @param {{id, name, provider, arn, description, regions}} payload
   * @returns {Promise<void>}
   */
  const updateCloudAccount = async ({ id, name, provider, arn, description, regions }) => {
    const token = localStorage.getItem('token')
    const response = await fetch(buildApiUrl('/cloud/update_cloud_data'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ id, name, description, regions })
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data?.detail || 'Error al actualizar la cuenta')
    updateAccount(id, { name, provider, arn, description, regions })
  }

  /**
   * Elimina una cuenta cloud del backend y del store.
   * @param {string} id - id de la cuenta a eliminar.
   * @returns {Promise<void>}
   */
  const removeCloudAccount = async (id) => {
    const token = localStorage.getItem('token')
    const response = await fetch(buildApiUrl('/cloud/delete_cloud_data'), {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ id })
    })
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data?.detail || 'Error al eliminar la cuenta')
    }
    deleteAccount(id)
  }

  return {
    accounts,
    selectedAccount,
    totalAccounts,
    addAccount,
    updateAccount,
    deleteAccount,
    selectAccount,
    loadSelectedAccount,
    loadAccounts,
    clearAccounts,
    registerAccount,
    updateCloudAccount,
    removeCloudAccount
  }
})
