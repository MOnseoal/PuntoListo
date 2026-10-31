"""Blueprint del negocio (función b).

ACT-12: pantalla "Configura tu negocio" (nombre, abreviatura, giro).
ACT-14 agregará aquí la edición del catálogo de servicios.
"""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from postgrest.exceptions import APIError

from .. import validaciones as v
from ..etiquetas import GIROS
from ..modelos import comercios
from ..seguridad import login_requerido

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
