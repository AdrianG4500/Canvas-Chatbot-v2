# worker/services/procesamiento_service.py
from openai import OpenAI
from shared.config import OPENAI_API_KEY, TEMP_DIR
from shared.models.db_services import obtener_asistente_interno_por_subtipo
import os
import time


client = OpenAI(api_key=OPENAI_API_KEY)

def analizar_codigo_con_asistente(path, asistente_id):
    """
    Analiza un archivo de código usando un asistente de OpenAI
    y devuelve el informe generado.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            contenido = f.read()

        if len(contenido) > 100_000:
            contenido = contenido[:100_000] + "\n\n... (truncado)"

        print(f"🧠 Enviando código a {asistente_id} para análisis...")

        # Crear thread
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Por favor, analiza el siguiente código y genera un informe detallado:\n\n{contenido}"
        )

        # Ejecutar run
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=asistente_id
        )

        # Esperar a que termine
        while run.status not in ["completed", "failed"]:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )

        if run.status == "failed":
            raise Exception(f"Run falló: {run.last_error}")

        # Obtener respuesta
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for msg in messages:
            if msg.role == "assistant":
                return msg.content[0].text.value

        raise Exception("No se recibió respuesta del asistente")

    except Exception as e:
        raise Exception(f"Error al analizar código con asistente: {e}")

def generar_nombre_informe(path):
    """Genera un nombre como 'archivo.py_informe.txt'"""
    base = os.path.basename(path)
    name = os.path.splitext(base)[0]
    return f"{name}_informe.txt"