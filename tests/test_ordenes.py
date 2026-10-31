"""Pruebas de órdenes, estados y aviso (ACT-15, 17 y 18) simulando Supabase."""
import re

import pytest
from postgrest.exceptions import APIError

from conftest import iniciar_sesion

COMERCIO = {"id": 1, "nombre": "Lavandería Ana", "abreviatura": "LAV",
            "giro": "lavanderia", "telefono": None}
CATALOGO = [
    {"id": 3, "nombre": "Lavado por kilo", "tipo_cobro": "kilo", "precio": 30, "activo": True},
    {"id": 5, "nombre": "Planchado", "tipo_cobro": "pieza", "precio": 15, "activo": True},
]
CLIENTES = [{"id": 7, "nombre": "María López", "telefono": "529931234567"}]


def orden_detalle(estado="recibido", telefono="529931234567"):
    return {
        "id": 10, "folio": "LAV-0001", "estado": estado, "fecha_entrega": "2026-11-05",
        "notas": "Sin suavizante", "creado_en": "2026-10-30T18:00:00+00:00",
        "actualizado_en": "2026-10-30T18:00:00+00:00",
        "clientes": {"id": 7, "nombre": "María López", "telefono": telefono},
        "orden_servicios": [{"id": 1, "cantidad": 3.5, "precio_unitario": 30,
                             "servicios": {"nombre": "Lavado por kilo", "tipo_cobro": "kilo"}}],
    }


@pytest.fixture
def con_negocio(cliente, monkeypatch):
    iniciar_sesion(cliente)
    monkeypatch.setattr("puntolisto.modelos.comercios.obtener_mi_comercio", lambda sb, uid: COMERCIO)
    monkeypatch.setattr("puntolisto.modelos.servicios.listar",
                        lambda sb, cid, solo_activos=False: CATALOGO)
    monkeypatch.setattr("puntolisto.modelos.clientes.listar",
                        lambda sb, cid, busqueda="", limite=200: CLIENTES)
    return cliente


# ------------------------------------------------------------ nueva orden
def test_formulario_muestra_clientes_y_servicios(con_negocio):
    texto = con_negocio.get("/ordenes/nueva?cliente_id=7").get_data(as_text=True)
    assert "María López" in texto and "Lavado por kilo" in texto and "Planchado" in texto
    assert re.search(r'value="7"\s+checked', texto)  # viene de "+ Cliente nuevo"


def test_crear_orden(con_negocio, monkeypatch):
    recibido = {}

    def crear_falso(sb, **datos):
        recibido.update(datos)
        return {"id": 10, "folio": "LAV-0001"}

    monkeypatch.setattr("puntolisto.modelos.ordenes.crear", crear_falso)
    respuesta = con_negocio.post("/ordenes/nueva", data={
        "csrf_token": "csrf-pruebas", "cliente_id": "7",
        "cantidad_3": "3,5", "cantidad_5": "", "fecha_entrega": "2026-11-05", "notas": " Sin suavizante "})
    assert respuesta.headers["Location"].endswith("/ordenes/10")
    assert recibido == {"cliente_id": 7, "servicios": [{"servicio_id": 3, "cantidad": 3.5}],
                        "fecha_entrega": "2026-11-05", "notas": "Sin suavizante"}


@pytest.mark.parametrize("datos, mensaje", [
    ({"cliente_id": "", "cantidad_3": "2"}, "Elige el cliente"),
    ({"cliente_id": "999", "cantidad_3": "2"}, "Elige el cliente"),  # cliente de otro negocio
    ({"cliente_id": "7"}, "al menos un servicio"),
    ({"cliente_id": "7", "cantidad_5": "1.5"}, "número entero"),       # pieza con decimales
    ({"cliente_id": "7", "cantidad_3": "0"}, "mayor que 0"),
    ({"cliente_id": "7", "cantidad_3": "dos"}, "mayor que 0"),
    ({"cliente_id": "7", "cantidad_3": "2", "fecha_entrega": "31-12-2026"}, "fecha de entrega no es válida"),
])
def test_orden_invalida(con_negocio, datos, mensaje):
    texto = con_negocio.post("/ordenes/nueva", data={"csrf_token": "csrf-pruebas", **datos}
                             ).get_data(as_text=True)
    assert mensaje in texto


