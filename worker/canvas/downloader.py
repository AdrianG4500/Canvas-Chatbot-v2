# worker/canvas/downloader.py
import os
import requests
from shared.config import CANVAS_TOKEN, CANVAS_BASE_URL, TEMP_DIR

def get_all_course_files(course_id):
    """Obtiene todos los archivos de un curso de Canvas (con paginación)"""
    if not course_id:
        raise ValueError("course_id es requerido")

    headers = {"Authorization": f"Bearer {CANVAS_TOKEN}"}
    url = f"{CANVAS_BASE_URL}/courses/{course_id}/files"
    params = {'per_page': 100}
    todos_los_archivos = []

    while url:
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            archivos = response.json()
            todos_los_archivos.extend(archivos)

            # Manejar paginación
            next_url = None
            if 'Link' in response.headers:
                links = response.headers['Link'].split(',')
                for link in links:
                    if 'rel="next"' in link:
                        next_url = link.split('<')[1].split('>')[0]
                        break
            url = next_url
            params = None

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error al obtener archivos de Canvas: {e}")

    return todos_los_archivos

def download_file(file_info):
    """Descarga un archivo de Canvas y lo guarda temporalmente"""
    file_name = file_info['filename'].replace(' ', '_')
    download_url = file_info['url']

    try:
        response = requests.get(
            download_url,
            headers={"Authorization": f"Bearer {CANVAS_TOKEN}"},
            timeout=30
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error al descargar {file_name}: {e}")

    # Asegurar directorio temporal
    os.makedirs(TEMP_DIR, exist_ok=True)
    file_path = os.path.join(TEMP_DIR, file_name)

    with open(file_path, 'wb') as f:
        f.write(response.content)

    return file_path