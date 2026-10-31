"""Repositorio de órdenes (capa Modelo).

La creación SIEMPRE pasa por la función RPC crear_orden() de la base de
datos: guarda orden + servicios en una sola transacción y el trigger
asigna el folio (ABREV-0001). Python nunca calcula el folio.
"""
import re

ESTADOS_ACTIVOS = ("recibido", "en_proceso", "listo")
ORDEN_ESTADOS = ("recibido", "en_proceso", "listo", "entregado")

COLUMNAS_DETALLE = (
    "id, folio, estado, fecha_entrega, notas, creado_en, actualizado_en, "
    "clientes(id, nombre, telefono), "
    "orden_servicios(id, cantidad, precio_unitario, servicios(nombre, tipo_cobro))"
)


# Columnas para las tarjetas: cliente con teléfono (para el botón de WhatsApp)
# y un resumen de servicios.
COLUMNAS_TARJETA = (
    "id, folio, estado, fecha_entrega, creado_en, actualizado_en, "
    "clientes(nombre, telefono), orden_servicios(cantidad, servicios(nombre, tipo_cobro))"
)


def _limpiar_folio(texto: str) -> str:
    """Solo letras, números y guion: lo que puede tener un folio."""
    return re.sub(r"[^A-Za-z0-9-]", "", texto or "").upper()


def listar(sb, comercio_id: int, estados: tuple[str, ...], busqueda: str = "",
           cliente_ids: list[int] | None = None, orden_por: str = "creado_en",
           limite: int = 200) -> list[dict]:
    """Órdenes en los estados indicados, de la más reciente a la más antigua.

    busqueda + cliente_ids: encuentra órdenes cuyo folio contenga el texto
    O cuyo cliente esté en cliente_ids (los ids salen de buscar clientes por
    nombre o teléfono en el repositorio de clientes).
    """
    consulta = (
        sb.table("ordenes").select(COLUMNAS_TARJETA)
        .eq("comercio_id", comercio_id)
        .in_("estado", list(estados))
    )
    folio = _limpiar_folio(busqueda)
    condiciones = []
    if folio:
        condiciones.append(f"folio.ilike.*{folio}*")
    if cliente_ids:
        condiciones.append(f"cliente_id.in.({','.join(str(int(i)) for i in cliente_ids)})")
    if busqueda.strip():
        if not condiciones:
            return []  # se buscó algo que no puede coincidir con nada
        consulta = consulta.or_(",".join(condiciones))

    respuesta = consulta.order(orden_por, desc=True).limit(limite).execute()
    return respuesta.data or []


def listar_activas(sb, comercio_id: int, limite: int = 200) -> list[dict]:
    """Órdenes que aún no se entregan (para el panel)."""
    return listar(sb, comercio_id, ESTADOS_ACTIVOS, limite=limite)


def listar_entregadas(sb, comercio_id: int, limite: int = 50) -> list[dict]:
    """Últimas órdenes entregadas (las más recientes primero)."""
    return listar(sb, comercio_id, ("entregado",), orden_por="actualizado_en", limite=limite)


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
