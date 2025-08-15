# worker/openai_utils/uploader.py

from shared.config import TEMP_DIR, OPENAI_API_KEY
from shared.models.db import Asistente, ArchivoProcesado
from shared.models.db_services import registrar_archivo
from openai import OpenAI
import os
import pandas as pd
import re
import time

# === CONFIGURACIÓN Y CLIENTE OPENAI ===
client = OpenAI(api_key=OPENAI_API_KEY)

# Asegurar que el directorio temporal exista
os.makedirs(TEMP_DIR, exist_ok=True)

# === EXTENSIONES PERMITIDAS ===
EXTENSIONES_DOCUMENTO = {
    "pdf", "doc", "docx", "xlsx", "csv", "txt", "md", "json", "xls"
}

EXTENSIONES_CODIGO = {
    "py", "r", "rmd", "cpp", "c", "java", "js", "ts", "html", "css", "ipynb", "sh", "sql"
}

# === FUNCIONES DE AYUDA ===
def es_documento_permitido(path):
    """
    Verifica si la extensión del archivo está permitida.
    """
    ext = os.path.splitext(path)[1][1:].lower()
    return ext in EXTENSIONES_DOCUMENTO or ext in EXTENSIONES_CODIGO

def es_archivo_codigo(path):
    """
    Verifica si el archivo es de código.
    """
    ext = os.path.splitext(path)[1][1:].lower()
    return ext in EXTENSIONES_CODIGO

def es_archivo_tabular(path):
    """
    Verifica si el archivo es un archivo de hoja de cálculo.
    """
    ext = os.path.splitext(path)[1][1:].lower()
    return ext in {"csv", "xls", "xlsx"}

def obtener_asistente_interno_por_subtipo(subtipo):
    """
    Obtiene un asistente interno de la base de datos por su subtipo.
    """
    asistente = Asistente.query.filter_by(
        categoria="interno",
        subtipo=subtipo
    ).first()
    if not asistente:
        raise Exception(f"Asistente interno no encontrado: {subtipo}")
    return asistente

# === CONVERSIÓN DE ARCHIVOS TABULARES A .TXT ===
def convertir_a_txt(path):
    """
    Convierte archivos .csv, .xls, .xlsx a .txt legible (formato tabulado).
    """
    ext = os.path.splitext(path)[1].lower()
    nuevo_path = path + ".txt"

    try:
        if ext == ".csv":
            df = pd.read_csv(path)
        elif ext == ".xls":
            df = pd.read_excel(path, engine='xlrd')
        elif ext == ".xlsx":
            df = pd.read_excel(path, engine='openpyxl')
        else:
            raise ValueError(f"Extensión no soportada para conversión: {ext}")

        # Guardar como texto plano con columnas separadas por tabuladores
        with open(nuevo_path, "w", encoding="utf-8") as f:
            # Escribir encabezados
            f.write("\t".join(df.columns.astype(str)) + "\n")
            # Escribir filas
            for _, row in df.iterrows():
                f.write("\t".join(row.astype(str)) + "\n")

        print(f"✅ {ext.upper()} convertido a TXT: {nuevo_path}")
        return nuevo_path

    except Exception as e:
        raise Exception(f"No se pudo convertir {path} a .txt: {e}")

