# SmartAudit AI

Plataforma de auditoría de seguridad cloud que combina análisis estático 
de infraestructura AWS con remediación inteligente generada por IA.

## ✅ Funcionalidades implementadas
- Autenticación con verificación de email y recuperación de contraseña
- Conexión a cuentas AWS mediante STS AssumeRole (rol de solo lectura), con guía integrada para crearlo
- Escaneo de recursos EC2, S3 e IAM, con auto-detección de regiones
- Detección de vulnerabilidades de seguridad mediante análisis estático (reglas IAM/EC2/S3)
- Análisis con IA (Google Gemini) usando contexto de negocio aportado por el usuario, sin duplicar lo ya detectado por el análisis estático
- Generación de recomendaciones y comandos AWS CLI de remediación por vulnerabilidad
- Escaneo en segundo plano con Celery + RabbitMQ
- Notificaciones de progreso en tiempo real con SSE
- Historial de auditorías por cuenta, con comparativa entre auditorías y panel de KPIs

## 🧠 Pendiente / mejoras futuras
- Marcar vulnerabilidades como resueltas (solo en UI, sin persistir todavía)
- Exportar auditorías a PDF
- Cobertura de tests sobre controllers, services, scanners y factories (hoy solo cubiertos los analyzers)
- Soporte para Azure/GCP (la arquitectura ya está preparada vía Factory, falta la implementación concreta)

## 🛠️ Stack
**Backend:** FastAPI, Celery, RabbitMQ, MongoDB, Boto3, Google Gemini API  
**Frontend:** Vue 3, PrimeVue, Pinia, Vue Router

## ⚠️ Estado
Trabajo Final de Grado — funcionalidades principales completas

## 👤 Autor
Mohamed Firas Bahri — Universidad de Salamanca