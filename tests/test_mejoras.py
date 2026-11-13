"""Pruebas del bloque 1 de mejoras: alertas, acciones rápidas, buscador,
filtros, ajustes, barra inferior y archivos de la app instalable."""
from datetime import date

import pytest

from conftest import iniciar_sesion
from puntolisto.ordenes import presentacion

HOY = date(2026, 11, 2)
COMERCIO = {"id": 1, "nombre": "Lavandería Ana", "abreviatura": "LAV",
            "giro": "lavanderia", "telefono": "529930000000"}


def orden(id_, estado, fecha=None, nombre="María López"):
    return {"id": id_, "folio": f"LAV-{id_:04d}", "estado": estado, "fecha_entrega": fecha,
            "creado_en": "2026-11-01T15:00:00+00:00", "actualizado_en": "2026-11-01T15:00:00+00:00",
            "clientes": {"nombre": nombre, "telefono": "529931234567"},
            "orden_servicios": [
                {"cantidad": 4.5, "servicios": {"nombre": "Lavado por kilo", "tipo_cobro": "kilo"}},
                {"cantidad": 1, "servicios": {"nombre": "Planchado", "tipo_cobro": "pieza"}}]}


@pytest.fixture
def con_negocio(cliente, monkeypatch):
    iniciar_sesion(cliente)
    monkeypatch.setattr("puntolisto.modelos.comercios.obtener_mi_comercio", lambda sb, uid: COMERCIO)
    monkeypatch.setattr("puntolisto.ordenes.presentacion.hoy_mexico", lambda: HOY)
    monkeypatch.setattr("puntolisto.etiquetas.hoy_mexico", lambda: HOY)
    return cliente


# ------------------------------------------------------ presentación
@pytest.mark.parametrize("estado, fecha, esperado", [
    ("recibido", "2026-11-01", "atrasada"),
    ("en_proceso", "2026-11-02", "hoy"),
    ("recibido", "2026-11-03", "manana"),
    ("recibido", "2026-11-09", None),
    ("recibido", None, None),
    ("listo", "2026-10-30", None),      # ya está lista: no es urgente para el negocio
    ("entregado", "2026-10-30", None),
])
def test_alertas(estado, fecha, esperado):
    assert presentacion.calcular_alerta(orden(1, estado, fecha), HOY) == esperado


def test_preparar_agrega_resumen_siguiente_y_whatsapp():
    lista = presentacion.preparar([orden(1, "recibido"), orden(2, "listo")], "Lavandería Ana", HOY)
    assert lista[0]["resumen"] == "Lavado por kilo 4.5 kg +1"
    assert lista[0]["siguiente"] == "en_proceso" and lista[0]["enlace_wa"] is None
    assert lista[1]["siguiente"] == "entregado"
    assert lista[1]["enlace_wa"].startswith("https://wa.me/529931234567?text=")


def test_secciones_por_prioridad():
    lista = presentacion.preparar([
        orden(1, "recibido", "2026-11-08"), orden(2, "listo"), orden(3, "en_proceso", "2026-11-01"),
        orden(4, "recibido", "2026-11-02"), orden(5, "en_proceso", "2026-11-05")], "N", HOY)
    secciones = presentacion.secciones_panel(lista)
    assert [t for t, _ in secciones] == ["Requieren atención", "Listas para avisar o entregar",
                                         "En proceso", "Recibidas"]
    assert [o["folio"] for o in secciones[0][1]] == ["LAV-0003", "LAV-0004"]  # la más atrasada primero
    assert presentacion.contar_por_estado(lista) == {"recibido": 2, "en_proceso": 2, "listo": 1}


# ------------------------------------------------------------ panel
def test_panel_muestra_alertas_y_acciones_rapidas(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.ordenes.listar_activas", lambda sb, cid: [
        orden(1, "recibido", "2026-11-01"), orden(2, "listo", nombre="Juan Pérez")])
    texto = con_negocio.get("/").get_data(as_text=True)
    assert "Requieren atención" in texto and "Atrasada" in texto
    assert "Empezar →" in texto                       # avanzar recibido -> en proceso
    assert 'class="accion wa"' in texto and "Avisar a Juan Pérez" in texto
    assert 'aria-label="Navegación principal"' in texto  # barra inferior
    assert 'name="volver" value="/"' in texto


