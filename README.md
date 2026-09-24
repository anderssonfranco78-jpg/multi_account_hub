# Centro de Mando de Cuentas y Negocios Independientes (Multi-Account Hub)
### Antigravity E-Commerce & Multi-Channel Autonomous Command Center

[![Architecture: Antigravity OS](https://img.shields.io/badge/Architecture-Antigravity%203%20Pilares-emerald.svg)](https://github.com/anderssonfranco78-jpg/multi_account_hub)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![UI: Zero--Build Tailwind](https://img.shields.io/badge/UI-Tailwind%20CSS%20CDN-cyan.svg)](index.html)
[![Cloud: n8n + Hetzner](https://img.shields.io/badge/Cloud-n8n%20Hetzner%20Docker-orange.svg)](automations_n8n/README_N8N.md)
[![Database: NocoDB](https://img.shields.io/badge/Database-NocoDB%20Relational-purple.svg)](https://josa-db.duckdns.org)
[![Tests: 100% Passing](https://img.shields.io/badge/Tests-82%2F82%20Pass%20(100%25)-green.svg)](tests/)

---

## 📑 Tabla de Contenidos Maestro
1. [Visión General del Sistema](#-1-visión-general-del-sistema)
2. [Conexión con los 3 Pilares Canónicos de Antigravity](#-2-conexión-con-los-3-pilares-canónicos-de-antigravity)
3. [Doctrina de Blindaje Anti-Baneos y Aislamiento Multi-Cuenta](#-3-doctrina-de-blindaje-anti-baneos-y-aislamiento-multi-cuenta)
4. [Estructura del Proyecto y Capas de la Arquitectura](#-4-estructura-del-proyecto-y-capas-de-la-arquitectura)
5. [Los 4 Negocios Ganadores Validados Iniciales](#-5-los-4-negocios-ganadores-validados-iniciales)
6. [Motor Backend en Python (`hub_engine.py`) y Manual de CLI](#-6-motor-backend-en-python-hub_enginepy-y-manual-de-cli)
7. [Panel Web Dashboard Interactivo (`index.html`)](#-7-panel-web-dashboard-interactivo-indexhtml)
8. [Paquete de Automatización en la Nube con n8n (`automations_n8n/`)](#-8-paquete-de-automatización-en-la-nube-con-n8n-automations_n8n)
9. [Aseguramiento de Calidad y Suite de Pruebas Unitarias](#-9-aseguramiento-de-calidad-y-suite-de-pruebas-unitarias)
10. [Enlaces Bidireccionales con el Segundo Cerebro (Obsidian)](#-10-enlaces-bidireccionales-con-el-segundo-cerebro-obsidian)

---

## 🧭 1. Visión General del Sistema

El **Multi-Account Hub** es la plataforma centralizada de mando, orquestación y monitoreo para gobernar múltiples marcas independientes de dropshipping orgánico sin inversión publicitaria (*Zero Ad Spend*), escalable de 4 a $N$ negocios simultáneos.

Cada negocio opera como una entidad económica y operativa completamente aislada, comercializando un producto ganador calificado bajo el estándar riguroso de las **7 Reglas de Oro** y distribuyendo contenido a través de un cluster de **4 canales de redes sociales**:
1. **YouTube Shorts:** Despacho programático público vía YouTube Data API v3.
2. **Instagram Reels:** Despacho programático vía Meta Graph API v20.0 (Container $\rightarrow$ Wait $\rightarrow$ Publish).
3. **Facebook Reels:** Despacho programático a Páginas oficiales vía Meta Graph API v20.0.
4. **TikTok USA:** Distribución orgánica protegida mediante hardware secundario (*Burner Phones* físicos con SIM USA MCC 310 y proxies móviles dedicados).

El ecosistema unifica la persistencia de datos atómica en JSON, un dashboard web interactivo de alta fidelidad estilo terminal trading/SaaS en español latino, flujos de automatización para n8n en servidores Hetzner Cloud y una suite exhaustiva de pruebas unitarias automáticas con cero dependencias externas.

---

## 🏛️ 2. Conexión con los 3 Pilares Canónicos de Antigravity

El Multi-Account Hub materializa la convergencia de la doctrina operativa de Antigravity documentada en el Segundo Cerebro (`[[06-Sistema-Operativo-Segundo-Cerebro-y-3-Pilares.md]]`):

```
┌────────────────────────────────────────────────────────────────────────┐
│                      ANTIGRAVITY 3-PILLAR ECOSYSTEM                    │
└────────────────────────────────────────────────────────────────────────┘
          ▲                                  ▲                           ▲
          │                                  │                           │
  [PILAR 1: MEMORIA & SABIDURÍA]    [PILAR 2: E-COMMERCE ORGÁNICO]  [PILAR 3: CREATIVIDAD & AUDIOVISUAL]
  • Obsidian Local REST API         • Dropshipping Hunter Engine     • Remotion Modalidad 3 (Comercial)
  • Obsidian MCP Server (14 tools)  • Filtro 7 Reglas de Oro (KO)    • Pausa acústica de 1.0s obligatoria
  • Hetzner Cloud VPS (Docker)      • Shopify Admin GraphQL MCP      • Beat Drop LiQWYD a -19.7 LUFS
  • n8n: andersson-n8n.duckdns.org  • Robot en la Nube (GitHub Act)  • Floating3DText volumétrico
  • NocoDB: josa-db.duckdns.org     • Proveedores YunExpress 7-12d   • Dual Voice: es-US-Neural2-C / B
          │                                  │                           │
          └──────────────────────────────────┼───────────────────────────┘
                                             ▼
                          [MULTI-ACCOUNT HUB CENTRAL]
                   • hub_engine.py (Python Atomic Core)
                   • index.html (Dashboard Trading/SaaS)
                   • automations_n8n/ (Triada de Oro Cloud)
```

- **Pilar 1 (Memoria, Gobernanza e Infraestructura Cloud):**
  - Conexión nativa con el servidor VPS Hetzner (`Ubuntu Linux` en Docker).
  - Flujos en `andersson-n8n.duckdns.org` y base de datos relacional en `josa-db.duckdns.org`.
  - Protocolo de Honestidad Radical: Auditorías cuantitativas estrictas y cero complacencia.
- **Pilar 2 (Dropshipping Orgánico y Cazador de Ganadores):**
  - Integración directa con los candidatos validados por `dropshipping_hunter`.
  - Evaluación matemática contra las 7 Reglas de Oro (Markup $\ge 3\text{x}$, margen neto $\ge 65\%$, ticket \$29–\$69 USD, efecto WOW en 0-3 segundos).
  - Integración con el catálogo de `Shopify MCP Server`.
- **Pilar 3 (Creación Audiovisual de Alta Conversión - Remotion Modalidad 3):**
  - Cada negocio almacena sus **4 Ganchos de Conversión** listos para producción:
    1. *Curiosidad Disruptiva* (Pattern Interrupt 0-1.2s).
    2. *Agitación de Dolor Real* (Emotional Visceral Trigger).
    3. *Ángulo Contrariano* (Challenging Conventional Wisdom).
    4. *Transformación Inmediata* (Split screen antes vs después).
  - Respeto estricto del silencio acústico de 1.0s, Beat Drop al segundo 3.0 exacto y tipografía flotante 3D.

---

## 🛡️ 3. Doctrina de Blindaje Anti-Baneos y Aislamiento Multi-Cuenta

Basado en `[[Runbook-Blindaje-AntiBaneos-MultiCuentas-y-Orquestacion.md]]`:

### 3.1. La Analogía de las Sucursales Independientes
En 2026, publicar productos dispares en una sola tienda o cuenta de redes sociales causa confusión algorítmica y destrucción de retención. Si una empresa matriz abre 4 locales gastronómicos independientes, cada uno tiene su propia clientela, personal y contabilidad. Si un local tiene una inspección sanitaria o cierra, **los otros 3 continúan facturando al 100% sin enterarse**.

### 3.2. Reglas de Aislamiento de Hardware y Red
1. **Separación Total de Credenciales:** Cada negocio cuenta con su propio correo de gestión (`.mgmt@antigravity-hub.internal`), perfil de navegador antidetect (Dolphin Anty / AdsPower) y proxy móvil 4G sticky independiente.
2. **Blindaje de TikTok USA (Hardware Fingerprinting & MCC):**
   - TikTok inspecciona >50 atributos de hardware a nivel de kernel y sensor (GPU renderer, giroscopio, acelerómetro, estado de batería, código de país de la tarjeta SIM).
   - El uso de emuladores o navegadores web de escritorio resulta en **Shadowban inmediato de 0 vistas**.
   - *Protocolo Operativo:* Subida manual/asistida desde un teléfono físico (*Burner Phone*, ej. Google Pixel 4a) con chip inactivo de operadoras de USA (Mint Mobile / AT&T, MCC 310/311, costo \$3 USD), idioma inglés nativo, GPS desactivado y proxy móvil sticky.
   - *Periodo de Calentamiento (Warm-up):* 3 a 5 días sin publicar ni colocar link en bio; consumo orgánico pasivo del nicho (10 min/día) para construir el *Trust Score*.
3. **YouTube Shorts & Meta Reels (Content Signals & Perceptual Hashing):**
   - No discriminan por chip telefónico ni GPS. Su tráfico es gobernado 100% por **señales de contenido y retención**.
   - Para evitar el baneo algorítmico por duplicación de video (*Perceptual Hashing / pHash Reach Suppression*), cada video es renderizado en Remotion con locución única, variación de fotogramas, despojo de metadatos EXIF y marcas de agua de audio únicas.

---

## 📁 4. Estructura del Proyecto y Capas de la Arquitectura

```
multi_account_hub/
├── data/
│   └── negocios.json                  # Persistencia canónica de negocios (JSON atómico)
├── hub_engine.py                      # Motor modular de backend Python y CLI interactivo
├── index.html                         # Panel web interactivo (Tailwind CSS CDN + Vanilla JS)
├── automations_n8n/
│   ├── flujo_despacho_triada_oro.json # Flujo n8n: Despacho a YouTube, Instagram y Facebook
│   ├── flujo_alerta_resumen_diario.json# Flujo n8n: Resumen nocturno a Telegram y WhatsApp
│   └── README_N8N.md                  # Runbook de despliegue Docker en Hetzner Cloud
├── tests/
│   ├── __init__.py
│   ├── test_hub.py                    # Suite exhaustiva de pruebas unitarias (100% cobertura)
│   └── test_health_stress.py          # Pruebas de estrés y límites del algoritmo de salud
├── requirements.txt                   # Manifiesto de dependencias estándar
└── README.md                          # Manual maestro de arquitectura y operaciones
```

---

## 🏆 5. Los 4 Negocios Ganadores Validados Iniciales

Los 4 negocios fundacionales provienen del dossier de auditoría de productos de Antigravity:

| Negocio | Nicho | Producto Asociado | Hunter Score | SRP (Venta) | Costo Puesto | Margen Neto % | Ganancia Neta | Salud Cuenta |
|---|---|---|---|---|---|---|---|---|
| **SteamFur Pro™** | Mascotas | Cepillo de Vapor Ultrasónico 3-en-1 | **100 / 100** | \$29.99 | \$3.50 | **83.4%** | **+\$25.02** | **96 / 100 🟢** |
| **ProSmile Ultrasonic™** | Salud Dental | Limpiador Dental Ultrasónico de Sarro | **100 / 100** | \$34.99 | \$8.20 | **71.8%** | **+\$25.13** | **98 / 100 🟢** |
| **SpineRelief Pro™** | Ergonomía | Cinturón Neumático de Descompresión L1-L5 | **97 / 100** | \$54.99 | \$14.80 | **68.7%** | **+\$37.75** | **95 / 100 🟢** |
| **AeroForce X3™** | Hogar & Autos | Mini Turbo Jet Blower 130,000 RPM | **97 / 100** | \$59.99 | \$16.80 | **67.6%** | **+\$40.55** | **97 / 100 🟢** |

### Semáforo Canónico de Estados de Canal (16 Canales Activos):
- 🟢 **Verde (`activo`):** Canal en régimen regular; publicación confirmada en las últimas 24h.
- 🟡 **Amarillo (`calentamiento`):** Canal en periodo de *warm-up* (días 1 a 5); sin bio link.
- 🔵 **Azul (`listo`):** Video renderizado y listo en cola para la franja de 11:00 AM o 7:00 PM EST.
- ⚪ **Gris (`pausado`):** Canal en espera o revisión programada.

---

## 🐍 6. Motor Backend en Python (`hub_engine.py`) y Manual de CLI

El motor `hub_engine.py` provee la lógica de datos con garantía de **escritura atómica** (vía archivos temporales y reemplazo con `os.replace`), cálculo matemático de salud de cuenta y comandos CLI.

### 6.1. Algoritmo Matemático de Puntaje de Salud (0 - 100)
El Account Health Score se calcula mediante una función ponderada multidimensional:
$$\text{Score} = w_c \cdot C + w_m \cdot M + w_r \cdot R + w_k \cdot K - P_{\text{inactividad}} - P_{\text{shadowban}}$$

- **Consistencia de Publicación ($C$, Peso 35%):** Evalúa el cumplimiento de 2 publicaciones diarias en los últimos 7 días.
- **Momento y Tráfico ($M$, Peso 30%):** Velocidad y volumen de reproducciones orgánicas normalizadas por canal.
- **Recencia ($R$, Peso 25%):** Penalización progresiva si han transcurrido más de 24 horas desde el último video. Si transcurren >72h, $R = 0$.
- **Conversión y Bio Clicks ($K$, Peso 10%):** Tasa de clics salientes hacia el checkout de la tienda.
- **Curva de Gracia en Calentamiento:** Las cuentas en estado `calentamiento` no son penalizadas por falta de clics en bio, preservando un puntaje base de 75-85 durante los días de warm-up.

### 6.2. Comandos CLI del Motor

```powershell
# Mostrar ayuda general
python hub_engine.py --help

# Listar todos los negocios registrados con métricas y salud
python hub_engine.py list

# Inspeccionar el detalle completo, credenciales y canales de un negocio
python hub_engine.py inspect --id steamfur-pro

# Auditar y recalcular la salud matemática de una cuenta
python hub_engine.py score --id prosmile-ultrasonic

# Registrar publicaciones, vistas y clics diarios
python hub_engine.py log-metrics --id aeroforce-x3 --posts 2 --views 24500 --clicks 610

# Archivar un negocio pausado
python hub_engine.py archive --id spinerelief-pro

# Desarchivar y reactivar un negocio
python hub_engine.py unarchive --id spinerelief-pro
```

---

## 💻 7. Panel Web Dashboard Interactivo (`index.html`)

El panel web ofrece una interfaz visual de monitoreo inspirada en terminales SaaS y trading, desarrollada con **Tailwind CSS (CDN)** y **Vanilla ECMAScript 2022** con **cero herramientas de build**, operable con doble clic en Windows (`file:///...`) o montada en cualquier servidor estático:

1. **Tarjetas Panorámicas Globales (KPIs en Vivo):**
   - *Negocios Activos:* Proporción de marcas operando en régimen normal (ej. `4 / 4 Activos`).
   - *Canales Totales:* Contador desglosado por red (ej. `16 Canales · 4 YT · 4 IG · 4 FB · 4 TK`).
   - *Videos Publicados Hoy:* Despacho diario completado (ej. `8 / 8 Videos`).
   - *Tráfico Estimado (24h):* Vistas acumuladas (ej. `158,400 reproducciones`).
   - *Clics a Tiendas:* Clics salientes hacia el checkout (ej. `4,120 clics`).
2. **Cuadrícula Interactiva de Negocios y Semáforos:**
   - Tarjetas de diseño premium oscuro con información de nicho, Hunter Score, Health Score dinámico y semáforo visual de 4 estados por canal.
3. **Modal Interactivo de Detalle (4 Pestañas Operativas):**
   - **Pestaña 1: Credenciales Aisladas:** Correo de gestión independiente, ID de perfil Dolphin Anty, IP del proxy móvil y dispositivo SIM asignado.
   - **Pestaña 2: Canales y Enlaces Directos:** Acceso en un clic a YouTube, Instagram, Facebook, TikTok y Shopify.
   - **Pestaña 3: Calendario de Publicaciones:** Horarios asignados de 11:00 AM y 7:00 PM EST con ángulos programados.
   - **Pestaña 4: 4 Ganchos de Conversión:** Visualización completa de los guiones de conversión con botón "Copiar Gancho" que provee retroalimentación visual inmediata.
4. **Módulo Dinámico "+ Nuevo Negocio":**
   - Formulario modal con validación en tiempo real para incorporar nuevos ganadores descubiertos por el Hunter, con pre-cálculo instantáneo de margen neto y markup.
5. **Buscador y Filtros en Tiempo Real:**
   - Búsqueda instantánea por nombre, nicho, producto o canal.
   - Filtros combinados por nicho, estado y plataforma con restablecimiento en 1 clic.
6. **Persistencia Híbrida y Exportador JSON:**
   - Las modificaciones locales se guardan en `localStorage` y se pueden exportar como archivo `negocios.json` descargable para sincronizar con el backend.

---

## ☁️ 8. Paquete de Automatización en la Nube con n8n (`automations_n8n/`)

Los flujos en formato estándar **n8n v1+** ejecutan la orquestación en el VPS Hetzner:

### 8.1. `flujo_despacho_triada_oro.json`
- **Disparador:** 11:00 AM y 7:00 PM EST (`America/New_York`).
- **Paso 1:** Valida la ventana pico algorítmica de EE. UU. (o flag de forzado).
- **Paso 2:** Obtiene videos en estado `READY` desde la tabla `Videos_Queue` de NocoDB (`josa-db.duckdns.org`).
- **Paso 3:** Sanitiza títulos (<100 caracteres, elimina tags HTML), deduplica hashtags y genera copys específicos para cada plataforma.
- **Paso 4:** Despacha en paralelo a **YouTube Shorts** (YouTube Data API v3), **Instagram Reels** (Meta Graph API v20.0 con contenedor y sondeo de transcodificación) y **Facebook Reels** (Meta Graph API v20.0).
- **Paso 5:** Registra auditoría en NocoDB actualizando el estado a `PUBLISHED` con las URLs en vivo.

### 8.2. `flujo_alerta_resumen_diario.json`
- **Disparador:** 21:30 EST (cierre nocturno).
- **Paso 1:** Consulta las publicaciones realizadas y el estado de los negocios en NocoDB.
- **Paso 2:** Agrega métricas consolidadas (videos publicados, vistas orgánicas, clics y CTR).
- **Paso 3:** Redacta un reporte ejecutivo con badges y emojis.
- **Paso 4:** Transmite el informe a **Telegram Bot API** y **WhatsApp Cloud API**.

> **Para la guía completa de despliegue Docker en 1 clic, Caddyfile y configuración de API Keys en Hetzner, consulta:**  
> 📖 [`automations_n8n/README_N8N.md`](automations_n8n/README_N8N.md)

---

## 🧪 9. Aseguramiento de Calidad y Suite de Pruebas Unitarias

El proyecto cuenta con una batería de pruebas unitarias automáticas desarrollada con la biblioteca estándar `unittest` de Python, garantizando cero roturas y 100% de confiabilidad.

### Ejecución de Pruebas en Windows PowerShell:

```powershell
# Ejecutar la suite completa de pruebas unitarias
python -m unittest discover -s tests -p "test_*.py"
```

Resultado de ejecución verificado:
```
..................................................................................
----------------------------------------------------------------------
Ran 82 tests in 5.204s

OK
```

### Áreas Validadas por la Suite:
- Persistencia atómica contra fallos repentinos de alimentación o caídas del sistema.
- Validación de esquemas y tipos de datos en `data/negocios.json`.
- Integridad matemática del algoritmo de Account Health Score en condiciones extremas y de borde.
- Detección precisa de flags de riesgo (`RIESGO_SHADOWBAN`, `RIESGO_DORMENCIA`, `PERIODO_WARMUP`).
- Comportamiento de comandos CLI y salidas de texto formateadas.

---

## 🔗 10. Enlaces Bidireccionales con el Segundo Cerebro (Obsidian)

Este proyecto se encuentra sincronizado con la bóveda canónica de Antigravity:

- `[[06-Sistema-Operativo-Segundo-Cerebro-y-3-Pilares.md]]` — Fundamentos de los 3 Pilares y doctrina de automatización.
- `[[Runbook-Blindaje-AntiBaneos-MultiCuentas-y-Orquestacion.md]]` — Manual maestro de aislamiento, proxies móviles y burner phones.
- `[[Runbook-Dropshipping-Hunter-y-Robot-Nube.md]]` — Metodología de prospección de ganadores y sincronización con GitHub Actions.
- `[[07-Manual-Maestro-Dropshipping-Seleccion-Producto-Ganador.md]]` — Las 7 Reglas de Oro y filtros Knockout.
- `[[Runbook-Memoria-Persistente-Obsidian-MCP-y-n8n.md]]` — Configuración de servidores Hetzner VPS, Caddy y base NocoDB.
- `[[01-Arquitectura-de-Servidor-y-Contexto-Maestro-Bots.md]]` — Parámetros de conexión SSH y contenedores de producción.
- `[[dossier_productos_ganadores.md]]` — Fichas técnicas completas de los 4 productos ganadores y sus guiones de Remotion.
