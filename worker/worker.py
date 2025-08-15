# worker/worker.py
import time
import logging
from config import DATABASE_URL, POLLING_INTERVAL
from shared.models.db import db
from flask import Flask

# === Configurar logging ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === Crear app para el worker ===
def create_worker_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,  # Recicla conexiones cada 5 min
        'pool_size': 5,       # Máximo 5 conexiones en el pool
        'max_overflow': 2,    # Hasta 2 adicionales si es necesario
        'pool_timeout': 30    # Timeout si no hay conexión disponible
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def main():
    app = create_worker_app()

    logger.info("🚀 Worker local iniciado")

    while True:
        try:
            # ✅ Usar app_context una sola vez
            with app.app_context():
                # === 1. Procesar consultas (cada 5 segundos) ===
                from services.consulta_service import procesar_nuevas_consultas
                procesar_nuevas_consultas()

                # === 2. Sincronizar archivos (cada 30 min) ===
                from services.archivo_service import sincronizar_archivos_canvas
                sincronizar_archivos_canvas()

            # ✅ Esperar antes del próximo ciclo
            time.sleep(POLLING_INTERVAL)  # 5 segundos

        except Exception as e:
            logger.error(f"❌ Error en worker: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()