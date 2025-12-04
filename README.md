# Sistema de Gestión de Congresos (Event Management System)

Este proyecto es una solución integral para la gestión de invitados a congresos, automatizando el proceso desde la búsqueda (sourcing) hasta la confirmación y validación de documentos.

## Componentes

1. **Plataforma Web (Python/Flask)**:
   - Panel de control tipo Kanban para visualizar el estado de los invitados.
   - Gestión de documentos (subida de pasaportes, boletos, etc.).
   - Inicio de sesión seguro.
   - Interfaz moderna y responsiva (Tailwind CSS + Glassmorphism).

2. **Automatización (n8n)**:
   - Flujos de trabajo para:
     - Búsqueda de prospectos (Web Scraping con Apify).
     - Envío de correos de invitación y recordatorios recursivos.
     - Gestión de respuestas RSVP.
     - Validación de documentos.
     - **Nuevo**: Webhook para envío masivo de invitaciones (Frontend -> n8n).
     - **Nuevo**: Asistente CRM en Telegram (Consultas en lenguaje natural).
     - **Nuevo**: Agente de Soporte WhatsApp con IA (LangChain).

3. **Base de Datos (Airtable)**:
   - Almacenamiento centralizado de la información de los clientes y sus estados.

## Estructura del Proyecto

```
/app                # Código fuente de la aplicación web Python
  /static           # Archivos CSS y JS
  /templates        # Plantillas HTML
  app.py            # Lógica del servidor Flask
/n8n_workflows      # Archivos JSON para importar en n8n
/documentation      # Guías de despliegue y configuración
```

## Instalación Rápida (Local)

1. Instalar dependencias:
   ```bash
   cd app
   pip install -r requirements.txt
   ```
2. Configurar `.env` (ver `app/app.py` para variables requeridas).
3. Ejecutar:
   ```bash
   python app.py
   ```

## Despliegue en Producción

Consulta la guía detallada en `documentation/DEPLOYMENT.md` para instalar en un VPS Ubuntu con Docker y Nginx.