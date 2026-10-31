"""Pruebas de los flujos de ACT-12 simulando las respuestas de Supabase."""
from types import SimpleNamespace

from supabase_auth.errors import AuthApiError

from puntolisto import create_app
from puntolisto.config import CLAVE_DESARROLLO
from conftest import iniciar_sesion, obtener_csrf, sesion_falsa


class AuthFalso:
    def __init__(self, sesion=None, error=None):
        self._sesion, self._error = sesion, error

    def _responder(self, *_args, **_kwargs):
        if self._error:
            raise self._error
        return SimpleNamespace(session=self._sesion)

    sign_in_with_password = sign_up = refresh_session = _responder


def cliente_supabase_falso(**kwargs):
    return lambda: SimpleNamespace(auth=AuthFalso(**kwargs))


COMERCIO = {"id": 1, "nombre": "Lavandería Ana", "abreviatura": "LAV",
            "giro": "lavanderia", "telefono": None}


# ------------------------------------------------------------------ básicas
def test_salud(cliente):
    datos = cliente.get("/salud").get_json()
    assert datos["flask_secret_configurada"]
    assert datos["supabase_url_configurada"] and datos["supabase_key_configurada"]


def test_en_vercel_sin_claves_no_tumba_la_app(monkeypatch):
    monkeypatch.setattr("puntolisto.EN_VERCEL", True)
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": CLAVE_DESARROLLO,
        "SUPABASE_URL": "",
        "SUPABASE_KEY": "",
    })
    cliente_v = app.test_client()
    salud = cliente_v.get("/salud")
    assert salud.status_code == 200
    aviso = cliente_v.get("/entrar")
    assert aviso.status_code == 503
    texto = aviso.get_data(as_text=True)
    assert "FLASK_SECRET_KEY" in texto
    assert "SUPABASE_URL" in texto


