# shared/models/db.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Table


db = SQLAlchemy()

# Modelos (ejemplos clave)
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    user_id = db.Column(db.String, primary_key=True)
    nombre = db.Column(db.String, nullable=False)
    email = db.Column(db.String)
    rol = db.Column(db.String, nullable=False)

class Curso(db.Model):
    __tablename__ = 'cursos'
    course_id = db.Column(db.String, primary_key=True)
    nombre = db.Column(db.String, nullable=False)
    lti_deployment_id = db.Column(db.String)
    vector_store_id = db.Column(db.String)
    asistente_principal_id = db.Column(db.String)

class Asistente(db.Model):
    __tablename__ = 'asistentes'
    asistente_id = db.Column(db.String, primary_key=True)
    nombre = db.Column(db.String, nullable=False)
    categoria = db.Column(db.String)
    subtipo = db.Column(db.String)
    modelo = db.Column(db.String)
    temperatura = db.Column(db.Numeric)
    top_p = db.Column(db.Numeric)
    instrucciones = db.Column(db.Text)
    vector_store_id = db.Column(db.String)
    creado_en = db.Column(db.DateTime, default=db.func.now())

class ArchivoProcesado(db.Model):
    __tablename__ = 'archivos_procesados'
    canvas_file_id = db.Column(db.String, primary_key=True)
    course_id = db.Column(db.String, db.ForeignKey('cursos.course_id'), nullable=False)
    filename = db.Column(db.String, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    file_id_openai = db.Column(db.String, nullable=False)

class HistorialConsulta(db.Model):
    __tablename__ = 'historial_consultas'
    consulta_id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('usuarios.user_id'))
    course_id = db.Column(db.String, db.ForeignKey('cursos.course_id'))
    thread_id = db.Column(db.String)
    asistente_id = db.Column(db.String)
    tipo = db.Column(db.String, nullable=False)
    estado = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    pregunta = db.Column(db.Text, nullable=False)
    respuesta = db.Column(db.Text)

class UsoMensual(db.Model):
    __tablename__ = 'uso_mensual'
    user_id = db.Column(db.String, db.ForeignKey('usuarios.user_id'), primary_key=True)
    course_id = db.Column(db.String, db.ForeignKey('cursos.course_id'), primary_key=True)
    mes = db.Column(db.Date, primary_key=True)
    total = db.Column(db.Integer, default=0)

class Hilo(db.Model):
    __tablename__ = 'hilos'
    thread_id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('usuarios.user_id'))
    course_id = db.Column(db.String, db.ForeignKey('cursos.course_id'))
    asistente_id = db.Column(db.String)
    creado_en = db.Column(db.DateTime, default=db.func.now())

class Mensaje(db.Model):
    __tablename__ = 'mensajes'
    mensaje_id = db.Column(db.String, primary_key=True)
    thread_id = db.Column(db.String, db.ForeignKey('hilos.thread_id'), nullable=False)
    pregunta = db.Column(db.Text, nullable=False)
    respuesta = db.Column(db.Text)
    fuentes = db.Column(db.JSON)  # Ej: ["archivo1.pdf", "datos.csv"]
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

curso_asistente = Table(
    'curso_asistente',
    db.Model.metadata,
    db.Column('course_id', db.String, db.ForeignKey('cursos.course_id')),
    db.Column('asistente_id', db.String, db.ForeignKey('asistentes.asistente_id')),
    db.Column('rol', db.String, nullable=False)  # ej: "principal", "evaluador", "reflexivo", "conceptual"
)