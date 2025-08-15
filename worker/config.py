# worker/config.py
from shared.config import *

# === Configuración específica del worker ===
POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL", 5))  # segundos
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")