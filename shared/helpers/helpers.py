import re

def extraer_fuentes(respuesta):
    """
    Extrae fuentes del formato: [Fuente: archivo.pdf] o (archivo.py)
    """
    # Ajusta el patrón según cómo tu asistente devuelve las fuentes
    fuentes = re.findall(r'\[Fuente:\s*([^\]]+)\]', respuesta)
    if not fuentes:
        fuentes = re.findall(r'\(([^)]+\.(pdf|py|R|ipynb|txt|docx))\)', respuesta)
    return fuentes or ["Documentos del curso"]


def procesar_respuesta_con_fuentes(respuesta):
    """
    - Extrae fuentes del formato OpenAI: 【64:0†archivo.pdf】
    - Convierte texto plano con - en listas Markdown
    - Añade saltos de línea entre párrafos
    - Devuelve texto con formato mejorado y lista de fuentes
    """
    # Extraer fuentes
    patron_fuente = r'【[^†]*†([^】]+)】'
    fuentes = re.findall(patron_fuente, respuesta)
    fuentes_unicas = list(set(fuentes))

    # Eliminar fuentes del texto
    texto_limpio = re.sub(patron_fuente, "", respuesta)

    # Añadir saltos de línea antes de números o títulos
    texto_limpio = re.sub(r'(\d+\. [A-Z])', r'\n\n\1', texto_limpio)  # 1. Geocodificación → \n\n1. Geocodificación
    texto_limpio = re.sub(r'(### [^-\n])', r'\n\n\1', texto_limpio)   # ### Sugerencias → \n\n### Sugerencias

    # Convertir "- Propósito:" en listas Markdown
    # Asegura que cada - esté precedido por \n si no lo está
    lines = texto_limpio.split('\n')
    processed_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- ') and not line.startswith('  - ') and not line.startswith('- '):
            processed_lines.append(f"- {stripped[2:]}")
        else:
            processed_lines.append(line)

    texto_formateado = '\n'.join(processed_lines)

    # Añadir fuentes al final en Markdown
    if fuentes_unicas:
        fuentes_md = "\n\n---\n\n**📄 Fuentes utilizadas:**\n" + "\n".join([f"- `{fuente}`" for fuente in fuentes_unicas])
        texto_final = texto_formateado + fuentes_md
    else:
        texto_final = texto_formateado

    return texto_final, fuentes_unicas

def limpiar_respuesta_openai(respuesta):
    """
    Limpia y normaliza la respuesta del asistente.
    """
    return respuesta.strip()

def generar_id_unico():
    """
    Genera un ID único para consultas o archivos.
    """
    import time
    return f"item_{int(time.time())}"

def generar_respuesta_formateada(user_name, course_name, nro_consulta, restantes, texto_respuesta, fuentes):
    fuentes_html = "".join([f"<li>{fuente}</li>" for fuente in fuentes])
    return f"""
    <p><strong>¡Hola {user_name}!</strong></p>
    <p>Consulta #{nro_consulta} respondida sobre <strong>{course_name}</strong>.</p>
    <p>{texto_respuesta}</p>
    <details>
        <summary>📄 Fuentes utilizadas</summary>
        <ul>{fuentes_html}</ul>
    </details>
    <p><em>Tienes {restantes} consultas restantes este mes.</em></p>
    """