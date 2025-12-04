# Sistema de Gestión de Congresos (Event Management System)

Este proyecto es una solución integral para la gestión de invitados a congresos, automatizando el proceso desde la búsqueda (sourcing) hasta la confirmación y validación de documentos.

## Componentes

1. **Plataforma Web (Python/Reflex)**:
   - Panel de control tipo Kanban para visualizar el estado de los invitados.
   - Gestión de documentos (subida de pasaportes, boletos, etc.).
   - Inicio de sesión seguro.
   - Interfaz moderna y responsiva (Reflex UI + Glassmorphism).

2. **Automatización (n8n)**:
   - Flujos de trabajo para:
     - Búsqueda de prospectos (Web Scraping con Apify).
     - Envío de correos de invitación y recordatorios recursivos.
     - Gestión de respuestas RSVP.
     - Validación de documentos.
     - **Nuevo**: Webhook para envío masivo de invitaciones (Frontend -> n8n).
     - **Nuevo**: Asistente CRM en Telegram (Consultas en lenguaje natural).
     - **Nuevo**: Agente de Soporte WhatsApp con IA (LangChain).

3. **Base de Datos (ClickUp)**:
   - Almacenamiento centralizado de la información de los clientes y sus estados (Listas y Tareas).

## Estructura del Proyecto

```
/app                # Código fuente de la aplicación web Python (Reflex)
  rxconfig.py       # Configuración de Reflex
  mdm.py            # Lógica y UI de la aplicación
/n8n_workflows      # Archivos JSON para importar en n8n
/documentation      # Guías de despliegue y configuración
```

## Instalación Rápida (Local)

1. Instalar dependencias:
   ```bash
   cd app
   pip install -r requirements.txt
   ```
2. Configurar `.env` (ver `app/mdm.py` para variables requeridas).
3. Inicializar y ejecutar Reflex:
   ```bash
   reflex init
   reflex run
   ```
   La app estará disponible en `http://localhost:3000`.

## Despliegue en Producción

- **VPS Genérico**: Consulta `documentation/DEPLOYMENT.md`.
- **Google Cloud (GCP)**: Consulta `documentation/GCP_DEPLOYMENT.md` para Ubuntu 24.04 LTS.