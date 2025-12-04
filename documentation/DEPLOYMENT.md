# Guía de Despliegue en VPS Ubuntu

Esta guía detalla los pasos para desplegar la solución completa (Plataforma Web Python + n8n) en un servidor VPS con Ubuntu 20.04/22.04.

## Prerrequisitos
- Un servidor VPS (DigitalOcean, AWS, Linode, etc.) con Ubuntu.
- Un dominio configurado (ej: `panel.tudominio.com` para la app y `n8n.tudominio.com` para n8n).
- Acceso SSH al servidor.

## 1. Preparación del Servidor

Actualiza el sistema e instala las herramientas necesarias:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx docker.io docker-compose git
sudo systemctl enable docker
sudo systemctl start docker
```

## 2. Instalación de n8n (Automatización)

Usaremos Docker para ejecutar n8n.

1. Crea un directorio para n8n:
   ```bash
   mkdir ~/n8n-docker
   cd ~/n8n-docker
   ```

2. Crea un archivo `docker-compose.yml`:
   ```yaml
   version: "3"
   services:
     n8n:
       image: n8nio/n8n
       ports:
         - "5678:5678"
       environment:
         - N8N_BASIC_AUTH_ACTIVE=true
         - N8N_BASIC_AUTH_USER=admin
         - N8N_BASIC_AUTH_PASSWORD=tu_password_seguro
         - N8N_HOST=n8n.tudominio.com
         - WEBHOOK_URL=https://n8n.tudominio.com/
       volumes:
         - ~/.n8n:/home/node/.n8n
       restart: always
   ```

3. Inicia n8n:
   ```bash
   sudo docker-compose up -d
   ```

4. Importa los flujos JSON ubicados en la carpeta `n8n_workflows` de este repositorio a tu instancia de n8n.

## 3. Instalación de la Plataforma Web (Python)

1. Clona este repositorio (o sube los archivos):
   ```bash
   cd ~
   git clone <tu-repo-url> app-gestion
   cd app-gestion/app
   ```

2. Crea un entorno virtual e instala dependencias:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configura las variables de entorno:
   Crea un archivo `.env` en la carpeta `app`:
   ```bash
   nano .env
   ```
   Contenido:
   ```
   SECRET_KEY=generar_una_clave_segura
   AIRTABLE_API_KEY=tu_api_key_de_airtable
   AIRTABLE_BASE_ID=id_de_tu_base
   AIRTABLE_TABLE_NAME=Clients
   N8N_WEBHOOK_URL=https://n8n.tudominio.com/webhook/trigger-sourcing
   ```

4. Prueba la aplicación:
   ```bash
   gunicorn --bind 0.0.0.0:5000 app:app
   ```
   (Presiona Ctrl+C para detener después de verificar que arranca).

5. Configura Systemd para mantener la app corriendo:
   ```bash
   sudo nano /etc/systemd/system/gestion-app.service
   ```
   Contenido:
   ```ini
   [Unit]
   Description=Gunicorn instance to serve Gestion App
   After=network.target

   [Service]
   User=root
   Group=www-data
   WorkingDirectory=/root/app-gestion/app
   Environment="PATH=/root/app-gestion/app/venv/bin"
   ExecStart=/root/app-gestion/app/venv/bin/gunicorn --workers 3 --bind unix:app.sock -m 007 app:app

   [Install]
   WantedBy=multi-user.target
   ```

   Inicia el servicio:
   ```bash
   sudo systemctl start gestion-app
   sudo systemctl enable gestion-app
   ```

## 4. Configuración de Nginx (Reverse Proxy)

Configura Nginx para servir tanto la app como n8n en puertos estándar (80/443).

1. Crea un archivo de configuración:
   ```bash
   sudo nano /etc/nginx/sites-available/gestion
   ```

2. Contenido (ejemplo básico):
   ```nginx
   # App Python
   server {
       listen 80;
       server_name panel.tudominio.com;

       location / {
           include proxy_params;
           proxy_pass http://unix:/root/app-gestion/app/app.sock;
       }
   }

   # n8n
   server {
       listen 80;
       server_name n8n.tudominio.com;

       location / {
           proxy_pass http://localhost:5678;
           proxy_set_header Connection '';
           proxy_http_version 1.1;
           chunked_transfer_encoding off;
           proxy_buffering off;
           proxy_cache off;
       }
   }
   ```

3. Activa el sitio y reinicia Nginx:
   ```bash
   sudo ln -s /etc/nginx/sites-available/gestion /etc/nginx/sites-enabled
   sudo nginx -t
   sudo systemctl restart nginx
   ```

4. (Opcional pero recomendado) Instala Certbot para HTTPS:
   ```bash
   sudo apt install python3-certbot-nginx
   sudo certbot --nginx -d panel.tudominio.com -d n8n.tudominio.com
   ```

## 5. Configuración de Airtable y Apify

1. **Airtable**:
   - Crea una base llamada "Event Management".
   - Crea una tabla "Clients".
   - Columnas necesarias: `Name` (Text), `Email` (Email), `Status` (Single Select: INVITACIÓN, ACEPTADO, EN ESPERA, VALIDACIÓN DOCTOS, ACEPTADOS), `Company` (Text), `LastContact` (Date), `Documents` (Attachments).

2. **Apify**:
   - Crea una cuenta en Apify.
   - Configura el actor "LinkedIn Profile Scraper".
   - Obtén tu API Token y colócalo en el nodo de n8n correspondiente.

## 6. Publicación en GitHub

1. Inicializa el repositorio localmente:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```
2. Crea un repositorio en GitHub.
3. Conecta y sube:
   ```bash
   git remote add origin <URL_DE_TU_REPO>
   git push -u origin master
   ```
