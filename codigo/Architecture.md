# Arquitectura de SmartAudit AI

## ¿Qué es SmartAudit AI?

Plataforma de auditoría de seguridad cloud para AWS. Permite a empresas y desarrolladores detectar vulnerabilidades en su infraestructura AWS mediante escaneo automático de recursos y análisis contextual con IA.

---

## Stack tecnológico

### Backend
- **FastAPI** — framework principal de la API REST
- **Celery** — gestión de tareas en segundo plano
- **RabbitMQ** — broker de mensajes para Celery
- **MongoDB** — base de datos principal
- **PyMongo Async** — driver asíncrono oficial de MongoDB
- **Boto3** — SDK de AWS para escaneo de recursos
- **Google Gemini API** — análisis con IA y generación de recomendaciones/comandos CLI
- **SSE (Server-Sent Events)** — notificaciones en tiempo real al frontend

### Frontend
- **Vue 3** — framework de interfaz de usuario
- **PrimeVue** — librería de componentes UI
- **Pinia** — gestión de estado global
- **Vue Router** — enrutamiento
- **Fetch API nativo** — peticiones HTTP (sin librería externa como Axios)
- **EventSource** — recepción de eventos SSE nativos del navegador

---

## Arquitectura general

```
Vue 3 (Frontend)
    │
    │ HTTP / SSE
    ▼
FastAPI (API REST)
    │                    │
    │ Celery.delay()     │ SSE endpoint
    ▼                    ▼
RabbitMQ            Cliente Vue
    │
    ▼
Celery Worker
    │
    ├── Boto3 → AWS (STS AssumeRole)
    │
    └── MongoDB (progreso + recursos)
```

---

## Decisiones de diseño

### 1. Separación entre Escaneo y Auditoría

**Decisión:** escaneo y auditoría son dos funcionalidades completamente separadas.

**Razonamiento:**
- El **escaneo** es una operación técnica — obtiene recursos de AWS con Boto3. Es costoso en tiempo y llamadas a la API de AWS.
- La **auditoría** es un análisis inteligente — interpreta los recursos escaneados con contexto del usuario y IA.
- Esta separación permite al usuario escanear una vez y auditar múltiples veces sin coste adicional.

**Consecuencia en el diseño:**
- Un usuario solo tiene **un scan activo por cuenta AWS** — se sobreescribe en cada escaneo.
- Un usuario puede tener **múltiples auditorías** por cuenta — se guarda historial completo.

---

### 2. Celery + RabbitMQ para tareas en segundo plano

**Decisión:** usar Celery con RabbitMQ como broker para ejecutar el escaneo en segundo plano.

**Alternativa descartada:** Worker manual con aio_pika.

**Razonamiento:**
- El escaneo de AWS puede tardar varios minutos — no puede ejecutarse en el hilo principal de FastAPI.
- Celery gestiona automáticamente la conexión a RabbitMQ, la declaración de colas, los reintentos y la cancelación de tareas.
- RabbitMQ garantiza que ningún mensaje (tarea de escaneo) se pierda aunque el worker caiga.
- En producción permite escalar workers independientemente de FastAPI.

---

### 3. SSE en vez de WebSocket para notificaciones de progreso

**Decisión:** usar Server-Sent Events (SSE) para notificar el progreso del escaneo al frontend.

**Alternativa descartada:** WebSocket, polling cada 5 segundos.

**Razonamiento:**
- La comunicación es **unidireccional** — solo el servidor necesita hablar con el cliente.
- SSE es más simple que WebSocket para casos unidireccionales.
- SSE usa HTTP estándar — sin cambio de protocolo ni handshake complejo.
- El navegador reconecta automáticamente si se pierde la conexión.
- Elimina el coste del polling (peticiones innecesarias cada 5 segundos).

---

### 4. STS AssumeRole para acceso a cuentas AWS del cliente

**Decisión:** usar AWS STS AssumeRole para acceder a las cuentas AWS de los clientes.

**Razonamiento:**
- El cliente nunca comparte sus credenciales permanentes con SmartAudit.
- STS genera credenciales temporales (máximo 1 hora) — si se roban, expiran solas.
- Es el estándar de la industria usado por herramientas como Wiz o Prisma Cloud.
- Se aplica el principio de mínimo privilegio — el rol solo tiene permisos de lectura.

