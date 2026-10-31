"""Pruebas del catálogo de servicios (ACT-14) simulando Supabase."""
import pytest
from postgrest.exceptions import APIError

from conftest import iniciar_sesion

COMERCIO = {"id": 1, "nombre": "Lavandería Ana", "abreviatura": "LAV",
            "giro": "lavanderia", "telefono": None}
LAVADO = {"id": 3, "nombre": "Lavado por kilo", "tipo_cobro": "kilo", "precio": 30, "activo": True}
EDREDON = {"id": 4, "nombre": "Edredón", "tipo_cobro": "pieza", "precio": 120, "activo": False}


@pytest.fixture
def con_negocio(cliente, monkeypatch):
    iniciar_sesion(cliente)
    monkeypatch.setattr("puntolisto.modelos.comercios.obtener_mi_comercio", lambda sb, uid: COMERCIO)
    return cliente


def test_catalogo_lista_activos_e_inactivos(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.servicios.listar", lambda sb, cid: [LAVADO, EDREDON])
    texto = con_negocio.get("/negocio/catalogo").get_data(as_text=True)
    assert "Lavado por kilo" in texto and "Por kilo · $30.00" in texto
    assert "Desactivado" in texto and "Activar" in texto and "Desactivar" in texto


def test_nuevo_servicio(con_negocio, monkeypatch):
    guardado = {}
    monkeypatch.setattr("puntolisto.modelos.servicios.crear",
                        lambda sb, cid, **datos: guardado.update(datos) or datos)
    respuesta = con_negocio.post("/negocio/catalogo/nuevo", data={
        "csrf_token": "csrf-pruebas", "nombre": " Planchado  express ", "tipo_cobro": "pieza",
        "precio": "$22,50"})
    assert respuesta.headers["Location"].endswith("/negocio/catalogo")
    assert guardado == {"nombre": "Planchado express", "tipo_cobro": "pieza", "precio": 22.5}


@pytest.mark.parametrize("datos, mensaje", [
    ({"nombre": "X", "tipo_cobro": "kilo", "precio": "10"}, "entre 2 y 80"),
    ({"nombre": "Lavado", "tipo_cobro": "litro", "precio": "10"}, "Elige cómo se cobra"),
    ({"nombre": "Lavado", "tipo_cobro": "kilo", "precio": "-5"}, "precio válido"),
    ({"nombre": "Lavado", "tipo_cobro": "kilo", "precio": "abc"}, "precio válido"),
])
def test_servicio_invalido(con_negocio, datos, mensaje):
    texto = con_negocio.post("/negocio/catalogo/nuevo",
                             data={"csrf_token": "csrf-pruebas", **datos}).get_data(as_text=True)
    assert mensaje in texto


def test_servicio_nombre_repetido(con_negocio, monkeypatch):
    def crear_falso(*_a, **_k):
        raise APIError({"code": "23505", "message": "duplicado", "details": "", "hint": ""})
    monkeypatch.setattr("puntolisto.modelos.servicios.crear", crear_falso)
    texto = con_negocio.post("/negocio/catalogo/nuevo", data={
        "csrf_token": "csrf-pruebas", "nombre": "Lavado", "tipo_cobro": "kilo", "precio": "30"}
    ).get_data(as_text=True)
    assert "Ya tienes un servicio con ese nombre." in texto


def test_editar_servicio(con_negocio, monkeypatch):
    guardado = {}
    monkeypatch.setattr("puntolisto.modelos.servicios.obtener", lambda sb, cid, sid: LAVADO)
    monkeypatch.setattr("puntolisto.modelos.servicios.actualizar",
                        lambda sb, cid, sid, **d: guardado.update(sid=sid, **d))
    assert 'value="30"' in con_negocio.get("/negocio/catalogo/3/editar").get_data(as_text=True)
    con_negocio.post("/negocio/catalogo/3/editar", data={
        "csrf_token": "csrf-pruebas", "nombre": "Lavado por kilo", "tipo_cobro": "kilo", "precio": "32"})
    assert guardado == {"sid": 3, "nombre": "Lavado por kilo", "tipo_cobro": "kilo", "precio": 32.0}


def test_desactivar_servicio(con_negocio, monkeypatch):
    recibido = {}

    def cambiar_falso(sb, cid, sid, activo):
        recibido.update(sid=sid, activo=activo)
        return {**LAVADO, "activo": activo}

    monkeypatch.setattr("puntolisto.modelos.servicios.cambiar_activo", cambiar_falso)
    respuesta = con_negocio.post("/negocio/catalogo/3/activo",
                                 data={"csrf_token": "csrf-pruebas", "activo": "0"})
    assert respuesta.headers["Location"].endswith("/negocio/catalogo")
    assert recibido == {"sid": 3, "activo": False}


def test_servicio_ajeno_da_404(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.servicios.obtener", lambda sb, cid, sid: None)
    assert con_negocio.get("/negocio/catalogo/99/editar").status_code == 404
