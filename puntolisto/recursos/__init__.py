"""Archivos de la interfaz: estilos, JavaScript, íconos y lo necesario para
instalar PuntoListo como app (manifest + service worker).

Se sirven con rutas de Flask para que funcionen igual en tu computadora y
en Vercel (allá la carpeta static de Flask no se usa).
"""
from pathlib import Path

from flask import Blueprint, redirect, send_from_directory, url_for

CARPETA = Path(__file__).parent
VERSION = "6"  # súbela cuando cambies app.css o app.js para que los teléfonos descarguen lo nuevo
EXTENSIONES = {".css", ".js", ".png"}

bp = Blueprint("recursos", __name__)


@bp.route("/recursos/<path:archivo>")
def archivo(archivo: str):
    if Path(archivo).suffix not in EXTENSIONES or "/" in archivo:
        return "", 404
    return send_from_directory(CARPETA, archivo, max_age=60 * 60 * 24 * 7)


@bp.route("/manifest.webmanifest")
def manifest():
    return send_from_directory(CARPETA, "manifest.webmanifest",
                               mimetype="application/manifest+json", max_age=60 * 60 * 24)


@bp.route("/sw.js")
def service_worker():
    # Debe servirse desde la raíz para controlar toda la app, y sin caché larga.
    respuesta = send_from_directory(CARPETA, "sw.js", mimetype="text/javascript", max_age=0)
    respuesta.headers["Cache-Control"] = "no-cache"
    return respuesta


@bp.route("/favicon.ico")
def favicon():
    return redirect(url_for("recursos.archivo", archivo="favicon.png"), code=301)
