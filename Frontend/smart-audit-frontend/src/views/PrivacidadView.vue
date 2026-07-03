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
          <h1>Política de Privacidad</h1>
          <p class="legal-date">Última actualización: julio de 2026</p>
        </header>

        <div class="legal-body">
          <section class="legal-section">
            <h2><span class="section-num">1.</span> Responsable del tratamiento</h2>
            <p>El responsable del tratamiento de los datos personales recogidos en <strong>SmartAudit AI</strong> es <strong>Mohamed Firas Bahri</strong>, estudiante de la Universidad de Salamanca, contactable en la dirección de correo electrónico indicada en la Plataforma. SmartAudit AI es un proyecto académico sin finalidad comercial.</p>
          </section>

          <section class="legal-section">
            <h2><span class="section-num">2.</span> Datos recogidos</h2>
            <p>La Plataforma recoge únicamente los datos estrictamente necesarios para su funcionamiento:</p>
            <ul>
              <li><strong>Datos de registro:</strong> nombre de usuario y contraseña (almacenada en formato hash bcrypt).</li>
              <li><strong>Datos de infraestructura:</strong> ARN de rol IAM, identificador de cuenta AWS y resultados de los análisis de seguridad realizados.</li>
            </ul>
          </section>

          <section class="legal-section">
            <h2><span class="section-num">3.</span> Finalidad del tratamiento</h2>
            <p>Los datos recogidos se utilizan exclusivamente para:</p>
            <ul>
              <li>Autenticar al usuario en la Plataforma.</li>
              <li>Realizar auditorías de seguridad sobre la cuenta cloud indicada por el usuario.</li>
              <li>Almacenar y mostrar el historial de auditorías del usuario dentro de la Plataforma.</li>
            </ul>
          </section>

          <section class="legal-section">
            <h2><span class="section-num">4.</span> Base jurídica</h2>
            <p>El tratamiento se basa en el consentimiento del usuario, prestado en el momento del registro. El usuario puede revocar dicho consentimiento en cualquier momento solicitando la eliminación de su cuenta.</p>
          </section>

          <section class="legal-section">
            <h2><span class="section-num">5.</span> Conservación de datos</h2>
            <p>Los datos se conservan mientras el usuario mantenga su cuenta activa. Una vez eliminada la cuenta, todos los datos asociados son borrados de forma permanente del sistema.</p>
          </section>

          <section class="legal-section">
            <h2><span class="section-num">6.</span> Transferencia a terceros</h2>
            <p>Los datos de configuración de la cuenta cloud y el contexto de auditoría son enviados a la API de <strong>Google Gemini</strong> para la generación de análisis de seguridad mediante IA. Este envío se produce únicamente cuando el usuario solicita de forma explícita un análisis IA. No se ceden datos a ningún otro tercero.</p>
          </section>

          <section class="legal-section">
            <h2><span class="section-num">7.</span> Derechos del usuario</h2>
            <p>De conformidad con el RGPD, el usuario tiene derecho a acceder, rectificar y suprimir sus datos. Para ejercer cualquiera de estos derechos, puede escribir a la dirección de correo electrónico indicada en la sección de contacto de la Plataforma.</p>
          </section>
        </div>

        <footer class="legal-footer">
          <router-link to="/terminos-y-condiciones" class="legal-footer-link">Términos y Condiciones</router-link>
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
  margin: 0 0 0.5rem;
}

.legal-section p:last-child { margin-bottom: 0; }

.legal-section ul {
  margin: 0.5rem 0 0;
  padding-left: 1.25rem;
  color: #8b949e;
  font-size: 0.9rem;
  line-height: 1.75;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.legal-section li { padding-left: 0.25rem; }

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