def test_panel_sin_sesion_redirige_a_entrar(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/entrar")


def test_post_sin_csrf_se_rechaza(cliente):
    respuesta = cliente.post("/entrar", data={"correo": "a@b.mx", "contrasena": "x"},
                             follow_redirects=True)
    assert "La página caducó" in respuesta.get_data(as_text=True)


# --------------------------------------------------------------------- entrar
def test_entrar_correcto_y_sin_negocio_lleva_a_configurar(cliente, monkeypatch):
    monkeypatch.setattr("puntolisto.auth.routes.nuevo_cliente",
                        cliente_supabase_falso(sesion=sesion_falsa()))
    monkeypatch.setattr("puntolisto.modelos.comercios.obtener_mi_comercio",
                        lambda sb, uid: None)
    csrf = obtener_csrf(cliente)

    respuesta = cliente.post("/entrar", data={"csrf_token": csrf, "correo": "ana@correo.mx",
                                              "contrasena": "12345678"})
    assert respuesta.headers["Location"].endswith("/")

    respuesta = cliente.get("/")
    assert respuesta.headers["Location"].endswith("/negocio/configurar")


def test_entrar_con_contrasena_incorrecta(cliente, monkeypatch):
    error = AuthApiError("Invalid login credentials", 400, "invalid_credentials")
    monkeypatch.setattr("puntolisto.auth.routes.nuevo_cliente", cliente_supabase_falso(error=error))
    csrf = obtener_csrf(cliente)

    respuesta = cliente.post("/entrar", data={"csrf_token": csrf, "correo": "ana@correo.mx",
                                              "contrasena": "mala"})
    texto = respuesta.get_data(as_text=True)
    assert "Correo o contraseña incorrectos." in texto
    assert 'value="ana@correo.mx"' in texto  # conserva el correo escrito


# ------------------------------------------------------------------- registro
def test_registro_valida_contrasenas(cliente):
    csrf = obtener_csrf(cliente)
    texto = cliente.post("/registro", data={"csrf_token": csrf, "correo": "ana@correo.mx",
                                            "contrasena": "12345678", "confirmar": "87654321"}
                         ).get_data(as_text=True)
    assert "Las contraseñas no coinciden." in texto


def test_registro_correcto_lleva_a_configurar(cliente, monkeypatch):
    monkeypatch.setattr("puntolisto.auth.routes.nuevo_cliente",
                        cliente_supabase_falso(sesion=sesion_falsa()))
    csrf = obtener_csrf(cliente)
    respuesta = cliente.post("/registro", data={"csrf_token": csrf, "correo": "ana@correo.mx",
                                                "contrasena": "12345678", "confirmar": "12345678"})
    assert respuesta.headers["Location"].endswith("/negocio/configurar")


def test_registro_correo_repetido(cliente, monkeypatch):
    error = AuthApiError("User already registered", 422, "user_already_exists")
    monkeypatch.setattr("puntolisto.auth.routes.nuevo_cliente", cliente_supabase_falso(error=error))
    csrf = obtener_csrf(cliente)
    texto = cliente.post("/registro", data={"csrf_token": csrf, "correo": "ana@correo.mx",
                                            "contrasena": "12345678", "confirmar": "12345678"}
                         ).get_data(as_text=True)
    assert "Ya existe una cuenta con ese correo." in texto


# -------------------------------------------------------- configurar negocio
def test_configurar_negocio(cliente, monkeypatch):
    iniciar_sesion(cliente)
    guardado = {}

    def crear_falso(sb, usuario_id, nombre, abreviatura, giro, telefono):
        guardado.update(nombre=nombre, abreviatura=abreviatura, giro=giro, telefono=telefono)
        return 4

    monkeypatch.setattr("puntolisto.modelos.comercios.obtener_mi_comercio", lambda sb, uid: None)
    monkeypatch.setattr("puntolisto.modelos.comercios.crear", crear_falso)

    respuesta = cliente.post("/negocio/configurar", data={
        "csrf_token": "csrf-pruebas", "nombre": "Lavandería Ana", "abreviatura": "",
        "giro": "lavanderia", "telefono": "993 123 4567"}, follow_redirects=False)

    assert respuesta.headers["Location"].endswith("/")
    assert guardado == {"nombre": "Lavandería Ana", "abreviatura": "LAV",
                        "giro": "lavanderia", "telefono": "529931234567"}


def test_configurar_rechaza_giro_invalido(cliente, monkeypatch):
    iniciar_sesion(cliente)
    monkeypatch.setattr("puntolisto.modelos.comercios.obtener_mi_comercio", lambda sb, uid: None)
    texto = cliente.post("/negocio/configurar", data={
        "csrf_token": "csrf-pruebas", "nombre": "Mi negocio", "abreviatura": "MN",
        "giro": "panaderia"}).get_data(as_text=True)
    assert "Elige el giro de tu negocio." in texto


# ---------------------------------------------------------------------- panel
def test_panel_agrupa_por_estado(cliente, monkeypatch):
    iniciar_sesion(cliente)
    monkeypatch.setattr("puntolisto.modelos.comercios.obtener_mi_comercio",
                        lambda sb, uid: COMERCIO)
    monkeypatch.setattr("puntolisto.modelos.ordenes.listar_activas", lambda sb, cid: [
        {"id": 2, "folio": "LAV-0002", "estado": "listo", "fecha_entrega": "2026-11-05",
         "clientes": {"nombre": "María López"}},
        {"id": 1, "folio": "LAV-0001", "estado": "recibido", "fecha_entrega": None,
         "clientes": {"nombre": "Juan Pérez"}},
    ])
    texto = cliente.get("/").get_data(as_text=True)
    assert "Lavandería Ana" in texto
    assert "LAV-0002" in texto and "María López" in texto and "05/11/2026" in texto
    assert "LAV-0001" in texto


def test_token_vencido_que_no_se_puede_renovar(cliente, monkeypatch):
    iniciar_sesion(cliente, expira_en=-10)
    error = AuthApiError("Invalid Refresh Token", 400, "refresh_token_not_found")
    monkeypatch.setattr("puntolisto.auth.sesion.nuevo_cliente", cliente_supabase_falso(error=error))
    respuesta = cliente.get("/")
    assert respuesta.headers["Location"].endswith("/entrar")
    with cliente.session_transaction() as s:
        assert "access_token" not in s


def test_token_vencido_se_renueva(cliente, monkeypatch):
    iniciar_sesion(cliente, expira_en=-10)
    nueva = sesion_falsa()
    nueva.access_token = "token-nuevo"
    monkeypatch.setattr("puntolisto.auth.sesion.nuevo_cliente", cliente_supabase_falso(sesion=nueva))
    monkeypatch.setattr("puntolisto.modelos.comercios.obtener_mi_comercio",
                        lambda sb, uid: COMERCIO)
    monkeypatch.setattr("puntolisto.modelos.ordenes.listar_activas", lambda sb, cid: [])
    assert cliente.get("/").status_code == 200
    with cliente.session_transaction() as s:
        assert s["access_token"] == "token-nuevo"


def test_salir_borra_la_sesion(cliente):
    iniciar_sesion(cliente)
    respuesta = cliente.post("/salir", data={"csrf_token": "csrf-pruebas"})
    assert respuesta.headers["Location"].endswith("/entrar")
    with cliente.session_transaction() as s:
        assert "access_token" not in s
