<template>
  <div class="home-page">
    <!-- Navbar -->
    <nav class="navbar">
      <div class="navbar-content">
        <div class="logo-section">
          <SmartAuditLogo :size="40" />
          <span class="brand-name">Smart Audit</span>
        </div>
        <div class="nav-actions">
          <Button 
            label="Iniciar Sesión" 
            text 
            @click="$router.push('/login')"
            class="nav-btn"
          />
          <Button 
            label="Registrarse" 
            @click="$router.push('/register')"
            class="register-btn"
          />
        </div>
      </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-text">
          <h1 class="hero-title">
            Auditoría de Seguridad en AWS
            <span class="highlight">Automatizada e Inteligente</span>
          </h1>
          <p class="hero-description">
            Smart Audit analiza tu infraestructura AWS en tiempo real, identifica vulnerabilidades 
            y proporciona recomendaciones de seguridad basadas en las mejores prácticas de la industria.
          </p>
          <div class="hero-buttons">
            <Button 
              label="Comenzar ahora" 
              icon="pi pi-arrow-right"
              iconPos="right"
              size="large"
              @click="$router.push('/register')"
              class="cta-button"
            />
            <Button 
              label="Ver demo" 
              icon="pi pi-play"
              outlined
              size="large"
              class="demo-button"
            />
          </div>
        </div>
        <div class="hero-visual">
          <div class="visual-card">
            <SmartAuditLogo :size="120" />
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features-section">
      <h2 class="section-title">Características Principales</h2>
      <div class="features-grid">
        <div class="feature-card" v-for="feature in features" :key="feature.title">
          <div class="feature-icon">
            <component :is="feature.icon" />
          </div>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.description }}</p>
        </div>
      </div>
    </section>

    <!-- Services Section -->
    <section class="services-section">
      <h2 class="section-title">Servicios AWS Soportados</h2>
      <div class="services-grid">
        <div class="service-card" v-for="service in services" :key="service.name">
          <div class="service-icon">{{ service.icon }}</div>
          <h4>{{ service.name }}</h4>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
      <div class="cta-content">
        <h2>¿Listo para asegurar tu infraestructura?</h2>
        <p>Comienza tu auditoría de seguridad hoy mismo</p>
        <Button 
          label="Crear cuenta gratis" 
          icon="pi pi-user-plus"
          size="large"
          @click="$router.push('/register')"
          class="cta-final-button"
        />
      </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
      <div class="footer-content">
        <div class="footer-logo">
          <SmartAuditLogo :size="32" />
          <span>Smart Audit</span>
        </div>
        <p class="footer-text">
          © 2026 Smart Audit - Trabajo Fin de Grado
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import Button from 'primevue/button';
import SmartAuditLogo from '../components/SmartAuditLogo.vue';
import { Shield, Search, BarChart3, Lock, Cloud, Zap } from 'lucide-vue-next';

const router = useRouter();

const features = ref([
  {
    title: 'Análisis Automático',
    description: 'Escaneo completo de recursos AWS identificando configuraciones inseguras.',
    icon: Search
  },
  {
    title: 'Detección de Vulnerabilidades',
    description: 'Identifica riesgos de seguridad basados en estándares CIS y AWS Well-Architected.',
    icon: Shield
  },
  {
    title: 'Reportes Detallados',
    description: 'Visualiza métricas y genera informes comprensivos de tu postura de seguridad.',
    icon: BarChart3
  },
  {
    title: 'Gestión IAM',
    description: 'Analiza usuarios, roles y políticas para detectar permisos excesivos.',
    icon: Lock
  },
  {
    title: 'Inventario Cloud',
    description: 'Mantén un registro actualizado de todos tus recursos en la nube.',
    icon: Cloud
  },
  {
    title: 'Auditorías Rápidas',
    description: 'Obtén resultados en minutos con nuestro motor de análisis optimizado.',
    icon: Zap
  }
]);

const services = ref([
  { name: 'EC2', icon: '🖥️' },
  { name: 'S3', icon: '🪣' },
  { name: 'IAM', icon: '👤' },
  { name: 'VPC', icon: '🔒' },
  { name: 'RDS', icon: '💾' },
  { name: 'Lambda', icon: 'λ' }
]);
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: #0d1117;
}

