# shared/models/db_services.py
from .db import db
from shared.helpers.helpers import normalizar_fecha

def registrar_archivo(canvas_file_id, filename, updated_at, file_id_openai, course_id):
    """Registra o actualiza un archivo procesado"""
    from .db import ArchivoProcesado

    # ✅ Normalizar updated_at a formato limpio
    updated_at = normalizar_fecha(updated_at)

    registro = ArchivoProcesado.query.filter_by(
        canvas_file_id=canvas_file_id,
        course_id=course_id
    ).first()

    if registro:
        # ✅ Actualizar solo si changed
        if str(registro.updated_at) != str(updated_at):
            registro.filename = filename
            registro.updated_at = updated_at
            registro.file_id_openai = file_id_openai
            db.session.commit()
            print(f"🔄 Archivo actualizado: {canvas_file_id}")
        else:
            print(f"🔁 Sin cambios: {canvas_file_id}")
    else:
        # ✅ Crear nuevo
        registro = ArchivoProcesado(
            canvas_file_id=canvas_file_id,
            filename=filename,
            updated_at=updated_at,
            file_id_openai=file_id_openai,
            course_id=course_id
        )
        db.session.add(registro)
        db.session.commit()
        print(f"✅ Nuevo archivo registrado: {canvas_file_id}")

    return registro


def obtener_asistente_interno_por_subtipo(subtipo):
    """
    Obtiene un asistente interno por su subtipo (ej: 'analizador_codigo').
    """
    from .db import Asistente  # Importación diferida

    try:
        asistente = Asistente.query.filter_by(
            categoria="interno",
            subtipo=subtipo
        ).first()

        if not asistente:
            raise Exception(f"Asistente interno no encontrado: {subtipo}")

        print(f"✅ Asistente encontrado: {asistente.asistente_id} ({asistente.subtipo})")
        return asistente

    except Exception as e:
        print(f"❌ Error al obtener asistente interno {subtipo}: {e}")
        raise


def registrar_usuario(user_id, nombre, email=None, rol="estudiante"):
    """Registra un usuario si no existe."""
    from .db import Usuario
    try:
        usuario = Usuario.query.get(user_id)
        if not usuario:
            usuario = Usuario(user_id=user_id, nombre=nombre, email=email, rol=rol)
            db.session.add(usuario)
            db.session.commit()
        return usuario
    except Exception as e:
        db.session.rollback()
        raise

def registrar_consulta(user_id, course_id):
    """
    Verifica y registra el uso mensual de consultas.
    Retorna True si el usuario puede consultar, False si superó el límite.
    """
    from .db import db, UsoMensual
    from datetime import date

    mes_actual = date.today().replace(day=1)

    uso = UsoMensual.query.filter_by(
        user_id=user_id,
        course_id=course_id,
        mes=mes_actual
    ).first()

    LIMITE_CONSULTAS = 25  # Ajustable

    if uso and uso.total >= LIMITE_CONSULTAS:
        return False

    if not uso:
        uso = UsoMensual(
            user_id=user_id,
            course_id=course_id,
            mes=mes_actual,
            total=0
        )
        db.session.add(uso)

    uso.total += 1
    db.session.commit()
    return True

def registrar_consulta_completa(user_id, course_id, user_full_name, course_name, pregunta, respuesta):
    """
    Registra una consulta completa en el historial.
    """
    from .db import HistorialConsulta

    try:
        consulta = HistorialConsulta(
            user_id=user_id,
            course_id=course_id,
            pregunta=pregunta,
            respuesta=respuesta,
            tipo="general",
            estado="completado"
        )
        db.session.add(consulta)
        db.session.commit()
        print(f"✅ Consulta registrada para usuario {user_id}")
        return consulta
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al registrar consulta: {e}")
        raise