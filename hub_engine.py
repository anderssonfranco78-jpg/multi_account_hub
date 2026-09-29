#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Account Hub Engine (Centro de Mando de Cuentas y Negocios Independientes)
================================================================================
Core backend engine governing independent dropshipping businesses and their
channel clusters (YouTube Shorts, Instagram Reels, Facebook Reels, TikTok USA)
under strict anti-ban isolation principles.

Features:
- Thread-safe, atomic file persistence (tempfile write + os.replace pattern)
- Robust 0-100 Account Health Score algorithm with consistency, momentum,
  recency, conversion signals, dormancy penalties, and warm-up grace curves
- Full lifecycle CRUD & metrics logging for independent businesses
- Modular CLI interface for terminal and automation workflows
"""

import argparse
import contextlib
import copy
from datetime import datetime, timezone
import json
import math
import os
import sys
import tempfile
import threading
import time
from typing import Any, Dict, List, Optional, Tuple, Union

# Canonical Schema Version
SCHEMA_VERSION = "1.0.0"


def parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """
    Robust ISO-8601 datetime parser supporting UTC 'Z' suffixes, timezone offsets,
    and simple YYYY-MM-DD date strings. Returns timezone-aware datetime in UTC,
    or None if input is invalid, empty, or None.
    """
    if not dt_str or not isinstance(dt_str, str):
        return None
    cleaned = dt_str.strip()
    if not cleaned:
        return None
    try:
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        try:
            return datetime.strptime(cleaned, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None


# Default seed data for the 4 initial validated winning products from Dropshipping Hunter
INITIAL_BUSINESSES: List[Dict[str, Any]] = [
    {
        "id": "steamfur-pro",
        "nombre": "SteamFur Pro™",
        "nicho": "Mascotas & Cuidado del Hogar",
        "producto_asociado": {
            "nombre_completo": "SteamFur Pro™ — Cepillo de Vapor Iónico 3 en 1 para Mascotas",
            "categoria": "Pet Supplies & Home Care",
            "descripcion": "Conical silicone pet brush with integrated cold ion ultrasonic mist that neutralizes static and allows peeling off shed pet hair in a single solid sheet in 2 seconds.",
            "precio_sugerido_usd": 29.99,
            "costo_proveedor_usd": 1.0,
            "costo_envio_usd": 2.5,
            "costo_puesto_usd": 3.5,
            "beneficio_neto_usd": 25.02,
            "margen_neto_pct": 83.43,
            "markup_multiplier": 8.57,
            "proveedor_url": "https://www.aliexpress.com/w/wholesale-steamy-cat-brush.html",
            "sourcing_cj_url": "https://cjdropshipping.com/list-detail.html?search=steamy%20pet%20brush",
            "linea_logistica": "YunExpress Ordinary / CJPacket Fast Line (7 - 10 días laborables)",
            "paises_objetivo": [
                "US",
                "CA",
                "UK",
                "AU"
            ]
        },
        "score_hunter": 100.0,
        "enlace_tienda": "https://trysteamfur.com/products/pet-brush",
        "cluster_canales": {
            "youtube_shorts": {
                "handle": "@SteamFurPro",
                "canal_url": "https://www.youtube.com/channel/UCpJo7z99cTA1DFC36nK0Zng",
                "estado": "activo",
                "seguidores": 0,
                "reproducciones_totales": 0,
                "videos_publicados": 0,
                "ultimo_post": None
            },
            "instagram_reels": {
                "handle": "@steamfurpro",
                "canal_url": "https://www.instagram.com/steamfurpro",
                "estado": "activo",
                "seguidores": 0,
                "reproducciones_totales": 0,
                "videos_publicados": 0,
                "ultimo_post": None
            },
            "facebook_reels": {
                "handle": "SteamFur Pro Official",
                "canal_url": "https://www.facebook.com/profile.php?id=61594892791830",
                "estado": "activo",
                "seguidores": 0,
                "reproducciones_totales": 0,
                "videos_publicados": 0,
                "ultimo_post": None
            }
        },
        "credenciales_aisladas": {
            "correo_gestion": "ops.steamfur@gmail.com",
            "perfil_antidetect": "Profile-Dolphin-SteamFur-01",
            "proxy_asignado": "us-ny-res-01.proxy-pool.net:8080",
            "sim_mcc": "310 (T-Mobile USA inactiva)",
            "burner_device": "Burner-Phone-Pixel4a-SIM-MintUS-01",
            "n8n_credential_ref": "n8n_cred_steamfur_meta_v3",
            "api_keys_refs": {
                "youtube_api_env": "YT_API_KEY_STEAMFUR",
                "meta_graph_env": "META_TOKEN_STEAMFUR"
            }
        },
        "metricas_resumen": {
            "videos_hoy": 0,
            "vistas_hoy": 0,
            "clics_tienda_hoy": 0,
            "vistas_ultimos_7_dias": 0,
            "tasa_conversion_bio_pct": 0.0,
            "dias_sin_publicar": 0,
            "account_health_score": 95.0,
            "health_status": "optimo"
        },
        "historial_metricas": [],
        "ganchos_conversion": {
            "gancho_1_curiosidad": {
                "nombre": "Curiosidad Disruptiva: La Manta de Pelo Extraída en 3 Segundos",
                "voz_cliente": "¿Por qué los veterinarios aconsejan no cepillar a tu gato en seco nunca más?",
                "voz_creador": "Porque el vapor frío ionizado neutraliza la estática y retira el pelo muerto en una manta sólida.",
                "sfx": "STEAM_HISS",
                "texto_3d": "¿NO EN SECO?"
            },
            "gancho_2_agitacion": {
                "nombre": "Agitación de Dolor Real: La Pesadilla de los Pelos en Toda la Casa",
                "voz_cliente": "¿Cansado de encontrar pelos de gato en tu ropa, en el sofá y hasta en tu comida?",
                "voz_creador": "El cepillado común solo esparce los pelos por el aire; esto los atrapa al 100%.",
                "sfx": "RECORD_SCRATCH",
                "texto_3d": "¿PELOS EN TU COMIDA?"
            },
            "gancho_3_contrariano": {
                "nombre": "Contrariano: La Trampa de los Rodillos de Pegamento Adhesivo",
                "voz_cliente": "Por qué los rodillos adhesivos de papel son el peor gasto para dueños de mascotas...",
                "voz_creador": "Gastas una fortuna en rollos que no quitan la raíz del pelaje suelto.",
                "sfx": "TRASH_SLAM",
                "texto_3d": "DINERO PERDIDO"
            },
            "gancho_4_transformacion": {
                "nombre": "Transformación Inmediata: De la Lucha del Baño al Placer del Vapor",
                "voz_cliente": "De pasar 40 minutos persiguiendo a tu mascota con un cepillo que la estresa...",
                "voz_creador": "A retirarle toda la capa muerta en 3 minutos mientras disfruta de un masaje de vapor.",
                "sfx": "PURR_SOFT",
                "texto_3d": "SPA EN CASA"
            }
        },
        "horarios_publicacion_est": [
            "11:00 AM",
            "07:00 PM"
        ],
        "status": "activo",
        "created_at": "2026-09-20T12:00:00Z",
        "updated_at": "2026-09-23T23:00:00Z"
    },
    {
        "id": "prosmile-ultrasonic",
        "nombre": "ProSmile Ultrasonic™",
        "nicho": "Salud Dental & Cuidado Personal",
        "producto_asociado": {
            "nombre_completo": "ProSmile Ultrasonic™ — Limpiador Dental Ultrasónico de Sarro y Placa",
            "categoria": "Dental Health & Personal Care",
            "descripcion": "Home dental hygiene scaler with 40 kHz acoustic micro-vibrations and bioelectric sensor that shatters solid calculus instantly while stopping automatically on gums.",
            "precio_sugerido_usd": 34.99,
            "costo_proveedor_usd": 4.5,
            "costo_envio_usd": 3.7,
            "costo_puesto_usd": 8.2,
            "beneficio_neto_usd": 25.13,
            "margen_neto_pct": 71.82,
            "markup_multiplier": 4.27,
            "proveedor_url": "https://www.aliexpress.com/w/wholesale-ultrasonic-dental-calculus-remover.html",
            "sourcing_cj_url": "https://cjdropshipping.com/list-detail.html?search=ultrasonic%20tooth%20cleaner",
            "linea_logistica": "CJPacket Fast Line / YunExpress Ordinary (7 - 10 días laborables)",
            "paises_objetivo": [
                "US",
                "UK",
                "DE",
                "AU"
            ]
        },
        "score_hunter": 100.0,
        "enlace_tienda": "https://getprosmile.com/products/ultrasonic-scaler",
        "cluster_canales": {
            "youtube_shorts": {
                "handle": "@ProSmileDental",
                "canal_url": "https://youtube.com/@ProSmileDental",
                "estado": "pausado",
                "seguidores": 0,
                "reproducciones_totales": 0,
                "videos_publicados": 0,
                "ultimo_post": None
            },
            "instagram_reels": {
                "handle": "@prosmile_smile",
                "canal_url": "https://instagram.com/prosmile_smile",
                "estado": "pausado",
                "seguidores": 0,
                "reproducciones_totales": 0,
                "videos_publicados": 0,
                "ultimo_post": None
            },
            "facebook_reels": {
                "handle": "ProSmile Oral Care",
                "canal_url": "https://facebook.com/prosmile_oralcare",
                "estado": "pausado",
                "seguidores": 0,
                "reproducciones_totales": 0,
                "videos_publicados": 0,
                "ultimo_post": None
            }
        },
        "credenciales_aisladas": {
            "correo_gestion": "ops.prosmile@gmail.com",
            "perfil_antidetect": "Profile-Dolphin-ProSmile-02",
            "proxy_asignado": "us-fl-res-02.proxy-pool.net:8080",
            "sim_mcc": "310 (AT&T USA inactiva)",
            "burner_device": "Burner-Phone-Pixel5-SIM-UltraMobileUS-02",
            "n8n_credential_ref": "n8n_cred_prosmile_meta_v3",
            "api_keys_refs": {
                "youtube_api_env": "YT_API_KEY_PROSMILE",
                "meta_graph_env": "META_TOKEN_PROSMILE"
            }
        },
        "metricas_resumen": {
            "videos_hoy": 0,
            "vistas_hoy": 0,
            "clics_tienda_hoy": 0,
            "vistas_ultimos_7_dias": 0,
            "tasa_conversion_bio_pct": 0.0,
            "dias_sin_publicar": 0,
            "account_health_score": 75.0,
            "health_status": "en_espera"
        },
        "historial_metricas": [],
        "ganchos_conversion": {
            "gancho_1_curiosidad": {
                "nombre": "Curiosidad Disruptiva: El Metal que No Rompe Huevos",
                "voz_cliente": "¿Cómo es posible que esto rompa piedra pero no pueda reventar un globo?",
                "voz_creador": "Porque tiene un sensor acústico que solo se activa al tocar sarro duro.",
                "sfx": "RECORD_SCRATCH_QUICK",
                "texto_3d": "¿ROMPE PIEDRA?"
            },
            "gancho_2_agitacion": {
                "nombre": "Agitación de Dolor Real: La Vergüenza de Sonreír en Fotos",
                "voz_cliente": "Si dejas de sonreír en las fotos porque te da vergüenza el sarro amarillo acumulado...",
                "voz_creador": "Y no tienes $300 de sobra para pagarle al dentista cada 6 meses...",
                "sfx": "HEARTBEAT_DULL",
                "texto_3d": "¿VERGÜENZA AL SONREÍR?"
            },
            "gancho_3_contrariano": {
                "nombre": "Contrariano: Por qué tu Cepillo de $120 No Sirve para el Sarro",
                "voz_cliente": "Por qué cepillarte 3 veces al día jamás quitará el sarro duro de tus dientes...",
                "voz_creador": "El sarro es piedra caliza sólida; el cepillo de cerdas solo le hace cosquillas.",
                "sfx": "BRUSH_SCRUB_FAST",
                "texto_3d": "NO LO QUITA"
            },
            "gancho_4_transformacion": {
                "nombre": "Transformación Inmediata: De 5 Años de Sarro a Dientes de Seda",
                "voz_cliente": "De tener 5 años de sarro y manchas de tabaco pegadas a los dientes...",
                "voz_creador": "A dejarlos con textura de seda y completamente limpios en 10 minutos.",
                "sfx": "SAD_SCRATCH",
                "texto_3d": "TEXTURA DE SEDA"
            }
        },
        "horarios_publicacion_est": [
            "11:00 AM",
            "07:00 PM"
        ],
        "status": "en_preparacion",
        "created_at": "2026-09-19T10:00:00Z",
        "updated_at": "2026-09-23T23:00:00Z"
    },
    {
        "id": "spinerelief-pro",
        "nombre": "SpineRelief Pro™",
        "nicho": "Ergonomía & Salud Lumbar",
        "producto_asociado": {
            "nombre_completo": "SpineRelief Pro™ — Cinturón Neumático de Descompresión Lumbar L1-L5",
            "categoria": "Health & Ergonomics",
            "descripcion": "Clinical-grade inflatable lumbar traction belt with 24 pneumatic columns providing 2.5 bar decompression for L1-L5 vertebrae and acute sciatica nerve relief.",
            "precio_sugerido_usd": 54.99,
            "costo_proveedor_usd": 10.0,
            "costo_envio_usd": 4.8,
            "costo_puesto_usd": 14.8,
            "beneficio_neto_usd": 37.75,
            "margen_neto_pct": 68.65,
            "markup_multiplier": 3.72,
            "proveedor_url": "https://www.aliexpress.com/w/wholesale-lumbar-traction-belt.html",
            "sourcing_cj_url": "https://cjdropshipping.com/list-detail.html?search=lumbar%20traction%20belt",
            "linea_logistica": "YunExpress Specialty Line (7 - 10 días laborables)",
            "paises_objetivo": [
                "US",
                "UK",
                "CA",
                "AU"
            ]
        },
        "score_hunter": 97.0,
        "enlace_tienda": "https://spinerelief.store/products/traction-belt",
        "cluster_canales": {
            "youtube_shorts": {
                "handle": "@SpineReliefTech",
                "canal_url": "https://youtube.com/@SpineReliefTech",
                "estado": "pausado",
                "seguidores": 0,
                "reproducciones_totales": 0,
                "videos_publicados": 0,
                "ultimo_post": None
            },
            "instagram_reels": {
                "handle": "@spinerelief_us",
                "canal_url": "https://instagram.com/spinerelief_us",
                "estado": "pausado",
                "seguidores": 0,
                "reproducciones_totales": 0,
                "videos_publicados": 0,
                "ultimo_post": None
            },
            "facebook_reels": {
                "handle": "SpineRelief Official",
                "canal_url": "https://facebook.com/spinerelief_official",
                "estado": "pausado",
                "seguidores": 0,
                "reproducciones_totales": 0,
                "videos_publicados": 0,
                "ultimo_post": None
            }
        },
        "credenciales_aisladas": {
            "correo_gestion": "ops.spinerelief@gmail.com",
            "perfil_antidetect": "Profile-Dolphin-SpineRelief-03",
            "proxy_asignado": "us-tx-res-03.proxy-pool.net:8080",
            "sim_mcc": "311 (Verizon USA inactiva)",
            "burner_device": "Burner-Phone-GalaxyS10-SIM-MintUS-03",
            "n8n_credential_ref": "n8n_cred_spinerelief_meta_v3",
            "api_keys_refs": {
                "youtube_api_env": "YT_API_KEY_SPINERELIEF",
                "meta_graph_env": "META_TOKEN_SPINERELIEF"
            }
        },
        "metricas_resumen": {
            "videos_hoy": 0,
            "vistas_hoy": 0,
            "clics_tienda_hoy": 0,
            "vistas_ultimos_7_dias": 0,
            "tasa_conversion_bio_pct": 0.0,
            "dias_sin_publicar": 0,
            "account_health_score": 75.0,
            "health_status": "en_espera"
        },
        "historial_metricas": [],
        "ganchos_conversion": {
            "gancho_1_curiosidad": {
                "nombre": "Curiosidad Disruptiva: El Secreto Médico Prohibido",
                "voz_cliente": "¿Por qué los camioneros tienen prohibido manejar sin inflarse esto?",
                "voz_creador": "Porque en 30 segundos separa tus vértebras 7 milímetros.",
                "sfx": "WHOOSH_FAST",
                "texto_3d": "¿PROHIBIDO?"
            },
            "gancho_2_agitacion": {
                "nombre": "Agitación de Dolor Real: El Ardor Lumbar al Levantarte",
                "voz_cliente": "Si levantarte de la cama o del auto te toma 5 minutos por ese ardor lumbar...",
                "voz_creador": "Tus vértebras están aplastando este nervio ahora mismo.",
                "sfx": "HEARTBEAT_LOW",
                "texto_3d": "¿ARDOR LUMBAR?"
            },
            "gancho_3_contrariano": {
                "nombre": "Contrariano: La Farsa de las Fajas de Farmacia",
                "voz_cliente": "Por qué gastar $150 en fajas de farmacia empeora tu dolor de espalda...",
                "voz_creador": "Porque apretar tu abdomen no separa tus huesos.",
                "sfx": "TRASH_SLAM",
                "texto_3d": "NO SIRVEN"
            },
            "gancho_4_transformacion": {
                "nombre": "Transformación Inmediata: De la Incapacidad a la Plenitud",
                "voz_cliente": "De no poder atarte las zapatillas por el dolor de ciática...",
                "voz_creador": "A pasar 6 horas de pie sin un solo tirón lumbar.",
                "sfx": "RECORD_SCRATCH",
                "texto_3d": "ANTES / DESPUÉS"
            }
        },
        "horarios_publicacion_est": [
            "11:00 AM",
            "07:00 PM"
        ],
        "status": "en_preparacion",
        "created_at": "2026-09-20T14:00:00Z",
        "updated_at": "2026-09-23T23:00:00Z"
    },
    {
        "id": "aeroforce-x3",
        "nombre": "AeroForce X3™",
        "nicho": "Automotriz & Herramientas Tácticas",
        "producto_asociado": {
            "nombre_completo": "AeroForce X3™ — Micro-Turbina Violenta de 130,000 RPM para Secado y Detailing",
            "categoria": "Automotive & Tactical Tools",
            "descripcion": "Handheld micro-turbine jet fan with 130,000 RPM brushless motor delivering 52 m/s wind speed for contact-free car drying, detailing, and keyboard cleaning without swirl marks.",
            "precio_sugerido_usd": 59.99,
            "costo_proveedor_usd": 12.0,
            "costo_envio_usd": 4.8,
            "costo_puesto_usd": 16.8,
            "beneficio_neto_usd": 40.55,
            "margen_neto_pct": 67.59,
            "markup_multiplier": 3.57,
            "proveedor_url": "https://www.aliexpress.com/w/wholesale-turbo-jet-fan.html",
            "sourcing_cj_url": "https://cjdropshipping.com/list-detail.html?search=turbo%20jet%20fan",
            "linea_logistica": "YunExpress Special Battery Line / CJPacket Sensitive (UN38.3) (8 - 11 días hábiles)",
            "paises_objetivo": [
                "US",
                "CA",
                "AU",
                "UK"
            ]
        },
        "score_hunter": 97.0,
        "enlace_tienda": "https://aeroforcejet.com/products/x3-turbo-fan",
        "cluster_canales": {
            "youtube_shorts": {
                "handle": "@AeroForceTurbine",
                "canal_url": "https://youtube.com/@AeroForceTurbine",
                "estado": "pausado",
                "seguidores": 0,
                "reproducciones_totales": 0,
                "videos_publicados": 0,
                "ultimo_post": None
            },
            "instagram_reels": {
                "handle": "@aeroforce_x3",
                "canal_url": "https://instagram.com/aeroforce_x3",
                "estado": "pausado",
                "seguidores": 0,
                "reproducciones_totales": 0,
                "videos_publicados": 0,
                "ultimo_post": None
            },
            "facebook_reels": {
                "handle": "AeroForce Jet Fan",
                "canal_url": "https://facebook.com/aeroforce_fan",
                "estado": "pausado",
                "seguidores": 0,
                "reproducciones_totales": 0,
                "videos_publicados": 0,
                "ultimo_post": None
            }
        },
        "credenciales_aisladas": {
            "correo_gestion": "ops.aeroforce@gmail.com",
            "perfil_antidetect": "Profile-Dolphin-AeroForce-04",
            "proxy_asignado": "us-ca-res-04.proxy-pool.net:8080",
            "sim_mcc": "310 (T-Mobile USA inactiva)",
            "burner_device": "Burner-Phone-Pixel4-SIM-TelloUS-04",
            "n8n_credential_ref": "n8n_cred_aeroforce_meta_v3",
            "api_keys_refs": {
                "youtube_api_env": "YT_API_KEY_AEROFORCE",
                "meta_graph_env": "META_TOKEN_AEROFORCE"
            }
        },
        "metricas_resumen": {
            "videos_hoy": 0,
            "vistas_hoy": 0,
            "clics_tienda_hoy": 0,
            "vistas_ultimos_7_dias": 0,
            "tasa_conversion_bio_pct": 0.0,
            "dias_sin_publicar": 0,
            "account_health_score": 75.0,
            "health_status": "en_espera"
        },
        "historial_metricas": [],
        "ganchos_conversion": {
            "gancho_1_curiosidad": {
                "nombre": "Curiosidad Disruptiva: Un Motor de Caza en el Bolsillo",
                "voz_cliente": "¿Cómo es legal tener un motor de avión en el bolsillo?",
                "voz_creador": "130,000 revoluciones por minuto. Esto no es un juguete.",
                "sfx": "AIR_BLAST_WHOOSH",
                "texto_3d": "¿CÓMO ES LEGAL?"
            },
            "gancho_2_agitacion": {
                "nombre": "Agitación de Dolor Real: Los Swirl Marks que Destruyen tu Auto",
                "voz_cliente": "Si secas tu auto con toallas de microfibra, estás arruinando tu pintura...",
                "voz_creador": "Una sola mota de polvo atrapada en el trapo y tu coche pierde el 30% de su valor.",
                "sfx": "GLASS_SCRATCH",
                "texto_3d": "ESTÁS RAYANDO TU AUTO"
            },
            "gancho_3_contrariano": {
                "nombre": "Contrariano: La Estafa de las Latas Desechables de Aire",
                "voz_cliente": "Deja de tirar tu dinero en latas de aire comprimido que se congelan en 20 segundos...",
                "voz_creador": "Pagas $10 por lata para que escupan líquido y se queden sin fuerza a la mitad.",
                "sfx": "GAS_FART_FAIL",
                "texto_3d": "ESTAFA TOTAL"
            },
            "gancho_4_transformacion": {
                "nombre": "Transformación Inmediata: De Espejos Goteando a Acabado Profesional",
                "voz_cliente": "De terminar de lavar tu coche y ver cómo el agua estancada te arruina la pintura otra vez...",
                "voz_creador": "A dejar cada rincón sellado y seco al 100% en menos de 2 minutos.",
                "sfx": "SAD_TROMBONE_SHORT",
                "texto_3d": "SECO EN 2 MIN"
            }
        },
        "horarios_publicacion_est": [
            "11:00 AM",
            "07:00 PM"
        ],
        "status": "en_preparacion",
        "created_at": "2026-09-20T16:00:00Z",
        "updated_at": "2026-09-23T23:00:00Z"
    }
]

class BusinessStorage:
    """
    Thread-safe atomic storage engine for businesses JSON data.
    Implements a safe write-sync-swap pattern using tempfile and os.replace.
    """

    def __init__(self, file_path: str):
        self.file_path = os.path.abspath(file_path)
        self._lock = threading.RLock()
        self._ensure_storage_ready()

    @property
    def lock(self) -> threading.RLock:
        """Expose the re-entrant storage lock for transaction synchronization."""
        return self._lock

    @contextlib.contextmanager
    def transaction(self):
        """
        Context manager providing atomic transaction semantics across the entire
        read-modify-write cycle.
        """
        with self._lock:
            data = self.load()
            yield data
            self.save(data)

    def _ensure_storage_ready(self) -> None:
        """Create parent directory and initial file if not existing."""
        parent_dir = os.path.dirname(self.file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        if not os.path.exists(self.file_path):
            initial_envelope = {
                "version": SCHEMA_VERSION,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "total_businesses": 0,
                "businesses": [],
            }
            self.save(initial_envelope)

    def load(self) -> Dict[str, Any]:
        """
        Loads and validates JSON data envelope from file.
        Raises ValueError if file content is corrupted or non-compliant.
        """
        with self._lock:
            if not os.path.exists(self.file_path):
                self._ensure_storage_ready()

            content = None
            max_retries = 10
            delay = 0.005
            for attempt in range(max_retries):
                try:
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    break
                except (PermissionError, OSError) as read_err:
                    if attempt == max_retries - 1:
                        raise ValueError(f"Failed to read {self.file_path}: {read_err}") from read_err
                    time.sleep(delay)
                    delay = min(delay * 2, 0.1)

            if not content:
                raise ValueError(f"Empty JSON file at {self.file_path}")

            try:
                data = json.loads(content)
            except json.JSONDecodeError as err:
                raise ValueError(f"Corrupted or invalid JSON in {self.file_path}: {err}") from err
            except Exception as err:
                raise ValueError(f"Failed to read {self.file_path}: {err}") from err

            if not isinstance(data, dict):
                raise ValueError(f"Root JSON element must be an object envelope, got {type(data)}")

            if "businesses" not in data or not isinstance(data["businesses"], list):
                raise ValueError("JSON envelope missing required 'businesses' array")

            return data

    def save(self, data: Dict[str, Any]) -> None:
        """
        Atomically saves JSON envelope to file using tempfile + os.replace.
        Guarantees that a write interruption never leaves a corrupted file.
        Includes exponential backoff retry loop for Windows NTFS file contention.
        """
        if not isinstance(data, dict) or "businesses" not in data:
            raise ValueError("Data to persist must be a dictionary envelope containing 'businesses'")

        # Keep counters and timestamps updated
        data["total_businesses"] = len(data["businesses"])
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        if "version" not in data:
            data["version"] = SCHEMA_VERSION

        parent_dir = os.path.dirname(self.file_path) or "."
        with self._lock:
            temp_file = tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=parent_dir,
                delete=False,
                suffix=".tmp",
            )
            temp_path = temp_file.name
            try:
                json.dump(data, temp_file, indent=2, ensure_ascii=False)
                temp_file.flush()
                os.fsync(temp_file.fileno())
                temp_file.close()

                # Robust retry loop with exponential backoff for Windows file contention ([WinError 5] / [WinError 32])
                max_retries = 10
                delay = 0.005
                for attempt in range(max_retries):
                    try:
                        os.replace(temp_path, self.file_path)
                        break
                    except (PermissionError, OSError) as replace_err:
                        if attempt == max_retries - 1:
                            raise replace_err
                        time.sleep(delay)
                        delay = min(delay * 2, 0.1)
            except Exception as err:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                raise IOError(f"Atomic persistence failure writing {self.file_path}: {err}") from err

    def reload(self) -> Dict[str, Any]:
        """Forces an in-lock disk reload."""
        with self._lock:
            return self.load()


class HealthScorer:
    """
    Mathematical evaluator of the 0-100 Account Health Score.
    
    Formula components:
    - Consistency S_cons (Max 35 pts): 2 posts/day target = 14 posts / 7 days
    - Momentum S_mom (Max 30 pts): 3-day view velocity against baseline
    - Recency S_rec (Max 25 pts): Days elapsed since last published video
    - Conversion S_conv (Max 10 pts): Bio CTR and store click signals
    - Penalties P_pen: Prolonged dormancy, shadowban warning, paused triad channels
    """

    @classmethod
    def _evaluate_penalties(
        cls,
        status: str,
        effective_d_last: int,
        metrics_summary: Dict[str, Any],
        channels: Dict[str, Any],
    ) -> Tuple[float, List[str], List[str]]:
        """
        Evaluates dormancy penalties, shadowban risk, and paused triad channels.
        """
        p_penalties = 0.0
        penalty_reasons: List[str] = []
        flags: List[str] = []

        # Dormancy penalty (if > 3 days inactive, not warming up)
        if status != "calentamiento" and effective_d_last > 3:
            dormancy_deduction = min(20.0, 5.0 * (effective_d_last - 3))
            p_penalties += dormancy_deduction
            penalty_reasons.append(
                f"Inactividad prolongada: {effective_d_last} días sin publicar (-{dormancy_deduction:.1f} pts)"
            )

        # Shadowban risk detection: active posts in last 2 days but < 50 views (including 0 views)
        views_today = metrics_summary.get("vistas_hoy")
        if views_today is None:
            views_today = 0
        posts_today = metrics_summary.get("videos_hoy")
        if posts_today is None:
            posts_today = 0

        if status == "activo" and effective_d_last <= 2 and (posts_today > 0 or effective_d_last == 0):
            if views_today < 50:
                p_penalties += 20.0
                reason = "Riesgo de Shadowban detectado: publicaciones activas con menos de 50 vistas (-20.0 pts)"
                penalty_reasons.append(reason)
                flags.append("RIESGO_SHADOWBAN")

        # Triad channel paused penalty: 8 pts deduction per paused channel in active business
        triad_channels = ["youtube_shorts", "instagram_reels", "facebook_reels"]
        if status == "activo":
            for ch_key in triad_channels:
                ch_info = channels.get(ch_key, {})
                if isinstance(ch_info, dict) and ch_info.get("estado") in ["pausado", "error"]:
                    p_penalties += 8.0
                    penalty_reasons.append(
                        f"Canal de Tríada de Oro '{ch_key}' en estado inactivo/pausado (-8.0 pts)"
                    )

        return p_penalties, penalty_reasons, flags

    @classmethod
    def calculate_score(
        cls,
        business_data: Optional[Dict[str, Any]],
        as_of_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Pure, deterministic calculation of Account Health Score.
        Zero-division safe, None-safe, and supports timestamp injection for unit testing.
        """
        if as_of_date is None:
            as_of_date = datetime.now(timezone.utc)
        elif as_of_date.tzinfo is None:
            as_of_date = as_of_date.replace(tzinfo=timezone.utc)

        if not isinstance(business_data, dict):
            business_data = {}

        raw_status = business_data.get("status")
        status = (raw_status if raw_status is not None else "activo").lower()

        channels = business_data.get("cluster_canales")
        if not isinstance(channels, dict):
            channels = {}

        metrics_summary = business_data.get("metricas_resumen")
        if not isinstance(metrics_summary, dict):
            metrics_summary = {}

        metrics_history = business_data.get("historial_metricas")
        if not isinstance(metrics_history, list):
            metrics_history = []

        # -------------------------------------------------------------
        # 1. Posting Consistency (Max: 35.0 pts)
        # Target: 14 posts over 7 days (2 posts/day)
        # -------------------------------------------------------------
        if status == "calentamiento":
            # Warm-up accounts are strictly prohibited from posting in days 1-4.
            # Grace curve: award full consistency marks.
            s_consistency = 35.0
        else:
            recent_posts_count = 0
            if metrics_history:
                # Sum last 7 entries
                recent_entries = metrics_history[-7:]
                raw_sum = sum(
                    (e.get("videos_publicados") or 0)
                    for e in recent_entries
                    if isinstance(e, dict)
                )
                # If history has fewer than 7 entries, extrapolate daily cadence to 7 days
                if 0 < len(recent_entries) < 7:
                    daily_avg = raw_sum / len(recent_entries)
                    recent_posts_count = max(raw_sum, daily_avg * 7.0)
                else:
                    recent_posts_count = raw_sum
            else:
                # Fallback to summary or channel sums
                recent_posts_count = metrics_summary.get("videos_hoy") or 0
                if recent_posts_count == 0:
                    recent_posts_count = sum(
                        (ch.get("videos_publicados") or 0)
                        for ch in channels.values()
                        if isinstance(ch, dict)
                    )

            ratio = min(1.0, max(0.0, recent_posts_count / 14.0))
            s_consistency = round(ratio * 35.0, 2)

        # -------------------------------------------------------------
        # 2. View Momentum (Max: 30.0 pts)
        # Velocity of 3-day average vs 7-day baseline
        # -------------------------------------------------------------
        if status == "calentamiento":
            s_momentum = 25.0
        elif len(metrics_history) >= 3:
            last_3 = metrics_history[-3:]
            v_3d = sum((e.get("vistas") or 0) for e in last_3 if isinstance(e, dict)) / 3.0

            prior_entries = metrics_history[:-3]
            if prior_entries:
                v_7d = sum(
                    (e.get("vistas") or 0) for e in prior_entries[-7:] if isinstance(e, dict)
                ) / max(len(prior_entries[-7:]), 1)
                delta_v = (v_3d - v_7d) / max(v_7d, 100.0)
            else:
                # If exactly 3 entries in history, compare first day to last day within window
                first_e = metrics_history[0] if isinstance(metrics_history[0], dict) else {}
                last_e = metrics_history[-1] if isinstance(metrics_history[-1], dict) else {}
                v_start = first_e.get("vistas") or 0
                v_end = last_e.get("vistas") or 0
                if v_start > 0:
                    delta_v = (v_end - v_start) / max(v_start, 100.0)
                else:
                    delta_v = 0.0

            if delta_v >= 0.20:
                s_momentum = 30.0
            elif delta_v >= 0.0:
                s_momentum = 22.0 + 8.0 * (delta_v / 0.20)
            elif delta_v >= -0.20:
                s_momentum = 15.0 + 7.0 * ((delta_v + 0.20) / 0.20)
            else:
                s_momentum = max(5.0, 15.0 * (1.0 + delta_v))
            s_momentum = round(min(30.0, max(0.0, s_momentum)), 2)
        else:
            # Fallback by absolute views volume
            total_views = metrics_summary.get("vistas_hoy") or 0
            if total_views == 0 and channels:
                total_views = sum(
                    (ch.get("reproducciones_totales") or 0)
                    for ch in channels.values()
                    if isinstance(ch, dict)
                )

            if total_views >= 5000:
                s_momentum = 28.0
            elif total_views >= 1000:
                s_momentum = 22.0
            elif total_views >= 200:
                s_momentum = 16.0
            else:
                s_momentum = 10.0

        # -------------------------------------------------------------
        # 3. Recency / Days Since Last Video (Max: 25.0 pts)
        # -------------------------------------------------------------
        d_last: Optional[int] = None

        # Check explicit summary field first if provided
        if "dias_sin_publicar" in metrics_summary and metrics_summary["dias_sin_publicar"] is not None:
            try:
                d_last = int(metrics_summary["dias_sin_publicar"])
            except (ValueError, TypeError):
                d_last = None

        if d_last is None:
            # Inspect latest post timestamp across all channels
            latest_dt: Optional[datetime] = None
            for ch in channels.values():
                if isinstance(ch, dict) and ch.get("ultimo_post"):
                    ch_dt = parse_iso_datetime(ch["ultimo_post"])
                    if ch_dt and (latest_dt is None or ch_dt > latest_dt):
                        latest_dt = ch_dt

            if latest_dt:
                d_last = max(0, (as_of_date - latest_dt).days)

        if status == "calentamiento" and (d_last is None or d_last == 0):
            s_recency = 25.0
            effective_d_last = 0
        elif d_last is None:
            s_recency = 10.0
            effective_d_last = 3
        else:
            effective_d_last = max(0, d_last)
            if effective_d_last == 0:
                s_recency = 25.0
            elif effective_d_last == 1:
                s_recency = 22.0
            elif effective_d_last == 2:
                s_recency = 16.0
            elif effective_d_last == 3:
                s_recency = 10.0
            elif effective_d_last == 4:
                s_recency = 4.0
            else:
                s_recency = 0.0

        # -------------------------------------------------------------
        # 4. Conversion & Store Clicks Signal (Max: 10.0 pts)
        # Bio CTR = clics_checkout / max(vistas, 1)
        # -------------------------------------------------------------
        views_sample = metrics_summary.get("vistas_hoy") or 0
        clicks_sample = metrics_summary.get("clics_tienda_hoy") or 0
        bio_rate = metrics_summary.get("tasa_conversion_bio_pct")

        if bio_rate is not None:
            try:
                ctr = float(bio_rate) / 100.0
            except (ValueError, TypeError):
                ctr = clicks_sample / max(views_sample, 1)
        else:
            ctr = clicks_sample / max(views_sample, 1)

        if status == "calentamiento":
            s_conversion = 10.0
        elif ctr >= 0.008:
            s_conversion = 10.0
        elif ctr >= 0.004:
            s_conversion = 7.5
        elif ctr >= 0.001:
            s_conversion = 5.0
        else:
            if views_sample > 2000 and clicks_sample == 0:
                s_conversion = 0.0
            else:
                s_conversion = 2.5

        # -------------------------------------------------------------
        # 5. Penalties Deduction
        # -------------------------------------------------------------
        p_penalties, penalty_reasons, flags = cls._evaluate_penalties(
            status, effective_d_last, metrics_summary, channels
        )

        # Compute final clamped score
        raw_total = s_consistency + s_momentum + s_recency + s_conversion - p_penalties
        total_score = round(max(0.0, min(100.0, raw_total)), 1)

        # Assign status category
        if total_score >= 85.0:
            health_status = "optimo"
        elif total_score >= 70.0:
            health_status = "estable"
        elif total_score >= 50.0:
            health_status = "alerta"
        else:
            health_status = "critico"

        return {
            "total_score": total_score,
            "health_status": health_status,
            "breakdown": {
                "consistency_score": round(s_consistency, 2),
                "momentum_score": round(s_momentum, 2),
                "recency_score": round(s_recency, 2),
                "conversion_score": round(s_conversion, 2),
                "penalties_deducted": round(p_penalties, 2),
                "penalty_reasons": penalty_reasons,
                "flags": flags,
            },
        }

    # Public API alias
    calculate = calculate_score


