"""Blueprint de planes de suscripción (simulación informativa, ACT-24).

No realiza cobros ni lee o escribe el plan en Supabase. Todas las cifras y
textos provienen de `puntolisto/planes.py`.
"""
from flask import Blueprint, abort, redirect, render_template, request, url_for

from .. import planes as cfg_planes
from ..seguridad import login_requerido, negocio_requerido

bp = Blueprint("planes", __name__, url_prefix="/planes")

PLANES_SOLICITABLES = ("fuerte", "cumbre")


@bp.route("", strict_slashes=False)
@login_requerido
@negocio_requerido
def inicio():
    return render_template(
        "planes/inicio.html",
        planes=cfg_planes.PLANES,
        plan_actual=cfg_planes.PLAN_ACTUAL,
        matriz=cfg_planes.MATRIZ_FUNCIONES,
        descuento_pct=round(cfg_planes.DESCUENTO_PRIMER_MES * 100),
    )


@bp.route("/solicitar", methods=["GET", "POST"])
@login_requerido
@negocio_requerido
def solicitar():
    if request.method == "GET":
        return redirect(url_for("planes.inicio"))
    plan = request.form.get("plan", "").strip()
    if plan not in PLANES_SOLICITABLES:
        abort(400)
    return redirect(url_for("planes.gracias", plan=plan))


@bp.route("/gracias/<plan>")
@login_requerido
@negocio_requerido
def gracias(plan: str):
    if plan not in PLANES_SOLICITABLES:
        abort(404)
    return render_template(
        "planes/gracias.html",
        plan=cfg_planes.PLANES_POR_CLAVE[plan],
    )


@bp.route("/vista-previa/<modulo>")
@login_requerido
@negocio_requerido
def vista_previa(modulo: str):
    clave_plan = cfg_planes.MODULOS_VISTA_PREVIA.get(modulo)
    if clave_plan is None:
        abort(404)
    return render_template(
        "planes/vista_previa.html",
        modulo=modulo,
        detalle=cfg_planes.DETALLES_VISTA_PREVIA[modulo],
        plan_requerido=cfg_planes.PLANES_POR_CLAVE[clave_plan],
        limites=cfg_planes.LIMITES,
    )
