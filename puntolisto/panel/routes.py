"""Blueprint del panel principal (función c): órdenes agrupadas por estado."""
from flask import Blueprint, current_app, g, render_template

from ..modelos import ordenes
from ..seguridad import login_requerido, negocio_requerido

bp = Blueprint("panel", __name__)


@bp.route("/")
@login_requerido
@negocio_requerido
def inicio():
    activas = ordenes.listar_activas(g.sb, g.comercio["id"])
    grupos = ordenes.agrupar_por_estado(activas)
    return render_template("panel/inicio.html", comercio=g.comercio, grupos=grupos,
                           total=len(activas))


@bp.route("/salud")
def salud():
    """Revisión rápida de que la configuración llegó a Vercel (no muestra las claves)."""
    return {
        "app": "PuntoListo",
        "supabase_url_configurada": bool(current_app.config["SUPABASE_URL"]),
        "supabase_key_configurada": bool(current_app.config["SUPABASE_KEY"]),
    }
