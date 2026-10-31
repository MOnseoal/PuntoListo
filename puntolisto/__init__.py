"""Fábrica de la aplicación (patrón "application factory").

Aquí se crea la app de Flask, se carga la configuración,
se activa la protección CSRF y se registran los Blueprints.
"""
from pathlib import Path

from flask import Flask, request

from .config import CLAVE_DESARROLLO, EN_VERCEL, Config

_PLANTILLAS = Path(__file__).resolve().parent / "templates"


def _variables_faltantes(app: Flask) -> list[str]:
    faltan = []
    if app.config.get("SECRET_KEY") == CLAVE_DESARROLLO:
        faltan.append("FLASK_SECRET_KEY")
    if not app.config.get("SUPABASE_URL"):
        faltan.append("SUPABASE_URL")
    if not app.config.get("SUPABASE_KEY"):
        faltan.append("SUPABASE_KEY")
    return faltan


def _pagina_falta_config(faltan: list[str]) -> tuple[str, int]:
    items = "".join(f"<li><code>{nombre}</code></li>" for nombre in faltan)
    html = f"""<!doctype html>
<html lang="es">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Falta configurar Vercel</title>
<body style="font-family:system-ui,sans-serif;max-width:40rem;margin:2rem auto;padding:0 1rem;line-height:1.5">
<h1>Falta configurar Vercel</h1>
<p>PuntoListo está desplegado, pero no encontró estas variables de entorno:</p>
<ul>{items}</ul>
<p>En Vercel entra a <strong>Settings → Environment Variables</strong>, agrégalas
en Production y Preview (los mismos valores de tu archivo <code>.env</code>)
y pulsa <strong>Redeploy</strong> en el último despliegue.</p>
</body>
</html>
"""
    return html, 503


def create_app(config_extra: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder=str(_PLANTILLAS))
    app.config.from_object(Config)
    if config_extra:
        app.config.update(config_extra)

    # En Vercel no reventamos al importar (eso sale como FUNCTION_INVOCATION_FAILED).
    # Mostramos un aviso hasta que existan las variables.
    if EN_VERCEL:
        @app.before_request
        def exigir_config_en_vercel():
            if request.path == "/salud":
                return None
            faltan = _variables_faltantes(app)
            if faltan:
                return _pagina_falta_config(faltan)
            return None

    # Seguridad compartida: token CSRF en todos los formularios POST
    from .seguridad import registrar_csrf
    registrar_csrf(app)

    # Etiquetas y filtros para las plantillas
    from .etiquetas import registrar_etiquetas
    registrar_etiquetas(app)

    # Blueprints (controladores). Cada módulo nuevo se agrega aquí.
    from .auth.routes import bp as auth_bp
    from .negocio.routes import bp as negocio_bp
    from .panel.routes import bp as panel_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(negocio_bp)
    app.register_blueprint(panel_bp)

    return app