/* Navbar */
.navbar {
  background: #0d1117;
  border-bottom: 1px solid rgba(34, 197, 94, 0.15);
  position: sticky;
  top: 0;
  z-index: 1000;
  padding: 1rem 2rem;
}

.navbar-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.brand-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: #22c55e;
}

.nav-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.register-btn {
  background: #22c55e;
  border: none;
}

.register-btn:hover {
  background: #16a34a;
}

/* Hero Section */
.hero-section {
  padding: 4rem 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.hero-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
  align-items: center;
}

.hero-title {
  font-size: 3rem;
  font-weight: 800;
  color: #e6edf3;
  margin: 0 0 1.5rem 0;
  line-height: 1.2;
}

.highlight {
  display: block;
  color: #22c55e;
}

.hero-description {
  font-size: 1.125rem;
  color: #8b949e;
  line-height: 1.7;
  margin-bottom: 2rem;
}

.hero-buttons {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.cta-button {
  background: #22c55e;
  border: none;
  padding: 0.75rem 2rem;
  font-weight: 600;
}

.cta-button:hover {
  background: #16a34a;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(34, 197, 94, 0.3);
}

.demo-button {
  border-color: #22c55e;
  color: #22c55e;
  font-weight: 600;
}

.hero-visual {
  display: flex;
  justify-content: center;
  align-items: center;
}

.visual-card {
  background: #161b22;
  border: 1px solid rgba(34, 197, 94, 0.25);
  padding: 3rem;
  border-radius: 20px;
  box-shadow: 0 0 40px rgba(34, 197, 94, 0.15);
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
}

/* Features Section */
.features-section {
  padding: 4rem 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.section-title {
  text-align: center;
  font-size: 2.5rem;
  font-weight: 700;
  color: #e6edf3;
  margin-bottom: 3rem;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.feature-card {
  background: #161b22;
  border: 1px solid rgba(34, 197, 94, 0.1);
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s, box-shadow 0.3s;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(34, 197, 94, 0.2);
  border-color: rgba(34, 197, 94, 0.3);
}

.feature-icon {
  width: 60px;
  height: 60px;
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #22c55e;
  margin-bottom: 1rem;
}

.feature-card h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #e6edf3;
  margin-bottom: 0.75rem;
}

.feature-card p {
  color: #8b949e;
  line-height: 1.6;
}

/* Services Section */
.services-section {
  padding: 4rem 2rem;
  background: #161b22;
  border-top: 1px solid rgba(34, 197, 94, 0.1);
  border-bottom: 1px solid rgba(34, 197, 94, 0.1);
}

.services-grid {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1.5rem;
}

.service-card {
  background: #21262d;
  border: 1px solid rgba(34, 197, 94, 0.08);
  padding: 1.5rem;
  border-radius: 12px;
  text-align: center;
  transition: transform 0.3s, border-color 0.3s;
}

.service-card:hover {
  transform: scale(1.05);
  border-color: rgba(34, 197, 94, 0.35);
}

.service-icon {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.service-card h4 {
  font-size: 1rem;
  font-weight: 600;
  color: #e6edf3;
  margin: 0;
}

/* CTA Section */
.cta-section {
  padding: 4rem 2rem;
  background: radial-gradient(ellipse at center, rgba(34, 197, 94, 0.1) 0%, #0d1117 70%);
  color: white;
  text-align: center;
}

.cta-content h2 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: #e6edf3;
}

.cta-content p {
  font-size: 1.25rem;
  margin-bottom: 2rem;
  color: #8b949e;
}

.cta-final-button {
  background: #22c55e;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  font-weight: 600;
  font-size: 1.1rem;
}

.cta-final-button:hover {
  background: #16a34a;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(34, 197, 94, 0.3);
}

/* Footer */
.footer {
  background: #0d1117;
  border-top: 1px solid rgba(34, 197, 94, 0.15);
  color: white;
  padding: 2rem;
  text-align: center;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
}

.footer-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: #22c55e;
}

.footer-text {
  color: #8b949e;
  margin: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .hero-content {
    grid-template-columns: 1fr;
  }

  .hero-title {
    font-size: 2rem;
  }

  .section-title {
    font-size: 1.75rem;
  }

  .navbar-content {
    flex-direction: column;
    gap: 1rem;
  }

  .cta-content h2 {
    font-size: 1.75rem;
  }
}
</style>

