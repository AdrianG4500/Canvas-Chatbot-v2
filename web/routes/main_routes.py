# web/routes/main_routes.py
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from shared.models.db import db, HistorialConsulta, Hilo, Mensaje, Curso, Asistente, ArchivoProcesado
from shared.models.db_services import registrar_usuario, registrar_consulta
from markdown import markdown as md
from shared.helpers.helpers import extraer_fuentes, generar_respuesta_formateada
import time

main_bp = Blueprint('main', __name__)

@main_bp.route("/", methods=["GET", "POST"])
def index():
    respuesta_formateada = None
    course_id = session.get("course_id")
    user_id = session.get("user_id")

    if not course_id:
        respuesta_formateada = "⚠️ Esta aplicación debe usarse desde Canvas."
        return render_template("index.html", respuesta_index=md(respuesta_formateada))

    # Obtener curso y asistentes
    try:
        curso = Curso.query.get(course_id)
        asistentes = []
        if curso:
            # Obtener asistentes asociados al curso
            from shared.models.db import curso_asistente
            asistentes = db.session.query(Asistente) \
                .join(curso_asistente) \
                .filter(curso_asistente.c.course_id == course_id) \
                .all()
    except Exception as e:
        print(f"❌ Error cargando asistentes: {e}")
        asistentes = []

    consulta_id = None  # Inicializar

    if request.method == "POST":
        if not user_id or not course_id:
            respuesta_formateada = "⚠️ No se pudo identificar al usuario o curso."
        else:
            # Registrar usuario
            registrar_usuario(user_id, session.get("user_full_name", "Estudiante"))

            # Verificar límite mensual
            if not registrar_consulta(user_id, course_id):
                respuesta_formateada = "🚫 Has alcanzado el límite mensual de consultas."
            else:
                pregunta = request.form.get("pregunta", "").strip()
                asistente_id_seleccionado = request.form.get("asistente_id")

                if not pregunta:
                    respuesta_formateada = "⚠️ La pregunta no puede estar vacía."
                elif not asistente_id_seleccionado:
                    respuesta_formateada = "⚠️ Debes seleccionar un asistente."
                else:
                    # Generar ID único
                    consulta_id = f"consulta_{int(time.time())}"
                    nueva_consulta = HistorialConsulta(
                        consulta_id=consulta_id,
                        user_id=user_id,
                        course_id=course_id,
                        pregunta=pregunta,
                        asistente_id=asistente_id_seleccionado,
                        tipo="general",
                        estado="pendiente"
                    )
                    db.session.add(nueva_consulta)
                    db.session.commit()
                    user_name = session.get('user_full_name', 'Estudiante')
                    respuesta_formateada = f"""
                        <p><strong>🔍 Analizando tu pregunta, {user_name}</strong> <span class="loader"></span></p>
                        <p>Estoy revisando los materiales del curso para darte una respuesta precisa.</p>
                        <ul>
                        <li>📚 Revisando documentos, código y recursos...</li>
                        <li>🧠 Analizando el contexto académico...</li>
                        <li>📝 Preparando una respuesta clara...</li>
                        </ul>
                        <p>Este proceso puede tardar un poco. ¡Gracias por tu paciencia!</p>
                        """

    print(f"📤 [DEBUG] Renderizando index.html con:")
    print(f"   - respuesta_index: {respuesta_formateada}")
    print(f"   - consulta_id: {consulta_id}")
    print(f"   - user_id: {user_id}")
    print(f"   - course_id: {course_id}")

    return render_template(
        "index.html",
        respuesta_index=respuesta_formateada,
        asistentes=asistentes,
        curso_nombre=session.get("course_name", "Tu curso"),
        consulta_id=consulta_id  # ✅ Pasar al frontend
    )

    


