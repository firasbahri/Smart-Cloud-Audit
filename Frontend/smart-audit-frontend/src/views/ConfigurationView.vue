<template>
  <div class="configuration-view">
    <div class="page-header flex align-items-center gap-3 mb-5">
      <Settings :size="32" class="page-icon p-3 border-round-xl shadow-3" />
      <div>
        <h2 class="m-0">Configuración</h2>
        <p class="subtitle m-0 mt-2">Gestiona la configuración de la aplicación y preferencias</p>
      </div>
    </div>

    <div class="config-sections grid">
      <div class="config-card card-1 col-12 lg:col-6 xl:col-4">
        <div class="card-header">
          <Lock :size="24" />
          <h3>Seguridad</h3>
        </div>
        <div class="config-item">
          <label>
            <Checkbox v-model="settings.enableMFA" inputId="enableMFA" binary />
            <div>
              <span class="label-text">Autenticación multifactor</span>
              <ShieldCheck :size="16" class="label-icon" />
            </div>
          </label>
        </div>
        <div class="config-item">
          <label>
            <Checkbox v-model="settings.enableSSO" inputId="enableSSO" binary />
            <div>
              <span class="label-text">Inicio de sesión único (SSO)</span>
              <Key :size="16" class="label-icon" />
            </div>
          </label>
        </div>
      </div>

      <div class="config-card card-2 col-12 lg:col-6 xl:col-4">
        <div class="card-header">
          <Mail :size="24" />
          <h3>Notificaciones</h3>
        </div>
        <div class="config-item">
          <label>
            <Checkbox v-model="settings.emailNotifications" inputId="emailNotifications" binary />
            <div>
              <span class="label-text">Notificaciones por correo</span>
              <BellRing :size="16" class="label-icon" />
            </div>
          </label>
        </div>
        <div class="config-item">
          <label>
            <Checkbox v-model="settings.criticalAlerts" inputId="criticalAlerts" binary />
            <div>
              <span class="label-text">Alertas para problemas críticos</span>
              <AlertTriangle :size="16" class="label-icon" />
            </div>
          </label>
        </div>
        <div class="config-item input-group">
          <label for="email" class="input-label">
            <AtSign :size="16" />
            Email para notificaciones:
          </label>
          <InputText
            id="email" 
            v-model="settings.email" 
            type="email" 
            placeholder="tu@email.com"
          />
        </div>
      </div>

      <div class="config-card card-3 col-12 lg:col-6 xl:col-4">
        <div class="card-header">
          <Palette :size="24" />
          <h3>Apariencia</h3>
        </div>
        <div class="config-item input-group">
          <label for="theme" class="input-label">
            <Sun :size="16" />
            Tema:
          </label>
          <Select
            v-model="settings.theme"
            :options="themeOptions"
            optionLabel="label"
            optionValue="value"
            inputId="theme"
          />
        </div>
        <div class="config-item">
          <label>
            <Checkbox v-model="settings.compactView" inputId="compactView" binary />
            <div>
              <span class="label-text">Vista compacta</span>
              <Minimize2 :size="16" class="label-icon" />
            </div>
          </label>
        </div>
      </div>

      <div class="config-card card-4 col-12 lg:col-6 xl:col-4">
        <div class="card-header">
          <Clock :size="24" />
          <h3>Escaneos Programados</h3>
        </div>
        <div class="config-item">
          <label>
            <Checkbox v-model="settings.enableScheduledScans" inputId="enableScheduledScans" binary />
            <div>
              <span class="label-text">Escaneos automáticos</span>
              <TimerReset :size="16" class="label-icon" />
            </div>
          </label>
        </div>
        <div class="config-item input-group">
          <label for="scanFrequency" class="input-label">
            <Calendar :size="16" />
            Frecuencia de escaneo:
          </label>
          <Select
            v-model="settings.scanFrequency"
            :options="scanOptions"
            optionLabel="label"
            optionValue="value"
            inputId="scanFrequency"
            :disabled="!settings.enableScheduledScans"
          />
        </div>
      </div>

      <div class="config-card card-5 col-12 lg:col-6 xl:col-4">
        <div class="card-header">
          <HardDrive :size="24" />
          <h3>Datos</h3>
        </div>
        <Button class="action-btn export-btn" icon="pi pi-download" label="Exportar configuración" @click="exportSettings" />
        <Button class="action-btn reset-btn" icon="pi pi-refresh" label="Restablecer valores por defecto" severity="secondary" outlined @click="resetSettings" />
      </div>
    </div>

    <div class="actions flex gap-3 justify-content-center flex-wrap">
      <Button class="btn-primary" icon="pi pi-save" label="Guardar Cambios" @click="saveSettings" />
      <Button class="btn-secondary" icon="pi pi-times" label="Descartar" severity="secondary" outlined @click="discardChanges" />
    </div>

    <transition name="fade-slide">
      <Message v-if="messageSaved" severity="success" class="success-message fixed bottom-0 right-0 mb-4 mr-4" :closable="false">
        <template #icon>
          <CheckCircle2 :size="20" />
        </template>
        Configuración guardada exitosamente
      </Message>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import Button from 'primevue/button';
