"""Configuración leída de variables de entorno.

En tu computadora vienen del archivo .env (que NUNCA se sube a GitHub).
En Vercel se capturan en Settings > Environment Variables.
"""
import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

CLAVE_DESARROLLO = "solo-para-desarrollo"
EN_VERCEL = bool(os.environ.get("VERCEL"))  # Vercel define esta variable automáticamente


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", CLAVE_DESARROLLO)
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

    # Cookie de sesión (guarda los tokens de Supabase, firmada con SECRET_KEY)
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    SESSION_COOKIE_HTTPONLY = True        # JavaScript no puede leerla
    SESSION_COOKIE_SAMESITE = "Lax"       # protege contra envíos desde otros sitios
    SESSION_COOKIE_SECURE = EN_VERCEL     # solo por HTTPS en producción
