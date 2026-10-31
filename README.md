# PuntoListo

Sistema web para registrar órdenes, controlar su estado y avisar a los clientes por WhatsApp
en pequeños negocios (lavanderías, sastrerías, talleres).

**Stack:** Python 3.14 · Flask 3.1 · Jinja2 · Pico CSS · Supabase (PostgreSQL + Auth + RLS) · Vercel

## Correr en tu computadora (Windows, PowerShell)

```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env      # y llena tus claves de Supabase
flask --app app run --debug --host 0.0.0.0
```

- Computadora: http://127.0.0.1:5000
- Teléfono (misma red WiFi): http://IP-DE-TU-PC:5000 (la IP sale con `ipconfig`)

## Pruebas

```powershell
python -m pytest
```

## Base de datos

Ejecutar en orden, una vez cada uno, en Supabase → SQL Editor:
`docs/sql/001_esquema.sql` y `docs/sql/002_permitir_borrar_cuenta.sql`.
Explicación completa en `docs/ACT-11_base_de_datos.md`.

## Despliegue

Cada `git push` a `main` publica en Vercel. Variables de entorno necesarias en Vercel:
`FLASK_SECRET_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`.
