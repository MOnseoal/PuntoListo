"""Fábrica de la aplicación (patrón "application factory").

Aquí se crea la app de Flask, se carga la configuración,
se activa la protección CSRF y se registran los Blueprints.
"""
from flask import Flask

from .config import CLAVE_DESARROLLO, EN_VERCEL, Config


def create_app(config_extra: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_extra:
        app.config.update(config_extra)

    if EN_VERCEL and app.config["SECRET_KEY"] == CLAVE_DESARROLLO:
        raise RuntimeError("Falta FLASK_SECRET_KEY en las variables de entorno de Vercel")

    # Seguridad compartida: token CSRF en todos los formularios POST
    from .seguridad import registrar_csrf
    registrar_csrf(app)

    # Etiquetas y filtros para las plantillas
    from .etiquetas import registrar_etiquetas
    registrar_etiquetas(app)

    # Blueprints (controladores). Cada módulo nuevo se agrega aquí.
    from .auth.routes import bp as auth_bp
    from .clientes.routes import bp as clientes_bp
    from .negocio.routes import bp as negocio_bp
    from .ordenes.routes import bp as ordenes_bp
    from .panel.routes import bp as panel_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(negocio_bp)
    app.register_blueprint(ordenes_bp)
    app.register_blueprint(panel_bp)

    # Página amable cuando algo no existe (o es de otro negocio)
    from flask import render_template

    @app.errorhandler(404)
    def no_encontrado(_error):
        return render_template("errores/404.html"), 404

    return app
