import os
from flask import Flask, session, g
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "movie_ticket_secret_key_default_2026")

    # Global context processor for templates
    @app.context_processor
    def inject_user():
        return {
            "current_user": session.get("user")
        }

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.customer import customer_bp
    from app.routes.admin import admin_bp
    from app.routes.dbms_demo import dbms_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(dbms_bp, url_prefix="/dbms-demo")

    return app
