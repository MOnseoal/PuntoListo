"""Repositorio de órdenes (capa Modelo).

Por ahora solo lo que necesita el panel (ACT-12). La creación de órdenes
se agrega en ACT-15 usando la función RPC crear_orden().
"""
ESTADOS_ACTIVOS = ("recibido", "en_proceso", "listo")


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


def agrupar_por_estado(ordenes: list[dict]) -> dict[str, list[dict]]:
    grupos = {estado: [] for estado in ESTADOS_ACTIVOS}
    for orden in ordenes:
        grupos.setdefault(orden["estado"], []).append(orden)
    return grupos
