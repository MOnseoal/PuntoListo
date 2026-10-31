"""Textos para mostrar. La base de datos guarda claves sin acentos;
aquí se traducen a lo que ve el comerciante."""
from datetime import date

GIROS = {
    "lavanderia": "Lavandería",
    "sastreria": "Sastrería",
    "taller": "Taller de reparación",
    "otro": "Otro",
}

ESTADOS = {
    "recibido": "Recibido",
    "en_proceso": "En proceso",
    "listo": "Listo",
    "entregado": "Entregado",
}

TIPOS_COBRO = {
    "kilo": "Por kilo",
    "pieza": "Por pieza",
    "ajuste": "Por ajuste",
}


def fecha_corta(valor) -> str:
    """'2026-11-05' -> '05/11/2026'."""
    if not valor:
        return ""
    if isinstance(valor, str):
        valor = date.fromisoformat(valor[:10])
    return valor.strftime("%d/%m/%Y")


def registrar_etiquetas(app) -> None:
    app.jinja_env.globals.update(GIROS=GIROS, ESTADOS=ESTADOS, TIPOS_COBRO=TIPOS_COBRO)
    app.jinja_env.filters["fecha_corta"] = fecha_corta
