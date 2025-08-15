# web/routes/admin_routes.py
from flask import Blueprint, render_template, request, jsonify, session
from shared.models.db import db, Curso, Asistente, curso_asistente
from shared.models.db_services import registrar_usuario
import openai
import logging
from openai import OpenAI
from shared.config import OPENAI_API_KEY

admin_bp = Blueprint('admin', __name__, url_prefix="/admin")

@admin_bp.route("/config")
def config():
    # Solo acceso si estás en sesión (puedes restringir más si quieres)
    if not session.get("user_id"):
        return "Acceso denegado", 403

    cursos = Curso.query.all()
    asistentes = Asistente.query.all()
    return render_template("admin_config.html", cursos=cursos, asistentes=asistentes)

client = OpenAI(api_key=OPENAI_API_KEY)

# === Crear Curso ===
@admin_bp.route("/crear_curso", methods=["POST"])
def crear_curso():
    data = request.get_json()
    course_id = data.get("course_id")
    nombre = data.get("nombre")
    lti_deployment_id = data.get("lti_deployment_id")
    vector_store_id = data.get("vector_store_id")

    if not course_id or not nombre:
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    curso = Curso.query.get(course_id)
    if curso:
        return jsonify({"error": "El curso ya existe"}), 400

    nuevo = Curso(
        course_id=course_id,
        nombre=nombre,
        lti_deployment_id=lti_deployment_id,
        vector_store_id=vector_store_id
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"status": "ok", "mensaje": "Curso creado"})

# === Crear Asistente (tipo predefinido) ===
@admin_bp.route("/crear_asistente", methods=["POST"])
def crear_asistente():
    data = request.get_json()
    subtipo = data.get("subtipo")
    curso_id = data.get("curso_id")
    vector_store_id = data.get("vector_store_id")

    curso = Curso.query.get(curso_id)
    if not curso:
        return jsonify({"error": "Curso no encontrado"}), 400

    # Nombre base
    nombre_base = curso.nombre.replace("Introduccion", "Introducción")
    nombre = f"Asistente {subtipo.title()} - {nombre_base}"

    # Instrucciones por subtipo
    instrucciones = {
        "general": f"Eres un asistente académico para {nombre_base}. Responde con claridad, usando negritas, emojis y listas.",
        "evaluador": f"Eres un creador de evaluaciones para {nombre_base}. Genera preguntas variadas y retroalimentación detallada.",
        "reflexivo": f"Eres un tutor socrático para {nombre_base}. Guía al estudiante con preguntas, no des respuestas directas.",
        "conceptual": f"Eres un experto en fundamentos teóricos de {nombre_base}. Sé riguroso y técnico.",
        "analizador_codigo": "Analiza código y genera un informe detallado: descripción, funciones, sugerencias, ejemplos.",
        "mapas_mentales": "Genera mapas mentales en Mermaid.js: nodo central → ramas → subtemas → ejemplos."
    }

    modelo = "gpt-4o"
    temperatura = {"general": 0.5, "evaluador": 0.7, "reflexivo": 0.8, "conceptual": 0.3}.get(subtipo, 0.5)
    top_p = {"general": 0.5, "evaluador": 0.9, "reflexivo": 0.95, "conceptual": 0.5}.get(subtipo, 0.7)

    # Crear en OpenAI
    try:
        asistente = client.beta.assistants.create(
            name=nombre,
            model=modelo,
            instructions=instrucciones.get(subtipo, ""),
            temperature=temperatura,
            top_p=top_p,
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}} if vector_store_id else None
        )
    except Exception as e:
        return jsonify({"error": f"Error en OpenAI: {str(e)}"}), 500

    # Guardar en DB
    nuevo = Asistente(
        asistente_id=asistente.id,
        nombre=nombre,
        categoria="externo" if subtipo in ["general", "evaluador", "reflexivo", "conceptual"] else "interno",
        subtipo=subtipo,
        modelo=modelo,
        temperatura=temperatura,
        top_p=top_p,
        instrucciones=instrucciones.get(subtipo),
        vector_store_id=vector_store_id
    )
    db.session.add(nuevo)
    db.session.commit()

    # Vincular al curso
    stmt = curso_asistente.insert().values(
        course_id=curso_id,
        asistente_id=asistente.id,
        rol=subtipo
    )
    db.session.execute(stmt)
    db.session.commit()

    return jsonify({"status": "ok", "id": asistente.id})

# === Actualizar Curso ===
@admin_bp.route("/actualizar_curso", methods=["POST"])
def actualizar_curso():
    data = request.get_json()
    curso = Curso.query.get(data["course_id"])
    if not curso:
        return jsonify({"error": "Curso no encontrado"}), 400
    curso.vector_store_id = data["vector_store_id"]
    db.session.commit()
    return jsonify({"status": "ok"})

# === Actualizar Asistente ===
@admin_bp.route("/actualizar_asistente", methods=["POST"])
def actualizar_asistente():
    data = request.get_json()
    asistente = Asistente.query.get(data["asistente_id"])
    if not asistente:
        return jsonify({"error": "Asistente no encontrado"}), 400
    asistente.vector_store_id = data["vector_store_id"]
    
    # Actualizar en OpenAI
    try:
        client.beta.assistants.update(
            asistente.asistente_id,
            tool_resources={"file_search": {"vector_store_ids": [data["vector_store_id"]]}} if data["vector_store_id"] else None
        )
    except Exception as e:
        return jsonify({"error": f"Error en OpenAI: {str(e)}"}), 500

    db.session.commit()
    return jsonify({"status": "ok"})