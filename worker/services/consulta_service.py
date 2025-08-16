# services/consulta_service.py
from shared.models.db import db, HistorialConsulta, Curso, Hilo, Mensaje, UsoMensual
from shared.models.db_services import registrar_usuario
from openai import OpenAI
from shared.config import OPENAI_API_KEY
from shared.helpers.helpers import extraer_fuentes, procesar_respuesta_con_fuentes
import logging
import time
import datetime

client = OpenAI(api_key=OPENAI_API_KEY)
logger = logging.getLogger(__name__)

# ✅ No uses ThreadPoolExecutor global aquí → el worker lo maneja
# El worker ya corre en paralelo consultas y archivos

def procesar_consulta_individual(consulta_id):
    """Procesa una consulta individual dentro de un app_context"""
    session = db.session()
    try:
        consulta = session.query(HistorialConsulta).get(consulta_id)
        print(f"🔍 Consulta encontrada: {consulta_id}")
        print(f"   Estado actual: {consulta.estado}")
        print(f"   Pregunta: {consulta.pregunta}")
        if not consulta or consulta.estado != "pendiente":
            return

        if consulta not in session:
            consulta = session.merge(consulta)
        logger.info(f"🧵 Procesando consulta {consulta_id} para usuario {consulta.user_id}")

        curso = session.query(Curso).get(consulta.course_id)
        print(f"   🎓 Curso: {curso.nombre if curso else 'No encontrado'}")
        if not curso:
            raise Exception("Curso no encontrado")

        asistente_id = consulta.asistente_id
        print(f"   🤖 Asistente ID: {asistente_id}")
        if not asistente_id:
            raise Exception("Asistente no configurado para el curso")

        # === 1. OBTENER O CREAR HILO ===
        hilo = session.query(Hilo).filter_by(
            user_id=consulta.user_id,
            course_id=consulta.course_id
        ).first()

        if not hilo:
            try:
                print("   🧵 No existe hilo, creando nuevo...")
                thread = client.beta.threads.create()
                hilo = Hilo(
                    thread_id=thread.id,
                    user_id=consulta.user_id,
                    course_id=consulta.course_id,
                    asistente_id=asistente_id
                )
                session.add(hilo)
                session.commit()
                logger.info(f"🧵 Hilo creado: {thread.id}")
            except Exception as e:
                logger.error(f"❌ Error creando hilo: {e}")
                consulta.estado = "error"
                consulta.respuesta = f"Error al crear conversación: {str(e)}"
                session.commit()
                return
        else:
            print(f"   🧵 Hilo existente: {hilo.thread_id}")

        # === 2. ENVIAR A OPENAI ===
        try:
            client.beta.threads.messages.create(
                thread_id=hilo.thread_id,
                role="user",
                content=consulta.pregunta
            )

            run = client.beta.threads.runs.create(
                thread_id=hilo.thread_id,
                assistant_id=asistente_id
            )

            while run.status in ["queued", "in_progress"]:
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(
                    thread_id=hilo.thread_id,
                    run_id=run.id
                )

            if run.status != "completed":
                raise Exception(f"Run falló: {run.last_error}")

            messages = client.beta.threads.messages.list(thread_id=hilo.thread_id)
            respuesta_recibida = None
            for msg in messages:
                if msg.role == "assistant":
                    respuesta_recibida = msg.content[0].text.value
                    break

            if not respuesta_recibida:
                raise Exception("No se recibió respuesta")

            texto_limpio, fuentes = procesar_respuesta_con_fuentes(respuesta_recibida)

            print(f"   🤖 Respuesta recibida: {respuesta_recibida[:100]}...")  # Muestra solo los primeros 100 caracteres
            # === 3. ACTUALIZAR CONSULTA ===
            try:
                consulta.respuesta = texto_limpio
                consulta.estado = "completado"
                consulta.thread_id = hilo.thread_id
                #print(f"   📦 Antes del commit: respuesta='{consulta.respuesta}'")
                #session.flush() 
                #session.commit()  # ✅ ¡Commit inmediato!
                logger.info(f"✅ Respuesta guardada en DB")
            except Exception as e:
                session.rollback()
                logger.error(f"❌ Error al guardar respuesta: {e}")

            # === 4. GUARDAR MENSAJE ===
            mensaje = Mensaje(
                mensaje_id=f"msg_{int(time.time())}",
                thread_id=hilo.thread_id,
                pregunta=consulta.pregunta,
                respuesta=texto_limpio,
                fuentes=fuentes
            )
            session.add(mensaje)

            # print consulta object
            print(f" Consulta despues de guardar mensaje: {consulta.consulta_id}, estado: {consulta.estado}, respuesta: {consulta.respuesta}")
            # === 5. ACTUALIZAR USO MENSUAL ===
            mes = datetime.date.today().replace(day=1)
            uso = session.query(UsoMensual).filter_by(
                user_id=consulta.user_id,
                course_id=consulta.course_id,
                mes=mes
            ).first()

            if uso:
                uso.total += 1
            else:
                nuevo_uso = UsoMensual(
                    user_id=consulta.user_id,
                    course_id=consulta.course_id,
                    mes=mes,
                    total=1
                )
                session.add(nuevo_uso)

            # Imprimir el objeto consulta
            print(f" Consulta despues de uso mensual: {consulta.consulta_id}, estado: {consulta.estado}, respuesta: {consulta.respuesta}")
            session.commit()
            logger.info(f"✅ Consulta {consulta_id} completada")

        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error con OpenAI: {e}")
            if consulta.estado != "error":
                consulta.estado = "error"   
                consulta.respuesta = str(e)
                session.commit()

    except Exception as e:
        logger.error(f"❌ Error procesando {consulta_id}: {e}")
        session.rollback()
    finally:
        session.close()  # ✅ Cierra la sesión

def procesar_nuevas_consultas():
    """Busca y procesa consultas pendientes (una por una, seguro)"""
    # Esta función será llamada por el worker con app_context
    pendientes = HistorialConsulta.query.filter_by(estado="pendiente").all()
    if not pendientes:
        return

    logger.info(f"📩 Iniciando procesamiento de {len(pendientes)} consultas pendientes")

    # ✅ Procesar una por una (más seguro que ThreadPool)
    for consulta in pendientes:
        try:
            procesar_consulta_individual(consulta.consulta_id)  # Usa la app registrada
        except Exception as e:
            logger.error(f"❌ Error procesando {consulta.consulta_id}: {e}")

    