"""Módulo de avisos por WhatsApp (función h).

No es un Blueprint: solo arma textos y enlaces. Si mañana cambia el
formato del mensaje o el canal (ej. API oficial de WhatsApp), solo se
modifica este archivo.
"""
from urllib.parse import quote

from ..giros import obtener_giro

BASE_WA = "https://wa.me/"


def mensaje_listo(nombre_cliente: str, folio: str, nombre_negocio: str,
                  giro: str | None = None) -> str:
    primer_nombre = (nombre_cliente or "").split(" ")[0] or "cliente"
    plantilla = obtener_giro(giro)
    vocabulario = plantilla["vocabulario"]
    return plantilla["mensaje_whatsapp"].format(
        nombre=primer_nombre,
        folio=folio,
        negocio=nombre_negocio,
        articulo=vocabulario["articulo"],
        articulos=vocabulario["articulos"],
        orden=vocabulario["orden"],
        ordenes=vocabulario["ordenes"],
        verbo_recoger=vocabulario["verbo_recoger"],
    )


def enlace_whatsapp(telefono: str, mensaje: str) -> str:
    """telefono en formato 52 + 10 dígitos. El texto se codifica (acentos, espacios, ¡!)."""
    digitos = "".join(c for c in (telefono or "") if c.isdigit())
    return f"{BASE_WA}{digitos}?text={quote(mensaje, safe='')}"


def enlace_orden_lista(orden: dict, nombre_negocio: str,
                       giro: str | None = None) -> str | None:
    """Enlace para avisar que la orden está lista, o None si falta el teléfono."""
    cliente = orden.get("clientes") or {}
    if not cliente.get("telefono"):
        return None
    mensaje = mensaje_listo(cliente.get("nombre", ""), orden["folio"], nombre_negocio, giro=giro)
    return enlace_whatsapp(cliente["telefono"], mensaje)
