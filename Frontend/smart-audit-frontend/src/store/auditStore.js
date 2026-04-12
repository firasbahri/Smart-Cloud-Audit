import { defineStore } from "pinia";
import { ref } from "vue";
import { buildApiUrl } from '../utils/api';

export const useAuditStore = defineStore("audit", () => {
  const audits = ref([]);
  const selectedAudit = ref(null);
  const id = ref("");
  const auditResult = ref(null);
  const auditCreatedAt = ref(null);
  const auditProgressByAccount = ref({});
  const auditingAccounts = ref({});
  const auditIdByAccount = ref({});

  const setAudits = (auditIdValue, data) => {
    const normalized = Array.isArray(data) ? data : [];
    id.value = auditIdValue || "";
    audits.value = normalized;
    auditResult.value = normalized;
  };

  const startAccountAudit = (accountId, auditId) => {
    auditingAccounts.value[accountId] = true;
    auditProgressByAccount.value[accountId] = 0;
    auditIdByAccount.value[accountId] = auditId;
  }

  const clearData = () => {
    id.value = "";
    audits.value = [];
    auditResult.value = null;
  };

  const loadAuditDataForAccount = async (account) => {
    const accountId = account?.id || account?.account_id || account;
    if (!accountId) {
      clearData();
      return null;
    }

    try {
      const endpoint = buildApiUrl(`/cloud/last-audit-result/${accountId}`);
      const token = localStorage.getItem('token');
      if (!token) {
        clearData();
        return null;
      }

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Error fetching audit result');
      }

      const data = await response.json();
      const result = data.vulnerabilities || data.results || [];
      const auditID = data.audit_id || "";
      const createdAt = data.created_at || null;  

      setAudits(auditID, result);
      auditCreatedAt.value = createdAt;
      if (auditID) {
        auditIdByAccount.value[accountId] = auditID;
      }

      return data;
    } catch (error) {
      console.error('Error loading audit data:', error);
      clearData();
      return null;
    }
  };

  return {
    audits,
    selectedAudit,
    id,
    auditResult,
    auditCreatedAt,
    auditProgressByAccount,
    setAudits,
    auditingAccounts,
    auditIdByAccount,
    clearData,
    startAccountAudit,
    loadAuditDataForAccount
  };
});



