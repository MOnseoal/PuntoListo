"""Configuración y constantes de los planes de suscripción (simulación).

Toda la información vive aquí para poder ajustar precios, límites o textos
en un solo lugar sin modificar las plantillas ni la base de datos.
"""

DESCUENTO_PRIMER_MES = 0.20

# Todas las cuentas se muestran en el plan gratuito (no se guarda en Supabase).
PLAN_ACTUAL = "partida"

LIMITES = {
    "partida": {"clientes": 15, "ordenes_mes": 50, "servicios": 5, "tickets_mes": 0},
    "fuerte": {"clientes": 30, "ordenes_mes": 150, "servicios": 10, "tickets_mes": 150},
    "cumbre": {"clientes": 100, "ordenes_mes": 500, "servicios": 30, "tickets_mes": 500},
}

LIMITES_GRATIS = LIMITES["partida"]

# Cuentas de demostración (docs/sql/demo_datos_prueba.sql).
# Si SALTAR_LIMITES_EN_DEMO es True, estas cuentas pueden seguir creando
# servicios/clientes/órdenes durante una presentación aunque superen LIMITES_GRATIS.
CUENTAS_DEMO = (
    "lavanderia@puntolisto.demo",
    "sastreria@puntolisto.demo",
    "taller@puntolisto.demo",
)
SALTAR_LIMITES_EN_DEMO = False


def cuenta_exenta(correo: str | None) -> bool:
    """Indica si el correo actual salta el bloqueo del plan gratuito."""
    if not SALTAR_LIMITES_EN_DEMO or not correo:
        return False
    return correo.strip().lower() in CUENTAS_DEMO


def limite_alcanzado(recurso: str, usados: int, correo: str | None = None) -> bool:
    """Devuelve True si ya se alcanzó o superó el tope de LIMITES_GRATIS."""
    if cuenta_exenta(correo):
        return False
    return usados >= LIMITES_GRATIS[recurso]


def mensaje_limite(recurso: str) -> str:
    """Mensaje amable al alcanzar el límite del plan gratuito, leyendo de LIMITES."""
    actual = PLANES_POR_CLAVE["partida"]["nombre"]
    siguiente = PLANES_POR_CLAVE["fuerte"]["nombre"]
    tope_gratis = LIMITES["partida"][recurso]
    tope_fuerte = LIMITES["fuerte"][recurso]
    if recurso == "ordenes_mes":
        return (
            f"Llegaste a tus {tope_gratis} órdenes de este mes en {actual}. "
            f"Con {siguiente} puedes registrar hasta {tope_fuerte}."
        )
    if recurso == "clientes":
        return (
            f"Llegaste a tus {tope_gratis} clientes en {actual}. "
            f"Con {siguiente} puedes registrar hasta {tope_fuerte}."
        )
    if recurso == "servicios":
        return (
            f"Llegaste a tus {tope_gratis} servicios activos en {actual}. "
            f"Con {siguiente} puedes tener hasta {tope_fuerte}."
        )
    raise KeyError(f"Recurso desconocido: {recurso}")


def construir_medidor(recurso: str, usados: int) -> dict:
    """Prepara los datos y el texto del medidor de uso para Ajustes y el Panel.

    Al llegar o pasar del 80 % del límite, el texto cambia a cuántos quedan
    (con palabras explícitas, sin depender solo del color).
    """
    tope = LIMITES_GRATIS[recurso]
    restantes = max(0, tope - usados)
    porcentaje = min(100, round(100 * usados / tope)) if tope > 0 else 100
    cerca_del_limite = tope > 0 and (usados / tope) >= 0.80

    if recurso == "ordenes_mes":
        titulo = "Órdenes este mes"
        if cerca_del_limite:
            unidad = "orden" if restantes == 1 else "órdenes"
            verbo = "queda" if restantes == 1 else "quedan"
            texto = f"Te {verbo} {restantes} {unidad} este mes ({usados} de {tope})"
        else:
            texto = f"Órdenes este mes: {usados} de {tope}"
    elif recurso == "clientes":
        titulo = "Clientes"
        if cerca_del_limite:
            unidad = "cliente" if restantes == 1 else "clientes"
            verbo = "queda" if restantes == 1 else "quedan"
            texto = f"Te {verbo} {restantes} {unidad} ({usados} de {tope})"
        else:
            texto = f"Clientes: {usados} de {tope}"
    elif recurso == "servicios":
        titulo = "Servicios activos"
        if cerca_del_limite:
            unidad = "servicio activo" if restantes == 1 else "servicios activos"
            verbo = "queda" if restantes == 1 else "quedan"
            texto = f"Te {verbo} {restantes} {unidad} ({usados} de {tope})"
        else:
            texto = f"Servicios activos: {usados} de {tope}"
    else:
        raise KeyError(f"Recurso desconocido: {recurso}")

    return {
        "recurso": recurso,
        "titulo": titulo,
        "usados": usados,
        "tope": tope,
        "restantes": restantes,
        "porcentaje": porcentaje,
        "alerta": cerca_del_limite,
        "lleno": usados >= tope,
        "texto": texto,
    }


