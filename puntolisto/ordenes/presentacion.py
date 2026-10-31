"""Prepara las órdenes para mostrarlas como tarjetas (sin consultar la BD).

Agrega a cada orden:
- alerta:    "atrasada" | "hoy" | "manana" | None   (solo si aún no está lista)
- resumen:   "Lavado por kilo 4.5 kg +1"
- siguiente: el estado al que avanza con la acción rápida (o None)
- enlace_wa: enlace de WhatsApp si está lista y el cliente tiene teléfono
"""
from datetime import date, datetime, timedelta

from .. import avisos
from ..etiquetas import HORA_MEXICO, cantidad_legible, hoy_mexico
from ..modelos.ordenes import siguiente_estado

ESTADOS_CON_ALERTA = ("recibido", "en_proceso")
TEXTO_ALERTA = {"atrasada": "Atrasada", "hoy": "Vence hoy", "manana": "Mañana"}


def calcular_alerta(orden: dict, hoy: date) -> str | None:
    if orden["estado"] not in ESTADOS_CON_ALERTA or not orden.get("fecha_entrega"):
        return None
    dias = (date.fromisoformat(orden["fecha_entrega"][:10]) - hoy).days
    if dias < 0:
        return "atrasada"
    if dias == 0:
        return "hoy"
    if dias == 1:
        return "manana"
    return None


def resumen_servicios(orden: dict) -> str:
    lineas = orden.get("orden_servicios") or []
    if not lineas:
        return ""
    primera = lineas[0]
    servicio = primera.get("servicios") or {}
    texto = f"{servicio.get('nombre', 'Servicio')} {cantidad_legible(primera['cantidad'], servicio.get('tipo_cobro', ''))}"
    if len(lineas) > 1:
        texto += f" +{len(lineas) - 1}"
    return texto


def preparar(ordenes: list[dict], nombre_negocio: str, hoy: date | None = None) -> list[dict]:
    hoy = hoy or hoy_mexico()
    for orden in ordenes:
        orden["alerta"] = calcular_alerta(orden, hoy)
        orden["resumen"] = resumen_servicios(orden)
        orden["siguiente"] = siguiente_estado(orden["estado"])
        orden["enlace_wa"] = (avisos.enlace_orden_lista(orden, nombre_negocio)
                              if orden["estado"] == "listo" else None)
    return ordenes


def _por_fecha(orden: dict) -> str:
    return orden.get("fecha_entrega") or "9999-12-31"


def secciones_panel(ordenes: list[dict]) -> list[tuple[str, list[dict]]]:
    """Agrupa por prioridad: primero lo urgente, luego lo listo para avisar."""
    atencion = sorted([o for o in ordenes if o["alerta"] in ("atrasada", "hoy")], key=_por_fecha)
    urgentes = {o["id"] for o in atencion}
    resto = [o for o in ordenes if o["id"] not in urgentes]
    secciones = [
        ("Requieren atención", atencion),
        ("Listas para avisar o entregar", [o for o in resto if o["estado"] == "listo"]),
        ("En proceso", sorted([o for o in resto if o["estado"] == "en_proceso"], key=_por_fecha)),
        ("Recibidas", sorted([o for o in resto if o["estado"] == "recibido"], key=_por_fecha)),
    ]
    return [(titulo, lista) for titulo, lista in secciones if lista]


def contar_por_estado(ordenes: list[dict]) -> dict[str, int]:
    conteo = {"recibido": 0, "en_proceso": 0, "listo": 0}
    for orden in ordenes:
        if orden["estado"] in conteo:
            conteo[orden["estado"]] += 1
    return conteo


LETRAS_DIA = ("L", "M", "M", "J", "V", "S", "D")


def semana_entregas(entregadas: list[dict], hoy: date | None = None) -> dict:
    """Órdenes entregadas por día en los últimos 7 días (para la mini gráfica).

    Devuelve {"dias": [{"letra", "total", "altura", "hoy"}...], "total": n}.
    La fecha de entrega real es `actualizado_en` (cuando pasó a "entregado").
    """
    hoy = hoy or hoy_mexico()
    dias = [hoy - timedelta(days=i) for i in range(6, -1, -1)]
    conteo = {d: 0 for d in dias}
    for orden in entregadas:
        marca = orden.get("actualizado_en")
        if not marca:
            continue
        dia = datetime.fromisoformat(marca.replace("Z", "+00:00")).astimezone(HORA_MEXICO).date()
        if dia in conteo:
            conteo[dia] += 1
    maximo = max(conteo.values()) or 1
    return {
        "dias": [{"letra": LETRAS_DIA[d.weekday()], "total": conteo[d],
                  "altura": round(100 * conteo[d] / maximo), "hoy": d == hoy} for d in dias],
        "total": sum(conteo.values()),
    }


def porcentajes_flujo(conteo: dict[str, int]) -> dict[str, int]:
    """Ancho (%) de cada tramo de la barra de flujo del panel."""
    total = sum(conteo.values())
    if not total:
        return {k: 0 for k in conteo}
    return {k: round(100 * v / total) for k, v in conteo.items()}
