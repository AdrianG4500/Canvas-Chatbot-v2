# worker/services/archivo_service.py
import os
from shared.models.db import db
from canvas.downloader import get_all_course_files, download_file
from openai_utils.uploader import subir_y_asociar_archivo
from shared.models.db import Curso, ArchivoProcesado
import logging
import time

logger = logging.getLogger(__name__)
ultima_ejecucion = {}

def normalizar_fecha(fecha):
    """
    Convierte cualquier formato de fecha a 'YYYY-MM-DD HH:MM:SS'
    Maneja: str, datetime, con T/Z, sin T/Z, etc.
    """
    if not fecha:
        return None
    if isinstance(fecha, str):
        # Reemplazar T por espacio y quitar Z
        fecha = fecha.replace("T", " ").replace("Z", "")
        return fecha[:19]  # Solo hasta segundos
    elif hasattr(fecha, 'strftime'):  # Es datetime
        return fecha.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return str(fecha)[:19]

def sincronizar_archivos_canvas():
    """Sincroniza archivos de Canvas con Supabase y OpenAI (cada 30 min por curso)"""
    cursos = Curso.query.all()
    if not cursos:
        logger.info("📭 No hay cursos registrados")
        return

    for curso in cursos:
        course_id = curso.course_id

        # ✅ 1. Ejecutar solo cada 30 minutos
        ahora = time.time()
        ultima = ultima_ejecucion.get(course_id, 0)
        if ahora - ultima < 30 * 60:  # 30 minutos
            continue
        ultima_ejecucion[course_id] = ahora

        try:
            logger.info(f"🔄 Procesando curso: {curso.course_id}")
            archivos_canvas = get_all_course_files(curso.course_id)
            if not archivos_canvas:
                logger.info(f"📭 No hay archivos en Canvas para el curso {curso.course_id}")
                continue

            # ✅ 2. Crear mapa de archivos en Canvas: {canvas_file_id: archivo}
            ids_en_canvas = {str(a["id"]): a for a in archivos_canvas}

            # ✅ 3. Obtener registros de la DB para este curso
            registros_db = {
                r.canvas_file_id: r
                for r in ArchivoProcesado.query.filter_by(course_id=curso.course_id)
            }

            # ✅ 4. Detectar nuevos o actualizados
            nuevos_o_actualizados = []
            for canvas_id, archivo in ids_en_canvas.items():
                registro = registros_db.get(canvas_id)
                updated_at_canvas = archivo.get("updated_at")

                # ⭐ Mostrar comparación
                print(f"\n📄 Archivo: {archivo['filename']}")
                print(f"   Canvas ID: {canvas_id}")
                print(f"   updated_at (Canvas): '{updated_at_canvas}' (tipo: {type(updated_at_canvas).__name__})")

                # ✅ Usar normalización consistente
                updated_at_canvas_norm = normalizar_fecha(updated_at_canvas)
                updated_at_db_norm = normalizar_fecha(registro.updated_at) if registro else None

                if registro:
                    print(f"   updated_at (DB):     '{updated_at_db_norm}'")
                    print(f"   ¿Iguales?            {updated_at_canvas_norm == updated_at_db_norm}")

                if not registro or updated_at_canvas_norm != updated_at_db_norm:
                    nuevos_o_actualizados.append(archivo)
                    print(f" 🔴 Será procesado (cambio detectado)")
                else:
                    print(f" ✅ No requiere actualización")

            logger.info(f"📦 {len(nuevos_o_actualizados)} archivos nuevos/actualizados")

            # ✅ 5. Procesar solo los que necesitan actualización
            for archivo in nuevos_o_actualizados:
                try:
                    path = download_file(archivo)
                    file_id = subir_y_asociar_archivo(
                        path=path,
                        vector_store_id=curso.vector_store_id,
                        canvas_file_id=str(archivo["id"]),
                        course_id=curso.course_id,
                        updated_at=archivo.get("updated_at")
                    )
                    os.remove(path)
                    logger.info(f"✅ Procesado: {archivo['filename']}")

                except Exception as e:
                    logger.error(f"❌ Error con {archivo['filename']}: {str(e)}")

        except Exception as e:
            logger.error(f"❌ Error procesando curso {curso.course_id}: {e}")

