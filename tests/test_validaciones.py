import pytest

from puntolisto import validaciones as v


@pytest.mark.parametrize("entrada, esperado", [
    ("9931234567", "529931234567"),
    ("993 123 4567", "529931234567"),
    ("993-123-45-67", "529931234567"),
    ("+52 993 123 4567", "529931234567"),
    ("52 9931234567", "529931234567"),
    ("12345", None),
    ("", None),
    ("99312345678", None),
])
def test_normalizar_telefono(entrada, esperado):
    assert v.normalizar_telefono(entrada) == esperado


@pytest.mark.parametrize("nombre, esperado", [
    ("Lavandería La Estrella", "LAV"),
    ("Ñañu Sastrería", "NAN"),
    ("  ", "PL"),
    ("7 Mares", "7MA"),
])
def test_sugerir_abreviatura(nombre, esperado):
    assert v.sugerir_abreviatura(nombre) == esperado


@pytest.mark.parametrize("entrada, esperado", [
    ("lav", "LAV"), ("SaS1", "SAS1"), ("ábc", "ABC"),
    ("LAVAND", None), ("LA V", None), ("", None), ("L-1", None),
])
def test_normalizar_abreviatura(entrada, esperado):
    assert v.normalizar_abreviatura(entrada) == esperado


def test_correo_valido():
    assert v.correo_valido("ana@correo.mx")
    assert not v.correo_valido("ana@correo")
    assert not v.correo_valido("")
