"""Punto de entrada de PuntoListo.

Vercel busca una variable llamada `app` en este archivo.
En tu computadora lo ejecutas con:  flask --app app run --debug
"""
from puntolisto import create_app

app = create_app()
