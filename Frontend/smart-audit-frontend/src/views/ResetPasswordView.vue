
<template>
  <div class="login-container">
    <Toast />

    <div class="login-card">
      <div class="login-header">
        <div class="logo-container">
          <SmartAuditLogo :size="40" />
        </div>
        <h1>Smart Audit</h1>
        <p class="subtitle">New password</p>
      </div>

      <!-- invalid / missing token -->
      <div v-if="!token" class="error-box">
        <p class="error-title">Invalid link</p>
        <p class="error-text">
          The reset link is invalid or has expired.
          Request a new one.
        </p>
        <router-link to="/forgot-password" class="action-link">
          Request new link
        </router-link>
      </div>

      <!-- success state -->
      <div v-else-if="done" class="success-box">
        <div class="success-icon">✓</div>
        <p class="success-title">Password updated</p>
        <p class="success-text">
          Your password has been reset successfully. You can now sign in.
        </p>
        <router-link to="/login" class="action-link">Sign in</router-link>
      </div>

      <!-- form -->
      <template v-else>
        <div class="flex flex-column gap-4">
          <div class="flex flex-column gap-2">
            <label for="password" class="font-semibold">New password</label>
            <Password
              id="password"
              v-model="password"
              placeholder="Minimum 8 characters"
              :feedback="true"
              toggleMask
              fluid
              :disabled="isLoading"
            />
            <span v-if="errors.password" class="field-error">{{ errors.password }}</span>
          </div>

          <div class="flex flex-column gap-2">
            <label for="confirm" class="font-semibold">Confirm password</label>
            <Password
              id="confirm"
              v-model="confirm"
              placeholder="Repeat your password"
              :feedback="false"
              toggleMask
              fluid
              :disabled="isLoading"
              @keydown.enter="submit"
            />
            <span v-if="errors.confirm" class="field-error">{{ errors.confirm }}</span>
          </div>

          <Button
            label="Reset password"
            icon="pi pi-lock"
            class="login-button"
            :loading="isLoading"
            :disabled="isLoading"
            @click="submit"
          />

          <div class="text-center mt-2">
            <router-link to="/login" class="back-link">
              ← Back to sign in
            </router-link>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import Button from 'primevue/button'
import Password from 'primevue/password'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'
import SmartAuditLogo from '../components/SmartAuditLogo.vue'
import { buildApiUrl } from '../utils/api'

const route = useRoute()
const toast = useToast()

const token = route.query.token || ''
const password = ref('')
const confirm = ref('')
const errors = ref({})
const isLoading = ref(false)
const done = ref(false)

const validate = () => {
  errors.value = {}
  if (!password.value) {
    errors.value.password = 'Password is required.'
  } else if (password.value.length < 8) {
    errors.value.password = 'Password must be at least 8 characters.'
  }
  if (!confirm.value) {
    errors.value.confirm = 'Please confirm your password.'
  } else if (password.value !== confirm.value) {
    errors.value.confirm = 'Passwords do not match.'
  }
  return Object.keys(errors.value).length === 0
}

const submit = async () => {
  if (!validate()) return
  isLoading.value = true
  try {
    const url = buildApiUrl(
      `/auth/reset-password/${token}` 
    )
    const res = await fetch(url, { method: 'POST' ,
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        new_password: password.value
      })
    }

    )
    if (res.ok) {
      done.value = true
    } else {
      const data = await res.json().catch(() => ({}))
      toast.add({
        severity: 'error',
        summary: 'Error',
        detail: data.detail || 'The link has expired or is invalid.',
        life: 5000
      })
    }
  } catch {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Could not reset password. Please try again.',
      life: 4000
    })
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0d1117;
  padding: 1rem;
}

.login-card {
  background: #161b22;
  border: 1px solid rgba(34, 197, 94, 0.15);
  border-radius: 16px;
  padding: 2.5rem;
  width: 100%;
  max-width: 440px;
  box-shadow: 0 0 40px rgba(0, 0, 0, 0.5);
  animation: fadeInUp 0.5s ease-out;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

.login-header {
  text-align: center;
  margin-bottom: 1.75rem;
}

.logo-container {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 16px;
  margin-bottom: 1rem;
}

.login-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: #e6edf3;
  margin: 0.5rem 0;
}

.subtitle {
  color: #8b949e;
  font-size: 0.95rem;
  margin: 0;
}

label {
  color: #c9d1d9;
  font-size: 0.9rem;
}

.field-error {
  color: #f87171;
  font-size: 0.8rem;
}

.login-button {
  width: 100%;
  padding: 0.75rem;
  font-weight: 600;
  background: #22c55e;
  border: none;
  transition: transform 0.2s, box-shadow 0.2s;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(34, 197, 94, 0.3);
  background: #16a34a;
}

.back-link {
  color: #22c55e;
  font-weight: 600;
  font-size: 0.9rem;
  text-decoration: none;
  transition: color 0.2s;
}

.back-link:hover {
  color: #4ade80;
  text-decoration: underline;
}

.action-link {
  color: #22c55e;
  font-weight: 600;
  font-size: 0.9rem;
  text-decoration: none;
}

.action-link:hover {
  color: #4ade80;
  text-decoration: underline;
}

/* success state */
.success-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 1.5rem;
  background: rgba(34, 197, 94, 0.07);
  border: 1px solid rgba(34, 197, 94, 0.25);
  border-radius: 12px;
  text-align: center;
}

.success-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  color: #22c55e;
}

.success-title {
  color: #e6edf3;
  font-weight: 600;
  font-size: 1rem;
  margin: 0;
}

.success-text {
  color: #8b949e;
  font-size: 0.875rem;
  line-height: 1.5;
  margin: 0;
}

/* error state */
.error-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 1.5rem;
  background: rgba(248, 113, 113, 0.07);
  border: 1px solid rgba(248, 113, 113, 0.25);
  border-radius: 12px;
  text-align: center;
}

.error-title {
  color: #fca5a5;
  font-weight: 600;
  font-size: 1rem;
  margin: 0;
}

.error-text {
  color: #8b949e;
  font-size: 0.875rem;
  line-height: 1.5;
  margin: 0;
}
</style>
