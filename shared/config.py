# shared/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# === SECRET KEY ===
SECRET_KEY = os.getenv("SECRET_KEY", "tu-clave-secreta")

# === SUPABASE ===
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# === CANVAS ===
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN")
CANVAS_BASE_URL = 'https://canvas.instructure.com/api/v1'

# === DATABASE ===
DATABASE_URL = os.getenv("DATABASE_URL", SUPABASE_URL)
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está definido")


# === OPENAI ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# === LTI ===
CANVAS_ISSUER = "https://canvas.instructure.com"
CANVAS_JWKS_URL = "https://sso.canvaslms.com/api/lti/security/jwks"
CANVAS_CLIENT_ID = os.getenv("CANVAS_CLIENT_ID")

# ✅ CORREGIDO: Nombre consistente
CANVAS_LOGIN_URL = "https://sso.canvaslms.com/api/lti/authorize_redirect"

TOKEN_URL = "https://sso.canvaslms.com/login/oauth2/token"

# === OTROS ===
TEMP_DIR = os.getenv("TEMP_DIR", "temp_files")
os.makedirs(TEMP_DIR, exist_ok=True)