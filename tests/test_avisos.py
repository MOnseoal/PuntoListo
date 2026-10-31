"""Pruebas del módulo de avisos por WhatsApp (ACT-18)."""
from urllib.parse import parse_qs, unquote, urlparse

from puntolisto import avisos


def test_mensaje_lleva_cliente_folio_y_negocio():
    texto = avisos.mensaje_listo("María López", "LAV-0001", "Lavandería La Estrella")
    assert "María" in texto and "LAV-0001" in texto and "Lavandería La Estrella" in texto
    assert "López" not in texto  # solo el primer nombre, más cercano


def test_enlace_wa_me_con_acentos_codificados():
    enlace = avisos.enlace_whatsapp("529931234567", "Hola María, ¿ya está lista?")
    partes = urlparse(enlace)
    assert partes.scheme == "https" and partes.netloc == "wa.me"
    assert partes.path == "/529931234567"
    assert " " not in enlace and "á" not in enlace  # todo codificado
    assert parse_qs(partes.query)["text"][0] == "Hola María, ¿ya está lista?"


def test_enlace_ignora_simbolos_en_el_telefono():
    assert avisos.enlace_whatsapp("+52 993-123-4567", "x").startswith("https://wa.me/529931234567?")


def test_enlace_orden_lista():
    orden = {"folio": "SAS-0007", "clientes": {"nombre": "Pedro Gómez", "telefono": "529930001111"}}
    enlace = avisos.enlace_orden_lista(orden, "Sastrería Beto")
    texto = unquote(enlace.split("text=")[1])
    assert enlace.startswith("https://wa.me/529930001111?text=")
    assert "Pedro" in texto and "SAS-0007" in texto and "Sastrería Beto" in texto


def test_enlace_orden_sin_telefono():
    assert avisos.enlace_orden_lista({"folio": "X-1", "clientes": None}, "N") is None