import Checkbox from 'primevue/checkbox';
import InputText from 'primevue/inputtext';
import Select from 'primevue/select';
import Message from 'primevue/message';
import { 
  Settings, Lock, Mail, Palette, Clock, HardDrive, 
  ShieldCheck, Key, BellRing, AlertTriangle, AtSign, 
  Sun, Minimize2, TimerReset, Calendar, CheckCircle2 
} from 'lucide-vue-next';

const settings = ref({
  enableMFA: true,
  enableSSO: false,
  emailNotifications: true,
  criticalAlerts: true,
  email: '',
  theme: 'light',
  compactView: false,
  enableScheduledScans: true,
  scanFrequency: 'weekly'
});

const messageSaved = ref(false);

const themeOptions = [
  { label: 'Claro', value: 'light' },
  { label: 'Oscuro', value: 'dark' },
  { label: 'Automático', value: 'auto' }
];

const scanOptions = [
  { label: 'Diario', value: 'daily' },
  { label: 'Semanal', value: 'weekly' },
  { label: 'Mensual', value: 'monthly' }
];

const saveSettings = () => {
  localStorage.setItem('appSettings', JSON.stringify(settings.value));
  messageSaved.value = true;
  setTimeout(() => {
    messageSaved.value = false;
  }, 3000);
};

const discardChanges = () => {
  const saved = localStorage.getItem('appSettings');
  if (saved) {
    settings.value = JSON.parse(saved);
  }
};

const resetSettings = () => {
  if (confirm('¿Está seguro de que desea restablecer todos los valores por defecto?')) {
    settings.value = {
      enableMFA: true,
      enableSSO: false,
      emailNotifications: true,
      criticalAlerts: true,
      email: '',
      theme: 'light',
      compactView: false,
      enableScheduledScans: true,
      scanFrequency: 'weekly'
    };
  }
};

const exportSettings = () => {
  const dataStr = JSON.stringify(settings.value, null, 2);
  const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
  const link = document.createElement('a');
  link.setAttribute('href', dataUri);
  link.setAttribute('download', 'smart-audit-config.json');
  link.click();
};

// Cargar configuración guardada al iniciar
const saved = localStorage.getItem('appSettings');
if (saved) {
  settings.value = JSON.parse(saved);
}
</script>

