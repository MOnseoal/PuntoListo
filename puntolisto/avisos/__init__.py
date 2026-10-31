"""Módulo de avisos por WhatsApp (función h).

No es un Blueprint: solo arma textos y enlaces. Si mañana cambia el
formato del mensaje o el canal (ej. API oficial de WhatsApp), solo se
modifica este archivo.
"""
from urllib.parse import quote

BASE_WA = "https://wa.me/"


def mensaje_listo(nombre_cliente: str, folio: str, nombre_negocio: str) -> str:
    primer_nombre = (nombre_cliente or "").split(" ")[0] or "cliente"
    return (
        f"Hola {primer_nombre}, te escribimos de {nombre_negocio}. "
        f"Tu orden {folio} ya está lista. Puedes pasar a recogerla cuando gustes. "
        f"¡Gracias por tu preferencia!"
    )


def enlace_whatsapp(telefono: str, mensaje: str) -> str:
    """telefono en formato 52 + 10 dígitos. El texto se codifica (acentos, espacios, ¡!)."""
    digitos = "".join(c for c in (telefono or "") if c.isdigit())
    return f"{BASE_WA}{digitos}?text={quote(mensaje, safe='')}"


def enlace_orden_lista(orden: dict, nombre_negocio: str) -> str | None:
    """Enlace para avisar que la orden está lista, o None si falta el teléfono."""
    cliente = orden.get("clientes") or {}
    if not cliente.get("telefono"):
        return None
    mensaje = mensaje_listo(cliente.get("nombre", ""), orden["folio"], nombre_negocio)
    return enlace_whatsapp(cliente["telefono"], mensaje)
