<template>
  <div class="login-page min-h-screen w-screen flex align-items-center justify-content-center relative overflow-hidden">
    <div class="animated-background">
      <div class="floating-icon" v-for="i in 6" :key="i" :style="{ '--delay': i * 0.5 + 's' }"></div>
    </div>
    
    <div class="login-card surface-card border-round-2xl shadow-7 p-6 md:p-8 text-center w-11 md:w-6 lg:w-4 relative z-2">
      <div class="icon-container inline-flex mb-4">
        <Shield class="main-icon" :size="64" :stroke-width="1.5" />
      </div>
      
      <h1 class="title m-0 mb-2">Smart AI Audit</h1>
      <p class="subtitle m-0 mb-5">Introduce el ARN del rol para conectar con AWS</p>
      
      <div class="input-group mb-4">
        <Key class="input-icon" :size="20" />
        <InputText
          v-model="localArn" 
          type="text" 
          placeholder="arn:aws:iam::123456789012:role/..."
          class="modern-input"
        />
      </div>
      
      <Button @click="startScan" :disabled="isLoading" class="modern-button w-full" fluid>
        <template #icon>
          <ProgressSpinner
            v-if="isLoading"
            style="width: 18px; height: 18px"
            strokeWidth="8"
            fill="transparent"
            animationDuration="1s"
          />
          <CloudCog v-else :size="20" />
        </template>
        <span>{{ isLoading ? 'Conectando con AWS...' : 'Iniciar Auditoría' }}</span>
      </Button>
      
      <transition name="fade-slide">
        <Message v-if="errorMsg" severity="error" class="error-banner mt-4 text-left" :closable="false">
          <template #icon>
            <AlertCircle :size="20" />
          </template>
          {{ errorMsg }}
        </Message>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useScanStore } from '../store/scanStore';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';
import Message from 'primevue/message';
import ProgressSpinner from 'primevue/progressspinner';
import { Shield, Key, CloudCog, AlertCircle } from 'lucide-vue-next';
import { buildApiUrl } from '../utils/api';

const router = useRouter();
const scanStore = useScanStore();
const localArn = ref('');
const isLoading = ref(false);
const errorMsg = ref('');

const startScan = async () => {
  if (!localArn.value) {
    errorMsg.value = 'Por favor, introduce un ARN.';
    return;
  }
  
  isLoading.value = true;
  errorMsg.value = '';

  try {
    const API_URL = buildApiUrl('/'); 

    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ arn: localArn.value })
    });

    if (!response.ok) throw new Error(`Error ${response.status}`);
    
    const data = await response.json();
    
    auditStore.setScanData(localArn.value, data.body ? JSON.parse(data.body) : data);
    
    router.push('/app/inventory');

  } catch (error) {
    console.error(error);
    errorMsg.value = 'Fallo de conexión. Revisa la consola o la URL.';
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.login-page {
  background: #0d1117;
}

.animated-background {
  position: absolute;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.floating-icon {
  position: absolute;
  width: 60px;
  height: 60px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  animation: float 6s ease-in-out infinite;
  animation-delay: var(--delay);
}

.floating-icon:nth-child(1) { top: 10%; left: 10%; }
.floating-icon:nth-child(2) { top: 20%; right: 15%; animation-duration: 7s; }
.floating-icon:nth-child(3) { bottom: 15%; left: 20%; animation-duration: 8s; }
.floating-icon:nth-child(4) { bottom: 30%; right: 10%; animation-duration: 6.5s; }
.floating-icon:nth-child(5) { top: 50%; left: 5%; animation-duration: 7.5s; }
.floating-icon:nth-child(6) { top: 60%; right: 5%; animation-duration: 8.5s; }

@keyframes float {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(5deg); }
}

.login-card {
  background: #161b22;
  border: 1px solid rgba(34, 197, 94, 0.15);
  backdrop-filter: blur(10px);
  max-width: 520px;
  animation: slideUp 0.6s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.icon-container {
  padding: 1.5rem;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 20px;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.main-icon {
  color: #22c55e;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
}

.title {
  font-size: 2rem;
  font-weight: 700;
  color: #22c55e;
}

.subtitle {
  color: #8b949e;
  font-size: 0.95rem;
}

.input-group {
  position: relative;
}

.input-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  z-index: 1;
}

.modern-input.p-inputtext {
  width: 100%;
  padding: 1rem 1rem 1rem 3rem;
  border: 2px solid rgba(34, 197, 94, 0.15);
  border-radius: 12px;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.modern-input.p-inputtext:focus {
  outline: none;
  border-color: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.15);
  transform: translateY(-2px);
}

.modern-button.p-button {
  padding: 1rem 2rem;
  background: #22c55e;
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(34, 197, 94, 0.3);
}

.modern-button.p-button:hover:not(:disabled) {
  transform: translateY(-2px);
  background: #16a34a;
  box-shadow: 0 6px 20px rgba(34, 197, 94, 0.4);
}

.modern-button.p-button:active:not(:disabled) {
  transform: translateY(0);
}

.modern-button.p-button:disabled {
  background: linear-gradient(135deg, #94a3b8 0%, #cbd5e1 100%);
  cursor: not-allowed;
  box-shadow: none;
}

.error-banner.p-message {
  border-radius: 12px;
  font-size: 0.9rem;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
