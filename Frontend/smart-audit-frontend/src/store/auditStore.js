import { defineStore } from "pinia";
import { ref } from "vue";
import { buildApiUrl } from '../utils/api';

export const useAuditStore = defineStore("audit", () => {
  const audits = ref([]);
  const selectedAudit = ref(null);
  const id = ref("");
  const auditResult = ref(null);       // static vulnerabilities
  const aiAuditResult = ref([]);       // AI vulnerabilities
  const aiAuditId = ref("");
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

  const setAiAudits = (auditIdValue, data) => {
    console.log('Estableciendo auditoría IA con ID:', auditIdValue, 'y datos:', data);
    aiAuditId.value = auditIdValue || "";
    aiAuditResult.value = Array.isArray(data) ? data : [];
  };

  const startAccountAudit = (accountId, auditId) => {
    auditingAccounts.value[accountId] = true;
    auditProgressByAccount.value[accountId] = 0;
    auditIdByAccount.value[accountId] = auditId;
  }

  const clearData = () => {
    id.value = "";
    aiAuditId.value = "";
    audits.value = [];
    auditResult.value = null;
    aiAuditResult.value = [];
  };

  const loadAuditsForAccount = async (account) => {
    const id = account.id || account.account_id;
    const token = localStorage.getItem("token");
    const url = buildApiUrl(`/cloud/my-audits/${id}`);
    try {
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        }
      });
      if (!response.ok) throw new Error(`Error fetching audits: ${response.statusText}`);
      const data = await response.json();
      audits.value = Array.isArray(data) ? data : [];
    } catch (error) {
      console.error("Failed to load audits:", error);
      audits.value = [];
    }
  }

  return {
    audits,
    selectedAudit,
    id,
    aiAuditId,
    auditResult,
    aiAuditResult,
    auditCreatedAt,
    auditProgressByAccount,
    setAudits,
    setAiAudits,
    auditingAccounts,
    auditIdByAccount,
    clearData,
    startAccountAudit,
    loadAuditsForAccount
  };
});



