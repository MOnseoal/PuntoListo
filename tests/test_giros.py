"""Pruebas de ACT-26: giros como plantillas, vocabulario por giro y descripción de la orden."""
from types import SimpleNamespace
import urllib.parse

import pytest

from conftest import iniciar_sesion
from puntolisto.avisos import enlace_orden_lista, mensaje_listo
from puntolisto.giros import GIROS, giro_valido, lista_giros, obtener_giro
from puntolisto.modelos import comercios, ordenes


CLAVES_ESPERADAS = [
    "lavanderia",
    "sastreria",
    "taller",
    "celulares",
    "relojeria",
    "tapiceria",
    "bordado",
    "otro",
]


def test_giros_tiene_los_ocho_giros_con_estructura_y_max_3_servicios():
    assert list(GIROS.keys()) == CLAVES_ESPERADAS
    for clave, info in GIROS.items():
        assert isinstance(info["nombre"], str) and info["nombre"]
        voc = info["vocabulario"]
        for termino in ("orden", "ordenes", "articulo", "articulos", "verbo_recoger"):
            assert isinstance(voc[termino], str) and voc[termino], f"Falta {termino} en {clave}"
        assert isinstance(info["placeholder_descripcion"], str) and info["placeholder_descripcion"]
        servicios = info["servicios_ejemplo"]
        assert 1 <= len(servicios) <= 3, f"{clave} tiene {len(servicios)} servicios (máx. 3)"
        for nombre, tipo_cobro, precio in servicios:
            assert nombre
            assert tipo_cobro in {"kilo", "pieza", "ajuste"}
            assert precio > 0
        assert "{nombre}" in info["mensaje_whatsapp"]
        assert "{folio}" in info["mensaje_whatsapp"]
        assert "{negocio}" in info["mensaje_whatsapp"]


def test_lista_giros_deja_otro_al_final():
    pares = lista_giros()
    assert len(pares) == 8
    assert pares[-1] == ("otro", "Otro")


def test_obtener_giro_con_clave_inexistente_devuelve_otro():
    assert obtener_giro("inexistente") == GIROS["otro"]
    assert obtener_giro(None) == GIROS["otro"]
    assert obtener_giro("") == GIROS["otro"]
    assert obtener_giro("celulares") == GIROS["celulares"]


@pytest.mark.parametrize("clave", CLAVES_ESPERADAS)
def test_giro_valido_acepta_los_ocho(clave):
    assert giro_valido(clave) is True


@pytest.mark.parametrize("invalido", ["", "panaderia", "LAVANDERIA", None])
def test_giro_valido_rechaza_invalidos(invalido):
    assert giro_valido(invalido) is False


@pytest.mark.parametrize("giro", ["lavanderia", "sastreria"])
def test_mensaje_whatsapp_lavanderia_y_sastreria_identico_al_anterior(giro):
    esperado = (
        "Hola María, te escribimos de Lavandería Estrella. "
        "Tu orden LAV-0001 ya está lista. "
        "Puedes pasar a recogerla cuando gustes. ¡Gracias por tu preferencia!"
    )
    assert mensaje_listo("María López", "LAV-0001", "Lavandería Estrella", giro=giro) == esperado


@pytest.mark.parametrize("giro", ["taller", "celulares", "relojeria", "tapiceria", "bordado", "otro"])
def test_cada_giro_nuevo_genera_enlace_wa_me_valido_y_codificado(giro):
    orden = {
        "folio": "CEL-0007",
        "clientes": {"nombre": "Juan Pérez", "telefono": "529931234567"},
    }
    url = enlace_orden_lista(orden, "TecnoFix", giro=giro)
    assert url is not None
    assert url.startswith("https://wa.me/529931234567?text=")
    query = url.split("?text=", 1)[1]
    assert " " not in query  # codificado con quote
    decodificado = urllib.parse.unquote(query)
    assert "Juan" in decodificado
    assert "CEL-0007" in decodificado
    assert "TecnoFix" in decodificado