**Flujo:**
```
SmartAudit → STS AssumeRole → credenciales temporales → escanea cuenta del cliente
```

---

### 5. Interfaces abstractas para desacoplar responsabilidades

**Decisión:** cada capa con múltiples implementaciones tiene su propia interfaz abstracta.

```
IRepository  → auditRepository, cloudRepository, ScanRepository, userRepository
IScanner     → AwsScanner (en el futuro AzureScanner, GCPScanner)
IAnalyzer    → AWSAnalyzer, que internamente orquesta IAM_Analyzer, ec2_analyzer y s3_analyzer
ILLMAnalyzer → GeminiAnalyzer (en el futuro, otros modelos de IA)
```

**Razonamiento:**
- Desacopla completamente cada capa de sus implementaciones concretas.
- Añadir un nuevo proveedor cloud (Azure) solo requiere crear `AzureScanner` que implemente `IScanner` — sin tocar nada más.
- Añadir nuevas reglas de seguridad solo requiere crear un nuevo analyzer y sumarlo dentro de `AWSAnalyzer` — sin tocar el scanner ni los servicios.
- Añadir un modelo de IA distinto a Gemini solo requiere implementar `ILLMAnalyzer` y sumarlo en `AIAnalyzerFactory` — sin tocar el controller ni los servicios.
- Permite cambiar de MongoDB a cualquier otra base de datos modificando solo el repositorio correspondiente.
- Garantiza consistencia en los métodos entre implementaciones.

---

### 6. Arquitectura en capas

**Decisión:** arquitectura en capas estricta — api → service → repository → BD.

```
Backend/
├── api/                   → recibe requests HTTP, devuelve responses
│     auth.py
│     cloud_audit.py
│     cloud_scan.py
│     cloudAuth.py
├── services/              → lógica de negocio, trabaja con modelos
│     auth_service.py
│     cloudAudit_service.py
│     cloudAuth_service.py
│     cloudScan_service.py
│     email_service.py
│     JSONSerializer.py
│     JSONDeserializer.py
├── Repositories/          → acceso a MongoDB
│     IRepository.py
│     auditRepository.py
│     cloudRepository.py
│     ScanRepository.py
│     userRepository.py
├── Model/                 → objetos del dominio
│     user.py, cloud.py, scanResult.py, auditResult.py
│     vulnerability.py, resource.py, s3Bucket.py
│     EC2_Model/ (EC2.py, Rule.py, SecurityGroup.py)
│     IAM_Model/ (IAMUser.py, IAMGroup.py, IAMRole.py)
├── controllers/           → orquesta el flujo de escaneo y auditoría
│     scan_Controller.py
│     auditController.py
├── scanners/              → obtienen recursos de AWS con Boto3
│     IScanner.py
│     AwsScanner.py
├── analyzer/              → detectan vulnerabilidades en los recursos
│     IAnalyzer.py
│     aws_analyzer.py
│     IAM_Analyzer.py
│     ec2_analyzer.py
│     s3_analyzer.py
│     iLLM_analyzer.py     → interfaz para analizadores con IA
│     gemini_analyzer.py   → implementación con Google Gemini
├── Factories/             → crean instancias de scanners, analizadores y recursos
│     scannerFactory.py
│     analyzerFactory.py   → elige el analizador estático según el proveedor
│     AIAnalyzerFactory.py → elige el motor de IA según el modelo configurado
│     awsFactory.py
├── celery_worker/         → gestión de tareas en segundo plano
│     celery_app.py
│     tasks.py
├── Requests.py            → DTOs de entrada
└── Responses.py           → DTOs de salida
```

**Razonamiento:**
- Cada capa solo conoce a la capa inmediatamente inferior.
- Los DTOs (Requests.py) solo existen en la capa api — los servicios y repositorios trabajan con modelos internos.
- La separación entre scanners (obtener recursos) y analyzers (detectar vulnerabilidades) permite añadir nuevas vulnerabilidades sin tocar el código de escaneo.
- Las Factories permiten añadir nuevos proveedores cloud (Azure, GCP) sin modificar el resto del sistema.

---

### 7. Estado del scan global en Pinia

**Decisión:** la conexión SSE y el estado del escaneo viven en el store de Pinia, no en los componentes Vue.

