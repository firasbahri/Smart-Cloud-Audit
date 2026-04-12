<template>
  <div class="register-container">
    <Toast />
    
    <div class="register-card">
      <div class="register-header">
        <div class="logo-container">
          <SmartAuditLogo :size="40" />
        </div>
        <h1>Smart Audit</h1>
        <p class="subtitle">Crea tu cuenta</p>
      </div>

      <Form v-slot="$form" :initialValues :resolver @submit="register" :disabled="isLoading" class="flex flex-column gap-4"  > 
        <div class="flex flex-column gap-2">
          <label for="username" class="font-semibold">Usuario</label>
          <InputText 
            id="username"
            name="username" 
            type="text" 
            placeholder="Elige un nombre de usuario" 
            fluid 
          />
          <Message v-if="$form.username?.invalid" severity="error" size="small">
            {{ $form.username.error.message }}
          </Message>
        </div>

        <div class="flex flex-column gap-2">
          <label for="email" class="font-semibold">Correo electrónico</label>
          <InputText 
            id="email"
            name="email" 
            type="email" 
            placeholder="tu@email.com" 
            fluid 
          />
          <Message v-if="$form.email?.invalid" severity="error" size="small">
            {{ $form.email.error.message }}
          </Message>
        </div>

        <div class="flex flex-column gap-2">
          <label for="password" class="font-semibold">Contraseña</label>
          <Password 
            id="password"
            name="password" 
            placeholder="Crea una contraseña segura" 
            toggleMask 
            fluid 
          >
            <template #footer>
              <p class="password-hint">
                Debe contener mínimo 8 caracteres, mayúsculas, minúsculas y números
              </p>
            </template>
          </Password>
          <Message v-if="$form.password?.invalid" severity="error" size="small">
            <ul class="my-0 px-4 flex flex-column gap-1">
              <li v-for="(error, index) of $form.password.errors" :key="index">
                {{ error.message }}
              </li>
            </ul>
          </Message>
        </div>

        <div class="flex flex-column gap-2">
          <label for="confirmPassword" class="font-semibold">Confirmar contraseña</label>
          <Password 
            id="confirmPassword"
            name="confirmPassword" 
            placeholder="Repite tu contraseña" 
            :feedback="false"
            toggleMask 
            fluid 
          />
          <Message v-if="$form.confirmPassword?.invalid" severity="error" size="small">
            {{ $form.confirmPassword.error.message }}
          </Message>
        </div>

        <Button 
          type="submit" 
          label="Crear cuenta" 
          icon="pi pi-user-plus"
          class="register-button"
          :loading="isLoading"
          :disabled="isLoading"
        />

        <div class="text-center mt-3">
          <span class="text-color-secondary">¿Ya tienes cuenta? </span>
          <router-link to="/login" class="login-link">
            Inicia sesión aquí
          </router-link>
        </div>
      </Form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { zodResolver } from '@primevue/forms/resolvers/zod';
import { z } from 'zod';
import { useToast } from 'primevue/usetoast';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Password from 'primevue/password';
import Message from 'primevue/message';
import Toast from 'primevue/toast';
import { Form } from '@primevue/forms';
import SmartAuditLogo from '../components/SmartAuditLogo.vue';
import { is } from 'zod/v4/locales';
import { buildApiUrl } from '../utils/api';

const router = useRouter();
const toast = useToast();
const isLoading = ref(false);

const initialValues = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
});

const resolver = zodResolver(
  z.object({
    username: z
      .string()
      .min(3, { message: 'El usuario debe tener al menos 3 caracteres.' })
      .max(20, { message: 'El usuario no puede exceder 20 caracteres.' })
      .regex(/^[a-zA-Z0-9_]+$/, { 
        message: 'Solo letras, números y guiones bajos.' 
      }),
    email: z
      .string()
      .min(1, { message: 'El correo es requerido.' })
      .email({ message: 'Formato de correo inválido.' }),
    password: z
      .string()
      .min(8, { message: 'Mínimo 8 caracteres.' })
      .max(50, { message: 'Máximo 50 caracteres.' })
      .refine((value) => /[a-z]/.test(value), {
        message: 'Debe tener una letra minúscula.'
      })
      .refine((value) => /[A-Z]/.test(value), {
        message: 'Debe tener una letra mayúscula.'
      })
      .refine((value) => /\d/.test(value), {
        message: 'Debe tener un número.'
      }),
    confirmPassword: z
      .string()
      .min(1, { message: 'Debes confirmar tu contraseña.' })
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Las contraseñas no coinciden.',
    path: ['confirmPassword']
  })
);

const register = async (e) => {
  if (!e?.valid) {
    return;
  }

   isLoading.value = true;
  isLoading.value = true;
  try{
    const API_URL = buildApiUrl('/auth/register');
    const response = await fetch(API_URL,{
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(e.values)
    })
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Error desconocido');
    }
      toast.add({ 
      severity: 'success', 
      summary: 'Verificación enviada', 
      detail: 'Por favor, verifica tu correo electrónico para activar tu cuenta.',
      life: 3000 
    });
      setTimeout(() => {
      router.push('/login');
    }, 2000);

  } catch (error) {
    console.error(error);
    toast.add({ 
      severity: 'error', 
      summary: 'Error de registro', 
      detail: error.message || 'Fallo al crear la cuenta',
      life: 3000 
    });
  } finally {
    isLoading.value = false;
  }

};
        
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0d1117;
  padding: 1rem;
}

.register-card {
  background: #161b22;
  border: 1px solid rgba(34, 197, 94, 0.15);
  border-radius: 16px;
  padding: 2.5rem;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 0 40px rgba(0, 0, 0, 0.5);
  animation: fadeInUp 0.5s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.register-header {
  text-align: center;
  margin-bottom: 2rem;
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
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

.register-header h1 {
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

.password-hint {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #8b949e;
  line-height: 1.4;
}

.register-button {
  width: 100%;
  padding: 0.75rem;
  font-weight: 600;
  background: #22c55e;
  border: none;
  transition: transform 0.2s, box-shadow 0.2s;
}

.register-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(34, 197, 94, 0.3);
  background: #16a34a;
}

.login-link {
  color: #22c55e;
  font-weight: 600;
  text-decoration: none;
  transition: color 0.2s;
}

.login-link:hover {
  color: #4ade80;
  text-decoration: underline;
}

/* Scrollbar personalizado para navegadores webkit */
.register-card::-webkit-scrollbar {
  width: 8px;
}

.register-card::-webkit-scrollbar-track {
  background: #21262d;
  border-radius: 4px;
}

.register-card::-webkit-scrollbar-thumb {
  background: rgba(34, 197, 94, 0.3);
  border-radius: 4px;
}

.register-card::-webkit-scrollbar-thumb:hover {
  background: rgba(34, 197, 94, 0.5);
}
</style>