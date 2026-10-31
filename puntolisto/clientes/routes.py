"""Blueprint de clientes (ACT-13): alta, edición, consulta y búsqueda."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from postgrest.exceptions import APIError

from .. import validaciones as v
from ..etiquetas import telefono_legible
from ..modelos import clientes
from ..seguridad import login_requerido, negocio_requerido

bp = Blueprint("clientes", __name__, url_prefix="/clientes")

MENSAJE_DUPLICADO = "Ya tienes un cliente con ese teléfono."


def _validar(formulario) -> tuple[dict, str | None]:
    """Devuelve (datos limpios, mensaje de error o None)."""
    nombre = " ".join(formulario.get("nombre", "").split())  # quita espacios dobles
    telefono_texto = formulario.get("telefono", "").strip()
    datos = {"nombre": nombre, "telefono": telefono_texto}

    if not v.nombre_valido(nombre):
        return datos, "El nombre debe tener entre 2 y 80 caracteres."
    telefono = v.normalizar_telefono(telefono_texto)
    if telefono is None:
        return datos, "El teléfono debe tener 10 dígitos (ej. 993 123 4567)."
    return {"nombre": nombre, "telefono": telefono}, None


@bp.route("/")
@login_requerido
@negocio_requerido
def lista():
    busqueda = request.args.get("q", "").strip()
    resultados = clientes.listar(g.sb, g.comercio["id"], busqueda)
    return render_template("clientes/lista.html", clientes=resultados, busqueda=busqueda)


@bp.route("/nuevo", methods=["GET", "POST"])
@login_requerido
@negocio_requerido
def nuevo():
    datos = {"nombre": "", "telefono": ""}

    if request.method == "POST":
        datos, error = _validar(request.form)
        if error:
            flash(error, "error")
        else:
            try:
                cliente = clientes.crear(g.sb, g.comercio["id"], datos["nombre"], datos["telefono"])
            except APIError as e:
                flash(MENSAJE_DUPLICADO if e.code == "23505" else "No se pudo guardar. Intenta de nuevo.",
                      "error")
            else:
                flash(f"Cliente {cliente['nombre']} guardado.", "exito")
                if request.args.get("volver") == "orden":
                    return redirect(url_for("ordenes.nueva", cliente_id=cliente["id"]))
                return redirect(url_for("clientes.lista"))

    return render_template("clientes/formulario.html", datos=datos, editando=False)


@bp.route("/<int:cliente_id>/editar", methods=["GET", "POST"])
@login_requerido
@negocio_requerido
def editar(cliente_id: int):
    cliente = clientes.obtener(g.sb, g.comercio["id"], cliente_id)
    if cliente is None:
        abort(404)

    datos = {"nombre": cliente["nombre"], "telefono": telefono_legible(cliente["telefono"])}

    if request.method == "POST":
        datos, error = _validar(request.form)
        if error:
            flash(error, "error")
        else:
            try:
                clientes.actualizar(g.sb, g.comercio["id"], cliente_id, datos["nombre"], datos["telefono"])
            except APIError as e:
                flash(MENSAJE_DUPLICADO if e.code == "23505" else "No se pudo guardar. Intenta de nuevo.",
                      "error")
            else:
                flash("Cambios guardados.", "exito")
                return redirect(url_for("clientes.lista"))

    return render_template("clientes/formulario.html", datos=datos, editando=True, cliente=cliente)
