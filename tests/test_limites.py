"""Pruebas de los límites reales del plan gratuito (ACT-25)."""
from datetime import date

import pytest

from conftest import iniciar_sesion
from puntolisto import planes
from puntolisto.modelos import clientes as mod_clientes
from puntolisto.modelos import ordenes as mod_ordenes
from puntolisto.modelos import servicios as mod_servicios

# Referencias originales antes del autouse de conftest
_contar_clientes_real = mod_clientes.contar
_contar_ordenes_real = mod_ordenes.contar_mes_actual
_contar_servicios_real = mod_servicios.contar_activos

COMERCIO = {"id": 1, "nombre": "Lavandería Ana", "abreviatura": "LAV",
            "giro": "lavanderia", "telefono": "529930000000"}
CATALOGO = [{"id": 3, "nombre": "Lavado por kilo", "tipo_cobro": "kilo", "precio": 30, "activo": True}]
CLIENTES = [{"id": 7, "nombre": "María López", "telefono": "529931234567"}]


@pytest.fixture
def con_negocio(cliente, monkeypatch):
    iniciar_sesion(cliente)
    monkeypatch.setattr("puntolisto.modelos.comercios.obtener_mi_comercio", lambda sb, uid: COMERCIO)
    monkeypatch.setattr("puntolisto.modelos.servicios.listar", lambda sb, cid, solo_activos=False: CATALOGO)
    monkeypatch.setattr("puntolisto.modelos.clientes.listar", lambda sb, cid, busqueda="", limite=200: CLIENTES)
    return cliente


# ---------------------------------------------------------- clientes (14 vs 15)
def test_clientes_en_14_permite_y_en_15_bloquea(con_negocio, monkeypatch):
    creados = []
    monkeypatch.setattr("puntolisto.modelos.clientes.crear",
                        lambda sb, cid, n, t: creados.append((n, t)) or {"id": 15, "nombre": n, "telefono": t})

    # Con 14 clientes (debajo del límite de 15): permite crear el 15
    monkeypatch.setattr("puntolisto.modelos.clientes.contar", lambda sb, cid: 14)
    r1 = con_negocio.post("/clientes/nuevo", data={
        "csrf_token": "csrf-pruebas", "nombre": "Pedro Infante", "telefono": "9931112233"})
    assert r1.status_code == 302
    assert len(creados) == 1

    # Con 15 clientes (en el límite): bloquea y muestra mensaje amable con botón a /planes
    monkeypatch.setattr("puntolisto.modelos.clientes.contar", lambda sb, cid: 15)
    r2 = con_negocio.post("/clientes/nuevo", data={
        "csrf_token": "csrf-pruebas", "nombre": "Otro Cliente", "telefono": "9934445566"})
    texto = r2.get_data(as_text=True)
    assert len(creados) == 1  # NO se llamó a clientes.crear
    assert "Llegaste a tus 15 clientes en Punto de Partida. Con Punto Fuerte puedes registrar hasta 30." in texto
    assert 'href="/planes"' in texto and "Ver planes" in texto


# ----------------------------------------------------------- órdenes (49 vs 50)
def test_ordenes_en_49_permite_y_en_50_bloquea_antes_del_rpc(con_negocio, monkeypatch):
    llamadas_rpc = []
    monkeypatch.setattr("puntolisto.modelos.ordenes.crear",
                        lambda sb, **d: llamadas_rpc.append(d) or {"id": 50, "folio": "LAV-0050"})

    # Con 49 órdenes este mes: permite crear la orden 50
    monkeypatch.setattr("puntolisto.modelos.ordenes.contar_mes_actual", lambda sb, cid, hoy=None: 49)
    r1 = con_negocio.post("/ordenes/nueva", data={
        "csrf_token": "csrf-pruebas", "cliente_id": "7", "cantidad_3": "2"})
    assert r1.status_code == 302 and len(llamadas_rpc) == 1

    # Con 50 órdenes este mes: bloquea ANTES de llamar a crear_orden
    monkeypatch.setattr("puntolisto.modelos.ordenes.contar_mes_actual", lambda sb, cid, hoy=None: 50)
    r2 = con_negocio.post("/ordenes/nueva", data={
        "csrf_token": "csrf-pruebas", "cliente_id": "7", "cantidad_3": "2"})
    texto = r2.get_data(as_text=True)
    assert len(llamadas_rpc) == 1  # NO se volvió a llamar a ordenes.crear
    assert "Llegaste a tus 50 órdenes de este mes en Punto de Partida. Con Punto Fuerte puedes registrar hasta 150." in texto
    assert 'href="/planes"' in texto and "Ver planes" in texto