def test_orden_invalida_conserva_lo_escrito(con_negocio):
    texto = con_negocio.post("/ordenes/nueva", data={
        "csrf_token": "csrf-pruebas", "cliente_id": "7", "cantidad_3": "4", "cantidad_5": "1.5",
        "notas": "Urgente"}).get_data(as_text=True)
    assert 'value="4"' in texto and "Urgente" in texto and re.search(r'value="7"\s+checked', texto)


def test_error_de_la_base_al_crear(con_negocio, monkeypatch):
    def crear_falso(sb, **_d):
        raise APIError({"code": "P0001", "message": "Uno o más servicios no existen", "details": "", "hint": ""})
    monkeypatch.setattr("puntolisto.modelos.ordenes.crear", crear_falso)
    texto = con_negocio.post("/ordenes/nueva", data={
        "csrf_token": "csrf-pruebas", "cliente_id": "7", "cantidad_3": "2"}).get_data(as_text=True)
    assert "No se pudo registrar la orden" in texto


def test_sin_servicios_activos(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.servicios.listar", lambda sb, cid, solo_activos=False: [])
    assert "No tienes servicios activos" in con_negocio.get("/ordenes/nueva").get_data(as_text=True)


# ---------------------------------------------------------------- detalle
def test_detalle_recibida_sin_boton_whatsapp(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.ordenes.obtener_detalle", lambda sb, cid, oid: orden_detalle())
    texto = con_negocio.get("/ordenes/10").get_data(as_text=True)
    assert "LAV-0001" in texto and "3.5 kg" in texto and "05/11/2026" in texto
    assert "Marcar como «En proceso»" in texto
    assert "wa.me" not in texto


def test_detalle_lista_muestra_boton_whatsapp(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.ordenes.obtener_detalle",
                        lambda sb, cid, oid: orden_detalle("listo"))
    texto = con_negocio.get("/ordenes/10").get_data(as_text=True)
    assert 'href="https://wa.me/529931234567?text=' in texto
    assert "Avisar por WhatsApp" in texto
    assert "Marcar como «Entregado»" in texto
    assert "Regresar a «En proceso»" in texto


def test_detalle_entregada_sin_botones_de_avance(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.ordenes.obtener_detalle",
                        lambda sb, cid, oid: orden_detalle("entregado"))
    texto = con_negocio.get("/ordenes/10").get_data(as_text=True)
    assert "Marcar como" not in texto and "wa.me" not in texto


def test_detalle_ajeno_da_404(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.ordenes.obtener_detalle", lambda sb, cid, oid: None)
    assert con_negocio.get("/ordenes/99").status_code == 404


# ---------------------------------------------------------------- estados
def test_marcar_lista_invita_a_avisar(con_negocio, monkeypatch):
    recibido = {}

    def cambiar_falso(sb, cid, oid, estado):
        recibido.update(oid=oid, estado=estado)
        return {"id": oid, "folio": "LAV-0001", "estado": estado}

    monkeypatch.setattr("puntolisto.modelos.ordenes.cambiar_estado", cambiar_falso)
    monkeypatch.setattr("puntolisto.modelos.ordenes.obtener_detalle",
                        lambda sb, cid, oid: orden_detalle("listo"))
    respuesta = con_negocio.post("/ordenes/10/estado", data={"csrf_token": "csrf-pruebas", "estado": "listo"},
                                 follow_redirects=True)
    assert recibido == {"oid": 10, "estado": "listo"}
    assert "Ahora avisa al cliente por WhatsApp" in respuesta.get_data(as_text=True)


def test_estado_invalido_da_400(con_negocio):
    assert con_negocio.post("/ordenes/10/estado",
                            data={"csrf_token": "csrf-pruebas", "estado": "perdido"}).status_code == 400


def test_estado_de_orden_ajena_da_404(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.ordenes.cambiar_estado", lambda sb, cid, oid, e: None)
    assert con_negocio.post("/ordenes/99/estado",
                            data={"csrf_token": "csrf-pruebas", "estado": "listo"}).status_code == 404


def test_entregadas_redirige_al_filtro(con_negocio):
    respuesta = con_negocio.get("/ordenes/entregadas")
    assert respuesta.headers["Location"].endswith("/ordenes/?estado=entregado")


def test_secuencia_de_estados():
    from puntolisto.modelos import ordenes
    assert ordenes.siguiente_estado("recibido") == "en_proceso"
    assert ordenes.siguiente_estado("listo") == "entregado"
    assert ordenes.siguiente_estado("entregado") is None
    assert ordenes.estado_anterior("recibido") is None
    assert ordenes.estado_anterior("listo") == "en_proceso"
