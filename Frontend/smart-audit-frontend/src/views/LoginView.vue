
<template>
  <div class="login-container">
    <Toast />
    
    <div class="login-card">
      <div class="login-header">
        <div class="logo-container">
          <SmartAuditLogo :size="40" />
        </div>
        <h1>Smart Audit</h1>
        <p class="subtitle">Inicia sesión en tu cuenta</p>
        <Message v-if="verificationMessage" severity="success" size="small" class="mt-3">
          {{ verificationMessage }}
        </Message>
      </div>

      <Form v-slot="$form" :initialValues :resolver @submit="onFormSubmit" :disabled="isLoading"  class="flex flex-column gap-4">
        <div class="flex flex-column gap-2">
          <label for="username" class="font-semibold">Usuario</label>
          <InputText 
            id="username"
            name="username" 
            type="text" 
            placeholder="Ingresa tu usuario" 
            fluid 
          />
          <Message v-if="$form.username?.invalid" severity="error" size="small">
            {{ $form.username.error.message }}
          </Message>
        </div>

        <div class="flex flex-column gap-2">
          <label for="password" class="font-semibold">Contraseña</label>
          <Password 
            id="password"
            name="password" 
            placeholder="Ingresa tu contraseña" 
            :feedback="false" 
            toggleMask 
            fluid 
          />
          <Message v-if="$form.password?.invalid" severity="error" size="small">
            <ul class="my-0 px-4 flex flex-column gap-1">
              <li v-for="(error, index) of $form.password.errors" :key="index">
                {{ error.message }}
              </li>
            </ul>
          </Message>
        </div>

        <Button 
          type="submit" 
          label="Iniciar Sesión" 
          icon="pi pi-sign-in"
          class="login-button"
          :loading="isLoading"
          :disabled="isLoading"
        />

        <div class="text-center mt-3">
          <span class="text-color-secondary">¿No tienes cuenta? </span>
          <router-link to="/register" class="register-link">
            Regístrate aquí
          </router-link>
        </div>
      </Form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
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
import { useRoute, useRouter } from 'vue-router';
import { onMounted } from 'vue';
import { buildApiUrl } from '../utils/api';

const toast = useToast();
const router= useRouter();
const route = useRoute();
const verificationMessage = ref('');
onMounted(() => {
  if (route.query.verified) {
    verificationMessage.value = 'Email verificado exitosamente. Ahora puedes iniciar sesión.';
  }
});
const initialValues = ref({
  username: '',
  password: ''
});
const isLoading = ref(false);
const resolver = zodResolver(
  z.object({
    username: z.string().min(1, { message: 'El usuario es requerido.' }),
    password: z.string().min(1, { message: 'La contraseña es requerida.' })
  })
);

const onFormSubmit = async(e) => {
  if (!e?.valid) {
    return;
  }

  isLoading.value = true;
  try{
    const API_URL = buildApiUrl('/auth/login');
    const response = await 
    fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: e.values.username,
        password: e.values.password
      })
    });
  const data = await response.json();
  console.log("response ",response.status)
  if (response.status === 403) {
    toast.add({
      severity: 'error',
      summary: 'Error de inicio de sesión',
      detail: 'Tu correo electrónico no ha sido verificado. Por favor, verifica tu correo para activar tu cuenta.',
      life: 3000
    });
  }

    if (response.status==200) {
      toast.add({ 
        severity: 'success', 
        summary: 'Inicio de sesión exitoso', 
        detail: 'Bienvenido a Smart Audit',
         life: 3000 
      });
      
      console.log("token es  ",data.token)
      localStorage.setItem('token', data.token);

      setTimeout(() => {
        router.push('/app/cloud-accounts');
      }, 2000);
    }
    else if (response.status==401){
      toast.add({ 
        severity: 'error', 
        summary: 'Error de inicio de sesión', 
        detail: 'Credenciales inválidas. Revisa tu usuario y contraseña.',
         life: 3000 
      });
    }
  
    
  }
  catch (error) {
    console.error(error);
    toast.add({ 
      severity: 'error', 
      summary: 'Error de inicio de sesión', 
      detail: error.message || 'Revisa tus credenciales e inténtalo de nuevo',
      life: 3000 
    });
}finally{
  isLoading.value = false;
}
};
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
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-header {
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

.register-link {
  color: #22c55e;
  font-weight: 600;
  text-decoration: none;
  transition: color 0.2s;
}

.register-link:hover {
  color: #4ade80;
  text-decoration: underline;
}
</style>