# ---------------------------------------------------------- servicios (4 vs 5)
def test_servicios_en_4_permite_y_en_5_bloquea_crear_y_reactivar(con_negocio, monkeypatch):
    creados = []
    cambios_activo = []
    monkeypatch.setattr("puntolisto.modelos.servicios.crear",
                        lambda sb, cid, **d: creados.append(d) or d)
    monkeypatch.setattr("puntolisto.modelos.servicios.cambiar_activo",
                        lambda sb, cid, sid, act: cambios_activo.append((sid, act)) or {"id": sid, "nombre": "S", "activo": act})

    # Con 4 servicios activos: permite crear el 5to y reactivar
    monkeypatch.setattr("puntolisto.modelos.servicios.contar_activos", lambda sb, cid: 4)
    r1 = con_negocio.post("/negocio/catalogo/nuevo", data={
        "csrf_token": "csrf-pruebas", "nombre": "Tintorería", "tipo_cobro": "pieza", "precio": "80"})
    assert r1.status_code == 302 and len(creados) == 1

    con_negocio.post("/negocio/catalogo/4/activo", data={"csrf_token": "csrf-pruebas", "activo": "1"})
    assert cambios_activo == [(4, True)]

    # Con 5 servicios activos: bloquea crear nuevo y bloquea reactivar (activo=1)
    monkeypatch.setattr("puntolisto.modelos.servicios.contar_activos", lambda sb, cid: 5)
    r2 = con_negocio.post("/negocio/catalogo/nuevo", data={
        "csrf_token": "csrf-pruebas", "nombre": "Planchado fino", "tipo_cobro": "pieza", "precio": "40"})
    texto = r2.get_data(as_text=True)
    assert len(creados) == 1
    assert "Llegaste a tus 5 servicios activos en Punto de Partida. Con Punto Fuerte puedes tener hasta 10." in texto

    r3 = con_negocio.post("/negocio/catalogo/4/activo",
                          data={"csrf_token": "csrf-pruebas", "activo": "1"}, follow_redirects=True)
    assert cambios_activo == [(4, True)]  # no se permitió reactivar
    assert "Llegaste a tus 5 servicios activos" in r3.get_data(as_text=True)

    # Desactivar (activo=0) NUNCA se bloquea aunque haya 5 activos
    con_negocio.post("/negocio/catalogo/3/activo", data={"csrf_token": "csrf-pruebas", "activo": "0"})
    assert cambios_activo[-1] == (3, False)


# ----------------------------------------- reinicio de órdenes al mes siguiente
def test_conteo_de_ordenes_vuelve_a_cero_el_mes_siguiente():
    ordenes_noviembre = [
        {"id": i, "creado_en": "2026-11-15T18:00:00-06:00"} for i in range(1, 51)
    ]

    class TablaFalsa:
        def select(self, *_a, **_k): return self
        def eq(self, *_a, **_k): return self
        def gte(self, *_a, **_k): return self
        def lt(self, *_a, **_k): return self
        def execute(self):
            return type("R", (), {"data": ordenes_noviembre, "count": None})()

    sb = type("SB", (), {"table": lambda self, _t: TablaFalsa()})()

    assert _contar_ordenes_real(sb, 1, hoy=date(2026, 11, 30)) == 50
    assert _contar_ordenes_real(sb, 1, hoy=date(2026, 12, 1)) == 0


def test_repositorios_contar_clientes_y_servicios():
    class TablaConCount:
        def __init__(self, n): self.n = n
        def select(self, *_a, **_k): return self
        def eq(self, *_a, **_k): return self
        def execute(self): return type("R", (), {"data": [], "count": self.n})()

    sb_c = type("SB", (), {"table": lambda self, _t: TablaConCount(14)})()
    sb_s = type("SB", (), {"table": lambda self, _t: TablaConCount(3)})()
    assert _contar_clientes_real(sb_c, 1) == 14
    assert _contar_servicios_real(sb_s, 1) == 3


