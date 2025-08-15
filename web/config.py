# web/config.py
from shared.config import *

# === Configuración específica del web ===
FLASK_ENV = os.getenv("FLASK_ENV", "production")
SECRET_KEY = os.getenv("SECRET_KEY", "tu-clave-secreta")
SESSION_TYPE = "filesystem"
DEBUG = FLASK_ENV == "development"

# LTI
LTI_HOST = "https://canvas.instructure.com"