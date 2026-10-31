"""Repositorio de órdenes (capa Modelo).

La creación SIEMPRE pasa por la función RPC crear_orden() de la base de
datos: guarda orden + servicios en una sola transacción y el trigger
asigna el folio (ABREV-0001). Python nunca calcula el folio.
"""
ESTADOS_ACTIVOS = ("recibido", "en_proceso", "listo")
ORDEN_ESTADOS = ("recibido", "en_proceso", "listo", "entregado")

COLUMNAS_DETALLE = (
    "id, folio, estado, fecha_entrega, notas, creado_en, actualizado_en, "
    "clientes(id, nombre, telefono), "
    "orden_servicios(id, cantidad, precio_unitario, servicios(nombre, tipo_cobro))"
)


def listar_activas(sb, comercio_id: int, limite: int = 100) -> list[dict]:
    """Órdenes que aún no se entregan, de la más reciente a la más antigua."""
    respuesta = (
        sb.table("ordenes")
        .select("id, folio, estado, fecha_entrega, creado_en, clientes(nombre)")
        .eq("comercio_id", comercio_id)
        .in_("estado", list(ESTADOS_ACTIVOS))
        .order("creado_en", desc=True)
        .limit(limite)
        .execute()
    )
    return respuesta.data or []


def listar_entregadas(sb, comercio_id: int, limite: int = 50) -> list[dict]:
    """Últimas órdenes entregadas (las más recientes primero)."""
    respuesta = (
        sb.table("ordenes")
        .select("id, folio, estado, fecha_entrega, actualizado_en, clientes(nombre)")
        .eq("comercio_id", comercio_id)
        .eq("estado", "entregado")
        .order("actualizado_en", desc=True)
        .limit(limite)
        .execute()
    )
    return respuesta.data or []


def agrupar_por_estado(ordenes: list[dict]) -> dict[str, list[dict]]:
    grupos = {estado: [] for estado in ESTADOS_ACTIVOS}
    for orden in ordenes:
        grupos.setdefault(orden["estado"], []).append(orden)
    return grupos


def crear(sb, cliente_id: int, servicios: list[dict], fecha_entrega: str | None,
          notas: str | None) -> dict:
    """servicios: [{"servicio_id": 1, "cantidad": 3.5}, ...]. Devuelve {"id", "folio"}."""
    respuesta = sb.rpc("crear_orden", {
        "p_cliente_id": cliente_id,
        "p_servicios": servicios,
        "p_fecha_entrega": fecha_entrega,
        "p_notas": notas,
    }).execute()
    return respuesta.data[0]


def obtener_detalle(sb, comercio_id: int, orden_id: int) -> dict | None:
    respuesta = (
        sb.table("ordenes").select(COLUMNAS_DETALLE)
        .eq("comercio_id", comercio_id).eq("id", orden_id)
        .limit(1).execute()
    )
    return respuesta.data[0] if respuesta.data else None


def cambiar_estado(sb, comercio_id: int, orden_id: int, estado: str) -> dict | None:
    respuesta = (
        sb.table("ordenes").update({"estado": estado})
        .eq("comercio_id", comercio_id).eq("id", orden_id)
        .execute()
    )
    return respuesta.data[0] if respuesta.data else None


def siguiente_estado(estado: str) -> str | None:
    i = ORDEN_ESTADOS.index(estado)
    return ORDEN_ESTADOS[i + 1] if i + 1 < len(ORDEN_ESTADOS) else None


def estado_anterior(estado: str) -> str | None:
    i = ORDEN_ESTADOS.index(estado)
    return ORDEN_ESTADOS[i - 1] if i > 0 else None
