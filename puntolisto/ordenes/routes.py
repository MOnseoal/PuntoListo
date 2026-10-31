"""Blueprint de órdenes.

ACT-15 (función d): nueva orden con folio, cliente y servicios del catálogo.
ACT-17 (función g): cambio de estado Recibido → En proceso → Listo → Entregado.
ACT-18 (función h): botón que abre WhatsApp con el aviso de "lista".
Mejoras: lista con buscador (folio, nombre o teléfono) y filtros, y
acciones rápidas desde las tarjetas que regresan a la página de origen.
"""
from datetime import date

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from postgrest.exceptions import APIError

from .. import avisos
from .. import validaciones as v
from ..etiquetas import ESTADOS, hoy_mexico
from ..modelos import clientes, ordenes, servicios
from ..seguridad import login_requerido, negocio_requerido
from . import presentacion

bp = Blueprint("ordenes", __name__, url_prefix="/ordenes")

# Filtros de la lista: clave -> (texto del chip, estados que incluye)
FILTROS = {
    "activas": ("Pendientes", ordenes.ESTADOS_ACTIVOS),
    "atencion": ("Urgentes", ("recibido", "en_proceso")),
    "recibido": ("Recibidas", ("recibido",)),
    "en_proceso": ("En proceso", ("en_proceso",)),
    "listo": ("Listas", ("listo",)),
    "entregado": ("Entregadas", ("entregado",)),
}


def _ruta_segura(destino: str | None, por_defecto: str) -> str:
    """Solo permite regresar a páginas de esta misma app (evita redirecciones a otros sitios)."""
    destino = (destino or "").rstrip("?")
    if destino.startswith("/") and not destino.startswith("//") and "\\" not in destino:
        return destino
    return por_defecto


def _leer_formulario(formulario, catalogo: list[dict], lista_clientes: list[dict]):
    """Valida la orden. Devuelve (datos para la BD, valores para re-mostrar, error)."""
    valores = {
        "cliente_id": formulario.get("cliente_id", ""),
        "fecha_entrega": formulario.get("fecha_entrega", ""),
        "notas": formulario.get("notas", "").strip(),
        "cantidades": {str(s["id"]): formulario.get(f"cantidad_{s['id']}", "").strip()
                       for s in catalogo},
    }

    ids_clientes = {str(c["id"]) for c in lista_clientes}
    if valores["cliente_id"] not in ids_clientes:
        return None, valores, "Elige el cliente de la orden."

    elegidos = []
    for servicio in catalogo:
        texto = valores["cantidades"][str(servicio["id"])]
        if not texto:
            continue
        cantidad = v.leer_numero(texto)
        if not v.cantidad_valida(cantidad, servicio["tipo_cobro"]):
            regla = ("un número mayor que 0 (ej. 3.5)" if servicio["tipo_cobro"] == "kilo"
                     else "un número entero mayor que 0")
            return None, valores, f"La cantidad de «{servicio['nombre']}» debe ser {regla}."
        elegidos.append({"servicio_id": servicio["id"], "cantidad": cantidad})

    if not elegidos:
        return None, valores, "Escribe la cantidad de al menos un servicio."

    fecha = None
    if valores["fecha_entrega"]:
        try:
            fecha = date.fromisoformat(valores["fecha_entrega"]).isoformat()
        except ValueError:
            return None, valores, "La fecha de entrega no es válida."

    if len(valores["notas"]) > 500:
        return None, valores, "Las notas pueden tener máximo 500 caracteres."

    datos = {"cliente_id": int(valores["cliente_id"]), "servicios": elegidos,
             "fecha_entrega": fecha, "notas": valores["notas"] or None}
    return datos, valores, None


@bp.route("/")
@login_requerido
@negocio_requerido
def lista():
    filtro = request.args.get("estado", "activas")
    if filtro not in FILTROS:
        filtro = "activas"
    busqueda = request.args.get("q", "").strip()[:60]
    cid = g.comercio["id"]

    # Buscar clientes por nombre o teléfono para incluir sus órdenes
    cliente_ids = [c["id"] for c in clientes.listar(g.sb, cid, busqueda, limite=50)] if busqueda else None

    estados = FILTROS[filtro][1]
    orden_por = "actualizado_en" if filtro == "entregado" else "creado_en"
    resultado = ordenes.listar(g.sb, cid, estados, busqueda, cliente_ids, orden_por=orden_por,
                               limite=50 if filtro == "entregado" else 200)
    resultado = presentacion.preparar(resultado, g.comercio["nombre"])
    if filtro == "atencion":
        resultado = sorted([o for o in resultado if o["alerta"] in ("atrasada", "hoy")],
                           key=lambda o: o["fecha_entrega"])  # la más atrasada primero

    return render_template("ordenes/lista.html", ordenes=resultado, filtro=filtro,
                           filtros=FILTROS, busqueda=busqueda)


@bp.route("/nueva", methods=["GET", "POST"])
@login_requerido
@negocio_requerido
def nueva():
    cid = g.comercio["id"]
    catalogo = servicios.listar(g.sb, cid, solo_activos=True)
    lista_clientes = clientes.listar(g.sb, cid, limite=1000)

    valores = {"cliente_id": request.args.get("cliente_id", ""), "fecha_entrega": "",
               "notas": "", "cantidades": {}}

    if request.method == "POST":
        datos, valores, error = _leer_formulario(request.form, catalogo, lista_clientes)
        if error:
            flash(error, "error")
        else:
            try:
                orden = ordenes.crear(g.sb, **datos)
            except APIError:
                flash("No se pudo registrar la orden. Revisa los datos e intenta de nuevo.", "error")
            else:
                flash(f"Orden {orden['folio']} registrada.", "exito")
                return redirect(url_for("ordenes.detalle", orden_id=orden["id"]))

    return render_template("ordenes/nueva.html", catalogo=catalogo, clientes=lista_clientes,
                           valores=valores)


@bp.route("/<int:orden_id>")
@login_requerido
@negocio_requerido
def detalle(orden_id: int):
    orden = ordenes.obtener_detalle(g.sb, g.comercio["id"], orden_id)
    if orden is None:
        abort(404)
    alerta = presentacion.calcular_alerta(orden, hoy_mexico())
    enlace_wa = None
    if orden["estado"] == "listo":
        enlace_wa = avisos.enlace_orden_lista(orden, g.comercio["nombre"])
    return render_template(
        "ordenes/detalle.html", orden=orden, enlace_wa=enlace_wa, alerta=alerta,
        siguiente=ordenes.siguiente_estado(orden["estado"]),
        anterior=ordenes.estado_anterior(orden["estado"]),
    )


@bp.route("/<int:orden_id>/estado", methods=["POST"])
@login_requerido
@negocio_requerido
def cambiar_estado(orden_id: int):
    nuevo = request.form.get("estado", "")
    if nuevo not in ESTADOS:
        abort(400)
    orden = ordenes.cambiar_estado(g.sb, g.comercio["id"], orden_id, nuevo)
    if orden is None:
        abort(404)
    if nuevo == "listo":
        flash(f"{orden['folio']} está lista. Ahora avisa al cliente por WhatsApp.", "exito")
    else:
        flash(f"{orden['folio']} cambió a «{ESTADOS[nuevo]}».", "exito")
    destino = _ruta_segura(request.form.get("volver"), url_for("ordenes.detalle", orden_id=orden_id))
    return redirect(destino)


@bp.route("/entregadas")
def entregadas():
    return redirect(url_for("ordenes.lista", estado="entregado"))