def resumen_uso(ordenes_mes: int, clientes_totales: int, servicios_activos: int) -> dict[str, dict]:
    """Devuelve los 3 medidores del plan gratuito listos para las plantillas."""
    return {
        "ordenes_mes": construir_medidor("ordenes_mes", ordenes_mes),
        "clientes": construir_medidor("clientes", clientes_totales),
        "servicios": construir_medidor("servicios", servicios_activos),
    }


def precio_primer_mes(precio: int | float) -> int:
    """Devuelve el precio del primer mes aplicando el 20 % de descuento."""
    return round(precio * (1 - DESCUENTO_PRIMER_MES))


PLANES = [
    {
        "clave": "partida",
        "nombre": "Punto de Partida",
        "etiqueta_corta": "Partida",
        "precio": 0,
        "precio_primer_mes": precio_primer_mes(0),
        "frase": "Para probar y arrancar.",
        "ideal_para": "Negocios que pasan de la libreta al celular y quieren ordenar sus entregas.",
        "destacado": False,
        "funciones": [
            {"texto": f"Hasta {LIMITES['partida']['ordenes_mes']} órdenes al mes", "incluida": True},
            {"texto": f"Hasta {LIMITES['partida']['clientes']} clientes registrados", "incluida": True},
            {"texto": f"Hasta {LIMITES['partida']['servicios']} servicios en el catálogo", "incluida": True},
            {"texto": "Registro de órdenes, folio y estados", "incluida": True},
            {"texto": "Aviso «Listo» por WhatsApp con mensaje estándar", "incluida": True},
            {"texto": "Historial de clientes (Últimos 30 días)", "incluida": True},
            {"texto": "Recordatorio si no recogen", "incluida": False},
            {"texto": "Ticket imprimible o PDF", "incluida": False},
            {"texto": "Mensaje de WhatsApp propio y marca del negocio", "incluida": False},
        ],
    },
    {
        "clave": "fuerte",
        "nombre": "Punto Fuerte",
        "etiqueta_corta": "Fuerte",
        "precio": 75,
        "precio_primer_mes": precio_primer_mes(75),
        "frase": "Para el negocio que ya vive de esto.",
        "ideal_para": "Lavanderías, sastrerías y talleres con clientela constante todos los días.",
        "destacado": True,
        "funciones": [
            {"texto": f"Hasta {LIMITES['fuerte']['ordenes_mes']} órdenes al mes", "incluida": True},
            {"texto": f"Hasta {LIMITES['fuerte']['clientes']} clientes registrados", "incluida": True},
            {"texto": f"Hasta {LIMITES['fuerte']['servicios']} servicios en el catálogo", "incluida": True},
            {"texto": "Registro de órdenes, folio y estados", "incluida": True},
            {"texto": "Aviso «Listo» por WhatsApp con mensaje estándar", "incluida": True},
            {"texto": "Recordatorio si no recogen", "incluida": True},
            {"texto": "Historial de clientes completo", "incluida": True},
            {"texto": f"Ticket imprimible o PDF ({LIMITES['fuerte']['tickets_mes']} al mes)", "incluida": True},
            {"texto": "Mensaje de WhatsApp propio y marca del negocio", "incluida": False},
        ],
    },
    {
        "clave": "cumbre",
        "nombre": "Punto Cumbre",
        "etiqueta_corta": "Cumbre",
        "precio": 150,
        "precio_primer_mes": precio_primer_mes(150),
        "frase": "Para varios empleados o sucursales.",
        "ideal_para": "Negocios con equipo de trabajo, más de un mostrador o alto volumen.",
        "destacado": False,
        "funciones": [
            {"texto": f"Hasta {LIMITES['cumbre']['ordenes_mes']} órdenes al mes", "incluida": True},
            {"texto": f"Hasta {LIMITES['cumbre']['clientes']} clientes registrados", "incluida": True},
            {"texto": f"Hasta {LIMITES['cumbre']['servicios']} servicios en el catálogo", "incluida": True},
            {"texto": "Todo lo de Punto Fuerte incluido", "incluida": True},
            {"texto": f"Ticket imprimible o PDF ({LIMITES['cumbre']['tickets_mes']} al mes)", "incluida": True},
            {"texto": "Mensaje de WhatsApp propio", "incluida": True},
            {"texto": "Logo y color del negocio", "incluida": True},
            {"texto": "Estados personalizados por giro", "incluida": True},
            {"texto": "Reporte semanal, varios usuarios y sucursales", "incluida": True},
            {"texto": "Soporte prioritario por WhatsApp", "incluida": True},
        ],
    },
]

