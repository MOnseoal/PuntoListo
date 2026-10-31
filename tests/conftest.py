"""Configuración de pruebas: app con claves falsas (no se conecta a Supabase)."""
import time
from types import SimpleNamespace

import pytest

from puntolisto import create_app


@pytest.fixture
def app():
    return create_app({
        "TESTING": True,
        "SECRET_KEY": "pruebas",
        "SUPABASE_URL": "https://falso.supabase.co",
        "SUPABASE_KEY": "sb_publishable_falsa",
    })


@pytest.fixture
def cliente(app):
    return app.test_client()


def obtener_csrf(cliente) -> str:
    """Abre una página para que se genere el token y lo devuelve."""
    cliente.get("/entrar")
    with cliente.session_transaction() as s:
        return s.get("csrf_token") or ""


def sesion_falsa(expira_en: int = 3600):
    usuario = SimpleNamespace(id="11111111-1111-1111-1111-111111111111", email="ana@correo.mx")
    return SimpleNamespace(access_token="token-acceso", refresh_token="token-refresco",
                           expires_at=int(time.time()) + expira_en, user=usuario)


def iniciar_sesion(cliente, expira_en: int = 3600) -> None:
    s_falsa = sesion_falsa(expira_en)
    with cliente.session_transaction() as s:
        s["access_token"] = s_falsa.access_token
        s["refresh_token"] = s_falsa.refresh_token
        s["expires_at"] = s_falsa.expires_at
        s["usuario_id"] = s_falsa.user.id
        s["email"] = s_falsa.user.email
        s["csrf_token"] = "csrf-pruebas"


@pytest.fixture(autouse=True)
def sin_entregadas_por_defecto(monkeypatch):
    """El panel también consulta las entregas de la semana; por defecto no hay
    ninguna (cada prueba puede reemplazarlo). Así ninguna prueba sale a internet."""
    monkeypatch.setattr("puntolisto.modelos.ordenes.listar_entregadas",
                        lambda sb, cid, limite=50: [])
