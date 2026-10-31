"""Seguridad compartida por todos los módulos.

- Protección CSRF: cada formulario POST lleva un token secreto que se
  compara con el guardado en la sesión. Así otro sitio no puede enviar
  formularios en nombre del comerciante.
- Decoradores @login_requerido y @negocio_requerido para las rutas.
"""
import secrets
from functools import wraps

from flask import flash, g, redirect, request, session, url_for

from .auth import sesion
from .modelos import comercios


# ---------------------------------------------------------------- CSRF
def _obtener_csrf() -> str:
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def registrar_csrf(app) -> None:
    app.jinja_env.globals["csrf_token"] = _obtener_csrf

    @app.before_request
    def verificar_csrf():
        if request.method != "POST":
            return None
        esperado = session.get("csrf_token")
        recibido = request.form.get("csrf_token", "")
        if not esperado or not secrets.compare_digest(esperado, recibido):
            flash("La página caducó. Intenta de nuevo.", "error")
            return redirect(request.url)
        return None


# ---------------------------------------------------------- Decoradores
def login_requerido(vista):
    """Exige sesión iniciada. Deja listos g.sb (cliente con el token) y g.usuario_id."""

    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not sesion.hay_sesion():
            flash("Inicia sesión para continuar.", "info")
            return redirect(url_for("auth.entrar"))

        if not sesion.renovar_si_expira():
            sesion.cerrar()
            flash("Tu sesión expiró. Vuelve a entrar.", "info")
            return redirect(url_for("auth.entrar"))

        g.sb = sesion.cliente_actual()
        g.usuario_id = session["usuario_id"]
        return vista(*args, **kwargs)

    return envoltura


def negocio_requerido(vista):
    """Exige que el comerciante ya haya configurado su negocio. Deja listo g.comercio.

    Debe ir DEBAJO de @login_requerido.
    """

    @wraps(vista)
    def envoltura(*args, **kwargs):
        g.comercio = comercios.obtener_mi_comercio(g.sb, g.usuario_id)
        if g.comercio is None:
            return redirect(url_for("negocio.configurar"))
        return vista(*args, **kwargs)

    return envoltura