def test_panel_vacio(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.ordenes.listar_activas", lambda sb, cid: [])
    assert "Todo al día" in con_negocio.get("/").get_data(as_text=True)


# --------------------------------------------- acción rápida y regreso
def test_accion_rapida_regresa_a_la_pagina_de_origen(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.ordenes.cambiar_estado",
                        lambda sb, cid, oid, e: {"id": oid, "folio": "LAV-0001", "estado": e})
    respuesta = con_negocio.post("/ordenes/1/estado", data={
        "csrf_token": "csrf-pruebas", "estado": "en_proceso", "volver": "/ordenes/?estado=recibido&q=mar"})
    assert respuesta.headers["Location"].endswith("/ordenes/?estado=recibido&q=mar")


@pytest.mark.parametrize("volver", ["https://sitio-malo.com", "//sitio-malo.com", "/\\sitio-malo.com", ""])
def test_regreso_a_otro_sitio_se_bloquea(con_negocio, monkeypatch, volver):
    monkeypatch.setattr("puntolisto.modelos.ordenes.cambiar_estado",
                        lambda sb, cid, oid, e: {"id": oid, "folio": "LAV-0001", "estado": e})
    respuesta = con_negocio.post("/ordenes/1/estado", data={
        "csrf_token": "csrf-pruebas", "estado": "en_proceso", "volver": volver})
    assert respuesta.headers["Location"].endswith("/ordenes/1")


# ------------------------------------------------ lista con buscador
def test_lista_busca_por_cliente_y_folio(con_negocio, monkeypatch):
    recibido = {}
    monkeypatch.setattr("puntolisto.modelos.clientes.listar",
                        lambda sb, cid, busqueda="", limite=200: [{"id": 7}, {"id": 9}])

    def listar_falso(sb, cid, estados, busqueda="", cliente_ids=None, orden_por="creado_en", limite=200):
        recibido.update(estados=estados, busqueda=busqueda, cliente_ids=cliente_ids)
        return [orden(1, "en_proceso")]

    monkeypatch.setattr("puntolisto.modelos.ordenes.listar", listar_falso)
    texto = con_negocio.get("/ordenes/?estado=en_proceso&q=mar").get_data(as_text=True)
    assert recibido == {"estados": ("en_proceso",), "busqueda": "mar", "cliente_ids": [7, 9]}
    assert "LAV-0001" in texto and "1 orden" in texto
    assert 'aria-current="true">En proceso' in texto


def test_filtro_urgentes(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.ordenes.listar", lambda *a, **k: [
        orden(3, "recibido", "2026-11-02"), orden(1, "recibido", "2026-10-28"), orden(2, "recibido", "2026-11-20")])
    texto = con_negocio.get("/ordenes/?estado=atencion").get_data(as_text=True)
    assert "LAV-0002" not in texto                                  # vence el 20: no es urgente
    assert texto.index("LAV-0001") < texto.index("LAV-0003")        # la más atrasada arriba


