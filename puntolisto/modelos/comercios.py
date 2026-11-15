"""Repositorio de comercios (capa Modelo).

Todas las consultas reciben `sb`, el cliente con el token del comerciante,
por lo que Supabase solo devuelve SU comercio (RLS).
"""
from ..giros import obtener_giro

COLUMNAS = "id, nombre, abreviatura, giro, giro_otro, telefono"


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
          telefono: str | None, giro_otro: str | None = None) -> int:
    """Crea el comercio y copia los servicios de ejemplo de la plantilla de su giro.

    Devuelve cuántos servicios de ejemplo se cargaron.
    """
    giro_otro_limpio = (giro_otro or "").strip() or None if giro == "otro" else None
    fila_comercio = {
        "usuario_id": usuario_id,
        "nombre": nombre,
        "abreviatura": abreviatura,
        "giro": giro,
        "telefono": telefono,
        "giro_otro": giro_otro_limpio,
    }
    respuesta = sb.table("comercios").insert(fila_comercio).execute()
    plantilla = obtener_giro(giro)
    ejemplos = plantilla["servicios_ejemplo"]
    comercio_id = (respuesta.data or [{}])[0].get("id") if respuesta.data else None
    if comercio_id is not None and ejemplos:
        filas_servicios = [
            {"comercio_id": comercio_id, "nombre": n, "tipo_cobro": tc, "precio": p}
            for n, tc, p in ejemplos
        ]
        insertados = sb.table("servicios").insert(filas_servicios).execute()
        return len(insertados.data or filas_servicios)
    return len(ejemplos)


def actualizar(sb, usuario_id: str, nombre: str, telefono: str | None) -> dict | None:
    """Solo nombre y teléfono. La abreviatura y el giro no se cambian para que
    los folios y el catálogo sigan siendo coherentes."""
    respuesta = (
        sb.table("comercios")
        .update({"nombre": nombre, "telefono": telefono})
        .eq("usuario_id", usuario_id)
        .execute()
    )
    return respuesta.data[0] if respuesta.data else None