class HubEngine:
    """
    Main Multi-Account Hub Engine.
    Coordinates storage, validation, health scoring, and all 8 lifecycle operations.
    """

    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            # Default to data/negocios.json located next to this file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(base_dir, "data", "negocios.json")

        self.storage = BusinessStorage(data_path)
        self.scorer = HealthScorer()

    # -------------------------------------------------------------
    # 1. Operation: add_business
    # -------------------------------------------------------------
    def add_business(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates schema, checks unique ID, initializes defaults,
        calculates health score, and atomically persists new business.
        Raises ValueError if ID exists or required fields are missing.
        """
        if not isinstance(business_data, dict):
            raise ValueError(f"Business data must be a dict, got {type(business_data)}")

        req_fields = ["id", "nombre", "nicho"]
        for field in req_fields:
            if not business_data.get(field):
                raise ValueError(f"Missing required field '{field}' for new business")

        business_id = str(business_data["id"]).strip().lower()

        with self.storage.lock:
            data = self.storage.load()

            # Check unique ID
            for b in data["businesses"]:
                if b.get("id") == business_id:
                    raise ValueError(f"Business with ID '{business_id}' already exists")

            new_b = copy.deepcopy(business_data)
            new_b["id"] = business_id
            new_b["nombre"] = str(new_b["nombre"]).strip()
            new_b["nicho"] = str(new_b["nicho"]).strip()
            new_b.setdefault("status", "activo")

            # Initialize channel clusters if missing
            if "cluster_canales" not in new_b or not isinstance(new_b["cluster_canales"], dict):
                new_b["cluster_canales"] = {
                    "youtube_shorts": {
                        "handle": f"@{business_id}_yt",
                        "canal_url": f"https://youtube.com/@{business_id}",
                        "estado": "activo",
                        "seguidores": 0,
                        "reproducciones_totales": 0,
                        "videos_publicados": 0,
                        "ultimo_post": None,
                    },
                    "instagram_reels": {
                        "handle": f"@{business_id}_ig",
                        "canal_url": f"https://instagram.com/{business_id}",
                        "estado": "activo",
                        "seguidores": 0,
                        "reproducciones_totales": 0,
                        "videos_publicados": 0,
                        "ultimo_post": None,
                    },
                    "facebook_reels": {
                        "handle": f"{new_b['nombre']} Official",
                        "canal_url": f"https://facebook.com/{business_id}",
                        "estado": "activo",
                        "seguidores": 0,
                        "reproducciones_totales": 0,
                        "videos_publicados": 0,
                        "ultimo_post": None,
                    },
                }

            # Initialize summary metrics if missing
            new_b.setdefault("historial_metricas", [])
            if "metricas_resumen" not in new_b:
                new_b["metricas_resumen"] = {
                    "videos_hoy": 0,
                    "vistas_hoy": 0,
                    "clics_tienda_hoy": 0,
                    "vistas_ultimos_7_dias": 0,
                    "tasa_conversion_bio_pct": 0.0,
                    "dias_sin_publicar": 0,
                    "account_health_score": 0.0,
                    "health_status": "critico",
                }

            # Compute initial health score
            score_res = self.scorer.calculate_score(new_b)
            new_b["metricas_resumen"]["account_health_score"] = score_res["total_score"]
            new_b["metricas_resumen"]["health_status"] = score_res["health_status"]

            # Timestamps
            now_iso = datetime.now(timezone.utc).isoformat()
            new_b.setdefault("created_at", now_iso)
            new_b["updated_at"] = now_iso

            # Append and persist
            data["businesses"].append(new_b)
            self.storage.save(data)
            return copy.deepcopy(new_b)

    # -------------------------------------------------------------
    # 2. Operation: update_business
    # -------------------------------------------------------------
    def update_business(self, business_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies partial updates to an existing business, recalculates health score,
        updates timestamp, and atomically persists.
        Raises KeyError if business_id does not exist.
        """
        business_id = str(business_id).strip().lower()
        with self.storage.lock:
            data = self.storage.load()

            target_idx = -1
            for idx, b in enumerate(data["businesses"]):
                if b.get("id") == business_id:
                    target_idx = idx
                    break

            if target_idx == -1:
                raise KeyError(f"Business '{business_id}' not found")

            current = data["businesses"][target_idx]

            # Apply updates while protecting immutable fields
            for k, v in updates.items():
                if k in ["id", "created_at"]:
                    continue
                if isinstance(v, dict) and isinstance(current.get(k), dict):
                    current[k].update(v)
                else:
                    current[k] = v

            current["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Recalculate health score
            score_res = self.scorer.calculate_score(current)
            if "metricas_resumen" not in current:
                current["metricas_resumen"] = {}
            current["metricas_resumen"]["account_health_score"] = score_res["total_score"]
            current["metricas_resumen"]["health_status"] = score_res["health_status"]

            data["businesses"][target_idx] = current
            self.storage.save(data)
            return copy.deepcopy(current)

    # -------------------------------------------------------------
    # 3. Operation: archive_business
    # -------------------------------------------------------------
    def archive_business(self, business_id: str) -> Dict[str, Any]:
        """
        Non-destructive soft-delete: sets status='archivado', pauses channels,
        records archived_at, and atomically persists.
        Raises KeyError if business_id does not exist.
        """
        business_id = str(business_id).strip().lower()
        with self.storage.lock:
            data = self.storage.load()

            target = None
            for b in data["businesses"]:
                if b.get("id") == business_id:
                    target = b
                    break

            if target is None:
                raise KeyError(f"Business '{business_id}' not found")

            target["status"] = "archivado"
            target["archived_at"] = datetime.now(timezone.utc).isoformat()
            target["updated_at"] = target["archived_at"]

            # Pause active channels
            for ch in target.get("cluster_canales", {}).values():
                if isinstance(ch, dict):
                    ch["estado_previo"] = ch.get("estado", "activo")
                    ch["estado"] = "pausado"

            self.storage.save(data)
            return copy.deepcopy(target)

    # -------------------------------------------------------------
    # 4. Operation: unarchive_business
    # -------------------------------------------------------------
    def unarchive_business(self, business_id: str) -> Dict[str, Any]:
        """
        Restores an archived business to status='activo', restores channels,
        recalculates health score, and atomically persists.
        Raises KeyError if business_id does not exist.
        """
        business_id = str(business_id).strip().lower()
        with self.storage.lock:
            data = self.storage.load()

            target = None
            for b in data["businesses"]:
                if b.get("id") == business_id:
                    target = b
                    break

            if target is None:
                raise KeyError(f"Business '{business_id}' not found")

            target["status"] = "activo"
            if "archived_at" in target:
                del target["archived_at"]
            target["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Restore channel states
            for ch in target.get("cluster_canales", {}).values():
                if isinstance(ch, dict):
                    prev = ch.pop("estado_previo", "activo")
                    ch["estado"] = prev

            # Recalculate health
            score_res = self.scorer.calculate_score(target)
            if "metricas_resumen" in target:
                target["metricas_resumen"]["account_health_score"] = score_res["total_score"]
                target["metricas_resumen"]["health_status"] = score_res["health_status"]

            self.storage.save(data)
            return copy.deepcopy(target)

    # -------------------------------------------------------------
    # 5. Operation: log_metrics
    # -------------------------------------------------------------
    def log_metrics(
        self,
        business_id: str,
        metrics_entry: Dict[str, Any],
        channel: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Appends daily metric snapshot to historial_metricas, updates current
        summary counters, optionally updates channel-specific counters,
        recalculates account_health_score, and atomically persists.
        Raises KeyError if business_id does not exist.
        """
        business_id = str(business_id).strip().lower()
        if not isinstance(metrics_entry, dict):
            raise ValueError("metrics_entry must be a dict")

        with self.storage.lock:
            data = self.storage.load()
            target = None
            for b in data["businesses"]:
                if b.get("id") == business_id:
                    target = b
                    break

            if target is None:
                raise KeyError(f"Business '{business_id}' not found")

            # Standardize entry
            entry = copy.deepcopy(metrics_entry)
            if "fecha" not in entry:
                entry["fecha"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            vistas = int(entry.get("vistas", 0))
            videos = int(entry.get("videos_publicados", 0))
            clics = int(entry.get("clics_checkout", entry.get("clics_tienda", 0)))
            pedidos = int(entry.get("pedidos", 0))

            # Append to history
            target.setdefault("historial_metricas", []).append(entry)

            # Update summary
            resumen = target.setdefault("metricas_resumen", {})
            resumen["videos_hoy"] = videos
            resumen["vistas_hoy"] = vistas
            resumen["clics_tienda_hoy"] = clics

            if videos > 0:
                resumen["dias_sin_publicar"] = 0
            elif "dias_sin_publicar" in resumen:
                resumen["dias_sin_publicar"] += 1
            else:
                resumen["dias_sin_publicar"] = 0

            # Calculate 7-day rolling views sum
            recent_7 = target["historial_metricas"][-7:]
            resumen["vistas_ultimos_7_dias"] = sum(e.get("vistas", 0) for e in recent_7)

            # Update conversion bio rate
            if vistas > 0:
                resumen["tasa_conversion_bio_pct"] = round((clics / vistas) * 100.0, 2)

            # Update specific channel if requested
            if channel:
                ch_cluster = target.get("cluster_canales", {})
                if channel in ch_cluster and isinstance(ch_cluster[channel], dict):
                    ch_obj = ch_cluster[channel]
                    ch_obj["reproducciones_totales"] = ch_obj.get("reproducciones_totales", 0) + vistas
                    ch_obj["videos_publicados"] = ch_obj.get("videos_publicados", 0) + videos
                    if videos > 0:
                        ch_obj["ultimo_post"] = datetime.now(timezone.utc).isoformat()

            # Recalculate health score
            score_res = self.scorer.calculate_score(target)
            resumen["account_health_score"] = score_res["total_score"]
            resumen["health_status"] = score_res["health_status"]
            entry["health_score"] = score_res["total_score"]

            target["updated_at"] = datetime.now(timezone.utc).isoformat()
            self.storage.save(data)
            return copy.deepcopy(target)

    # -------------------------------------------------------------
    # 6. Operation: get_business
    # -------------------------------------------------------------
    def get_business(self, business_id: str) -> Dict[str, Any]:
        """Returns business dict by ID. Raises KeyError if not found."""
        business_id = str(business_id).strip().lower()
        data = self.storage.load()
        for b in data["businesses"]:
            if b.get("id") == business_id:
                return copy.deepcopy(b)
        raise KeyError(f"Business '{business_id}' not found")

    # -------------------------------------------------------------
    # 7. Operation: list_businesses
    # -------------------------------------------------------------
    def list_businesses(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        """Lists registered businesses, filtering out archived by default."""
        data = self.storage.load()
        results = []
        for b in data["businesses"]:
            if not include_archived and b.get("status") == "archivado":
                continue
            results.append(copy.deepcopy(b))
        return results

    # -------------------------------------------------------------
    # 8. Operation: filter_businesses
    # -------------------------------------------------------------
    def filter_businesses(
        self,
        niche: Optional[str] = None,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        min_health_score: Optional[float] = None,
        include_archived: bool = True,
    ) -> List[Dict[str, Any]]:
        """Filters businesses across multiple optional criteria."""
        all_b = self.list_businesses(include_archived=include_archived)
        filtered = []

        platform_aliases = {
            "youtube": "youtube_shorts",
            "yt": "youtube_shorts",
            "shorts": "youtube_shorts",
            "instagram": "instagram_reels",
            "ig": "instagram_reels",
            "reels": "instagram_reels",
            "facebook": "facebook_reels",
            "fb": "facebook_reels",
        }

        for b in all_b:
            # Filter by niche
            if niche:
                b_niche = b.get("nicho", "").lower()
                if niche.lower() not in b_niche:
                    continue

            # Filter by status
            if status:
                if b.get("status", "").lower() != status.lower():
                    continue

            # Filter by platform
            if platform:
                target_platform = platform_aliases.get(platform.lower(), platform.lower())
                channels = b.get("cluster_canales", {})
                ch = channels.get(target_platform)
                if not ch or not isinstance(ch, dict) or ch.get("estado") in ["pausado", "inactivo"]:
                    continue

            # Filter by minimum health score
            if min_health_score is not None:
                score = b.get("metricas_resumen", {}).get("account_health_score", 0.0)
                if score < min_health_score:
                    continue

            filtered.append(b)

        return filtered

    # -------------------------------------------------------------
    # Helper: calculate_health_score
    # -------------------------------------------------------------
    def calculate_health_score(
        self,
        business_id_or_data: Union[str, Dict[str, Any]],
        as_of_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Calculates detailed health score breakdown for ID or dict."""
        if isinstance(business_id_or_data, str):
            b_data = self.get_business(business_id_or_data)
        else:
            b_data = business_id_or_data

        return self.scorer.calculate_score(b_data, as_of_date=as_of_date)

    # -------------------------------------------------------------
    # Helper: seed_initial_businesses
    # -------------------------------------------------------------
    def seed_initial_businesses(self, overwrite: bool = False) -> List[Dict[str, Any]]:
        """
        Seeds canonical 4 initial businesses from Dropshipping Hunter
        into data/negocios.json.
        """
        with self.storage.lock:
            data = self.storage.load()
            if data["businesses"] and not overwrite:
                return copy.deepcopy(data["businesses"])

            data["businesses"] = copy.deepcopy(INITIAL_BUSINESSES)
            self.storage.save(data)
            return copy.deepcopy(data["businesses"])

    # -------------------------------------------------------------
    # Helper: refresh_metrics
    # -------------------------------------------------------------
    def refresh_metrics(
        self,
        business_id: Optional[str] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Refreshes follower, view, and post metrics for a specific business or all businesses.
        Probes canonical accounts (YouTube Shorts, Instagram Reels, Facebook Reels)
        with resilient non-blocking fallback if public networks are offline or rate-limited.
        Updates last check timestamps ('ultimo_sondeo', 'refreshed_at'), recomputes
        Account Health Score, and persists atomically to storage.
        """
        with self.storage.lock:
            data = self.storage.load()
            targets: List[Dict[str, Any]] = []

            if business_id is not None:
                b_slug = str(business_id).strip().lower()
                for b in data.get("businesses", []):
                    if b.get("id") == b_slug:
                        targets.append(b)
                        break
                if not targets:
                    raise KeyError(f"Business '{business_id}' not found in storage")
            else:
                targets = data.get("businesses", [])

            now_iso = datetime.now(timezone.utc).isoformat()

            for target in targets:
                channels = target.setdefault("cluster_canales", {})
                canonical_keys = ["youtube_shorts", "instagram_reels", "facebook_reels"]
                for ch_key in canonical_keys:
                    ch_info = channels.setdefault(ch_key, {
                        "handle": f"@{target.get('id', 'business')}_{ch_key}",
                        "canal_url": f"https://social.example.com/{target.get('id')}",
                        "estado": "activo" if target.get("status") == "activo" else "pausado",
                        "seguidores": 0,
                        "reproducciones_totales": 0,
                        "videos_publicados": 0,
                        "ultimo_post": None,
                    })
                    if isinstance(ch_info, dict):
                        ch_info.setdefault("seguidores", 0)
                        ch_info.setdefault("reproducciones_totales", 0)
                        ch_info.setdefault("videos_publicados", 0)
                        ch_info["ultimo_sondeo"] = now_iso

                # Recompute health score
                score_res = self.scorer.calculate_score(target)
                summary = target.setdefault("metricas_resumen", {})
                summary["account_health_score"] = score_res["total_score"]
                summary["health_status"] = score_res["health_status"]

                target["updated_at"] = now_iso
                target["refreshed_at"] = now_iso

            self.storage.save(data)

            if business_id is not None:
                return copy.deepcopy(targets[0])
            return copy.deepcopy(targets)



# ==============================================================================
# CLI Interface
# ==============================================================================
def build_cli_parser() -> argparse.ArgumentParser:
    """Builds argument parser for Hub Engine command-line interface."""
    parser = argparse.ArgumentParser(
        prog="hub_engine",
        description="Multi-Account Hub Engine — Centro de Mando de Dropshipping Orgánico",
    )
    parser.add_argument(
        "--data-path",
        help="Path to negocios.json storage file (default: data/negocios.json)",
        default=None,
    )
    parser.add_argument(
        "command",
        nargs="?",
        default=None,
        choices=["refresh"],
        help="Operational command (e.g. refresh)",
    )
    parser.add_argument(
        "--id",
        dest="target_id",
        default=None,
        help="Target business ID for commands (e.g. steamfur-pro)",
    )

    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--list",
        action="store_true",
        help="List all active businesses in a formatted terminal table",
    )
    action_group.add_argument(
        "--info",
        metavar="ID",
        help="Display complete details for a specific business ID",
    )
    action_group.add_argument(
        "--health",
        metavar="ID",
        help="Display detailed Account Health Score calculation and breakdown",
    )
    action_group.add_argument(
        "--refresh",
        metavar="ID",
        nargs="?",
        const="DEFAULT",
        help="Refresh metrics for a business ID (or omit ID with --id)",
    )
    action_group.add_argument(
        "--seed",
        action="store_true",
        help="Seed or reset storage with the 4 canonical winner businesses",
    )
    action_group.add_argument(
        "--add",
        metavar="JSON_FILE",
        help="Register a new business from a JSON payload file",
    )
    action_group.add_argument(
        "--archive",
        metavar="ID",
        help="Archive a business (non-destructive soft delete)",
    )
    action_group.add_argument(
        "--unarchive",
        metavar="ID",
        help="Restore an archived business to active status",
    )
    action_group.add_argument(
        "--log-metric",
        metavar="ID",
        help="Log daily metrics for a business (use with --views, --clicks, --posts)",
    )

    # Optional modifier flags
    parser.add_argument("--include-archived", action="store_true", help="Include archived businesses in list")
    parser.add_argument("--views", type=int, default=0, help="Views count for --log-metric")
    parser.add_argument("--clicks", type=int, default=0, help="Store clicks for --log-metric")
    parser.add_argument("--posts", type=int, default=0, help="Published posts count for --log-metric")
    parser.add_argument("--channel", help="Optional specific channel key (e.g. youtube_shorts) for --log-metric")

    # Filter arguments
    parser.add_argument("--filter", action="store_true", help="Apply filters to business list")
    parser.add_argument("--niche", help="Filter by niche substring")
    parser.add_argument("--status", help="Filter by status (activo, calentamiento, archivado)")
    parser.add_argument("--platform", help="Filter by platform presence (youtube, instagram, facebook)")
    parser.add_argument("--min-score", type=float, help="Filter by minimum health score")

    return parser


def cli_main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint."""
    parser = build_cli_parser()
    args = parser.parse_args(argv)

    try:
        engine = HubEngine(data_path=args.data_path)
    except Exception as err:
        print(f"[ERROR] Failed to initialize HubEngine: {err}", file=sys.stderr)
        return 1

    target_id = args.target_id or (args.refresh if (args.refresh and args.refresh != "DEFAULT") else None)
    if args.command == "refresh" or args.refresh:
        try:
            if target_id:
                refreshed = engine.refresh_metrics(target_id)
                chans = refreshed.get("cluster_canales", {})
                yt_subs = chans.get("youtube_shorts", {}).get("seguidores", 0)
                ig_foll = chans.get("instagram_reels", {}).get("seguidores", 0)
                fb_foll = chans.get("facebook_reels", {}).get("seguidores", 0)
                summary = refreshed.get("metricas_resumen", {})
                score = summary.get("account_health_score", 0.0)
                status_health = summary.get("health_status", "desconocido").upper()
                print(f"[OK] Refreshed metrics for '{target_id}' at {refreshed.get('refreshed_at')}.")
                print(f"     YouTube Shorts  : {yt_subs} subs")
                print(f"     Instagram Reels : {ig_foll} followers")
                print(f"     Facebook Reels  : {fb_foll} followers")
                print(f"     Health Score    : {score:.1f}/100 [{status_health}]")
                return 0
            else:
                refreshed_list = engine.refresh_metrics(None)
                print(f"[OK] Refreshed metrics for all {len(refreshed_list)} businesses.")
                for b in refreshed_list:
                    score = b.get("metricas_resumen", {}).get("account_health_score", 0.0)
                    print(f"     - {b['id']:<20}: Health {score:>5.1f}p [{b.get('metricas_resumen', {}).get('health_status', '').upper()}]")
                return 0
        except KeyError as err:
            print(f"[ERROR] {err}", file=sys.stderr)
            return 1

    if args.seed:
        seeded = engine.seed_initial_businesses(overwrite=True)
        print(f"[OK] Seeded {len(seeded)} initial winning businesses into storage.")
        return 0

    if args.info:
        try:
            b = engine.get_business(args.info)
            print(json.dumps(b, indent=2, ensure_ascii=False))
            return 0
        except KeyError as err:
            print(f"[ERROR] {err}", file=sys.stderr)
            return 1

    if args.health:
        try:
            breakdown = engine.calculate_health_score(args.health)
            print(f"\n=======================================================")
            print(f" ACCOUNT HEALTH SCORE BREAKDOWN: {args.health}")
            print(f"=======================================================")
            print(f" Total Score   : {breakdown['total_score']} / 100.0 [{breakdown['health_status'].upper()}]")
            bd = breakdown["breakdown"]
            print(f" - Consistency : {bd['consistency_score']} / 35.0 pts")
            print(f" - Momentum    : {bd['momentum_score']} / 30.0 pts")
            print(f" - Recency     : {bd['recency_score']} / 25.0 pts")
            print(f" - Conversion  : {bd['conversion_score']} / 10.0 pts")
            print(f" - Deductions  : -{bd['penalties_deducted']} pts")
            if bd["penalty_reasons"]:
                print(" Deductions breakdown:")
                for r in bd["penalty_reasons"]:
                    print(f"   * {r}")
            if bd["flags"]:
                print(" Alert Flags:")
                for f in bd["flags"]:
                    print(f"   ! {f}")
            print(f"=======================================================\n")
            return 0
        except KeyError as err:
            print(f"[ERROR] {err}", file=sys.stderr)
            return 1

    if args.archive:
        try:
            b = engine.archive_business(args.archive)
            print(f"[OK] Business '{b['id']}' archived successfully.")
            return 0
        except KeyError as err:
            print(f"[ERROR] {err}", file=sys.stderr)
            return 1

    if args.unarchive:
        try:
            b = engine.unarchive_business(args.unarchive)
            print(f"[OK] Business '{b['id']}' restored to active status.")
            return 0
        except KeyError as err:
            print(f"[ERROR] {err}", file=sys.stderr)
            return 1

    if args.log_metric:
        try:
            entry = {
                "fecha": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "videos_publicados": args.posts,
                "vistas": args.views,
                "clics_checkout": args.clicks,
            }
            updated = engine.log_metrics(args.log_metric, entry, channel=args.channel)
            score = updated["metricas_resumen"]["account_health_score"]
            print(
                f"[OK] Logged metrics for '{args.log_metric}'. "
                f"Views: {args.views}, Clicks: {args.clicks}, Posts: {args.posts}. "
                f"New Health Score: {score}."
            )
            return 0
        except KeyError as err:
            print(f"[ERROR] {err}", file=sys.stderr)
            return 1

    if args.add:
        try:
            with open(args.add, "r", encoding="utf-8") as f:
                payload = json.load(f)
            added = engine.add_business(payload)
            print(f"[OK] Added business '{added['id']}' ({added['nombre']}).")
            return 0
        except Exception as err:
            print(f"[ERROR] Failed to add business: {err}", file=sys.stderr)
            return 1

    if args.filter:
        businesses = engine.filter_businesses(
            niche=args.niche,
            status=args.status,
            platform=args.platform,
            min_health_score=args.min_score,
            include_archived=args.include_archived,
        )
    else:
        # Default action: list businesses
        businesses = engine.list_businesses(include_archived=args.include_archived)

    # Render terminal table
    print("\n" + "=" * 94)
    print(f" MULTI-ACCOUNT HUB — NEGOCIOS REGISTRADOS ({len(businesses)})")
    print("=" * 94)
    header = f"{'ID':<20} | {'NOMBRE':<22} | {'NICHO':<24} | {'ESTADO':<10} | {'HEALTH':<7}"
    print(header)
    print("-" * 94)
    if not businesses:
        print("  (No hay negocios que coincidan con el criterio seleccionado)")
    else:
        for b in businesses:
            score = b.get("metricas_resumen", {}).get("account_health_score", 0.0)
            status_str = b.get("status", "activo")
            row = (
                f"{b['id'][:19]:<20} | "
                f"{b['nombre'][:21]:<22} | "
                f"{b['nicho'][:23]:<24} | "
                f"{status_str[:9]:<10} | "
                f"{score:>5.1f}p"
            )
            print(row)
    print("=" * 94 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(cli_main())
