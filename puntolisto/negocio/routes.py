"""Blueprint del negocio (función b).

ACT-12: pantalla "Configura tu negocio" (nombre, abreviatura, giro).
ACT-14: catálogo de servicios (agregar, editar, activar/desactivar).
"""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from postgrest.exceptions import APIError

from .. import validaciones as v
from ..etiquetas import GIROS, TIPOS_COBRO
from ..modelos import comercios, servicios
from ..seguridad import login_requerido, negocio_requerido

bp = Blueprint("negocio", __name__, url_prefix="/negocio")


@bp.route("/configurar", methods=["GET", "POST"])
@login_requerido
def configurar():
    if comercios.obtener_mi_comercio(g.sb, g.usuario_id):
        return redirect(url_for("panel.inicio"))

    datos = {
        "nombre": request.form.get("nombre", "").strip(),
        "abreviatura": request.form.get("abreviatura", "").strip(),
        "giro": request.form.get("giro", ""),
        "telefono": request.form.get("telefono", "").strip(),
    }

    if request.method == "POST":
        abreviatura = v.normalizar_abreviatura(
            datos["abreviatura"] or v.sugerir_abreviatura(datos["nombre"])
        )
        telefono = v.normalizar_telefono(datos["telefono"]) if datos["telefono"] else None

        if not v.nombre_valido(datos["nombre"]):
            flash("El nombre del negocio debe tener entre 2 y 80 caracteres.", "error")
        elif abreviatura is None:
            flash("La abreviatura debe tener de 1 a 5 letras o números, sin espacios.", "error")
        elif datos["giro"] not in GIROS:
            flash("Elige el giro de tu negocio.", "error")
        elif datos["telefono"] and telefono is None:
            flash("El teléfono debe tener 10 dígitos.", "error")
        else:
            try:
                cargados = comercios.crear(
                    g.sb, g.usuario_id, datos["nombre"], abreviatura, datos["giro"], telefono
                )
            except APIError as error:
                if error.code == "23505":  # ya tenía negocio (doble clic o dos pestañas)
                    return redirect(url_for("panel.inicio"))
                flash("No se pudo guardar tu negocio. Intenta de nuevo.", "error")
            else:
                flash(
                    f"¡Listo! Tus folios serán {abreviatura}-0001, {abreviatura}-0002… "
                    f"Cargamos {cargados} servicios de ejemplo que podrás editar.",
                    "exito",
                )
                return redirect(url_for("panel.inicio"))

    return render_template("negocio/configurar.html", datos=datos)


# ======================================================================
# ACT-14: catálogo de servicios configurable
# ======================================================================
MENSAJE_SERVICIO_DUPLICADO = "Ya tienes un servicio con ese nombre."


def _validar_servicio(formulario) -> tuple[dict, str | None]:
    nombre = " ".join(formulario.get("nombre", "").split())
    tipo = formulario.get("tipo_cobro", "")
    precio_texto = formulario.get("precio", "").strip()
    datos = {"nombre": nombre, "tipo_cobro": tipo, "precio": precio_texto}

    if not v.nombre_valido(nombre):
        return datos, "El nombre del servicio debe tener entre 2 y 80 caracteres."
    if tipo not in TIPOS_COBRO:
        return datos, "Elige cómo se cobra el servicio."
    precio = v.leer_numero(precio_texto) if precio_texto else 0.0
    if not v.precio_valido(precio):
        return datos, "Escribe un precio válido (ej. 45 o 45.50)."
    return {"nombre": nombre, "tipo_cobro": tipo, "precio": round(precio, 2)}, None


@bp.route("/catalogo")
@login_requerido
@negocio_requerido
def catalogo():
    lista = servicios.listar(g.sb, g.comercio["id"])
    return render_template("negocio/catalogo.html", servicios=lista)


@bp.route("/catalogo/nuevo", methods=["GET", "POST"])
@login_requerido
@negocio_requerido
def servicio_nuevo():
    datos = {"nombre": "", "tipo_cobro": "", "precio": ""}
    if request.method == "POST":
        datos, error = _validar_servicio(request.form)
        if error:
            flash(error, "error")
        else:
            try:
                servicios.crear(g.sb, g.comercio["id"], **datos)
            except APIError as e:
                flash(MENSAJE_SERVICIO_DUPLICADO if e.code == "23505"
                      else "No se pudo guardar. Intenta de nuevo.", "error")
            else:
                flash(f"Servicio {datos['nombre']} agregado.", "exito")
                return redirect(url_for("negocio.catalogo"))
    return render_template("negocio/servicio_form.html", datos=datos, editando=False)


@bp.route("/catalogo/<int:servicio_id>/editar", methods=["GET", "POST"])
@login_requerido
@negocio_requerido
def servicio_editar(servicio_id: int):
    servicio = servicios.obtener(g.sb, g.comercio["id"], servicio_id)
    if servicio is None:
        abort(404)
    datos = {"nombre": servicio["nombre"], "tipo_cobro": servicio["tipo_cobro"],
             "precio": f"{float(servicio['precio']):g}"}
    if request.method == "POST":
        datos, error = _validar_servicio(request.form)
        if error:
            flash(error, "error")
        else:
            try:
                servicios.actualizar(g.sb, g.comercio["id"], servicio_id, **datos)
            except APIError as e:
                flash(MENSAJE_SERVICIO_DUPLICADO if e.code == "23505"
                      else "No se pudo guardar. Intenta de nuevo.", "error")
            else:
                flash("Cambios guardados. Las órdenes anteriores conservan su precio.", "exito")
                return redirect(url_for("negocio.catalogo"))
    return render_template("negocio/servicio_form.html", datos=datos, editando=True,
                           servicio=servicio)


@bp.route("/catalogo/<int:servicio_id>/activo", methods=["POST"])
@login_requerido
@negocio_requerido
def servicio_activo(servicio_id: int):
    activar = request.form.get("activo") == "1"
    servicio = servicios.cambiar_activo(g.sb, g.comercio["id"], servicio_id, activar)
    if servicio is None:
        abort(404)
    if activar:
        flash(f"{servicio['nombre']} vuelve a aparecer en las órdenes nuevas.", "exito")
    else:
        flash(f"{servicio['nombre']} ya no aparecerá en las órdenes nuevas.", "info")
    return redirect(url_for("negocio.catalogo"))