def test_configurar_negocio_con_giro_nuevo_carga_sus_servicios_ejemplo(cliente, monkeypatch):
    iniciar_sesion(cliente)
    monkeypatch.setattr("puntolisto.modelos.comercios.obtener_mi_comercio", lambda sb, uid: None)

    tablas_insertadas = {}

    class TablaFalsa:
        def __init__(self, nombre_tabla):
            self.nombre_tabla = nombre_tabla

        def insert(self, payload):
            tablas_insertadas[self.nombre_tabla] = payload
            return self

        def execute(self):
            if self.nombre_tabla == "comercios":
                fila = {"id": 42, **tablas_insertadas["comercios"]}
                return SimpleNamespace(data=[fila])
            return SimpleNamespace(data=tablas_insertadas.get(self.nombre_tabla, []))

    sb_falso = SimpleNamespace(table=lambda nombre: TablaFalsa(nombre))
    monkeypatch.setattr("puntolisto.auth.sesion.cliente_actual", lambda: sb_falso)

    respuesta = cliente.post("/negocio/configurar", data={
        "csrf_token": "csrf-pruebas",
        "nombre": "Cell Express",
        "abreviatura": "CEL",
        "giro": "celulares",
        "giro_otro": "Texto que debe ignorarse",
        "telefono": "9931234567",
    })
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/")
    assert tablas_insertadas["comercios"]["giro"] == "celulares"
    assert tablas_insertadas["comercios"]["giro_otro"] is None
    servicios_creados = tablas_insertadas["servicios"]
    assert len(servicios_creados) == 3
    nombres = [s["nombre"] for s in servicios_creados]
    assert nombres == [s[0] for s in GIROS["celulares"]["servicios_ejemplo"]]


def test_configurar_negocio_con_otro_guarda_giro_otro_y_valida_longitud(cliente, monkeypatch):
    iniciar_sesion(cliente)
    monkeypatch.setattr("puntolisto.modelos.comercios.obtener_mi_comercio", lambda sb, uid: None)

    # Más de 40 caracteres se rechaza
    resp_largo = cliente.post("/negocio/configurar", data={
        "csrf_token": "csrf-pruebas",
        "nombre": "Mi Negocio",
        "abreviatura": "MIN",
        "giro": "otro",
        "giro_otro": "x" * 41,
    })
    assert "40 caracteres" in resp_largo.get_data(as_text=True)

    # Con 40 caracteres o menos se guarda en giro_otro
    guardado = {}

    def crear_falso(sb, usuario_id, nombre, abreviatura, giro, telefono, giro_otro=None):
        guardado.update(giro=giro, giro_otro=giro_otro)
        return {"id": 1}

    monkeypatch.setattr("puntolisto.modelos.comercios.crear", crear_falso)
    resp_ok = cliente.post("/negocio/configurar", data={
        "csrf_token": "csrf-pruebas",
        "nombre": "Calzado Don Pepe",
        "abreviatura": "CAL",
        "giro": "otro",
        "giro_otro": "Reparación de calzado",
    })
    assert resp_ok.status_code == 302
    assert guardado == {"giro": "otro", "giro_otro": "Reparación de calzado"}


def test_descripcion_orden_200_se_acepta_201_se_rechaza_y_vacia_funciona(cliente, monkeypatch):
    iniciar_sesion(cliente)
    comercio_cel = {"id": 1, "nombre": "Cell Express", "abreviatura": "CEL",
                    "giro": "celulares", "giro_otro": None, "telefono": None}
    catalogo = [{"id": 3, "nombre": "Cambio de pantalla", "tipo_cobro": "pieza", "precio": 850, "activo": True}]
    clientes_lista = [{"id": 7, "nombre": "María López", "telefono": "529931234567"}]

    monkeypatch.setattr("puntolisto.modelos.comercios.obtener_mi_comercio", lambda sb, uid: comercio_cel)
    monkeypatch.setattr("puntolisto.modelos.servicios.listar", lambda sb, cid, solo_activos=False: catalogo)
    monkeypatch.setattr("puntolisto.modelos.clientes.listar", lambda sb, cid, busqueda="", limite=200: clientes_lista)

    recibido = {}

    def crear_falso(sb, **datos):
        recibido.clear()
        recibido.update(datos)
        return {"id": 10, "folio": "CEL-0001"}

    monkeypatch.setattr("puntolisto.modelos.ordenes.crear", crear_falso)

    # 1) 201 caracteres se rechaza
    desc_201 = "a" * 201
    resp_201 = cliente.post("/ordenes/nueva", data={
        "csrf_token": "csrf-pruebas", "cliente_id": "7", "cantidad_3": "1",
        "descripcion": desc_201,
    })
    assert "200 caracteres" in resp_201.get_data(as_text=True)

    # 2) 200 caracteres exactos se acepta
    desc_200 = "b" * 200
    resp_200 = cliente.post("/ordenes/nueva", data={
        "csrf_token": "csrf-pruebas", "cliente_id": "7", "cantidad_3": "1",
        "descripcion": desc_200,
    })
    assert resp_200.status_code == 302
    assert recibido["descripcion"] == desc_200

    # 3) Sin descripción sigue funcionando igual
    resp_vacia = cliente.post("/ordenes/nueva", data={
        "csrf_token": "csrf-pruebas", "cliente_id": "7", "cantidad_3": "1",
        "descripcion": "   ",
    })
    assert resp_vacia.status_code == 302
    assert "descripcion" not in recibido


