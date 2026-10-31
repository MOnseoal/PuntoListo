"""Repositorio de comercios (capa Modelo).

Todas las consultas reciben `sb`, el cliente con el token del comerciante,
por lo que Supabase solo devuelve SU comercio (RLS).
"""
COLUMNAS = "id, nombre, abreviatura, giro, telefono"


def obtener_mi_comercio(sb, usuario_id: str) -> dict | None:
    respuesta = (
        sb.table("comercios")
        .select(COLUMNAS)
        .eq("usuario_id", usuario_id)
        .limit(1)
        .execute()
    )
    return respuesta.data[0] if respuesta.data else None


def crear(sb, usuario_id: str, nombre: str, abreviatura: str, giro: str,
          telefono: str | None) -> int:
    """Crea el comercio y copia los servicios de ejemplo de su giro.

    Devuelve cuántos servicios de ejemplo se cargaron.
    """
    sb.table("comercios").insert({
        "usuario_id": usuario_id,
        "nombre": nombre,
        "abreviatura": abreviatura,
        "giro": giro,
        "telefono": telefono,
    }).execute()
    cargados = sb.rpc("cargar_servicios_ejemplo", {}).execute()
    return cargados.data or 0
