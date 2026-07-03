<template>
  <div class="legal-page">
    <nav class="legal-nav">
      <div class="legal-nav-content">
        <router-link to="/" class="back-link">
          <i class="pi pi-arrow-left" /> Smart Audit
        </router-link>
      </div>
    </nav>

    <main class="legal-main">
      <div class="legal-container">
        <header class="legal-header">
          <h1>Términos y Condiciones de Uso</h1>
          <p class="legal-date">Última actualización: julio de 2026</p>
        </header>

        <div class="legal-body">
          <section class="legal-section">
            <h2><span class="section-num">1.</span> Objeto</h2>
            <p>Los presentes Términos y Condiciones regulan el uso de <strong>SmartAudit AI</strong> (en adelante, "la Plataforma"), una herramienta de auditoría de seguridad para infraestructuras cloud desarrollada como Trabajo de Fin de Grado en el marco del Grado en Ingeniería Informática de la Universidad de Salamanca.</p>
          </section>

          <section class="legal-section">
            <h2><span class="section-num">2.</span> Naturaleza del servicio</h2>
            <p>SmartAudit AI es un proyecto académico. Su uso está destinado a fines demostrativos y de evaluación, no constituyendo un servicio comercial. El titular del proyecto no garantiza la disponibilidad continua ni la ausencia de errores en la Plataforma.</p>
          </section>

          <section class="legal-section">
            <h2><span class="section-num">3.</span> Uso del servicio</h2>
            <p>El usuario se compromete a utilizar la Plataforma únicamente sobre cuentas cloud de las que sea titular o esté debidamente autorizado, y a no emplear el servicio con fines maliciosos o contrarios a la legislación vigente.</p>
          </section>

          <section class="legal-section">
            <h2><span class="section-num">4.</span> Acceso a cuentas cloud de terceros</h2>
            <p>La Plataforma requiere acceso de solo lectura a la cuenta cloud del usuario mediante un rol IAM configurado por el propio usuario. SmartAudit AI no solicita ni almacena credenciales permanentes, limitándose a obtener credenciales temporales mediante el mecanismo <strong>AWS STS AssumeRole</strong>.</p>
          </section>

          <section class="legal-section">
            <h2><span class="section-num">5.</span> Limitación de responsabilidad</h2>
            <p>Dado su carácter académico, SmartAudit AI se ofrece "tal cual", sin garantías de ningún tipo. El titular del proyecto no será responsable de daños derivados del uso de las recomendaciones generadas por la Plataforma, siendo responsabilidad del usuario validar y aplicar dichas recomendaciones bajo su propio criterio.</p>
          </section>

          <section class="legal-section">
            <h2><span class="section-num">6.</span> Propiedad intelectual</h2>
            <p>El código fuente de la Plataforma es de acceso público y se encuentra disponible en el repositorio del proyecto.</p>
          </section>

          <section class="legal-section">
            <h2><span class="section-num">7.</span> Modificaciones</h2>
            <p>Estos Términos y Condiciones pueden ser modificados en cualquier momento, siendo la versión vigente la publicada en la Plataforma.</p>
          </section>
        </div>

        <footer class="legal-footer">
          <router-link to="/politica-privacidad" class="legal-footer-link">Política de Privacidad</router-link>
          <span class="legal-footer-sep">·</span>
          <router-link to="/" class="legal-footer-link">Volver al inicio</router-link>
        </footer>
      </div>
    </main>
  </div>
</template>

<script setup>
</script>

<style scoped>
.legal-page {
  min-height: 100vh;
  background: #0d1117;
  color: #e6edf3;
  font-family: 'Inter', system-ui, sans-serif;
}

/* Nav */
.legal-nav {
  background: #0d1117;
  border-bottom: 1px solid rgba(34, 197, 94, 0.15);
  padding: 1rem 2rem;
  position: sticky;
  top: 0;
  z-index: 10;
}

.legal-nav-content {
  max-width: 760px;
  margin: 0 auto;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: #22c55e;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
  transition: opacity 0.15s;
}

.back-link:hover { opacity: 0.75; }

/* Main */
.legal-main {
  padding: 3rem 2rem 5rem;
}

.legal-container {
  max-width: 760px;
  margin: 0 auto;
}

/* Header */
.legal-header {
  margin-bottom: 2.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #2d333b;
}

.legal-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: #e6edf3;
  margin: 0 0 0.5rem;
  line-height: 1.3;
  text-wrap: balance;
}

.legal-date {
  color: #768390;
  font-size: 0.85rem;
  margin: 0;
}

/* Sections */
.legal-body {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.legal-section {
  padding: 1.5rem 0;
  border-bottom: 1px solid #21262d;
}

.legal-section:last-child {
  border-bottom: none;
}

.legal-section h2 {
  font-size: 1rem;
  font-weight: 600;
  color: #e6edf3;
  margin: 0 0 0.75rem;
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.section-num {
  color: #22c55e;
  font-variant-numeric: tabular-nums;
  font-size: 0.9rem;
  flex-shrink: 0;
}

.legal-section p {
  color: #8b949e;
  font-size: 0.9rem;
  line-height: 1.75;
  margin: 0;
}

.legal-section strong {
  color: #c9d1d9;
  font-weight: 500;
}

/* Footer */
.legal-footer {
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid #2d333b;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.legal-footer-link {
  color: #768390;
  font-size: 0.85rem;
  text-decoration: none;
  transition: color 0.15s;
}

.legal-footer-link:hover { color: #22c55e; }

.legal-footer-sep {
  color: #2d333b;
  font-size: 0.85rem;
}
</style>
