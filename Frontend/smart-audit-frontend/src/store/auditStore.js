import { defineStore } from "pinia";
import { ref } from "vue";
import { buildApiUrl } from '../utils/api';

export const useAuditStore = defineStore("audit", () => {
  const audits = ref([]);
  const auditsLoading = ref(false);
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
    auditResult.value = normalized;
  };

  const setAiAudits = (auditIdValue, data) => {
    aiAuditId.value = auditIdValue || "";
    aiAuditResult.value = Array.isArray(data) ? data : [];
  };

  const computeCounts = (vulnerabilities = []) => {
    const c = { critical: 0, high: 0, medium: 0, low: 0 };
    for (const v of vulnerabilities) {
      const s = (v.severity || "").toLowerCase();
      if (s === "critical") c.critical++;
      else if (s === "high") c.high++;
      else if (s === "medium") c.medium++;
      else if (s === "low") c.low++;
    }
    return c;
  };

  const normalizeAudit = (a) => ({
    ...a,
    vulnerabilities: a.vulnerabilities || [],
    counts: a.counts || computeCounts(a.vulnerabilities),
    origin: a.origin || "static",
  });

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
    auditsLoading.value = true;
    try {
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        }
      });
      if (response.status === 404) { audits.value = []; return; }
      if (!response.ok) throw new Error(`Error fetching audits: ${response.statusText}`);
      const data = await response.json();
      audits.value = (Array.isArray(data) ? data : []).map(normalizeAudit);
    } catch (error) {
      console.error("Failed to load audits:", error);
      audits.value = [];
    } finally {
      auditsLoading.value = false;
    }
  }

  return {
    audits,
    auditsLoading,
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



