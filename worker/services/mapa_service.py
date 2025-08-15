# worker/services/mapa_service.py
from openai import OpenAI
from shared.config import OPENAI_API_KEY
import time

client = OpenAI(api_key=OPENAI_API_KEY)

def generar_mapa_mental(contenido):
    """Genera un mapa mental en Mermaid.js a partir de contenido"""
    try:
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Genera un mapa mental en formato Mermaid.js del siguiente contenido:\n\n{contenido}"
        )
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id="asst_mapas_mentales"  # ID real del asistente
        )

        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        return messages.data[0].content[0].text.value
    except Exception as e:
        return f"❌ Error: {e}"