"""Pruebas del módulo de clientes (ACT-13) simulando Supabase."""
import pytest
from postgrest.exceptions import APIError

from conftest import iniciar_sesion

COMERCIO = {"id": 1, "nombre": "Lavandería Ana", "abreviatura": "LAV",
            "giro": "lavanderia", "telefono": None}
MARIA = {"id": 7, "nombre": "María López", "telefono": "529931234567", "creado_en": "2026-10-30"}


@pytest.fixture
def con_negocio(cliente, monkeypatch):
    iniciar_sesion(cliente)
    monkeypatch.setattr("puntolisto.modelos.comercios.obtener_mi_comercio",
                        lambda sb, uid: COMERCIO)
    return cliente


def error_duplicado():
    return APIError({"code": "23505", "message": "duplicate key value", "details": "", "hint": ""})


# ---------------------------------------------------------------- lista
def test_lista_muestra_clientes_con_telefono_legible(con_negocio, monkeypatch):
    recibido = {}

    def listar_falso(sb, comercio_id, busqueda=""):
        recibido.update(comercio_id=comercio_id, busqueda=busqueda)
        return [MARIA]

    monkeypatch.setattr("puntolisto.modelos.clientes.listar", listar_falso)
    texto = con_negocio.get("/clientes/?q=mar").get_data(as_text=True)
    assert "María López" in texto and "993 123 4567" in texto
    assert recibido == {"comercio_id": 1, "busqueda": "mar"}


def test_lista_vacia(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.clientes.listar", lambda sb, cid, busqueda="": [])
    assert "Aún no tienes clientes" in con_negocio.get("/clientes/").get_data(as_text=True)


def test_lista_requiere_sesion(cliente):
    assert cliente.get("/clientes/").headers["Location"].endswith("/entrar")


# ---------------------------------------------------------------- nuevo
def test_nuevo_cliente_normaliza_datos(con_negocio, monkeypatch):
    guardado = {}

    def crear_falso(sb, comercio_id, nombre, telefono):
        guardado.update(comercio_id=comercio_id, nombre=nombre, telefono=telefono)
        return {"id": 8, "nombre": nombre, "telefono": telefono}

    monkeypatch.setattr("puntolisto.modelos.clientes.crear", crear_falso)
    respuesta = con_negocio.post("/clientes/nuevo", data={
        "csrf_token": "csrf-pruebas", "nombre": "  Juan   Pérez ", "telefono": "993-123-4567"})
    assert respuesta.headers["Location"].endswith("/clientes/")
    assert guardado == {"comercio_id": 1, "nombre": "Juan Pérez", "telefono": "529931234567"}


@pytest.mark.parametrize("nombre, telefono, mensaje", [
    ("J", "9931234567", "El nombre debe tener entre 2 y 80 caracteres."),
    ("Juan", "12345", "El teléfono debe tener 10 dígitos"),
    ("Juan", "", "El teléfono debe tener 10 dígitos"),
])
def test_nuevo_cliente_invalido(con_negocio, nombre, telefono, mensaje):
    texto = con_negocio.post("/clientes/nuevo", data={
        "csrf_token": "csrf-pruebas", "nombre": nombre, "telefono": telefono}).get_data(as_text=True)
    assert mensaje in texto
    assert f'value="{nombre}"' in texto  # conserva lo escrito


def test_nuevo_cliente_telefono_repetido(con_negocio, monkeypatch):
    def crear_falso(*_args):
        raise error_duplicado()

    monkeypatch.setattr("puntolisto.modelos.clientes.crear", crear_falso)
    texto = con_negocio.post("/clientes/nuevo", data={
        "csrf_token": "csrf-pruebas", "nombre": "Juan", "telefono": "9931234567"}).get_data(as_text=True)
    assert "Ya tienes un cliente con ese teléfono." in texto


# ---------------------------------------------------------------- editar
def test_editar_muestra_datos_actuales(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.clientes.obtener", lambda sb, cid, id_: MARIA)
    texto = con_negocio.get("/clientes/7/editar").get_data(as_text=True)
    assert 'value="María López"' in texto and 'value="993 123 4567"' in texto


def test_editar_guarda_cambios(con_negocio, monkeypatch):
    guardado = {}
    monkeypatch.setattr("puntolisto.modelos.clientes.obtener", lambda sb, cid, id_: MARIA)
    monkeypatch.setattr("puntolisto.modelos.clientes.actualizar",
                        lambda sb, cid, id_, nombre, tel: guardado.update(id=id_, nombre=nombre, tel=tel))
    respuesta = con_negocio.post("/clientes/7/editar", data={
        "csrf_token": "csrf-pruebas", "nombre": "María López Cruz", "telefono": "993 765 4321"})
    assert respuesta.headers["Location"].endswith("/clientes/")
    assert guardado == {"id": 7, "nombre": "María López Cruz", "tel": "529937654321"}


def test_editar_cliente_inexistente_o_ajeno_da_404(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.clientes.obtener", lambda sb, cid, id_: None)
    respuesta = con_negocio.get("/clientes/999/editar")
    assert respuesta.status_code == 404
    assert "No encontramos eso" in respuesta.get_data(as_text=True)
