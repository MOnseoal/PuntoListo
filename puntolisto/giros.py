"""Catálogo de giros de negocio como plantillas (ACT-26).

Cada giro define su nombre visible, su vocabulario ('orden', 'articulo', etc.),
hasta 3 servicios de ejemplo (acorde al límite de 3 servicios en Punto de Partida)
y su plantilla de mensaje para WhatsApp.
"""

MENSAJE_CLASICO = (
    "Hola {nombre}, te escribimos de {negocio}. "
    "Tu orden {folio} ya está lista. Puedes pasar a recogerla cuando gustes. "
    "¡Gracias por tu preferencia!"
)

GIROS: dict[str, dict] = {
    "lavanderia": {
        "clave": "lavanderia",
        "nombre": "Lavandería",
        "vocabulario": {
            "orden": "orden",
            "ordenes": "órdenes",
            "articulo": "prenda",
            "articulos": "prendas",
            "verbo_recoger": "pasar a recogerla",
        },
        "placeholder_descripcion": "Ej. 1 bolsa azul con ropa de color y 1 edredón",
        "servicios_ejemplo": [
            ("Lavado por kilo", "kilo", 30),
            ("Lavado y planchado por kilo", "kilo", 45),
            ("Planchado por pieza", "pieza", 15),
        ],
        "mensaje_whatsapp": MENSAJE_CLASICO,
    },
    "sastreria": {
        "clave": "sastreria",
        "nombre": "Sastrería",
        "vocabulario": {
            "orden": "orden",
            "ordenes": "órdenes",
            "articulo": "prenda",
            "articulos": "prendas",
            "verbo_recoger": "pasar a recogerla",
        },
        "placeholder_descripcion": "Ej. Pantalón azul marino, subir 3 cm de largo",
        "servicios_ejemplo": [
            ("Dobladillo de pantalón", "ajuste", 60),
            ("Ajuste de cintura", "ajuste", 80),
            ("Cambio de cierre", "ajuste", 70),
        ],
        "mensaje_whatsapp": MENSAJE_CLASICO,
    },
    "taller": {
        "clave": "taller",
        "nombre": "Taller de reparación",
        "vocabulario": {
            "orden": "reparación",
            "ordenes": "reparaciones",
            "articulo": "equipo",
            "articulos": "equipos",
            "verbo_recoger": "pasar a recogerlo",
        },
        "placeholder_descripcion": "Ej. Licuadora Oster gris, no enciende",
        "servicios_ejemplo": [
            ("Diagnóstico", "pieza", 100),
            ("Reparación general", "ajuste", 250),
            ("Cambio de pieza", "pieza", 150),
        ],
        "mensaje_whatsapp": (
            "Hola {nombre}, te escribimos de {negocio}. "
            "Tu {articulo} con folio {folio} ya está listo. Puedes {verbo_recoger} cuando gustes. "
            "¡Gracias por tu preferencia!"
        ),
    },
    "celulares": {
        "clave": "celulares",
        "nombre": "Reparación de celulares",
        "vocabulario": {
            "orden": "reparación",
            "ordenes": "reparaciones",
            "articulo": "equipo",
            "articulos": "equipos",
            "verbo_recoger": "pasar a recogerlo",
        },
        "placeholder_descripcion": "Ej. Samsung A14 negro, pantalla rota, sin funda",
        "servicios_ejemplo": [
            ("Cambio de pantalla", "pieza", 650),
            ("Cambio de batería", "pieza", 380),
            ("Revisión y limpieza", "ajuste", 150),
        ],
        "mensaje_whatsapp": (
            "Hola {nombre}, te escribimos de {negocio}. "
            "Tu {articulo} con folio {folio} ya está reparado y listo para entrega. "
            "Puedes {verbo_recoger} cuando gustes. ¡Gracias por tu preferencia!"
        ),
    },
    "relojeria": {
        "clave": "relojeria",
        "nombre": "Relojería",
        "vocabulario": {
            "orden": "reparación",
            "ordenes": "reparaciones",
            "articulo": "reloj",
            "articulos": "relojes",
            "verbo_recoger": "pasar a recogerlo",
        },
        "placeholder_descripcion": "Ej. Casio dorado extensible metálico, no da la hora",
        "servicios_ejemplo": [
            ("Cambio de pila", "pieza", 80),
            ("Ajuste de extensible", "ajuste", 60),
            ("Servicio general y limpieza", "ajuste", 250),
        ],
        "mensaje_whatsapp": (
            "Hola {nombre}, te escribimos de {negocio}. "
            "Tu {articulo} con folio {folio} ya está listo. "
            "Puedes {verbo_recoger} cuando gustes. ¡Gracias por tu preferencia!"
        ),
    },
    "tapiceria": {
        "clave": "tapiceria",
        "nombre": "Tapicería",
        "vocabulario": {
            "orden": "trabajo",
            "ordenes": "trabajos",
            "articulo": "mueble",
            "articulos": "muebles",
            "verbo_recoger": "pasar a recogerlo",
        },
        "placeholder_descripcion": "Ej. 4 sillas de comedor de madera, tapizar en tela gris",
        "servicios_ejemplo": [
            ("Tapizado de silla", "pieza", 350),
            ("Reparación de cojín o espuma", "ajuste", 220),
            ("Tapizado de sillón", "pieza", 1800),
        ],
        "mensaje_whatsapp": (
            "Hola {nombre}, te escribimos de {negocio}. "
            "Tu {articulo} con folio {folio} ya está terminado y listo. "
            "Puedes {verbo_recoger} cuando gustes. ¡Gracias por tu preferencia!"
        ),
    },
    "bordado": {
        "clave": "bordado",
        "nombre": "Bordado y serigrafía",
        "vocabulario": {
            "orden": "pedido",
            "ordenes": "pedidos",
            "articulo": "prenda",
            "articulos": "prendas",
            "verbo_recoger": "pasar a recogerlo",
        },
        "placeholder_descripcion": "Ej. 12 playeras polo negras talla M, logo en pecho izquierdo",
        "servicios_ejemplo": [
            ("Bordado de nombre o texto", "pieza", 45),
            ("Bordado de logotipo", "pieza", 85),
            ("Estampado en serigrafía", "pieza", 35),
        ],
        "mensaje_whatsapp": (
            "Hola {nombre}, te escribimos de {negocio}. "
            "Tu pedido {folio} ya está terminado y listo. "
            "Puedes {verbo_recoger} cuando gustes. ¡Gracias por tu preferencia!"
        ),
    },
    "otro": {
        "clave": "otro",
        "nombre": "Otro",
        "vocabulario": {
            "orden": "orden",
            "ordenes": "órdenes",
            "articulo": "artículo",
            "articulos": "artículos",
            "verbo_recoger": "pasar a recogerla",
        },
        "placeholder_descripcion": "Ej. Descripción breve de lo que dejó el cliente",
        "servicios_ejemplo": [
            ("Servicio básico", "pieza", 100),
            ("Servicio por hora", "ajuste", 150),
            ("Servicio especial", "pieza", 250),
        ],
        "mensaje_whatsapp": MENSAJE_CLASICO,
    },
}

NOMBRES_GIROS: dict[str, str] = {clave: datos["nombre"] for clave, datos in GIROS.items()}


def giro_valido(clave: str | None) -> bool:
    """Devuelve True si la clave pertenece al catálogo de GIROS."""
    return bool(clave and clave in GIROS)


def obtener_giro(clave: str | None) -> dict:
    """Devuelve la plantilla del giro indicado; si no existe, devuelve 'otro'."""
    if clave and clave in GIROS:
        return GIROS[clave]
    return GIROS["otro"]


def lista_giros() -> list[tuple[str, str]]:
    """Lista de (clave, nombre) para los selectores, con 'Otro' al final."""
    claves = [c for c in GIROS if c != "otro"] + ["otro"]
    return [(c, GIROS[c]["nombre"]) for c in claves]
