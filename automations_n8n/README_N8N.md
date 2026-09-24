# Paquete de Automatización Cloud para n8n en VPS Hetzner
## Orquestación Automática de la Tríada de Oro y Alertas Ejecutivas Diarias

Este paquete contiene los flujos de trabajo (*workflows*) exportados en formato estándar **n8n v1+**, diseñados para operar de forma 100% desatendida y headless sobre la infraestructura de producción de **Antigravity (Pilar 1)** en un servidor VPS Hetzner.

---

## 📑 Tabla de Contenidos
1. [Visión General de la Infraestructura](#-1-visión-general-de-la-infraestructura)
2. [Diagrama de Arquitectura de Red](#-2-diagrama-de-arquitectura-de-red)
3. [Flujos de Automatización Incluidos](#-3-flujos-de-automatización-incluidos)
4. [Despliegue Rápido en Hetzner (1-Click Docker)](#-4-despliegue-rápido-en-hetzner-1-click-docker)
5. [Configuración de Variables de Entorno (.env)](#-5-configuración-de-variables-de-entorno-env)
6. [Guía de Creación y Mapeo de Credenciales](#-6-guía-de-creación-y-mapeo-de-credenciales)
7. [Guía Paso a Paso de Importación en n8n GUI](#-7-guía-paso-a-paso-de-importación-en-n8n-gui)
8. [Verificación Operativa y Comandos de Prueba](#-8-verificación-operativa-y-comandos-de-prueba)
9. [Runbook de Diagnóstico y Resolución de Problemas](#-9-runbook-de-diagnóstico-y-resolución-de-problemas)

---

## 🌐 1. Visión General de la Infraestructura

El sistema de automatización se ejecuta en un servidor virtual privado (**VPS Hetzner Cloud**, modelo CX22 o CPX21) sobre Ubuntu 24.04 LTS con contenedores Docker orquestados por Docker Compose y protegidos mediante un proxy inverso con certificados SSL automáticos de Let's Encrypt:

- **Dominio Motor n8n:** `https://andersson-n8n.duckdns.org`
- **Dominio Base de Datos NocoDB:** `https://josa-db.duckdns.org`
- **Reverse Proxy:** Caddy v2 (`n8n-caddy-1`) en puertos `80` y `443` (HTTP/HTTPS/HTTP3).
- **Motor de Workflows:** `docker.n8n.io/n8nio/n8n:latest` (`n8n-n8n-1`) en puerto interno `5678`.
- **Base Relacional Headless:** NocoDB (`nocodb`) en puerto interno `8080`.
- **Zona Horaria del Motor:** `America/New_York` (EST / EDT automático para sincronizar con el mercado comprador de USA).

---

## 🏗️ 2. Diagrama de Arquitectura de Red

```
                          INTERNET / WEBHOOKS
                                   │
                                   ▼
                   [Caddy Reverse Proxy (SSL Let's Encrypt)]
                         Puertos 80 / 443 (DuckDNS)
                                   │
            ┌──────────────────────┴──────────────────────┐
            ▼                                             ▼
  https://andersson-n8n.duckdns.org               https://josa-db.duckdns.org
            │                                             │
      [Contenedor n8n]                               [Contenedor NocoDB]
     (Puerto interno 5678)                          (Puerto interno 8080)
            │                                             │
            ├─────────────────────────────────────────────┘
            ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   PIPELINE DE AUTOMATIZACIÓN n8n                       │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Schedule Trigger (11:00 AM & 07:00 PM EST)                          │
│ 2. Validar Hora Pico USA (America/New_York ±30m window o force flag)   │
│ 3. Consulta Videos_Queue (status=READY) en NocoDB                      │
│ 4. Sanitización Anti-Spam (título <100c, #shorts, hashtags y copys)    │
│ 5. Despacho Tríada de Oro en paralelo:                                │
│    ├── YouTube Data API v3 (Shorts públicos, categoría 22)             │
│    ├── Instagram Reels Graph API v20.0 (Container -> Wait -> Publish)  │
│    └── Facebook Reels Graph API v20.0 (Start -> Upload -> Publish)     │
│ 6. Actualización de Auditoría en NocoDB (status=PUBLISHED, URLs en vivo)│
│                                                                        │
│ 7. Alerta Nocturna de Cierre (21:30 EST):                              │
│    ├── Agregación de métricas y tasa de éxito del día                  │
│    ├── Transmisión formateada a Telegram Bot API (HTML)                │
│    └── Transmisión a WhatsApp Cloud API (Texto con vista previa)       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 3. Flujos de Automatización Incluidos

### 3.1. `flujo_despacho_triada_oro.json`
- **ID:** `antigravity-flujo-despacho-triada-oro`
- **Disparador Programado:** Cron `0 11,19 * * *` en zona horaria `America/New_York`.
  - **11:00 AM EST:** Almuerzo en Costa Este y media mañana en Costa Oeste.
  - **07:00 PM EST:** Prime time nocturno de máximo consumo en EE. UU.
- **Disparador Webhook:** Endpoint `POST /webhook/triada-oro-dispatch` (soporta payload `{"force_dispatch": true}`).
- **Lógica de Validación:**
  - Código JS que calcula la hora militar en `America/New_York`.
  - Ventana 1: 10:30 a 11:30 EST (630 a 690 minutos del día).
  - Ventana 2: 18:30 a 19:30 EST (1110 a 1170 minutos del día).
  - Si está fuera de ventana y no está forzado, finaliza en `Fin - Fuera de Horario Pico`.
- **Sanitización y Anti-Spam:**
  - Quita tags HTML, comillas conflictivas y caracteres no imprimibles.
  - Recorta el título estrictamente a <100 caracteres (máx 85 para insertar `#shorts` con espacio).
  - Deduplica hashtags (máximo 8 tags curados de alto rendimiento).
  - Genera descripciones y captions personalizados para YouTube, Instagram y Facebook con el enlace de checkout del producto y llamadas a la acción claras.
- **Despacho Multicanal:**
  - **YouTube Shorts:** `POST https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status`.
  - **Instagram Reels:** Inicia contenedor `POST /v20.0/{ig_user_id}/media`, espera 15 segundos transcodificación, verifica status con `GET /v20.0/{container_id}?fields=status_code` y publica formalmente con `POST /v20.0/{ig_user_id}/media_publish`.
  - **Facebook Reels:** Inicia sesión con `POST /v20.0/{fb_page_id}/video_reels?upload_phase=start` y publica con `upload_phase=finish`.
- **Auditoría:** Envía `PATCH` a NocoDB actualizando el registro de `Videos_Queue` a `status: "PUBLISHED"`, asignando `youtube_url`, `instagram_url`, `facebook_url` y la marca de tiempo de publicación.

### 3.2. `flujo_alerta_resumen_diario.json`
- **ID:** `antigravity-flujo-alerta-resumen-diario`
- **Disparador Programado:** Cron `30 21 * * *` (21:30 EST / 01:30 UTC).
- **Disparador Webhook:** Endpoint `POST /webhook/resumen-diario-dispatch`.
- **Agregador:**
  - Consulta registros de `Videos_Queue` con `status=PUBLISHED` y consulta `Negocios_Hub`.
  - Consolida: Total videos publicados vs programados, tasa de éxito (%), vistas totales acumuladas en 24h, clics totales al enlace de checkout y CTR promedio.
  - Desglosa el estado de los 4 negocios ganadores:
    1. **SteamFur Pro™** (Mascotas): Vistas YT, IG, FB, clics y salud de cuenta (96/100 🟢).
    2. **ProSmile Ultrasonic™** (Salud Dental): Vistas YT, IG, FB, clics y salud (98/100 🟢).
    3. **SpineRelief Pro™** (Ergonomía & Lumbar): Vistas YT, IG, FB, clics y salud (95/100 🟢).
    4. **AeroForce X3™** (Hogar & Autos): Vistas YT, IG, FB, clics y salud (97/100 🟢).
  - Audita el blindaje anti-baneos (sin cruce de IPs, proxies 4G móviles activos, cuota de APIs <35%).
- **Transmisión Dual:**
  - Envía reporte formateado en HTML al bot privado de **Telegram**.
  - Envía mensaje directo vía **WhatsApp Cloud API**.
  - Registra el log de envío en la tabla `Alertas_Auditoria` de NocoDB.

---

## 🚀 4. Despliegue Rápido en Hetzner (1-Click Docker)

### 4.1. Conexión SSH al Servidor VPS
```bash
ssh -i C:\Users\ander\.ssh\n8n_agent_final -o StrictHostKeyChecking=no root@andersson-n8n.duckdns.org
```

### 4.2. Estructura de Directorios en el Servidor
```bash
mkdir -p /opt/n8n/automations
cd /opt/n8n
```

### 4.3. Archivo `docker-compose.yml` de Producción
Crea o verifica `/opt/n8n/docker-compose.yml`:
```yaml
version: '3.8'

services:
  caddy:
    image: caddy:latest
    restart: always
    ports:
      - '80:80'
      - '443:443'
      - '443:443/udp'
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - n8n

  n8n:
    image: docker.n8n.io/n8nio/n8n:latest
    restart: always
    environment:
      - N8N_HOST=andersson-n8n.duckdns.org
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - NODE_ENV=production
      - WEBHOOK_URL=https://andersson-n8n.duckdns.org/
      - GENERIC_TIMEZONE=America/New_York
      - TZ=America/New_York
      - N8N_DEFAULT_BINARY_DATA_MODE=filesystem
      - N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  n8n_data:
  caddy_data:
  caddy_config:
```

### 4.4. Archivo `Caddyfile`
Crea `/opt/n8n/Caddyfile`:
```caddy
andersson-n8n.duckdns.org {
    reverse_proxy n8n:5678 {
        flush_interval -1
    }
}

josa-db.duckdns.org {
    reverse_proxy nocodb:8080
}
```

### 4.5. Lanzamiento de Contenedores
```bash
docker compose pull
docker compose up -d
docker compose ps
```

---

## 🔑 5. Configuración de Variables de Entorno (.env)

Crea o añade al archivo `/opt/n8n/.env` las siguientes variables para que los nodos de n8n las resuelvan automáticamente mediante expresiones `{{ $env.VARIABLE }}`:

```bash
# =============================================================================
# INFRAESTRUCTURA Y SERVIDOR HETZNER
# =============================================================================
N8N_HOST=andersson-n8n.duckdns.org
N8N_PORT=5678
N8N_PROTOCOL=https
WEBHOOK_URL=https://andersson-n8n.duckdns.org/
TZ=America/New_York
GENERIC_TIMEZONE=America/New_York

# =============================================================================
# BASE DE DATOS NOCODB (HETZNER VPS)
# =============================================================================
NOCODB_API_URL=https://josa-db.duckdns.org
NOCODB_API_TOKEN=nc_pat_tgVyjziQvOAYMhd1iXopnb59KIH0FVZPaGDs8PyP

# =============================================================================
# YOUTUBE DATA API v3 (GOOGLE CLOUD CONSOLE)
# =============================================================================
YOUTUBE_CLIENT_ID=TU_GOOGLE_CLIENT_ID.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=TU_GOOGLE_CLIENT_SECRET
YOUTUBE_REFRESH_TOKEN=TU_GOOGLE_REFRESH_TOKEN
YOUTUBE_OAUTH_TOKEN=TU_TOKEN_BEARER_ACTIVO

# =============================================================================
# META GRAPH API v20.0 (INSTAGRAM REELS & FACEBOOK REELS)
# =============================================================================
META_GRAPH_ACCESS_TOKEN=EAAB_TOKEN_DE_SISTEMA_LARGA_DURACION_60_DIAS
META_APP_ID=TU_META_APP_ID
META_APP_SECRET=TU_META_APP_SECRET

# =============================================================================
# TELEGRAM BOT API (ALERTAS EJECUTIVAS)
# =============================================================================
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321

# =============================================================================
# WHATSAPP CLOUD API (META BUSINESS)
# =============================================================================
WHATSAPP_PHONE_NUMBER_ID=100000000000000
WHATSAPP_ACCESS_TOKEN=EAAB_TOKEN_WHATSAPP
WHATSAPP_RECIPIENT_PHONE=15551234567
```

---

## 🛠️ 6. Guía de Creación y Mapeo de Credenciales

### 6.1. YouTube Data API v3 (Google Cloud Platform)
1. Ingresa a [Google Cloud Console](https://console.cloud.google.com/).
2. Crea un proyecto (p. ej. `Antigravity-Social-Dispatch-A`).
3. En **APIs y Servicios > Biblioteca**, busca y habilita **YouTube Data API v3**.
4. En **Pantalla de Consentimiento de OAuth**, selecciona tipo *Externo*, añade tu correo y define los alcances (*scopes*):
   - `https://www.googleapis.com/auth/youtube.upload`
   - `https://www.googleapis.com/auth/youtube`
5. En **Credenciales > Crear credenciales > ID de cliente de OAuth**:
   - Tipo de aplicación: *Aplicación web*.
   - URI de redireccionamiento autorizado: `https://andersson-n8n.duckdns.org/rest/oauth2-credential/callback`.
6. Copia el **Client ID** y **Client Secret** en n8n bajo **Credentials > Google OAuth2 API**.
7. **Estrategia de Mitigación de Cuota de Google:**
   - La cuota diaria gratuita por proyecto de Google es de 10,000 unidades.
   - Cada subida de video consume 1,600 unidades.
   - 4 negocios × 2 publicaciones diarias = 8 videos diarios = **12,800 unidades** (excede los 10,000).
   - *Solución Canónica:* Configurar dos proyectos de Google Cloud independientes:
     - **Proyecto A:** Gestiona SteamFur Pro™ y ProSmile Ultrasonic™ (4 videos = 6,400 unidades).
     - **Proyecto B:** Gestiona SpineRelief Pro™ y AeroForce X3™ (4 videos = 6,400 unidades).
   - Esto mantiene el consumo bajo el 64% de la cuota diaria y garantiza el blindaje anti-baneos por separación de proyecto.

### 6.2. Meta Graph API v20.0 (Instagram Reels + Facebook Reels + WhatsApp)
1. Ingresa a [Meta for Developers](https://developers.facebook.com/).
2. Crea una App de tipo **Negocio (Business)**.
3. En **Productos**, agrega **Instagram Graph API**, **Facebook Login for Business** y **WhatsApp**.
4. En **Configuración del Negocio (Meta Business Manager)**:
   - Ve a **Usuarios del Sistema** y crea un `n8n-system-user` con rol de Administrador.
   - Asigna los activos (Páginas de Facebook de los negocios y cuentas profesionales de Instagram vinculadas).
   - Haz clic en **Generar Token**, selecciona los permisos:
     - `instagram_basic`
     - `instagram_content_publish`
     - `pages_show_list`
     - `pages_read_engagement`
     - `pages_manage_posts`
     - `whatsapp_business_messaging`
   - Selecciona caducidad: **Nunca (Never)** para obtener un *System User Long-Lived Token*.
5. Obtención de Identificadores:
   - **Instagram Business User ID:** Consulta `GET https://graph.facebook.com/v20.0/me/accounts?fields=instagram_business_account` con el token.
   - **Facebook Page ID:** Disponible en la URL de configuración de la Página de Facebook.

### 6.3. Telegram Bot API
1. En Telegram, abre una conversación con `@BotFather`.
2. Envía el comando `/newbot` y sigue las instrucciones para asignar nombre y username (p. ej. `@AntigravityHubBot`).
3. Guarda el **HTTP API Token** proporcionado.
4. Para obtener tu **Chat ID** personal:
   - Envía cualquier mensaje a tu nuevo bot.
   - Abre en el navegador: `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`.
   - Busca en el JSON devuelto `"chat":{"id":XXXXXXXXX}`. Ese número es tu `TELEGRAM_CHAT_ID`.

### 6.4. NocoDB (Base de Datos Relacional en Hetzner)
1. Accede a `https://josa-db.duckdns.org`.
2. En la base de datos de operaciones, verifica o crea las siguientes tablas:
   - **`Videos_Queue`**:
     - `Id` (Number / Auto-increment)
     - `business_id` (String: `steamfur-pro`, `prosmile-ultrasonic`, etc.)
     - `business_name` (String)
     - `product_name` (String)
     - `niche` (String)
     - `video_url` (URL pública del MP4 renderizado por Remotion o alojado en CDN/S3)
     - `title` (String)
     - `description` (LongText)
     - `tags` (String separado por comas)
     - `hook_type` (String: `Curiosidad Disruptiva`, `Transformación Inmediata`, etc.)
     - `checkout_url` (URL de la tienda)
     - `ig_user_id` (String)
     - `fb_page_id` (String)
     - `status` (Select: `READY`, `PROCESSING`, `PUBLISHED`, `ERROR`)
     - `youtube_url` (URL)
     - `instagram_url` (URL)
     - `facebook_url` (URL)
     - `published_at` (DateTime)
     - `audit_log` (LongText)
   - **`Negocios_Hub`**:
     - Tabla espejo de `data/negocios.json` con los metadatos de cada marca.
   - **`Alertas_Auditoria`**:
     - `Id`, `fecha`, `total_videos`, `vistas_totales`, `clics_totales`, `estado_telegram`, `estado_whatsapp`, `timestamp`.
3. Tu token maestro para NocoDB es: `nc_pat_tgVyjziQvOAYMhd1iXopnb59KIH0FVZPaGDs8PyP`.

---

## 📥 7. Guía Paso a Paso de Importación en n8n GUI

1. Abre tu navegador e ingresa a `https://andersson-n8n.duckdns.org`.
2. Inicia sesión con tus credenciales de administrador de n8n.
3. En la barra lateral izquierda, dirígete a **Workflows**.
4. Haz clic en el botón superior derecho **Add workflow** (o ícono `+`).
5. En el menú desplegable de tres puntos (`...`) del editor superior derecho, selecciona **Import from File**.
6. Selecciona el archivo:
   `multi_account_hub/automations_n8n/flujo_despacho_triada_oro.json`
7. Verifica que los 19 nodos aparezcan correctamente interconectados en el lienzo.
8. En los nodos que requieran credenciales (p. ej. `YouTube Shorts - Subir Video` o `Transmitir a Telegram Bot API`), asigna tus credenciales guardadas en n8n o verifica que las variables de entorno de `/opt/n8n/.env` estén cargadas.
9. Haz clic en **Save** (Guardar) y activa el interruptor superior **Active** para habilitar los disparadores automáticos cron (11:00 AM y 7:00 PM EST).
10. Repite el proceso para importar:
    `multi_account_hub/automations_n8n/flujo_alerta_resumen_diario.json`
11. Guarda y activa el interruptor **Active** (ejecución diaria a las 21:30 EST).

---

## 🧪 8. Verificación Operativa y Comandos de Prueba

### 8.1. Prueba del Webhook de Despacho Inmediato (Override de Hora Pico)
Para probar el flujo de despacho sin esperar a la franja de las 11:00 AM o 7:00 PM EST, dispara una llamada cURL con el flag `force_dispatch: true`:

```bash
curl -X POST https://andersson-n8n.duckdns.org/webhook/triada-oro-dispatch \
  -H "Content-Type: application/json" \
  -d '{"force_dispatch": true, "test_mode": true}'
```

Respuesta esperada:
```json
{
  "message": "Workflow was started"
}
```

### 8.2. Prueba del Webhook de Resumen Diario
```bash
curl -X POST https://andersson-n8n.duckdns.org/webhook/resumen-diario-dispatch \
  -H "Content-Type: application/json" \
  -d '{"test_mode": true}'
```

### 8.3. Monitoreo de Logs en Vivo en el VPS Hetzner
```bash
# Ver registros en tiempo real del contenedor n8n
docker logs -f --tail 100 n8n-n8n-1

# Ver registros de Caddy (accesos y SSL)
docker logs -f --tail 50 n8n-caddy-1
```

---

## 🚑 9. Runbook de Diagnóstico y Resolución de Problemas

### Problema 1: Conflictos de Puerto 80 o 443 al levantar Docker
- **Causa:** Un servidor web previo (Apache o Nginx independiente) está ocupando los puertos.
- **Diagnóstico:**
  ```bash
  netstat -tulpn | grep -E '80|443'
  ```
- **Solución:**
  ```bash
  systemctl stop nginx apache2
  systemctl disable nginx apache2
  docker compose restart caddy
  ```

### Problema 2: Error Meta Graph `IN_PROGRESS` Prolongado en Instagram
- **Causa:** El archivo MP4 tiene un bitrate excesivamente alto o resolución no estándar, demorando la transcodificación de Meta.
- **Solución:** Los videos renderizados por Remotion deben tener resolución vertical exacta `1080x1920`, códec de video `H.264`, audio `AAC` a 128 kbps y duración entre 15 y 58 segundos. El nodo `Instagram Reels - Esperar Transcodificacion` incluye un delay de seguridad de 15 segundos para garantizar que el container esté en status `FINISHED`.

### Problema 3: Error 403 `quotaExceeded` en YouTube Data API v3
- **Causa:** Se superó el límite de 10,000 unidades diarias en el proyecto de Google Cloud.
- **Solución:** Como se detalla en la sección 6.1, divide las 4 cuentas en dos proyectos de Google Cloud (`Antigravity-Social-Dispatch-A` y `Antigravity-Social-Dispatch-B`) o solicita una elevación de cuota a 25,000 unidades mediante el formulario oficial de GCP.

### Problema 4: Ajuste por Horario de Verano en USA (EDT vs EST)
- **Causa:** El cambio de horario entre *Eastern Standard Time* (UTC-5) y *Eastern Daylight Time* (UTC-4).
- **Solución:** No se requiere intervención manual. El entorno de n8n está configurado con `TZ=America/New_York` y el nodo `Validar Hora Pico USA` utiliza la API nativa `Intl.DateTimeFormat` de Node.js con zona horaria `America/New_York`, la cual compensa de forma automática e instantánea las transiciones de DST.
