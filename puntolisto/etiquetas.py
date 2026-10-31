"""Textos para mostrar. La base de datos guarda claves sin acentos;
aquí se traducen a lo que ve el comerciante."""
from datetime import date, datetime, timedelta, timezone

# Tabasco usa la hora del centro de México (UTC-6, sin horario de verano desde 2022).
# Se usa un desfase fijo para no depender de la base de zonas horarias del servidor.
HORA_MEXICO = timezone(timedelta(hours=-6))

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
    """'2026-11-05' -> '05/11/2026'. Las fechas con hora (UTC) se pasan a hora de México."""
    if not valor:
        return ""
    if isinstance(valor, str):
        if len(valor) > 10:
            valor = datetime.fromisoformat(valor.replace("Z", "+00:00"))
        else:
            valor = date.fromisoformat(valor)
    if isinstance(valor, datetime):
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=timezone.utc)
        valor = valor.astimezone(HORA_MEXICO)
    return valor.strftime("%d/%m/%Y")


def telefono_legible(valor) -> str:
    """'529931234567' o '9931234567' -> '993 123 4567'. Otro texto se deja igual."""
    todos = "".join(c for c in (valor or "") if c.isdigit())
    if len(todos) == 12 and todos.startswith("52"):
        todos = todos[2:]
    if len(todos) != 10:
        return valor or ""
    digitos = todos
    return f"{digitos[:3]} {digitos[3:6]} {digitos[6:]}"


UNIDADES = {  # (singular, plural)
    "kilo": ("kg", "kg"),
    "pieza": ("pieza", "piezas"),
    "ajuste": ("ajuste", "ajustes"),
}


def dinero(valor) -> str:
    """45 -> '$45.00'."""
    try:
        return f"${float(valor):,.2f}"
    except (TypeError, ValueError):
        return ""


def numero_corto(valor) -> str:
    """3.50 -> '3.5', 2.0 -> '2'."""
    try:
        return f"{float(valor):g}"
    except (TypeError, ValueError):
        return ""


def cantidad_legible(cantidad, tipo_cobro: str) -> str:
    """(3.5, 'kilo') -> '3.5 kg'; (2, 'pieza') -> '2 piezas'; (1, 'ajuste') -> '1 ajuste'."""
    singular, plural = UNIDADES.get(tipo_cobro, ("", ""))
    texto = numero_corto(cantidad)
    unidad = singular if texto == "1" else plural
    return f"{texto} {unidad}".strip()


def registrar_etiquetas(app) -> None:
    app.jinja_env.globals.update(GIROS=GIROS, ESTADOS=ESTADOS, TIPOS_COBRO=TIPOS_COBRO)
    app.jinja_env.filters["fecha_corta"] = fecha_corta
    app.jinja_env.filters["telefono_legible"] = telefono_legible
    app.jinja_env.filters["dinero"] = dinero
    app.jinja_env.filters["numero_corto"] = numero_corto
    app.jinja_env.globals["cantidad_legible"] = cantidad_legible
