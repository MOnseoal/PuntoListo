"""Pruebas de la sección informativa de planes y vistas previas (ACT-24)."""
import pytest

from conftest import iniciar_sesion, obtener_csrf
from puntolisto import planes

COMERCIO = {"id": 1, "nombre": "Lavandería Ana", "abreviatura": "LAV",
            "giro": "lavanderia", "telefono": "529930000000"}


class SupabaseSoloLecturaComercio:
    """Falla si cualquier ruta de planes intenta escribir o llamar RPC en Supabase."""
    def table(self, nombre):
        raise AssertionError(f"No se debe consultar ni escribir en la tabla {nombre}")

    def rpc(self, nombre, *_a, **_k):
        raise AssertionError(f"No se debe llamar a la función RPC {nombre}")


@pytest.fixture
def con_negocio(cliente, monkeypatch):
    iniciar_sesion(cliente)
    monkeypatch.setattr("puntolisto.auth.sesion.cliente_actual",
                        lambda: SupabaseSoloLecturaComercio())
    monkeypatch.setattr("puntolisto.modelos.comercios.obtener_mi_comercio",
                        lambda sb, uid: COMERCIO)
    return cliente


# ------------------------------------------------------------------ constantes
def test_constantes_y_calculo_primer_mes():
    assert planes.DESCUENTO_PRIMER_MES == 0.20
    assert planes.PLAN_ACTUAL == "partida"
    assert planes.LIMITES_GRATIS == planes.LIMITES["partida"]
    assert planes.LIMITES["partida"] == {"clientes": 15, "ordenes_mes": 50, "servicios": 5, "tickets_mes": 0}
    assert planes.LIMITES["fuerte"] == {"clientes": 30, "ordenes_mes": 150, "servicios": 10, "tickets_mes": 150}
    assert planes.LIMITES["cumbre"] == {"clientes": 100, "ordenes_mes": 500, "servicios": 30, "tickets_mes": 500}
    assert planes.precio_primer_mes(75) == 60
    assert planes.precio_primer_mes(150) == 120


# ------------------------------------------------------------------- seguridad
@pytest.mark.parametrize("ruta, metodo", [
    ("/planes", "get"),
    ("/planes/gracias/fuerte", "get"),
    ("/planes/vista-previa/ticket", "get"),
    ("/planes/solicitar", "post"),
])
def test_rutas_de_planes_exigen_sesion(cliente, ruta, metodo):
    if metodo == "post":
        csrf = obtener_csrf(cliente)
        respuesta = cliente.post(ruta, data={"csrf_token": csrf, "plan": "fuerte"})
    else:
        respuesta = cliente.get(ruta)
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/entrar")


def test_post_solicitar_sin_csrf_falla(con_negocio):
    respuesta = con_negocio.post("/planes/solicitar", data={"plan": "fuerte"}, follow_redirects=True)
    assert "La página caducó" in respuesta.get_data(as_text=True)


@pytest.mark.parametrize("plan_invalido", ["", "partida", "gratis", "oro", "otro"])
def test_post_solicitar_con_plan_invalido_se_rechaza(con_negocio, plan_invalido):
    respuesta = con_negocio.post("/planes/solicitar",
                                 data={"csrf_token": "csrf-pruebas", "plan": plan_invalido})
    assert respuesta.status_code == 400


# ------------------------------------------------------------ pantalla /planes
def test_pantalla_planes_muestra_nombres_precios_descuentos_y_matriz(con_negocio):
    respuesta = con_negocio.get("/planes")
    assert respuesta.status_code == 200
    texto = respuesta.get_data(as_text=True)

    # Tres nombres y precios 0, 75 y 150
    for nombre in ("Punto de Partida", "Punto Fuerte", "Punto Cumbre"):
        assert nombre in texto
    for precio in ("$0", "$75", "$150"):
        assert precio in texto

    # Primer mes con 20 % de descuento (60 y 120) y aviso de simulación
    assert "Primer mes $60 (-20 % para nuevos usuarios)" in texto
    assert "Primer mes $120 (-20 % para nuevos usuarios)" in texto
    assert "Vista previa: aún no se realiza ningún cobro." in texto
    assert "Tu plan actual" in texto and "Más elegido" in texto

    # Matriz con límites de órdenes (50/150/500), clientes (15/30/100) y servicios (5/10/30)
    for valor in ("50", "150", "500", "15", "30", "100", "5", "10", "150 al mes", "500 al mes", "Últimos 30 días"):
        assert f"<strong>{valor}</strong>" in texto


