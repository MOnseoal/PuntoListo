"""Textos para mostrar. La base de datos guarda claves sin acentos;
aquí se traducen a lo que ve el comerciante."""
from datetime import date, datetime, timedelta, timezone

from flask import g, has_request_context

from .giros import NOMBRES_GIROS, lista_giros, obtener_giro

# Tabasco usa la hora del centro de México (UTC-6, sin horario de verano desde 2022).
# Se usa un desfase fijo para no depender de la base de zonas horarias del servidor.
HORA_MEXICO = timezone(timedelta(hours=-6))

GIROS = NOMBRES_GIROS

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


DIAS = ("lun", "mar", "mié", "jue", "vie", "sáb", "dom")
MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
DIAS_LARGOS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")


def hoy_mexico() -> date:
    """Fecha de hoy en México (el servidor de Vercel trabaja en UTC)."""
    return datetime.now(HORA_MEXICO).date()


def _a_fecha(valor) -> date | None:
    if not valor:
        return None
    if isinstance(valor, datetime):
        return valor.astimezone(HORA_MEXICO).date()
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(str(valor)[:10])


def fecha_amigable(valor) -> str:
    """'hoy', 'mañana', 'ayer' o 'lun 2 nov'."""
    fecha = _a_fecha(valor)
    if fecha is None:
        return ""
    diferencia = (fecha - hoy_mexico()).days
    if diferencia == 0:
        return "hoy"
    if diferencia == 1:
        return "mañana"
    if diferencia == -1:
        return "ayer"
    return f"{DIAS[fecha.weekday()]} {fecha.day} {MESES[fecha.month - 1]}"


def saludo() -> str:
    """'Buenos días' / 'Buenas tardes' / 'Buenas noches' según la hora de México."""
    hora = datetime.now(HORA_MEXICO).hour
    if 5 <= hora < 12:
        return "Buenos días"
    if 12 <= hora < 19:
        return "Buenas tardes"
    return "Buenas noches"


PALABRAS_MENORES = {"de", "del", "la", "las", "el", "los", "y", "e"}


def iniciales(nombre: str) -> str:
    """'Lavandería La Estrella' -> 'LE'; 'María López' -> 'ML'; 'Ana' -> 'A'."""
    palabras = [p for p in (nombre or "").split() if p.lower() not in PALABRAS_MENORES]
    if len(palabras) > 2:
        palabras = [palabras[0], palabras[-1]]
    return "".join(p[0] for p in palabras[:2]).upper() or "?"


def dia_y_mes(valor) -> tuple[str, str]:
    """'2026-11-05' -> ('5', 'nov') para el bloque de fecha de las tarjetas."""
    fecha = _a_fecha(valor if not isinstance(valor, str) or len(valor) <= 10
                     else datetime.fromisoformat(valor.replace("Z", "+00:00")))
    if fecha is None:
        return ("", "")
    return (str(fecha.day), MESES[fecha.month - 1])


def fecha_larga_hoy() -> str:
    """'Viernes 30 oct'."""
    hoy = hoy_mexico()
    return f"{DIAS_LARGOS[hoy.weekday()]} {hoy.day} {MESES[hoy.month - 1]}"


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


def plantilla_giro_actual() -> dict:
    """Devuelve la plantilla del giro del comercio actual en sesión."""
    giro = None
    if has_request_context():
        comercio = g.get("comercio") or {}
        giro = comercio.get("giro")
    return obtener_giro(giro)


def voc(termino: str = "orden", mayuscula: bool = False) -> str:
    """Devuelve el término del vocabulario según el giro del negocio actual."""
    vocabulario = plantilla_giro_actual()["vocabulario"]
    valor = vocabulario.get(termino, termino)
    if mayuscula and valor:
        return valor[:1].upper() + valor[1:]
    return valor


def registrar_etiquetas(app) -> None:
    from . import planes

    app.jinja_env.globals.update(
        GIROS=GIROS,
        LISTA_GIROS=lista_giros(),
        ESTADOS=ESTADOS,
        TIPOS_COBRO=TIPOS_COBRO,
        PLAN_ACTUAL_INFO=planes.PLANES_POR_CLAVE[planes.PLAN_ACTUAL],
        MODULOS_VISTA_PREVIA=planes.MODULOS_VISTA_PREVIA,
        DETALLES_VISTA_PREVIA=planes.DETALLES_VISTA_PREVIA,
        PLANES_POR_CLAVE=planes.PLANES_POR_CLAVE,
        voc=voc,
        plantilla_giro_actual=plantilla_giro_actual,
    )
    app.jinja_env.filters["fecha_corta"] = fecha_corta
    app.jinja_env.filters["fecha_amigable"] = fecha_amigable
    app.jinja_env.globals["fecha_larga_hoy"] = fecha_larga_hoy
    app.jinja_env.globals["saludo"] = saludo
    app.jinja_env.globals["dia_y_mes"] = dia_y_mes
    app.jinja_env.filters["iniciales"] = iniciales
    app.jinja_env.filters["telefono_legible"] = telefono_legible
    app.jinja_env.filters["dinero"] = dinero
    app.jinja_env.filters["numero_corto"] = numero_corto
    app.jinja_env.globals["cantidad_legible"] = cantidad_legible
