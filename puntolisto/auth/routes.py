"""Blueprint de autenticación (función a): registro, entrar y salir."""
import httpx
from flask import Blueprint, flash, redirect, render_template, request, url_for
from supabase import AuthError

from .. import validaciones as v
from ..supabase_cliente import nuevo_cliente
from . import sesion

bp = Blueprint("auth", __name__)

MENSAJES_ERROR = {
    "invalid_credentials": "Correo o contraseña incorrectos.",
    "email_not_confirmed": "Confirma tu correo antes de entrar (revisa tu bandeja).",
    "user_already_exists": "Ya existe una cuenta con ese correo. Inicia sesión.",
    "email_exists": "Ya existe una cuenta con ese correo. Inicia sesión.",
    "weak_password": "La contraseña es muy débil. Usa al menos 8 caracteres.",
    "email_address_invalid": "El correo no es válido.",
    "over_request_rate_limit": "Demasiados intentos. Espera unos minutos.",
    "over_email_send_rate_limit": "Demasiados intentos. Espera unos minutos.",
    "signup_disabled": "El registro de cuentas está desactivado.",
}
MENSAJE_GENERICO = "No se pudo completar. Intenta de nuevo."
MENSAJE_SIN_CONEXION = "No pudimos conectar con el servidor. Revisa tu internet."


def _mensaje_de(error: AuthError) -> str:
    return MENSAJES_ERROR.get(getattr(error, "code", None), MENSAJE_GENERICO)


@bp.route("/entrar", methods=["GET", "POST"])
def entrar():
    if sesion.hay_sesion():
        return redirect(url_for("panel.inicio"))

    correo = request.form.get("correo", "").strip().lower()

    if request.method == "POST":
        contrasena = request.form.get("contrasena", "")
        if not correo or not contrasena:
            flash("Escribe tu correo y tu contraseña.", "error")
        else:
            try:
                respuesta = nuevo_cliente().auth.sign_in_with_password(
                    {"email": correo, "password": contrasena}
                )
                sesion.guardar(respuesta.session)
                return redirect(url_for("panel.inicio"))
            except AuthError as error:
                flash(_mensaje_de(error), "error")
            except httpx.HTTPError:
                flash(MENSAJE_SIN_CONEXION, "error")

    return render_template("auth/entrar.html", correo=correo)


@bp.route("/registro", methods=["GET", "POST"])
def registro():
    if sesion.hay_sesion():
        return redirect(url_for("panel.inicio"))

    correo = request.form.get("correo", "").strip().lower()

    if request.method == "POST":
        contrasena = request.form.get("contrasena", "")
        confirmar = request.form.get("confirmar", "")

        if not v.correo_valido(correo):
            flash("Escribe un correo válido.", "error")
        elif len(contrasena) < v.LONGITUD_MIN_CONTRASENA:
            flash(f"La contraseña debe tener al menos {v.LONGITUD_MIN_CONTRASENA} caracteres.", "error")
        elif contrasena != confirmar:
            flash("Las contraseñas no coinciden.", "error")
        else:
            try:
                respuesta = nuevo_cliente().auth.sign_up({"email": correo, "password": contrasena})
            except AuthError as error:
                flash(_mensaje_de(error), "error")
            except httpx.HTTPError:
                flash(MENSAJE_SIN_CONEXION, "error")
            else:
                if respuesta.session is None:
                    # Pasa si "Confirm email" está activado en Supabase
                    flash("Cuenta creada. Revisa tu correo para confirmarla y luego entra.", "info")
                    return redirect(url_for("auth.entrar"))
                sesion.guardar(respuesta.session)
                flash("¡Cuenta creada! Ahora configura tu negocio.", "exito")
                return redirect(url_for("negocio.configurar"))

    return render_template("auth/registro.html", correo=correo)


@bp.route("/salir", methods=["POST"])
def salir():
    sesion.cerrar()
    flash("Cerraste sesión.", "info")
    return redirect(url_for("auth.entrar"))
