# Guía de Despliegue en Google Cloud Platform (Ubuntu 24.04 LTS)

Esta guía detalla paso a paso cómo desplegar el Sistema de Gestión de Congresos (Web App + n8n) en una instancia "limpia" de Google Cloud Compute Engine con Ubuntu 24.04 LTS.

## 1. Prerrequisitos en GCP Console

Antes de entrar a la consola SSH, asegúrate de configurar esto en Google Cloud:

1.  **Crear Instancia**:
    *   OS: Ubuntu 24.04 LTS (x86/64).
    *   Máquina: e2-medium (2 vCPU, 4GB RAM) o superior recomendado para correr n8n y la web app fluidamente.
    *   Disco: Al menos 20GB.

2.  **Configurar Firewall**:
    *   Asegúrate de marcar las casillas **"Allow HTTP traffic"** y **"Allow HTTPS traffic"** al crear la instancia.
    *   Si vas a usar puertos personalizados (no recomendado en producción), abre los puertos en la red VPC.

## 2. Configuración Inicial del Servidor

Conéctate por SSH a tu instancia y ejecuta:

```bash
# Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# Instalar herramientas básicas
sudo apt install -y git curl wget unzip python3-pip python3-venv python3-dev build-essential nginx
```

## 3. Instalación de Docker (Para n8n)

Ubuntu 24.04 facilita la instalación de Docker.

```bash
# Instalar Docker
sudo apt install -y docker.io docker-compose-v2

# Iniciar y habilitar Docker
sudo systemctl start docker
sudo systemctl enable docker

# Agregar tu usuario al grupo docker (para no usar sudo con docker)
sudo usermod -aG docker $USER
```
*Nota: Cierra sesión y vuelve a entrar para que el cambio de grupo surta efecto, o ejecuta `newgrp docker`.*

## 4. Clonar el Repositorio

```bash
cd ~
# Clona tu repositorio (asegúrate de que sea público o usa un token personal)
git clone https://github.com/mafloress/MDM.git app-gestion

cd app-gestion
```

## 5. Despliegue de n8n (Automatización)

1.  Crea el directorio de datos para n8n:
    ```bash
    mkdir -p ~/.n8n
    ```

2.  Crea un archivo `docker-compose.yml` en la raíz del proyecto (o usa el siguiente comando para generarlo):

    ```bash
cat <<EOF > docker-compose.yml
version: "3"
services:
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=tu_password_seguro  # <--- CAMBIA ESTO
      - WEBHOOK_URL=http://TU_IP_PUBLICA_O_DOMINIO:5678/
    volumes:
      - ~/.n8n:/home/node/.n8n
    restart: always
EOF
    ```
    *Nota: Reemplaza `TU_IP_PUBLICA_O_DOMINIO` con la IP externa de tu instancia GCP.*

3.  Inicia n8n:
    ```bash
    docker compose up -d
    ```

## 6. Despliegue de la Web App (Python/Reflex)

1.  Instalar Node.js (Requerido por Reflex):
    ```bash
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
    ```

2.  Prepara el entorno Python:
    ```bash
    cd ~/app-gestion/app
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  Configura las variables de entorno:
    Crea el archivo `.env`:
    ```bash
    nano .env
    ```
    Pega y edita lo siguiente:
    ```ini
CLICKUP_API_TOKEN=tu_token_personal_de_clickup
CLICKUP_LIST_ID=id_de_la_lista_de_clientes
# URL del webhook de n8n (apuntando al contenedor local o IP pública)
N8N_WEBHOOK_URL=http://localhost:5678/webhook/trigger-sourcing
N8N_INVITE_WEBHOOK_URL=http://localhost:5678/webhook/send-invitations
    ```

4.  Inicializar Reflex:
    ```bash
    reflex init
    ```

5.  Crear servicio Systemd (para que corra en segundo plano):
    ```bash
    sudo nano /etc/systemd/system/gestion-app.service
    ```
    Contenido (ajusta `TU_USUARIO` por tu nombre de usuario en linux, ej: `ubuntu`):
    ```ini
[Unit]
Description=Reflex App Service
After=network.target

[Service]
User=TU_USUARIO
Group=www-data
WorkingDirectory=/home/TU_USUARIO/app-gestion/app
Environment="PATH=/home/TU_USUARIO/app-gestion/app/venv/bin:/usr/bin"
ExecStart=/home/TU_USUARIO/app-gestion/app/venv/bin/reflex run
Restart=always

[Install]
WantedBy=multi-user.target
    ```
    *Ojo: Reemplaza `TU_USUARIO` con el resultado de ejecutar `whoami`.*

6.  Iniciar el servicio:
    ```bash
    sudo systemctl start gestion-app
    sudo systemctl enable gestion-app
    ```

## 7. Configuración de Nginx (Proxy Inverso)

Configuraremos Nginx para que:
- La Web App (Reflex) sea accesible en el puerto 80 (HTTP).
- n8n sea accesible en el puerto 5678.

1.  Crear configuración de Nginx:
    ```bash
    sudo nano /etc/nginx/sites-available/gestion
    ```

2.  Contenido:
    ```nginx
    server {
        listen 80;
        server_name _;  # Acepta cualquier IP/Dominio

        location / {
            proxy_pass http://localhost:3000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
        
        # Proxy para el backend de Reflex (Websockets)
        location /_event {
            proxy_pass http://localhost:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
            proxy_set_header Host $host;
        }
        
        location /ping {
            proxy_pass http://localhost:8000;
        }
    }
    ```

3.  Activar y reiniciar Nginx:
    ```bash
    sudo ln -s /etc/nginx/sites-available/gestion /etc/nginx/sites-enabled
    sudo rm /etc/nginx/sites-enabled/default
    sudo nginx -t
    sudo systemctl restart nginx
    ```

## 8. Verificación Final

1.  **Web App**: Abre `http://TU_IP_PUBLICA` en tu navegador. Deberías ver el Login.
2.  **n8n**: Abre `http://TU_IP_PUBLICA:5678`. Deberías ver el login de n8n (usuario/pass definidos en el paso 5).
    *   *Nota: Si no carga n8n, verifica en GCP Firewall que el puerto 5678 esté abierto. Si solo permitiste HTTP/HTTPS (80/443), deberás configurar Nginx para redirigir un path a n8n o abrir el puerto 5678 en la VPC Network.*

## 9. Importar Flujos en n8n

1.  Entra a n8n (`http://TU_IP_PUBLICA:5678`).
2.  Ve a "Workflows" > "Import from File".
3.  Sube los archivos JSON que están en la carpeta `n8n_workflows` de tu repositorio (descárgalos a tu PC local primero o cópialos).

¡Listo! Tu sistema está operativo en la nube.