<style scoped>
.configuration-view {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.page-header {
  animation: slideDown 0.6s ease-out;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}

.page-icon {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
  animation: rotate 3s ease-in-out infinite;
}

@keyframes rotate {
  0%, 100% { transform: rotate(0deg); }
  50% { transform: rotate(180deg); }
}

.page-header h2 {
  margin: 0;
  color: #e6edf3;
  font-size: 2rem;
  font-weight: 700;
}

.subtitle {
  color: #8b949e;
  font-size: 1rem;
}

.config-sections {
  row-gap: 1.5rem;
  margin-bottom: 2rem;
}

.config-card {
  background: #161b22;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
  border: 1px solid rgba(34, 197, 94, 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
  animation: slideUp 0.6s ease-out both;
}

.card-1 { animation-delay: 0.1s; }
.card-2 { animation-delay: 0.2s; }
.card-3 { animation-delay: 0.3s; }
.card-4 { animation-delay: 0.4s; }
.card-5 { animation-delay: 0.5s; }

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.config-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px -4px rgba(0,0,0,0.1);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background: #21262d;
  border-bottom: 1px solid rgba(34, 197, 94, 0.1);
}

.card-header svg {
  color: #22c55e;
  flex-shrink: 0;
}

.card-header h3 {
  margin: 0;
  color: #e6edf3;
  font-size: 1.125rem;
  font-weight: 600;
}

.config-item {
  margin: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.config-item label {
  color: #c9d1d9;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.config-item label:hover {
  color: #22c55e;
}

.config-item label > div {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}

.label-text {
  flex: 1;
  font-weight: 500;
}

.label-icon {
  color: #94a3b8;
}

.config-item :deep(.p-checkbox) {
  width: 20px;
  height: 20px;
}

.input-group .input-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #8b949e;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.input-group .input-label svg {
  color: #22c55e;
}

.config-item :deep(.p-inputtext),
.config-item :deep(.p-select) {
  width: 100%;
  padding: 0.875rem;
  border: 2px solid rgba(34, 197, 94, 0.15);
  border-radius: 12px;
  font-size: 0.95rem;
  color: #c9d1d9;
  transition: all 0.3s ease;
  background: #21262d;
}

.config-item :deep(.p-inputtext:focus),
.config-item :deep(.p-select.p-focus) {
  outline: none;
  border-color: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.15);
  transform: translateY(-2px);
}

.config-item :deep(.p-select.p-disabled) {
  background-color: #161b22;
  color: #8b949e;
  cursor: not-allowed;
  transform: none;
}

.action-btn.p-button {
  width: 100%;
  margin: 0 1.5rem;
  margin-top: 0.75rem;
  padding: 0.875rem 1.5rem;
  border: 2px solid rgba(34, 197, 94, 0.15);
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.action-btn.p-button:first-of-type {
  width: calc(100% - 3rem);
}

.action-btn.p-button:last-of-type {
  width: calc(100% - 3rem);
  margin-bottom: 1.5rem;
}

.export-btn.p-button {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border-color: #10b981;
}

.export-btn.p-button:hover {
  transform: translateY(-2px);
  background: linear-gradient(135deg, #0ea271 0%, #047857 100%);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.reset-btn.p-button {
  background: #21262d;
  color: #8b949e;
  border: 2px solid rgba(34, 197, 94, 0.15);
}

.reset-btn.p-button:hover {
  background: #161b22;
  border-color: #22c55e;
  color: #22c55e;
  transform: translateY(-2px);
}

.actions {
  animation: slideUp 0.6s ease-out 0.6s both;
}

.btn-primary.p-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 2.5rem;
  background: #22c55e;
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 700;
  font-size: 1rem;
  box-shadow: 0 4px 15px rgba(34, 197, 94, 0.3);
  transition: all 0.3s ease;
}

.btn-primary.p-button:hover {
  transform: translateY(-2px);
  background: #16a34a;
  box-shadow: 0 6px 20px rgba(34, 197, 94, 0.4);
}

.btn-primary.p-button:active {
  transform: translateY(0);
}

.btn-secondary.p-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 2rem;
  background: #21262d;
  color: #8b949e;
  border: 2px solid rgba(34, 197, 94, 0.15);
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.btn-secondary.p-button:hover {
  background: #161b22;
  border-color: #22c55e;
  color: #22c55e;
  transform: translateY(-2px);
}

.success-message.p-message {
  background: linear-gradient(135deg, #dcfce7, #bbf7d0);
  color: #15803d;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(21, 128, 61, 0.3);
  font-weight: 600;
  z-index: 1000;
  animation: slideInRight 0.4s ease-out;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