def test_solicitar_plan_redirige_a_gracias_sin_escribir_en_bd(con_negocio):
    for clave, nombre in (("fuerte", "Punto Fuerte"), ("cumbre", "Punto Cumbre")):
        respuesta = con_negocio.post("/planes/solicitar",
                                     data={"csrf_token": "csrf-pruebas", "plan": clave})
        assert respuesta.status_code == 302
        assert respuesta.headers["Location"].endswith(f"/planes/gracias/{clave}")

        confirmacion = con_negocio.get(f"/planes/gracias/{clave}").get_data(as_text=True)
        assert f"Gracias por tu interés en {nombre}." in confirmacion
        assert "Esta es una demostración y no se hizo ningún cobro." in confirmacion


def test_gracias_con_plan_inexistente_da_404(con_negocio):
    assert con_negocio.get("/planes/gracias/inexistente").status_code == 404


# -------------------------------------------------------------- vistas previas
@pytest.mark.parametrize("modulo, plan_esperado", [
    ("recordatorio", "Punto Fuerte"),
    ("ticket", "Punto Fuerte"),
    ("historial", "Punto Fuerte"),
    ("mensaje-propio", "Punto Cumbre"),
    ("marca", "Punto Cumbre"),
    ("estados", "Punto Cumbre"),
    ("reporte", "Punto Cumbre"),
    ("equipo", "Punto Cumbre"),
])
def test_modulos_vista_previa_responden_200_y_piden_plan_correcto(con_negocio, modulo, plan_esperado):
    respuesta = con_negocio.get(f"/planes/vista-previa/{modulo}")
    assert respuesta.status_code == 200
    texto = respuesta.get_data(as_text=True)
    assert f"Vista previa del plan {plan_esperado}" in texto
    assert "Ver planes" in texto and "Quiero este plan" in texto


def test_vista_previa_ticket_usa_limite_de_constantes(con_negocio):
    texto = con_negocio.get("/planes/vista-previa/ticket").get_data(as_text=True)
    assert f"Hasta {planes.LIMITES['fuerte']['tickets_mes']} tickets al mes en Punto Fuerte" in texto
    assert "Imprimir / PDF" in texto


def test_vista_previa_modulo_inexistente_da_404(con_negocio):
    respuesta = con_negocio.get("/planes/vista-previa/no-existe")
    assert respuesta.status_code == 404


# --------------------------------------------- entradas en Ajustes y en Panel
def test_entradas_en_ajustes_y_panel(con_negocio, monkeypatch):
    monkeypatch.setattr("puntolisto.modelos.servicios.listar", lambda sb, cid, solo_activos=False: [])
    ajustes_html = con_negocio.get("/negocio/ajustes").get_data(as_text=True)
    assert "Tu plan" in ajustes_html and "Punto de Partida" in ajustes_html
    assert "Funciones de los planes" in ajustes_html
    for modulo in planes.MODULOS_VISTA_PREVIA:
        assert f"/planes/vista-previa/{modulo}" in ajustes_html

    monkeypatch.setattr("puntolisto.modelos.ordenes.listar_activas", lambda sb, cid: [])
    monkeypatch.setattr("puntolisto.modelos.ordenes.listar_entregadas", lambda sb, cid, limite=50: [])
    panel_html = con_negocio.get("/").get_data(as_text=True)
    assert "Punto de Partida" in panel_html and 'href="/planes"' in panel_html