PLANES_POR_CLAVE = {p["clave"]: p for p in PLANES}

# Matriz comparativa: la misma lista de filas para los 3 planes.
MATRIZ_FUNCIONES = [
    {
        "funcion": "Órdenes por mes",
        "partida": str(LIMITES["partida"]["ordenes_mes"]),
        "fuerte": str(LIMITES["fuerte"]["ordenes_mes"]),
        "cumbre": str(LIMITES["cumbre"]["ordenes_mes"]),
    },
    {
        "funcion": "Clientes",
        "partida": str(LIMITES["partida"]["clientes"]),
        "fuerte": str(LIMITES["fuerte"]["clientes"]),
        "cumbre": str(LIMITES["cumbre"]["clientes"]),
    },
    {
        "funcion": "Servicios en el catálogo",
        "partida": str(LIMITES["partida"]["servicios"]),
        "fuerte": str(LIMITES["fuerte"]["servicios"]),
        "cumbre": str(LIMITES["cumbre"]["servicios"]),
    },
    {
        "funcion": "Registro de órdenes, folio y estados",
        "partida": True,
        "fuerte": True,
        "cumbre": True,
    },
    {
        "funcion": "Aviso «Listo» por WhatsApp con mensaje estándar",
        "partida": True,
        "fuerte": True,
        "cumbre": True,
    },
    {
        "funcion": "Recordatorio si no recogen",
        "partida": False,
        "fuerte": True,
        "cumbre": True,
    },
    {
        "funcion": "Historial de clientes",
        "partida": "Últimos 30 días",
        "fuerte": "Completo",
        "cumbre": "Completo",
    },
    {
        "funcion": "Ticket imprimible o PDF",
        "partida": False,
        "fuerte": f"{LIMITES['fuerte']['tickets_mes']} al mes",
        "cumbre": f"{LIMITES['cumbre']['tickets_mes']} al mes",
    },
    {
        "funcion": "Mensaje de WhatsApp propio",
        "partida": False,
        "fuerte": False,
        "cumbre": True,
    },
    {
        "funcion": "Logo y color del negocio",
        "partida": False,
        "fuerte": False,
        "cumbre": True,
    },
    {
        "funcion": "Estados personalizados por giro",
        "partida": False,
        "fuerte": False,
        "cumbre": True,
    },
    {
        "funcion": "Reporte semanal de ventas y entregas",
        "partida": False,
        "fuerte": False,
        "cumbre": True,
    },
    {
        "funcion": "Varios usuarios (empleados) con permisos",
        "partida": False,
        "fuerte": False,
        "cumbre": True,
    },
    {
        "funcion": "Varias sucursales con vista general",
        "partida": False,
        "fuerte": False,
        "cumbre": True,
    },
    {
        "funcion": "Soporte prioritario por WhatsApp",
        "partida": False,
        "fuerte": False,
        "cumbre": True,
    },
]

# Módulos con pantalla de vista previa -> plan mínimo requerido
MODULOS_VISTA_PREVIA = {
    "recordatorio": "fuerte",
    "ticket": "fuerte",
    "historial": "fuerte",
    "mensaje-propio": "cumbre",
    "marca": "cumbre",
    "estados": "cumbre",
    "reporte": "cumbre",
    "equipo": "cumbre",
}

DETALLES_VISTA_PREVIA = {
    "recordatorio": {
        "titulo": "Recordatorio si no recogen",
        "resumen": "Avisa por WhatsApp cuando una orden lleva varios días lista en mostrador.",
    },
    "ticket": {
        "titulo": "Ticket imprimible o PDF",
        "resumen": "Comprobante con folio, servicios y total para imprimir o enviar por WhatsApp.",
    },
    "historial": {
        "titulo": "Historial completo de clientes",
        "resumen": "Consulta todas las órdenes anteriores y preferencias de cada cliente.",
    },
    "mensaje-propio": {
        "titulo": "Mensaje de WhatsApp propio",
        "resumen": "Personaliza el texto del aviso con variables como {nombre}, {folio} y {negocio}.",
    },
    "marca": {
        "titulo": "Logo y color del negocio",
        "resumen": "Pon tu logotipo y el color de tu marca en tus órdenes y comprobantes.",
    },
    "estados": {
        "titulo": "Estados personalizados por giro",
        "resumen": "Adapta los pasos de trabajo a tu taller, sastrería o lavandería.",
    },
    "reporte": {
        "titulo": "Reporte semanal de ventas y entregas",
        "resumen": "Mira cuánto vendiste, cuántas órdenes entregaste y tus días más fuertes.",
    },
    "equipo": {
        "titulo": "Equipo y sucursales",
        "resumen": "Agrega empleados con permisos de mostrador y administra varias sucursales.",
    },
}
