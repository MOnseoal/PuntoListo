"""Blueprint del panel principal (función c).

Muestra lo importante primero: órdenes atrasadas o que vencen hoy, luego
las listas para avisar, las que están en proceso y las recién recibidas.
"""
from flask import Blueprint, current_app, g, render_template

from .. import planes
from ..modelos import ordenes
from ..ordenes import presentacion
from ..seguridad import login_requerido, negocio_requerido

bp = Blueprint("panel", __name__)


@bp.route("/")
@login_requerido
@negocio_requerido
def inicio():
    cid = g.comercio["id"]
    activas = presentacion.preparar(ordenes.listar_activas(g.sb, cid),
                                    g.comercio["nombre"], giro=g.comercio.get("giro"))
    entregadas = ordenes.listar_entregadas(g.sb, cid, limite=200)
    conteo = presentacion.contar_por_estado(activas)
    medidor_ordenes = planes.construir_medidor(
        "ordenes_mes", ordenes.contar_mes_actual(g.sb, cid)
    )
    return render_template(
        "panel/inicio.html",
        comercio=g.comercio,
        secciones=presentacion.secciones_panel(activas),
        conteo=conteo,
        flujo=presentacion.porcentajes_flujo(conteo),
        urgentes=sum(1 for o in activas if o["alerta"] in ("atrasada", "hoy")),
        semana=presentacion.semana_entregas(entregadas),
        total=len(activas),
        medidor_ordenes=medidor_ordenes,
    )


@bp.route("/salud")
def salud():
    """Revisión rápida de que la configuración llegó a Vercel (no muestra las claves)."""
    return {
        "app": "PuntoListo",
        "supabase_url_configurada": bool(current_app.config["SUPABASE_URL"]),
        "supabase_key_configurada": bool(current_app.config["SUPABASE_KEY"]),
    }
