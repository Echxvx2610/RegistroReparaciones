from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Reparacion(db.Model):
    __tablename__ = 'reparaciones'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # nueva clave primaria
    serial_number = db.Column(db.String(50), nullable=False)  # ya no es clave
    item = db.Column(db.String(100), nullable=False)
    familia = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    area = db.Column(db.String(100), nullable=False)
    centro_costo = db.Column(db.String(100), nullable=False)
    semana = db.Column(db.String(20), nullable=False)
    fecha_registro = db.Column(db.String, nullable=False)
    numero_empleado = db.Column(db.String(50), nullable=False)
    nombre_empleado_completo = db.Column(db.String(200), nullable=False)
    nombre_empleado = db.Column(db.String(100), nullable=False)
    apellido_empleado = db.Column(db.String(100), nullable=False)
    puesto = db.Column(db.String(100), nullable=False)
    turno = db.Column(db.String(50), nullable=False)
    codigo_falla = db.Column(db.String(50), nullable=False)
    descripcion_falla = db.Column(db.String(200), nullable=False)
    descripcion_defecto = db.Column(db.String(200), nullable=False)
    ref_esquematico = db.Column(db.String(100), nullable=True)
    item_pn = db.Column(db.String(100), nullable=True)
    secuencia = db.Column(db.String, nullable=False)
    tiempo_reparacion = db.Column(db.String,nullable=False)

    def __repr__(self):
        return f"<Reparacion {self.id} - {self.serial_number} - {self.item}>"
