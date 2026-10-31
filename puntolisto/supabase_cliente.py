"""Creación del cliente de Supabase.

IMPORTANTE: se crea un cliente NUEVO en cada petición. Nunca uno global,
porque en el servidor conviven peticiones de distintos comerciantes y
el token de uno podría usarse para otro.
"""
from flask import current_app
from supabase import Client, ClientOptions, create_client


def nuevo_cliente() -> Client:
    """Cliente sin usuario: solo para registrarse, entrar o renovar el token."""
    return create_client(
        current_app.config["SUPABASE_URL"],
        current_app.config["SUPABASE_KEY"],
        options=ClientOptions(persist_session=False, auto_refresh_token=False),
    )


def cliente_con_token(access_token: str) -> Client:
    """Cliente que actúa como el comerciante: Supabase aplica RLS con su token."""
    cliente = nuevo_cliente()
    cliente.postgrest.auth(access_token)
    return cliente
