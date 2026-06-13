
<template>
  <div class="login-container">
    <Toast />

    <div class="login-card">
      <div class="login-header">
        <div class="logo-container">
          <SmartAuditLogo :size="40" />
        </div>
        <h1>Smart Audit</h1>
        <p class="subtitle">Recupera tu contraseña</p>
      </div>

      <div v-if="sent" class="success-box">
        <div class="success-icon">✓</div>
        <p class="success-title">Correo enviado</p>
        <p class="success-text">
          Si existe una cuenta con <strong>{{ sentEmail }}</strong>, recibirás un
          enlace para restablecer tu contraseña.
        </p>
        <router-link to="/login" class="back-link">Volver al inicio de sesión</router-link>
      </div>

      <template v-else>
        <p class="hint">
          Escribe tu correo y te enviaremos un enlace para restablecer tu contraseña.
        </p>

        <div class="flex flex-column gap-4">
          <div class="flex flex-column gap-2">
            <label for="email" class="font-semibold">Correo electrónico</label>
            <InputText
              id="email"
              v-model="email"
              type="email"
              placeholder="tu@correo.com"
              fluid
              :disabled="isLoading"
              @keydown.enter="submit"
            />
            <span v-if="emailError" class="field-error">{{ emailError }}</span>
          </div>

          <Button
            label="Enviar enlace"
            icon="pi pi-send"
            class="login-button"
            :loading="isLoading"
            :disabled="isLoading"
            @click="submit"
          />

          <div class="text-center mt-2">
            <router-link to="/login" class="back-link">
              ← Volver al inicio de sesión
            </router-link>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'
import SmartAuditLogo from '../components/SmartAuditLogo.vue'
import { buildApiUrl } from '../utils/api'

const toast = useToast()
const email = ref('')
const emailError = ref('')
const isLoading = ref(false)
const sent = ref(false)
const sentEmail = ref('')

const validate = () => {
  if (!email.value.trim()) {
    emailError.value = 'El correo es requerido.'
    return false
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) {
    emailError.value = 'Ingresa un correo válido.'
    return false
  }
  emailError.value = ''
  return true
}

const submit = async () => {
  if (!validate()) return
  isLoading.value = true
  try {
    const url = buildApiUrl(`/auth/forgot-password`)
    await fetch(url, { 
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: email.value.trim()
      })
    })
    sentEmail.value = email.value.trim()
    sent.value = true
  } catch {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'No se pudo enviar el correo. Inténtalo de nuevo.',
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

.hint {
  color: #8b949e;
  font-size: 0.875rem;
  line-height: 1.5;
  margin: 0 0 1.5rem;
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

.success-text strong {
  color: #c9d1d9;
}
</style>
