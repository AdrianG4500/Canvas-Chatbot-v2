# web/Dockerfile
FROM python:3.10-slim

# Evita que los logs se almacenen en bufer
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Puerto (Render lo maneja)
EXPOSE 5000

# Comando de inicio
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]