def test_modelo_ordenes_crear_envia_p_descripcion_al_rpc():
    enviado = {}

    class RpcFalso:
        def __init__(self, fn, params):
            enviado["fn"] = fn
            enviado["params"] = params

        def execute(self):
            return SimpleNamespace(data=[{"id": 10, "folio": "CEL-0001"}])

    sb_falso = SimpleNamespace(rpc=lambda fn, params: RpcFalso(fn, params))
    ordenes.crear(
        sb_falso,
        cliente_id=7,
        servicios=[{"servicio_id": 3, "cantidad": 1}],
        fecha_entrega="2026-11-05",
        notas="Con funda",
        descripcion="Samsung A54 negro",
    )
    assert enviado["fn"] == "crear_orden"
    assert enviado["params"]["p_descripcion"] == "Samsung A54 negro"


def test_vocabulario_cambia_segun_giro_y_muestra_descripcion_en_tarjeta_y_detalle(cliente, monkeypatch):
    iniciar_sesion(cliente)
    comercio_cel = {"id": 1, "nombre": "Cell Express", "abreviatura": "CEL",
                    "giro": "celulares", "giro_otro": None, "telefono": None}
    monkeypatch.setattr("puntolisto.modelos.comercios.obtener_mi_comercio", lambda sb, uid: comercio_cel)
    monkeypatch.setattr("puntolisto.modelos.servicios.listar",
                        lambda sb, cid, solo_activos=False: [{"id": 3, "nombre": "Diagnóstico", "tipo_cobro": "ajuste", "precio": 150, "activo": True}])
    monkeypatch.setattr("puntolisto.modelos.clientes.listar",
                        lambda sb, cid, busqueda="", limite=200: [{"id": 7, "nombre": "María", "telefono": "529931234567"}])

    # Formulario de nueva orden usa vocabulario de celulares ("Nueva reparación") y su placeholder
    html_nueva = cliente.get("/ordenes/nueva").get_data(as_text=True)
    assert "Nueva reparación" in html_nueva
    assert "Registrar reparación" in html_nueva
    assert "Samsung A14" in html_nueva

    # Detalle de orden muestra "¿Qué dejó?" cuando hay descripción, y la omite cuando es None
    orden_con_desc = {
        "id": 10, "folio": "CEL-0001", "estado": "recibido", "fecha_entrega": "2026-11-05",
        "descripcion": "iPhone 13 azul, pantalla estrellada", "notas": None,
        "creado_en": "2026-10-30T18:00:00+00:00", "actualizado_en": "2026-10-30T18:00:00+00:00",
        "clientes": {"id": 7, "nombre": "María", "telefono": "529931234567"},
        "orden_servicios": [{"id": 1, "cantidad": 1, "precio_unitario": 150,
                             "servicios": {"nombre": "Diagnóstico", "tipo_cobro": "ajuste"}}],
    }
    monkeypatch.setattr("puntolisto.modelos.ordenes.obtener_detalle", lambda sb, cid, oid: orden_con_desc)
    html_detalle = cliente.get("/ordenes/10").get_data(as_text=True)
    assert "Reparación CEL-0001" in html_detalle
    assert "¿Qué dejó?" in html_detalle
    assert "iPhone 13 azul, pantalla estrellada" in html_detalle

    monkeypatch.setattr("puntolisto.modelos.ordenes.listar", lambda sb, *a, **kw: [orden_con_desc])
    html_lista = cliente.get("/ordenes/").get_data(as_text=True)
    assert "descripcion-corta" in html_lista
    assert "iPhone 13 azul, pantalla estrellada" in html_lista

    orden_sin_desc = {**orden_con_desc, "descripcion": None}
    monkeypatch.setattr("puntolisto.modelos.ordenes.obtener_detalle", lambda sb, cid, oid: orden_sin_desc)
    html_detalle_sin = cliente.get("/ordenes/10").get_data(as_text=True)
    assert "¿Qué dejó?" not in html_detalle_sin

    monkeypatch.setattr("puntolisto.modelos.ordenes.listar", lambda sb, *a, **kw: [orden_sin_desc])
    html_lista_sin = cliente.get("/ordenes/").get_data(as_text=True)
    assert "descripcion-corta" not in html_lista_sin
