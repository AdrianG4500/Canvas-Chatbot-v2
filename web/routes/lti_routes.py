# web/routes/lti_routes.py
from flask import Blueprint, request, session, redirect, current_app, jsonify
import jwt
import requests
import json
import logging
import secrets
from datetime import datetime
from urllib.parse import urlencode
from shared.config import (
    CANVAS_ISSUER,
    CANVAS_JWKS_URL,
    CANVAS_CLIENT_ID,
    CANVAS_LOGIN_URL,
    SECRET_KEY
)
from shared.models.db import db, Usuario, Curso
import os

# === Configurar logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Blueprint ===
lti_bp = Blueprint('lti', __name__, url_prefix="/lti")

# === Claim URLs ===
CLAIM_CONTEXT = "https://purl.imsglobal.org/spec/lti/claim/context"
CLAIM_DEPLOYMENT_ID = "https://purl.imsglobal.org/spec/lti/claim/deployment_id"


# === JWKS Endpoint (para Canvas) ===
@lti_bp.route('/.well-known/jwks.json')
def jwks():
    """Endpoint para que Canvas obtenga tu clave pública"""
    try:
        with open(os.path.join(current_app.root_path, '..', '.well-known', 'jwks.json'), 'r') as f:
            jwks_data = json.load(f)
        return jsonify(jwks_data), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        logger.error(f"❌ Error al leer JWKS: {e}")
        return jsonify({"error": "JWKS no disponible"}), 500

# === LTI Login (Step 1) ===
@lti_bp.route("/login", methods=["GET", "POST"])
def login():
    logger.info(f"📥 /lti/login recibido: {request.method}")

    # Leer parámetros (GET o POST)
    data = request.form if request.method == "POST" else request.args

    # Parámetros obligatorios
    iss = data.get("iss")
    login_hint = data.get("login_hint")
    target_link_uri = data.get("target_link_uri")
    lti_message_hint = data.get("lti_message_hint", "")
    client_id = data.get("client_id")
    lti_deployment_id = data.get("lti_deployment_id", "")
    
    logger.info(f"🔍 lti_message_hint recibido: {lti_message_hint}")
    logger.info(f"📩 Datos recibidos: {dict(data)}")

    if not all([login_hint, target_link_uri, client_id]):
        logger.warning("❌ Faltan parámetros en /login")
        return "Faltan parámetros", 400

    # Generar state y nonce
    state = secrets.token_urlsafe(16)
    nonce = secrets.token_urlsafe(16)
    session['state'] = state
    session['nonce'] = nonce
    session['lti_message_hint'] = lti_message_hint
    session['lti_deployment_id'] = lti_deployment_id

    # Construir URL de autorización
    params = {
        "scope": "openid",
        "response_type": "id_token",
        "client_id": client_id,
        "redirect_uri": target_link_uri,
        "login_hint": login_hint,
        "state": state,
        "nonce": nonce,
        "response_mode": "form_post",
        "prompt": "none",
        "lti_deployment_id": lti_deployment_id,
        "id_token_signed_response_alg": "RS256"
    }

    auth_url = CANVAS_LOGIN_URL + "?" + urlencode(params)
    logger.info(f"➡️ Redirigiendo a: {auth_url}")
    return redirect(auth_url)

# === LTI Launch (Step 2) ===
@lti_bp.route("/launch", methods=["POST"])
def launch():
    logger.info("✅ /lti/launch recibido")

    # Validar state
    received_state = request.form.get('state')
    expected_state = session.get('state')
    if not received_state or received_state != expected_state:
        logger.warning(f"❌ State inválido: esperado={expected_state}, recibido={received_state}")
        return "Estado inválido", 400

    # Obtener id_token
    id_token = request.form.get('id_token')
    if not id_token:
        logger.warning("❌ No se recibió id_token")
        return "Falta id_token", 400

    try:
        # Decodificar header para obtener kid
        unverified_header = jwt.get_unverified_header(id_token)
        jwks = requests.get(CANVAS_JWKS_URL).json()
        public_keys = {
            key["kid"]: jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
            for key in jwks["keys"]
        }
        key = public_keys[unverified_header["kid"]]

        # Decodificar token
        decoded = jwt.decode(
            id_token,
            key=key,
            algorithms=["RS256"],
            audience=CANVAS_CLIENT_ID,
            issuer=CANVAS_ISSUER
        )

        # Validar nonce
        expected_nonce = session.get("nonce")
        received_nonce = decoded.get("nonce")
        if received_nonce != expected_nonce:
            logger.warning(f"❌ Nonce inválido: {received_nonce}")
            return "Nonce inválido", 400

        # Obtener deployment_id
        deployment_id = decoded.get(CLAIM_DEPLOYMENT_ID)
        if not deployment_id:
            logger.warning("❌ No se encontró deployment_id")
            return "No se encontró deployment_id", 400

        # Buscar curso por deployment_id
        curso = Curso.query.filter_by(lti_deployment_id=deployment_id).first()
        if not curso:
            logger.warning(f"❌ deployment_id no registrado: {deployment_id}")
            return "⚠️ Este curso no está configurado aún.", 400

        # Extraer datos del usuario
        user_id = decoded.get('sub')
        user_full_name = decoded.get('name') or f"{decoded.get('given_name', '')} {decoded.get('family_name', '')}".strip()
        if not user_full_name.strip():
            user_full_name = "Estudiante sin nombre"

        # Extraer nombre del curso
        context = decoded.get(CLAIM_CONTEXT, {})
        course_name = context.get("title", "Curso desconocido")

        # ✅ Registrar usuario si no existe
        usuario = Usuario.query.get(user_id)
        if not usuario:
            usuario = Usuario(
                user_id=user_id,
                nombre=user_full_name,
                email=decoded.get('email'),
                rol="estudiante"
            )
            db.session.add(usuario)
            db.session.commit()
            logger.info(f"✅ Usuario registrado: {user_id}")

        # Guardar en sesión
        session['user_id'] = user_id
        session['course_id'] = curso.course_id
        session['course_name'] = course_name
        session['user_full_name'] = user_full_name

        logger.info(f"✅ Autenticación exitosa: {user_full_name} → {course_name}")

        return redirect("/")

    except jwt.PyJWTError as e:
        logger.error(f"❌ Error JWT: {e}")
        return f"❌ Error validando token: {str(e)}", 400
    except Exception as e:
        logger.error(f"❌ Error interno: {e}")
        return f"❌ Error interno: {str(e)}", 500