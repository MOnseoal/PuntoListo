"""Validaciones de formularios (sin depender de Flask ni de Supabase)."""
import re
import unicodedata

PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PATRON_ABREVIATURA = re.compile(r"^[A-Z0-9]{1,5}$")
LONGITUD_MIN_CONTRASENA = 8


def normalizar_telefono(texto: str) -> str | None:
    """Convierte lo que escribe el usuario al formato de la BD: 52 + 10 dígitos.

    '993 123 4567', '993-123-4567', '+52 993 123 4567' -> '529931234567'
    Devuelve None si no es un número válido de 10 dígitos.
    """
    digitos = re.sub(r"\D", "", texto or "")
    if len(digitos) == 12 and digitos.startswith("52"):
        digitos = digitos[2:]
    if len(digitos) != 10:
        return None
    return "52" + digitos


def sin_acentos(texto: str) -> str:
    normal = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in normal if not unicodedata.combining(c))


def sugerir_abreviatura(nombre: str) -> str:
    """'Lavandería Ánge' -> 'LAV'. Si no hay letras, 'PL'."""
    limpio = re.sub(r"[^A-Z0-9]", "", sin_acentos(nombre or "").upper())
    return limpio[:3] or "PL"


def normalizar_abreviatura(texto: str) -> str | None:
    abrev = sin_acentos((texto or "").strip()).upper()
    return abrev if PATRON_ABREVIATURA.match(abrev) else None


def correo_valido(correo: str) -> bool:
    return bool(PATRON_CORREO.match(correo or ""))


def nombre_valido(nombre: str) -> bool:
    return 2 <= len((nombre or "").strip()) <= 80


PRECIO_MAXIMO = 99_999_999.99


def leer_numero(texto: str) -> float | None:
    """'3,5' o '3.5' -> 3.5. Vacío o inválido -> None."""
    limpio = (texto or "").strip().replace(",", ".").replace("$", "").replace(" ", "")
    if not limpio:
        return None
    try:
        valor = float(limpio)
    except ValueError:
        return None
    if valor != valor or valor in (float("inf"), float("-inf")):  # NaN o infinito
        return None
    return valor


def precio_valido(valor: float | None) -> bool:
    return valor is not None and 0 <= valor <= PRECIO_MAXIMO


def cantidad_valida(valor: float | None, tipo_cobro: str) -> bool:
    """Por kilo admite decimales (3.5 kg); por pieza o ajuste solo enteros."""
    if valor is None or valor <= 0 or valor > 9999:
        return False
    if tipo_cobro == "kilo":
        return round(valor, 2) == valor
    return valor == int(valor)