def test_filtro_desconocido_usa_pendientes(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.ordenes.listar", lambda *a, **k: [])
    texto = con_negocio.get("/ordenes/?estado=xyz").get_data(as_text=True)
    assert 'aria-current="true">Pendientes' in texto


def test_busqueda_de_folio_en_el_modelo():
    """El filtro or_ combina folio y clientes, y limpia caracteres peligrosos."""
    from puntolisto.modelos import ordenes

    class Consulta:
        def __init__(self): self.filtros = []
        def __getattr__(self, nombre):
            def metodo(*args, **kwargs):
                self.filtros.append((nombre, args))
                return self
            return metodo
        def execute(self):
            return type("R", (), {"data": []})()

    consulta = Consulta()
    sb = type("SB", (), {"table": lambda self, t: consulta})()
    ordenes.listar(sb, 1, ("recibido",), "lav-0001),x", [7, 9])
    assert ("or_", ("folio.ilike.*LAV-0001X*,cliente_id.in.(7,9)",)) in consulta.filtros


# ------------------------------------------------------------ ajustes
def test_ajustes_muestra_y_guarda(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.servicios.listar", lambda sb, cid, solo_activos=False: [{}, {}])
    texto = con_negocio.get("/negocio/ajustes").get_data(as_text=True)
    assert 'value="Lavandería Ana"' in texto and 'value="993 000 0000"' in texto
    assert "2 servicios activos" in texto and "Cerrar sesión" in texto

    guardado = {}
    monkeypatch.setattr("puntolisto.modelos.comercios.actualizar",
                        lambda sb, uid, nombre, tel: guardado.update(nombre=nombre, tel=tel) or {})
    respuesta = con_negocio.post("/negocio/ajustes", data={
        "csrf_token": "csrf-pruebas", "nombre": "Lavandería  Ana Express", "telefono": ""})
    assert respuesta.headers["Location"].endswith("/negocio/ajustes")
    assert guardado == {"nombre": "Lavandería Ana Express", "tel": None}


# ----------------------------------------------- app instalable (PWA)
def test_archivos_de_la_app(cliente):
    manifest = cliente.get("/manifest.webmanifest")
    assert manifest.status_code == 200 and manifest.mimetype == "application/manifest+json"
    assert manifest.get_json()["display"] == "standalone"
    sw = cliente.get("/sw.js")
    assert sw.status_code == 200 and sw.headers["Cache-Control"] == "no-cache"
    for archivo in ("app.css", "app.js", "icono-192.png", "icono-512.png", "icono-mascara-512.png"):
        assert cliente.get(f"/recursos/{archivo}").status_code == 200, archivo


@pytest.mark.parametrize("ruta", ["/recursos/__init__.py", "/recursos/../config.py",
                                  "/recursos/manifest.webmanifest"])
def test_no_se_sirven_otros_archivos(cliente, ruta):
    assert cliente.get(ruta).status_code == 404


def test_sin_barra_inferior_antes_de_configurar(cliente):
    assert 'aria-label="Navegación principal"' not in cliente.get("/entrar").get_data(as_text=True)


# ------------------------------------------------- rediseño v2
def test_semana_de_entregas():
    entregadas = [{"actualizado_en": "2026-11-02T18:00:00+00:00"},   # lunes 2 nov (hoy)
                  {"actualizado_en": "2026-11-02T20:00:00+00:00"},
                  {"actualizado_en": "2026-11-01T02:00:00+00:00"},   # sábado 31 oct en México (UTC-6)
                  {"actualizado_en": "2026-10-20T18:00:00+00:00"}]   # fuera de la semana
    semana = presentacion.semana_entregas(entregadas, HOY)
    assert semana["total"] == 3
    assert [d["letra"] for d in semana["dias"]] == ["M", "M", "J", "V", "S", "D", "L"]
    assert semana["dias"][-1] == {"letra": "L", "total": 2, "altura": 100, "hoy": True}
    assert semana["dias"][4]["total"] == 1  # sábado


def test_porcentajes_de_flujo():
    assert presentacion.porcentajes_flujo({"recibido": 2, "en_proceso": 1, "listo": 1}) == \
        {"recibido": 50, "en_proceso": 25, "listo": 25}
    assert presentacion.porcentajes_flujo({"recibido": 0, "en_proceso": 0, "listo": 0}) == \
        {"recibido": 0, "en_proceso": 0, "listo": 0}


@pytest.mark.parametrize("nombre, esperado", [
    ("Lavandería La Estrella", "LE"), ("María López", "ML"), ("Ana", "A"), ("", "?"),
    ("Taller de Reparación Hnos. Cruz", "TC")])
def test_iniciales(nombre, esperado):
    from puntolisto.etiquetas import iniciales
    assert iniciales(nombre) == esperado


def test_panel_v2_muestra_resumen_accesos_y_semana(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.ordenes.listar_activas", lambda sb, cid: [
        orden(1, "recibido", "2026-11-01"), orden(2, "listo"), orden(3, "en_proceso", "2026-11-09")])
    monkeypatch.setattr("puntolisto.modelos.ordenes.listar_entregadas", lambda sb, cid, limite=50: [
        {"actualizado_en": "2026-11-02T18:00:00+00:00"}])
    texto = con_negocio.get("/").get_data(as_text=True)
    assert 'class="avatar"' in texto and ">LA<" in texto                 # iniciales de Lavandería Ana
    assert '<p class="cifra">3 <small>órdenes</small></p>' in texto
    assert "1 urgente" in texto                                         # la atrasada
    assert "Nueva orden" in texto and "Nuevo cliente" in texto and "Catálogo" in texto
    assert "1 en 7 días" in texto
    assert 'class="central"' in texto                                   # botón + de la barra


def test_detalle_muestra_pasos(con_negocio, monkeypatch):
    base = orden(1, "listo", "2026-11-05")
    base.update(notas=None, orden_servicios=[{"cantidad": 2, "precio_unitario": 15,
                                               "servicios": {"nombre": "Planchado", "tipo_cobro": "pieza"}}])
    monkeypatch.setattr("puntolisto.modelos.ordenes.obtener_detalle", lambda sb, cid, oid: base)
    texto = con_negocio.get("/ordenes/1").get_data(as_text=True)
    assert texto.count('class="paso hecho') == 2 and 'class="paso  actual"' in texto
    assert 'style="width: 50%"' in texto                                # avance hasta "Lista"
    assert "2 piezas" in texto and "Avisar por WhatsApp" in texto


def test_ajustes_tiene_selector_de_tema(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.servicios.listar", lambda sb, cid, solo_activos=False: [])
    texto = con_negocio.get("/negocio/ajustes").get_data(as_text=True)
    for opcion in ("auto", "light", "dark"):
        assert f'data-tema-opcion="{opcion}"' in texto
    for color in ("original", "verde", "azul"):
        assert f'data-color-opcion="{color}"' in texto


def test_lista_ordena_por_prioridad_y_llegada_y_tiene_vista_cuadricula(con_negocio, monkeypatch):
    o1 = {**orden(1, "recibido", None), "creado_en": "2026-11-01T10:00:00+00:00"}
    o2 = {**orden(2, "recibido", None), "creado_en": "2026-11-02T10:00:00+00:00"}
    o3 = {**orden(3, "recibido", "2026-11-03"), "creado_en": "2026-11-02T12:00:00+00:00"}
    monkeypatch.setattr("puntolisto.modelos.ordenes.listar", lambda *a, **k: [o2, o3, o1])
    texto = con_negocio.get("/ordenes/").get_data(as_text=True)
    # Primero la que tiene fecha próxima (LAV-0003), luego la que llegó primero (LAV-0001) antes que LAV-0002
    assert texto.index("LAV-0003") < texto.index("LAV-0001") < texto.index("LAV-0002")
    assert 'data-vista-opcion="lista"' in texto
    assert 'data-vista-opcion="cuadricula"' in texto
