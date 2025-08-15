# web/app.py
from flask import Flask
from shared.models.db import db
from shared.config import SECRET_KEY
from web.routes.main_routes import main_bp
from web.routes.lti_routes import lti_bp
from web.routes.admin_routes import admin_bp
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    
    # ✅ 1. Configurar DATABASE_URL
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ✅ 2. Vincular db con la app
    db.init_app(app)  

    # ✅ 3. Registrar blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(lti_bp)
    app.register_blueprint(admin_bp)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)