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
            label="Sign In"
            text
            @click="$router.push('/login')"
            class="nav-btn"
          />
          <Button
            label="Register" 
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
            Cloud Security Auditing
            <span class="highlight">Automated and Intelligent</span>
          </h1>
          <p class="hero-description">
            Smart Audit analyzes your infrastructure in real time, identifies vulnerabilities
            and provides security recommendations based on industry best practices.
          </p>
          <div class="hero-buttons">
            <Button 
              label="Get started"
              icon="pi pi-arrow-right"
              iconPos="right"
              size="large"
              @click="$router.push('/register')"
              class="cta-button"
            />
            <Button 
              label="View demo"
              icon="pi pi-play"
              outlined
              size="large"
              class="demo-button"
            />
          </div>
        </div>
        <div class="hero-visual">
          <Card class="visual-card">
            <template #content>
            <SmartAuditLogo :size="120" />
            </template>
          </Card>
        </div>
      </div>
    </section>

  
    <section class="features-section">
      <h2 class="section-title">Key Features</h2>
      <div class="features-grid">
        <Card class="feature-card" v-for="feature in features" :key="feature.title">
          <template #content>
            <div class="feature-icon">
              <component :is="feature.icon" />
            </div>
            <h3>{{ feature.title }}</h3>
            <p>{{ feature.description }}</p>
          </template>
        </Card>
      </div>
    </section>

   
    <section class="services-section">
      <h2 class="section-title">Supported AWS Services</h2>
      <div class="services-grid">
        <Card class="service-card" v-for="service in services" :key="service.name">
          <template #content>
            <div class="service-icon">{{ service.icon }}</div>
            <Tag :value="service.name" severity="secondary" class="service-tag" />
          </template>
        </Card>
      </div>
    </section>


    <section class="cta-section">
      <div class="cta-content">
        <h2>Ready to secure your infrastructure?</h2>
        <p>Start your security audit today</p>
        <Button
          label="Create free account"
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
        <nav class="footer-links">
          <a href="mailto:contacto@smartaudit-ai.com">Contact</a>
          <a href="mailto:soporte@smartaudit-ai.com">Support</a>
          <router-link to="/politica-privacidad">Privacy</router-link>
          <router-link to="/terminos-y-condiciones">Terms</router-link>
        </nav>
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
import Card from 'primevue/card';
import Tag from 'primevue/tag';
import SmartAuditLogo from '../components/SmartAuditLogo.vue';
import { Shield, Search, BarChart3, Lock, Cloud, Zap } from 'lucide-vue-next';

const router = useRouter();

const features = ref([
  {
    title: 'Automatic Analysis',
    description: 'Full scan of AWS resources identifying insecure configurations.',
    icon: Search
  },
  {
    title: 'Vulnerability Detection',
    description: 'Identifies security risks based on CIS and AWS Well-Architected standards.',
    icon: Shield
  },
  {
    title: 'Detailed Reports',
    description: 'Visualize metrics and generate comprehensive reports of your security posture.',
    icon: BarChart3
  },
  {
    title: 'IAM Management',
    description: 'Analyze users, roles and policies to detect excessive permissions.',
    icon: Lock
  },
  {
    title: 'Cloud Inventory',
    description: 'Keep an up-to-date record of all your cloud resources.',
    icon: Cloud
  },
  {
    title: 'Fast Audits',
    description: 'Get results in minutes with our optimized analysis engine.',
    icon: Zap
  }
]);

const services = ref([
  { name: 'EC2', icon: '🖥️' },
  { name: 'S3', icon: '🪣' },
  { name: 'IAM', icon: '👤' }
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
  box-shadow: 0 0 40px rgba(34, 197, 94, 0.15);
  animation: float 3s ease-in-out infinite;
}

.visual-card :deep(.p-card-body) {
  padding: 3rem;
  display: flex;
  justify-content: center;
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
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s, box-shadow 0.3s;
}

.feature-card :deep(.p-card-body) {
  padding: 2rem;
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
  text-align: center;
  transition: transform 0.3s, border-color 0.3s;
}

.service-card :deep(.p-card-body) {
  padding: 1.5rem;
}

.service-card:hover {
  transform: scale(1.05);
  border-color: rgba(34, 197, 94, 0.35);
}

.service-icon {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.service-tag {
  margin-top: 0.25rem;
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

.footer-links {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.footer-links a {
  color: #8b949e;
  font-size: 0.9rem;
  text-decoration: none;
  transition: color 0.2s ease;
}

.footer-links a:hover {
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

