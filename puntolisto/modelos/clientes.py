"""Repositorio de clientes (capa Modelo).

Cada función recibe `sb` (cliente con el token del comerciante) y el
comercio_id; RLS además impide tocar clientes de otro negocio.
"""
import re

COLUMNAS = "id, nombre, telefono, creado_en"


def _limpiar_busqueda(texto: str) -> str:
    """Quita caracteres que tienen significado especial en los filtros."""
    return re.sub(r"[%_,()*\\:\"']", " ", texto or "").strip()


def listar(sb, comercio_id: int, busqueda: str = "", limite: int = 200) -> list[dict]:
    """Clientes en orden alfabético. Si hay búsqueda:
    - solo dígitos -> busca dentro del teléfono
    - texto        -> busca dentro del nombre (sin importar mayúsculas)
    """
    consulta = sb.table("clientes").select(COLUMNAS).eq("comercio_id", comercio_id)

    busqueda = _limpiar_busqueda(busqueda)
    digitos = re.sub(r"\D", "", busqueda)
    if busqueda and digitos == busqueda.replace(" ", ""):
        consulta = consulta.like("telefono", f"%{digitos}%")
    elif busqueda:
        consulta = consulta.ilike("nombre", f"%{busqueda}%")

    respuesta = consulta.order("nombre").limit(limite).execute()
    return respuesta.data or []


def obtener(sb, comercio_id: int, cliente_id: int) -> dict | None:
    respuesta = (
        sb.table("clientes")
        .select(COLUMNAS)
        .eq("comercio_id", comercio_id)
        .eq("id", cliente_id)
        .limit(1)
        .execute()
    )
    return respuesta.data[0] if respuesta.data else None


def crear(sb, comercio_id: int, nombre: str, telefono: str) -> dict:
    respuesta = sb.table("clientes").insert({
        "comercio_id": comercio_id,
        "nombre": nombre,
        "telefono": telefono,
    }).execute()
    return respuesta.data[0]


def actualizar(sb, comercio_id: int, cliente_id: int, nombre: str, telefono: str) -> dict | None:
    respuesta = (
        sb.table("clientes")
        .update({"nombre": nombre, "telefono": telefono})
        .eq("comercio_id", comercio_id)
        .eq("id", cliente_id)
        .execute()
    )
    return respuesta.data[0] if respuesta.data else None