@main_bp.route("/estado_consulta/<consulta_id>")
def estado_consulta(consulta_id):
    """
    Endpoint para que el frontend verifique si ya hay respuesta.
    Usado por el polling en index.html.
    """
    print(f"🔍 [DEBUG] Consultando estado de: {consulta_id}")
    consulta = HistorialConsulta.query.get(consulta_id)
    if not consulta:
        return jsonify({"error": "Consulta no encontrada"}), 404

    print(f"✅ [DEBUG] Estado: {consulta.estado}, respuesta_len={len(consulta.respuesta) if consulta.respuesta else 0}")
    return jsonify({
        "estado": consulta.estado,
        "respuesta": consulta.respuesta,
        "thread_id": consulta.thread_id
    })


@main_bp.route("/debug/consulta/<consulta_id>")
def debug_consulta(consulta_id):
    """Endpoint de depuración para ver el estado completo de una consulta."""
    print(f"🔍 [DEBUG] Consultando estado de: {consulta_id}")  # 🔥 Añadir este print
    consulta = HistorialConsulta.query.get(consulta_id)
    if not consulta:
        return jsonify({"error": "No encontrada"}), 404

    hilo = Hilo.query.get(consulta.thread_id) if consulta.thread_id else None
    mensajes = Mensaje.query.filter_by(thread_id=consulta.thread_id).all() if consulta.thread_id else []

    print(f"✅ [DEBUG] Estado actual: {consulta.estado}, respuesta_len={len(consulta.respuesta) if consulta.respuesta else 0}")
    return jsonify({
        "consulta": {
            "id": consulta.consulta_id,
            "pregunta": consulta.pregunta,
            "respuesta": consulta.respuesta,
            "estado": consulta.estado,
            "thread_id": consulta.thread_id,
            "timestamp": consulta.timestamp
        },
        "hilo": {
            "thread_id": hilo.thread_id if hilo else None,
            "asistente_id": hilo.asistente_id if hilo else None
        } if hilo else None,
        "mensajes": [
            {"pregunta": m.pregunta, "respuesta": m.respuesta, "timestamp": m.timestamp}
            for m in mensajes
        ]
    })


@main_bp.route("/admin")
def admin():
    """Panel de administración para ver historial y archivos."""
    try:
        # Obtener todos los cursos
        cursos_completos = Curso.query.all()
        if not cursos_completos:
            return render_template("admin.html", error="⚠️ No hay cursos registrados.", cursos=[], registros=[], historial=[], consultas=[], archivos_por_curso={})

        # Obtener registros de archivos procesados
        registros_db = ArchivoProcesado.query.all()

        # Obtener historial de consultas
        historial = HistorialConsulta.query \
            .order_by(HistorialConsulta.timestamp.desc()) \
            .limit(50).all()

        # Agrupar mensajes por hilo
        hilos_data = {}
        for h in Hilo.query.all():
            hilos_data[h.thread_id] = {
                "user_id": h.user_id,
                "course_id": h.course_id,
                "mensajes": []
            }

        for msg in Mensaje.query.order_by(Mensaje.timestamp).all():
            if msg.thread_id in hilos_data:
                hilos_data[msg.thread_id]["mensajes"].append({
                    "pregunta": msg.pregunta,
                    "respuesta": msg.respuesta,
                    "timestamp": msg.timestamp
                })

        return render_template("admin.html", historial=historial, hilos=hilos_data)

    except Exception as e:
        print(f"❌ Error en /admin: {e}")
        return render_template("admin.html", error="❌ Error al cargar el panel de administración.", cursos=[], registros=[], historial=[], consultas=[], archivos_por_curso={})

@main_bp.route("/reportar_feedback", methods=["POST"])
def reportar_feedback():
    data = request.get_json()
    consulta_id = data.get("consulta_id")
    feedback = data.get("feedback")

    # Guardar en CSV (para empezar)
    with open("feedback.csv", "a", encoding="utf-8") as f:
        f.write(f"{consulta_id},{feedback},{time.time()}\n")

    return jsonify({"status": "ok"})


@main_bp.route("/test")
def test_local():
    """Ruta temporal para pruebas locales."""
    session["user_id"] = "test_user_123"
    session["course_id"] = "91340000000002198"
    session["user_full_name"] = "Usuario de Prueba"
    session["course_name"] = "Microeconomia Aplicada MFE 2025"
    print("🔑 Sesión iniciada localmente con usuario de prueba.")
    return redirect("/")