# ------------------------------- acciones sobre lo existente nunca se bloquean
def test_acciones_sobre_existentes_nunca_se_bloquean_en_el_limite(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.clientes.contar", lambda sb, cid: 15)
    monkeypatch.setattr("puntolisto.modelos.ordenes.contar_mes_actual", lambda sb, cid, hoy=None: 50)
    monkeypatch.setattr("puntolisto.modelos.servicios.contar_activos", lambda sb, cid: 3)

    # 1. Editar cliente existente
    monkeypatch.setattr("puntolisto.modelos.clientes.obtener",
                        lambda sb, cid, id_: {"id": 7, "nombre": "María", "telefono": "529931234567"})
    monkeypatch.setattr("puntolisto.modelos.clientes.actualizar",
                        lambda sb, cid, id_, n, t: {"id": id_, "nombre": n, "telefono": t})
    assert con_negocio.post("/clientes/7/editar", data={
        "csrf_token": "csrf-pruebas", "nombre": "María Editada", "telefono": "9931234567"}).status_code == 302

    # 2. Editar servicio existente
    monkeypatch.setattr("puntolisto.modelos.servicios.obtener", lambda sb, cid, sid: CATALOGO[0])
    monkeypatch.setattr("puntolisto.modelos.servicios.actualizar", lambda sb, cid, sid, **d: d)
    assert con_negocio.post("/negocio/catalogo/3/editar", data={
        "csrf_token": "csrf-pruebas", "nombre": "Lavado", "tipo_cobro": "kilo", "precio": "35"}).status_code == 302

    # 3. Ver detalle de orden, cambiar estado y ver enlace de WhatsApp
    orden_lista = {
        "id": 10, "folio": "LAV-0010", "estado": "listo", "fecha_entrega": "2026-11-15",
        "notas": None, "creado_en": "2026-11-10T15:00:00+00:00",
        "actualizado_en": "2026-11-10T15:00:00+00:00",
        "clientes": {"id": 7, "nombre": "María López", "telefono": "529931234567"},
        "orden_servicios": [{"id": 1, "cantidad": 2, "precio_unitario": 30,
                             "servicios": {"nombre": "Lavado", "tipo_cobro": "kilo"}}],
    }
    monkeypatch.setattr("puntolisto.modelos.ordenes.obtener_detalle", lambda sb, cid, oid: orden_lista)
    monkeypatch.setattr("puntolisto.modelos.ordenes.cambiar_estado",
                        lambda sb, cid, oid, est: {"id": oid, "folio": "LAV-0010", "estado": est})

    detalle_html = con_negocio.get("/ordenes/10").get_data(as_text=True)
    assert "Avisar por WhatsApp" in detalle_html and "https://wa.me/529931234567" in detalle_html
    assert con_negocio.post("/ordenes/10/estado", data={
        "csrf_token": "csrf-pruebas", "estado": "entregado"}).status_code == 302


# ------------------------------------------------------------ medidores de uso
def test_medidores_en_ajustes_y_panel_cambian_texto_al_80_por_ciento(con_negocio, monkeypatch):
    # Debajo del 80 % (38 de 50 = 76 %)
    monkeypatch.setattr("puntolisto.modelos.ordenes.contar_mes_actual", lambda sb, cid, hoy=None: 38)
    monkeypatch.setattr("puntolisto.modelos.clientes.contar", lambda sb, cid: 8)
    monkeypatch.setattr("puntolisto.modelos.servicios.contar_activos", lambda sb, cid: 2)

    ajustes_38 = con_negocio.get("/negocio/ajustes").get_data(as_text=True)
    assert "Órdenes este mes: 38 de 50" in ajustes_38
    assert "Clientes: 8 de 15" in ajustes_38
    assert "Servicios activos: 2 de 5" in ajustes_38

    # En o arriba del 80 % (40 de 50 -> quedan 10; 4 de 5 -> queda 1)
    monkeypatch.setattr("puntolisto.modelos.ordenes.contar_mes_actual", lambda sb, cid, hoy=None: 40)
    monkeypatch.setattr("puntolisto.modelos.clientes.contar", lambda sb, cid: 13)
    monkeypatch.setattr("puntolisto.modelos.servicios.contar_activos", lambda sb, cid: 5)

    ajustes_40 = con_negocio.get("/negocio/ajustes").get_data(as_text=True)
    assert "Te quedan 10 órdenes este mes" in ajustes_40
    assert "Te quedan 2 clientes" in ajustes_40
    assert "Te quedan 0 servicios activos" in ajustes_40

    monkeypatch.setattr("puntolisto.modelos.ordenes.listar_activas", lambda sb, cid: [])
    panel_40 = con_negocio.get("/").get_data(as_text=True)
    assert "Te quedan 10 órdenes este mes" in panel_40


def test_exencion_opcional_para_cuentas_demo(monkeypatch):
    monkeypatch.setattr(planes, "SALTAR_LIMITES_EN_DEMO", True)
    assert not planes.limite_alcanzado("servicios", 6, "lavanderia@puntolisto.demo")
    assert planes.limite_alcanzado("servicios", 6, "otro@negocio.mx")
