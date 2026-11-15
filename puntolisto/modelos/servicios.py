"""Repositorio del catálogo de servicios (capa Modelo)."""
COLUMNAS = "id, nombre, tipo_cobro, precio, activo"


def listar(sb, comercio_id: int, solo_activos: bool = False) -> list[dict]:
    consulta = sb.table("servicios").select(COLUMNAS).eq("comercio_id", comercio_id)
    if solo_activos:
        consulta = consulta.eq("activo", True)
    respuesta = consulta.order("activo", desc=True).order("nombre").execute()
    return respuesta.data or []


def contar_activos(sb, comercio_id: int) -> int:
    """Total de servicios activos en el catálogo del comercio."""
    respuesta = (
        sb.table("servicios")
        .select("id", count="exact")
        .eq("comercio_id", comercio_id)
        .eq("activo", True)
        .execute()
    )
    if getattr(respuesta, "count", None) is not None:
        return int(respuesta.count)
    return len(respuesta.data or [])


def obtener(sb, comercio_id: int, servicio_id: int) -> dict | None:
    respuesta = (
        sb.table("servicios").select(COLUMNAS)
        .eq("comercio_id", comercio_id).eq("id", servicio_id)
        .limit(1).execute()
    )
    return respuesta.data[0] if respuesta.data else None


def crear(sb, comercio_id: int, nombre: str, tipo_cobro: str, precio: float) -> dict:
    respuesta = sb.table("servicios").insert({
        "comercio_id": comercio_id, "nombre": nombre,
        "tipo_cobro": tipo_cobro, "precio": precio,
    }).execute()
    return respuesta.data[0]


def actualizar(sb, comercio_id: int, servicio_id: int, nombre: str, tipo_cobro: str,
               precio: float) -> dict | None:
    respuesta = (
        sb.table("servicios")
        .update({"nombre": nombre, "tipo_cobro": tipo_cobro, "precio": precio})
        .eq("comercio_id", comercio_id).eq("id", servicio_id)
        .execute()
    )
    return respuesta.data[0] if respuesta.data else None


def cambiar_activo(sb, comercio_id: int, servicio_id: int, activo: bool) -> dict | None:
    """Desactivar en vez de borrar: las órdenes viejas siguen mostrando el servicio."""
    respuesta = (
        sb.table("servicios").update({"activo": activo})
        .eq("comercio_id", comercio_id).eq("id", servicio_id)
        .execute()
    )
    return respuesta.data[0] if respuesta.data else None