**Razonamiento:**
- Los componentes Vue se destruyen al navegar entre rutas — si el SSE viviera en un componente, se perdería la conexión.
- El store de Pinia persiste durante toda la sesión — la conexión SSE sobrevive a la navegación.
- Permite mostrar el progreso del escaneo en cualquier página de la aplicación mediante un componente flotante global.

---

### 8. Scan automático configurable por el usuario  

**Decisión:** el escaneo automático por intervalo es opcional y configurable por el usuario.

**Razonamiento:**
- El escaneo consume llamadas a la API de AWS — puede tener coste.
- Empresas diferentes tienen necesidades distintas de frecuencia.
- El usuario es quien mejor sabe con qué frecuencia cambia su infraestructura.

**Opciones de configuración:**
- Desactivado (por defecto)
- Cada 24 horas
- Cada semana
- Cada mes

---

### 9. Pregunta de escaneo previo antes de auditar

**Decisión:** antes de lanzar una nueva auditoría, SmartAudit pregunta al usuario si quiere escanear primero.

**Razonamiento:**
- La auditoría analiza los datos del último scan — si el scan es antiguo, los resultados pueden no reflejar el estado real de AWS.
- El usuario puede haber corregido vulnerabilidades y querer verificarlo — necesita un nuevo scan antes de auditar.
- La app no puede saber si el usuario ha hecho cambios en AWS — solo el usuario lo sabe.

---

### 10. Auditoría en dos etapas: análisis estático primero, IA después

**Decisión:** la auditoría con IA nunca se ejecuta sola — siempre recibe como entrada las vulnerabilidades que ya encontró el análisis estático, y se le pide explícitamente que no las repita.

**Razonamiento:**
- El análisis estático (reglas fijas sobre IAM/EC2/S3) es instantáneo, gratuito y determinista — cubre los casos conocidos sin depender de ninguna API externa.
- El análisis con IA (Google Gemini) tiene coste y latencia, así que tiene más sentido como una segunda pasada que aporte valor añadido: relacionar hallazgos entre sí (cadenas de ataque), priorizarlos según el contexto de negocio del usuario, y detectar configuraciones sospechosas que las reglas fijas no cubren.
- Separar ambos en `AuditResult` distintos (`origin: "static"` / `origin: "ai"`) permite comparar resultados, mostrar cada uno en su propia pestaña y no perder el análisis estático si la llamada a Gemini falla.

**Consecuencia en el diseño:** `AuditController` no conoce a `GeminiAnalyzer` directamente — pide el analizador a `AIAnalyzerFactory` según un parámetro `modelo`, igual que `AnalyzerFactory` resuelve el analizador estático según el `provider`. Cambiar de modelo de IA (o añadir uno nuevo) no requiere tocar el controller ni los servicios.

---

## Modelo de datos principal

### Scan
```json
{
  "scan_id": "uuid",
  "user_id": "ref",
  "account_id": "ref",
  "status": "running | completed | failed",
  "progress": 0-100,
  "resources": {
    "iam": {...},
    "ec2": {...},
    "s3": {...}
  },
  "scan_date": "datetime"
}
```

### Auditoría
```json
{
  "audit_id": "uuid",
  "user_id": "ref",
  "account_id": "ref",
  "scan_snapshot": {...},
  "vulnerabilities": [...],
  "audit_date": "datetime"
}
```

---

## Vulnerabilidades detectadas

Esta tabla cubre el análisis **estático** (reglas fijas). El análisis con **IA** no está limitado a este catálogo: puede proponer hallazgos contextuales adicionales (cadenas de ataque entre recursos, riesgos específicos del negocio del usuario, etc.) que no encajan en una regla predefinida.

### IAM
| Vulnerabilidad | Severidad |
|---|---|
| Usuario/Grupo con AdministratorAccess | CRITICAL |
| Usuario/Grupo con permisos admin via inline policies | CRITICAL |
| Usuario sin MFA con permisos elevados | HIGH |
| Usuario inactivo +90 días | MEDIUM |
| Access key antigua +90 días | MEDIUM |

### EC2
| Vulnerabilidad | Severidad |
|---|---|
| Instancia con IP pública directa | MEDIUM |
| Security Group con puerto abierto a 0.0.0.0/0 | HIGH |
| Volumen EBS sin cifrar | MEDIUM |

### S3
| Vulnerabilidad | Severidad |
|---|---|
| Bucket público | CRITICAL |
| Bucket sin cifrado | MEDIUM |
| Bucket sin versionado | LOW |