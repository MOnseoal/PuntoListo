"""Manejo de la sesión del comerciante.

Supabase entrega dos tokens al iniciar sesión:
- access_token: dura 1 hora y se manda en cada consulta (RLS lo usa).
- refresh_token: sirve para pedir un access_token nuevo cuando el anterior vence.

Ambos se guardan en la cookie de sesión de Flask, firmada con SECRET_KEY.
Así el servidor no guarda nada entre peticiones (necesario en Vercel).
"""
import time

import httpx
from flask import session
from supabase import AuthError

from ..supabase_cliente import cliente_con_token, nuevo_cliente

CLAVES_SESION = ("access_token", "refresh_token", "expires_at", "usuario_id", "email")
MARGEN_SEGUNDOS = 60  # renovar un minuto antes de que venza


def guardar(sesion_supabase) -> None:
    session.permanent = True
    session["access_token"] = sesion_supabase.access_token
    session["refresh_token"] = sesion_supabase.refresh_token
    session["expires_at"] = int(sesion_supabase.expires_at or time.time() + 3600)
    session["usuario_id"] = sesion_supabase.user.id
    session["email"] = sesion_supabase.user.email


def cerrar() -> None:
    for clave in CLAVES_SESION:
        session.pop(clave, None)


def hay_sesion() -> bool:
    return "access_token" in session and "refresh_token" in session


def renovar_si_expira() -> bool:
    """Renueva el access_token si está por vencer. Devuelve False si no se pudo."""
    if session.get("expires_at", 0) - time.time() > MARGEN_SEGUNDOS:
        return True
    try:
        respuesta = nuevo_cliente().auth.refresh_session(session["refresh_token"])
    except (AuthError, httpx.HTTPError):
        return False
    if not respuesta.session:
        return False
    guardar(respuesta.session)
    return True


def cliente_actual():
    return cliente_con_token(session["access_token"])
