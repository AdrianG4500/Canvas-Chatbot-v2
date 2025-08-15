# scripts/test_worker.py
import sys
import os

# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.models.db import db
from flask import Flask
from shared.config import DATABASE_URL

# Crear una app temporal para el contexto
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Vincular db con la app
db.init_app(app)

# Ahora sí puedes usar el contexto
with app.app_context():
    # Tu código de prueba
    from shared.models.db import HistorialConsulta

    c = HistorialConsulta(
        consulta_id="test_123",
        user_id="user_456",
        course_id="course_789",
        pregunta="¿Qué es un monopolio?",
        tipo="general",
        estado="pendiente"
    )
    db.session.add(c)
    db.session.commit()
    print("✅ Consulta de prueba creada")

    # Leer para verificar
    consultas = HistorialConsulta.query.all()
    for con in consultas:
        print(f"🔍 {con.consulta_id}: {con.pregunta} ({con.estado})")