# === ANÁLISIS DE CÓDIGO CON ASISTENTE DE OPENAI ===
def analizar_codigo_con_asistente(path, asistente_id):
    """
    Analiza un archivo de código usando un asistente de OpenAI y devuelve un informe detallado.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            contenido = f.read()

        if len(contenido) > 100_000:
            contenido = contenido[:100_000] + "\n\n... (contenido truncado)"

        print(f"🧠 Enviando código a {asistente_id} para análisis...")

        # Crear un thread
        thread = client.beta.threads.create()
        print(f"🧵 Thread creado: {thread.id}")

        # Enviar el contenido del código al asistente
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Por favor, analiza el siguiente código y genera un informe detallado:\n\n{contenido}"
        )
        print(f"💬 Mensaje enviado al thread {thread.id}")

        # Ejecutar el asistente
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=asistente_id
        )
        print(f"🚀 Run iniciado: {run.id}")

        # Esperar a que el run termine
        while run.status in ["queued", "in_progress"]:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            print(f"⏳ Run status: {run.status}")

        if run.status == "completed":
            print("✅ Run completado.")
        else:
            raise Exception(f"❌ Run falló: {run.status} - {run.last_error}")

        # Obtener la respuesta del asistente
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for msg in messages:
            if msg.role == "assistant":
                informe = msg.content[0].text.value
                print("📋 Informe generado por el asistente:")
                print(f"   {informe[:200]}...")
                return informe

        raise Exception("❌ No se recibió respuesta del asistente")

    except Exception as e:
        print(f"❌ Error al analizar código: {e}")
        raise

# === GENERAR NOMBRE DEL INFORME ===
def generar_nombre_informe(path):
    """
    Genera un nombre como 'archivo.py_informe.txt' a partir del nombre original.
    """
    base = os.path.basename(path)
    name = os.path.splitext(base)[0]
    return f"{name}_informe.txt"

# === SUBIR Y ASOCIAR ARCHIVO AL VECTOR STORE ===
def subir_y_asociar_archivo(path, vector_store_id, canvas_file_id, course_id, updated_at=None):
    """
    Sube un archivo al vector store de OpenAI. Si es código, lo analiza primero.
    Registra el archivo en la base de datos.
    """
    print(f"\n📤 INICIANDO SUBIDA: {os.path.basename(path)}")
    print(f"   Vector Store ID: {vector_store_id}")
    print(f"   Ruta: {path}")
    print(f"   Canvas File ID: {canvas_file_id}")
    print(f"   Course ID: {course_id}")

    # Validar existencia del archivo
    if not os.path.exists(path):
        raise Exception(f"❌ Archivo no encontrado: {path}")

    # Validar tipo de archivo
    if not es_documento_permitido(path):
        raise Exception(f"❌ Tipo no permitido: {os.path.basename(path)}")

    file_id = None
    temp_path = None

    try:
        # === 1. PROCESAR SEGÚN TIPO DE ARCHIVO ===
        if es_archivo_codigo(path):
            # ✅ Generar nombre del informe
            
            nombre_informe = generar_nombre_informe(path)
            ruta_informe = os.path.join(TEMP_DIR, nombre_informe)

            # ✅ Verificar si el informe ya fue subido (y no ha cambiado)
            registro_informe = ArchivoProcesado.query.filter_by(
                filename=nombre_informe,
                course_id=course_id
            ).first()

            if registro_informe and os.path.exists(ruta_informe):
                # ✅ Ya existe el informe, usarlo
                path_a_subir = ruta_informe
                nombre_final = nombre_informe
                print(f"📄 Usando informe existente: {ruta_informe}")
            else:
                # ✅ Generar nuevo informe
                print("🐍 ARCHIVO DE CÓDIGO → usando asistente interno")
                asistente = obtener_asistente_interno_por_subtipo("analizador_codigo")
                informe = analizar_codigo_con_asistente(path, asistente.asistente_id)

                temp_path = ruta_informe
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.write(informe)
                path_a_subir = temp_path
                nombre_final = nombre_informe

        elif es_archivo_tabular(path):
            nombre_txt = os.path.basename(path) + ".txt"
            ruta_txt = os.path.join(TEMP_DIR, nombre_txt)

            # ✅ Verificar si ya se convirtió
            registro_txt = ArchivoProcesado.query.filter_by(
                filename=nombre_txt,
                course_id=course_id
            ).first()

            if registro_txt and os.path.exists(ruta_txt):
                path_a_subir = ruta_txt
                nombre_final = nombre_txt
                print(f"📄 Usando TXT existente: {ruta_txt}")
            else:
                temp_path = convertir_a_txt(path)
                path_a_subir = temp_path
                nombre_final = nombre_txt

        else:
            print("📄 ARCHIVO DOCUMENTO → subiendo directamente")
            path_a_subir = path
            nombre_final = os.path.basename(path)

        # === 2. SUBIR A OPENAI ===
        print(f"⬆️ Subiendo a OpenAI: {nombre_final}")
        with open(path_a_subir, "rb") as f:
            file_response = client.files.create(file=f, purpose="assistants")
        file_id = file_response.id
        print(f"✅ Archivo subido a OpenAI. ID: {file_id}")

        # === 3. ASOCIAR AL VECTOR STORE ===
        print(f"🔗 Asociando al vector store {vector_store_id}...")
        vs_file = client.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_id
        )
        print(f"✅ Asociado al vector store. VS File ID: {vs_file.id}")

        # === 4. REGISTRAR EN BASE DE DATOS ===
        print(f"💾 Registrando en base de datos...")
        registrar_archivo(
            canvas_file_id=canvas_file_id,
            filename=nombre_final,
            updated_at=updated_at or str(os.path.getmtime(path)),
            file_id_openai=file_id,
            course_id=course_id
        )
        print(f"✅ Registro completado en DB.")

        return file_id

    except Exception as e:
        print(f"❌ ERROR FATAL al subir {os.path.basename(path)}: {str(e)}")
        if file_id:
            try:
                client.files.delete(file_id)
                print(f"🧹 Archivo {file_id} eliminado de OpenAI por fallo.")
            except Exception as del_e:
                print(f"⚠️ No se pudo eliminar {file_id} de OpenAI: {del_e}")
        raise

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print(f"🗑️ Temporal eliminado: {temp_path}")
            except Exception as e:
                print(f"❌ No se pudo eliminar temporal {temp_path}: {e}")


# +++++++++++++++++++++++++++++++++++++++++++++++++++
# === LISTAR ARCHIVOS DEL VECTOR STORE ===
def listar_archivos_vector_store(vector_store_id):
    """
    Lista los archivos asociados a un vector store.
    """
    try:
        vs_files = client.vector_stores.files.list(vector_store_id=vector_store_id).data
        archivos = []
        for f in vs_files:
            file_info = client.files.retrieve(f.id)
            archivos.append({
                "id": f.id,
                "name": file_info.filename,
                "created_at": file_info.created_at
            })
        print(f"🔍 {len(archivos)} archivos encontrados en vector store {vector_store_id}")
        return archivos
    except Exception as e:
        print(f"❌ Error al listar archivos del vector store {vector_store_id}: {e}")
        return []
