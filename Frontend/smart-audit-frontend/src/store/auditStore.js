import { defineStore } from "pinia";
import { ref } from "vue";
import { set } from "zod";

export const useAuditStore = defineStore("audit", () => {
  const audits = ref([]);
  const selectedAudit = ref(null);
  const id = ref("");
  const auditResult = ref(null);
  const auditProgressByAccount = ref({});
  const auditingAccounts = ref({});
  const auditIdByAccount = ref({});

  const setAudits = (auditId,data) => {
    auditId.value = auditId;
    audits.value = data;
  }

  const startAccountAudit = (accountId, auditId) => {
    auditingAccounts.value[accountId] = true;
    auditProgressByAccount.value[accountId] = 0;
    auditIdByAccount.value[accountId] = auditId;
  }

  const clearData = () => {
    id.value = "";
    auditResult.value = null;
  }

  return {
    audits,
    selectedAudit,
    id,
    auditResult,
    auditProgressByAccount,
    setAudits,
    auditingAccounts,
    auditIdByAccount,
    clearData,
    startAccountAudit,
  };
});


