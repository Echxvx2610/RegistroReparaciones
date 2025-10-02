from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import pandas as pd
from models import db, Reparacion
from resources.tools.typewriter import (
    load_excel_data, search_assembly_info, get_current_user, 
    load_data_user, SerialNumberManager
)
import os 
import webbrowser
import sqlite3
import csv
from datetime import datetime

# Importar el gestor de datos actualizado
from data_manager import (
    get_database_path, ensure_data_files, get_excel_path, 
    sync_files_from_network
)

# Importar secret key de variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Crear instancia de app
app = Flask(__name__)

# Configurar la base de datos SQLite
database_path = get_database_path()
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Inicializar la base de datos
db.init_app(app)

# Permite CORS de cualquier origen (en desarrollo)
CORS(app, origins="*")

# Inicializar el manager de números de serie
serial_manager = SerialNumberManager()

# Asegurar que los archivos de datos estén disponibles
ensure_data_files()

print(f"Base de datos SQLite configurada en: {database_path}")

def parse_serial_number(serial):
    try:
        parts = serial.strip().split()
        if len(parts) != 2:
            return None
        
        left_part, job = parts[0], parts[1]
        
        # Verificar que tenga al menos los componentes mínimos
        if len(left_part) < 14:
            return None
        
        # Extraer componentes fijos
        default_char = left_part[0]  # Siempre posición 0
        identificador = left_part[1:5]  # Posiciones 1-4 (4 caracteres)
        fecha_hex = left_part[5:8]  # Posiciones 5-7 (3 caracteres)
        
        # El ensamble es todo lo que queda después de los componentes fijos
        ensamble_raw = left_part[8:]  # Desde posición 8 hasta el final
        
        # Formatear el ensamble según su longitud
        if len(ensamble_raw) == 7:
            # Caso normal: 7 caracteres -> 003-XXXXX-YZ
            ensamble_formateado = f"003-{ensamble_raw[:-2]}-{ensamble_raw[-2:]}"
        elif len(ensamble_raw) == 8:
            # Caso especial: 8 caracteres -> 003-XXXXX-YZW
            ensamble_formateado = f"003-{ensamble_raw[:-3]}-{ensamble_raw[-3:]}"
        elif len(ensamble_raw) == 6:
            # Nuevo caso: 6 caracteres -> 003-XXXX-YY
            ensamble_formateado = f"003-{ensamble_raw[:-2]}-{ensamble_raw[-2:]}"
        else:
            # Otros casos: mantener formato original pero con prefijo
            ensamble_formateado = f"003-{ensamble_raw}"
        
        return {
            "identificador": identificador,
            "fecha_hex": fecha_hex,
            "ensamble_formateado": ensamble_formateado,
            "ensamble_raw": ensamble_raw,  # Agregado para debug
            "job": job,
            "longitud_ensamble": len(ensamble_raw)  # Agregado para debug
        }
        
    except Exception as e:
        print(f"Error al analizar el número de serie: {e}")
        return None

def serial_exists_in_db(serial_number, job, sequence):
    """
    Función para verificar si un serial específico ya existe en la base de datos
    """
    try:
        existing = Reparacion.query.filter_by(
            serial_number=serial_number
        ).first()
        return existing is not None
    except Exception as e:
        print(f"Error al verificar duplicado en base de datos: {e}")
        return False

def save_register(data):
    """
    Guardar registro en la base de datos SQLite usando SQLAlchemy
    """
    try:
        # Crear nueva instancia del modelo
        nueva_reparacion = Reparacion(
            serial_number=data.get('serialNumber', ''),
            item=data.get('item', ''),
            familia=data.get('familia', ''),
            descripcion=data.get('descripcion', ''),
            area=data.get('area', ''),
            centro_costo=data.get('centroCosto', ''),
            semana=data.get('semana', ''),
            fecha_registro=data.get('fechaRegistro', ''),
            numero_empleado=data.get('numeroEmpleado', ''),
            nombre_empleado_completo=data.get('nombreEmpleadoCompleto', ''),
            nombre_empleado=data.get('nombreEmpleado', ''),
            apellido_empleado=data.get('apellidoEmpleado', ''),
            puesto=data.get('puesto', ''),
            turno=data.get('turno', ''),
            codigo_falla=data.get('codigoFalla', ''),
            descripcion_falla=data.get('descripcionFalla', ''),
            descripcion_defecto=data.get('descripcionDefecto', ''),
            ref_esquematico=data.get('refEsquematico', ''),
            item_pn=data.get('itemPN', ''),
            secuencia=data.get('secuencia', ''),
            tiempo_reparacion=data.get('tiempoReparacion', '')
        )

        db.session.add(nueva_reparacion)
        db.session.commit()
        
        print("Registro guardado exitosamente en la base de datos SQLite!")
        return True
        
    except Exception as e:
        print(f"Error al guardar en la base de datos: {e}")
        db.session.rollback()
        return False

@app.route("/ingenieria")
def ingenieria_login():
    """Página de login para ingeniería"""
    return send_from_directory("templates", "ingenieria-login.html")

@app.route("/ingenieria/dashboard")
def ingenieria_dashboard():
    """Página de dashboard para ingeniería"""
    return send_from_directory("templates", "ingenieria-dashboard.html")

@app.route("/api/ingenieria/login", methods=["POST"])
def ingenieria_auth():
    """Endpoint para autenticación de ingeniería"""
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        #INGENIERIA_PASSWORD = 
        
        if password == INGENIERIA_PASSWORD:
            return jsonify({
                "success": True,
                "message": "Autenticación exitosa"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Contraseña incorrecta"
            }), 401
            
    except Exception as e:
        print(f"Error en autenticación: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/ingenieria/stats", methods=["GET"])
def ingenieria_stats():
    """Endpoint para obtener estadísticas del dashboard"""
    try:
        fecha_inicio = request.args.get('fecha_inicio', None)
        fecha_fin = request.args.get('fecha_fin', None)
        
        # Query base
        query = Reparacion.query
        
        # Aplicar filtros de fecha si se proporcionan
        if fecha_inicio:
            query = query.filter(Reparacion.fecha_registro >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Reparacion.fecha_registro <= fecha_fin)
        
        # Estadísticas generales
        total_reparaciones = query.count()
        
        # Reparaciones por área
        reparaciones_por_area = db.session.query(
            Reparacion.area,
            db.func.count(Reparacion.id).label('count')
        ).filter(
            (Reparacion.fecha_registro >= fecha_inicio if fecha_inicio else True) &
            (Reparacion.fecha_registro <= fecha_fin if fecha_fin else True)
        ).group_by(Reparacion.area).all()
        
        # Top 10 códigos de falla más comunes
        top_fallas = db.session.query(
            Reparacion.codigo_falla,
            Reparacion.descripcion_falla,
            db.func.count(Reparacion.id).label('count')
        ).filter(
            (Reparacion.fecha_registro >= fecha_inicio if fecha_inicio else True) &
            (Reparacion.fecha_registro <= fecha_fin if fecha_fin else True)
        ).group_by(Reparacion.codigo_falla, Reparacion.descripcion_falla)\
         .order_by(db.func.count(Reparacion.id).desc())\
         .limit(10).all()
        
        # Reparaciones por familia
        reparaciones_por_familia = db.session.query(
            Reparacion.familia,
            db.func.count(Reparacion.id).label('count')
        ).filter(
            (Reparacion.fecha_registro >= fecha_inicio if fecha_inicio else True) &
            (Reparacion.fecha_registro <= fecha_fin if fecha_fin else True)
        ).group_by(Reparacion.familia)\
         .order_by(db.func.count(Reparacion.id).desc())\
         .limit(10).all()
        
        # Reparaciones por turno
        reparaciones_por_turno = db.session.query(
            Reparacion.turno,
            db.func.count(Reparacion.id).label('count')
        ).filter(
            (Reparacion.fecha_registro >= fecha_inicio if fecha_inicio else True) &
            (Reparacion.fecha_registro <= fecha_fin if fecha_fin else True)
        ).group_by(Reparacion.turno).all()
        
        # Tiempo promedio de reparación por área
        tiempo_promedio_area = db.session.query(
            Reparacion.area,
            db.func.avg(db.cast(Reparacion.tiempo_reparacion, db.Float)).label('avg_time')
        ).filter(
            (Reparacion.fecha_registro >= fecha_inicio if fecha_inicio else True) &
            (Reparacion.fecha_registro <= fecha_fin if fecha_fin else True)
        ).group_by(Reparacion.area).all()
        
        reparaciones_por_semana_raw = db.session.query(
            Reparacion.semana,
            db.func.count(Reparacion.id).label('count')
        ).filter(
            (Reparacion.fecha_registro >= fecha_inicio if fecha_inicio else True) &
            (Reparacion.fecha_registro <= fecha_fin if fecha_fin else True)
        ).group_by(Reparacion.semana).all()
        
        # Ordenar por número de semana extraído
        def extraer_numero_semana(semana_str):
            try:
                # Extraer número de "Wk 12" -> 12
                return int(semana_str.replace('Wk', '').replace('wk', '').strip())
            except:
                return 0
        
        reparaciones_por_semana = sorted(
            [{"semana": semana, "count": count} for semana, count in reparaciones_por_semana_raw],
            key=lambda x: extraer_numero_semana(x['semana'])
        )
        
        reparaciones_por_empleado = db.session.query(
            Reparacion.nombre_empleado_completo,
            db.func.count(Reparacion.id).label('count')
        ).filter(
            (Reparacion.fecha_registro >= fecha_inicio if fecha_inicio else True) &
            (Reparacion.fecha_registro <= fecha_fin if fecha_fin else True),
            Reparacion.nombre_empleado_completo.isnot(None),
            Reparacion.nombre_empleado_completo != ''
        ).group_by(Reparacion.nombre_empleado_completo)\
         .order_by(db.func.count(Reparacion.id).desc())\
         .limit(10).all()
        
        top_empleados = db.session.query(
            Reparacion.nombre_empleado_completo
        ).filter(
            (Reparacion.fecha_registro >= fecha_inicio if fecha_inicio else True) &
            (Reparacion.fecha_registro <= fecha_fin if fecha_fin else True),
            Reparacion.nombre_empleado_completo.isnot(None),
            Reparacion.nombre_empleado_completo != ''
        ).group_by(Reparacion.nombre_empleado_completo)\
         .order_by(db.func.count(Reparacion.id).desc())\
         .limit(5).all()
        
        top_empleados_nombres = [emp[0] for emp in top_empleados]
        
        # Obtener reparaciones por semana para cada empleado top
        reparaciones_semana_empleado = {}
        for empleado in top_empleados_nombres:
            datos_raw = db.session.query(
                Reparacion.semana,
                db.func.count(Reparacion.id).label('count')
            ).filter(
                Reparacion.nombre_empleado_completo == empleado,
                (Reparacion.fecha_registro >= fecha_inicio if fecha_inicio else True),
                (Reparacion.fecha_registro <= fecha_fin if fecha_fin else True)
            ).group_by(Reparacion.semana).all()
            
            # Ordenar por número de semana
            datos_ordenados = sorted(
                [{"semana": semana, "count": count} for semana, count in datos_raw],
                key=lambda x: extraer_numero_semana(x['semana'])
            )
            
            reparaciones_semana_empleado[empleado] = datos_ordenados
        
        return jsonify({
            "total_reparaciones": total_reparaciones,
            "por_area": [{"area": area, "count": count} for area, count in reparaciones_por_area],
            "top_fallas": [{"codigo": codigo, "descripcion": desc, "count": count} for codigo, desc, count in top_fallas],
            "por_familia": [{"familia": familia, "count": count} for familia, count in reparaciones_por_familia],
            "por_turno": [{"turno": turno, "count": count} for turno, count in reparaciones_por_turno],
            "tiempo_promedio_area": [{"area": area, "avg_time": round(float(avg_time or 0) / 60, 2)} for area, avg_time in tiempo_promedio_area], # Convertir a minutos ( dividir entre 60)
            "por_semana": reparaciones_por_semana,
            "por_empleado": [{"empleado": empleado, "count": count} for empleado, count in reparaciones_por_empleado],
            "semana_empleado": reparaciones_semana_empleado
        })
        
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/")
def index():
    return send_from_directory("templates", "reparaciones.html")

@app.route('/api/sync-files', methods=['POST'])
def sync_files():
    """Endpoint para sincronizar archivos desde la red"""
    try:
        success = sync_files_from_network()
        if success:
            return jsonify({
                'success': True,
                'message': 'Archivos sincronizados exitosamente'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Error durante la sincronización'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }), 500

@app.route('/api/generate-serial', methods=['POST'])
def generate_serial():
    """
    Endpoint para generar números de serie
    """
    try:
        data = request.get_json()
        print("Datos recibidos (generate_serial):", data)
        
        # Cambiar secuencia a un valor numérico
        sequence_map = {
            'BOTTOM': '10',
            'TOP': '20'
        }
        data['sequence'] = sequence_map.get(data.get('sequence', '').upper(), data.get('sequence', ''))
        
        # Validar que todos los campos necesarios estén presentes
        required_fields = ['identificador', 'fecha', 'ensamble', 'job', 'sequence']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Campo requerido faltante: {field}'
                }), 400
        
        # Generar el número de serie usando la clase existente
        serial_number = serial_manager.generate_serial_number(
            data['identificador'],
            data['fecha'].upper(),
            data['ensamble'].upper(),
            data['job'],
            data['sequence']
        )
        
        if serial_number:
            return jsonify({
                'success': True,
                'serial_number': serial_number,
                'message': 'Número de serie generado exitosamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error al generar el número de serie'
            }), 500
            
    except Exception as e:
        print(f"Error en generate_serial: {e}")
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@app.route('/api/get-last-id', methods=['POST'])
def get_last_id():
    """
    Endpoint para obtener el último ID usado para un job específico usando la base de datos
    """
    try:
        data = request.get_json()
        job = data.get('job')
        sequence = data.get('sequence', 'BOTTOM')
        
        if not job:
            return jsonify({
                'success': False,
                'error': 'Job es requerido'
            }), 400

        # Mapeo de secuencia legible a valor numérico
        sequence_map = {
            'BOTTOM': '10',
            'TOP': '20'
        }
        sequence_mapped = sequence_map.get(sequence.upper(), sequence)

        # Obtener todos los registros para este job/secuencia desde la base de datos
        try:
            registros = Reparacion.query.filter_by(secuencia=sequence_mapped).all()
            
            ids = []
            for registro in registros:
                serial = registro.serial_number.strip()
                row_job = serial_manager.extract_job_from_serial(serial)
                
                if row_job.strip() == job.strip():
                    try:
                        current_id = int(serial[1:5])
                        ids.append(current_id)
                    except ValueError:
                        pass
            
            last_id = max(ids) if ids else 0
            next_id = last_id + 1
            
        except Exception as e:
            print(f"Error al obtener último ID desde base de datos: {e}")
            last_id = 0
            next_id = 1

        return jsonify({
            'success': True,
            'last_id': last_id,
            'next_id': next_id
        })
        
    except Exception as e:
        print(f"Error en get_last_id: {e}")
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@app.route("/api/serial_info", methods=["POST"])
def scan_sn():
    data = request.get_json(force=True, silent=True)
    sn = data.get("serialNumber", "")
    
    # Usar la función para extraer el ensamble formateado
    sn_info = parse_serial_number(sn)

    if not sn_info:
        return jsonify({"ok": False, "error": "Serial inválido - No se pudo parsear"}), 400
    
    if not sn_info.get("ensamble_formateado"):
        return jsonify({"ok": False, "error": "Serial inválido - Ensamble no encontrado"}), 400

    item_code = sn_info["ensamble_formateado"]

    _, df_ensamble_filter, error = load_excel_data()
    if error:
        return jsonify({"ok": False, "error": error}), 500

    descripcion, familia = search_assembly_info(item_code, df_ensamble_filter)

    if descripcion and familia:
        return jsonify({
            "item": item_code,
            "familia": familia,
            "descripcion": descripcion
        })
    else:
        return jsonify({"ok": False, "error": "S/N no encontrado en base de datos"}), 404

@app.route("/api/area", methods=["GET"])
def get_areas():
    return jsonify([
        {"area": "SMT", "cc": "8942"},
        {"area": "THL", "cc": "8943"},
        {"area": "TNT", "cc": "8944"},
    ])

@app.route("/api/failure-codes", methods=["GET"])
def get_failure_codes():
    return jsonify([
        {"code": "10", "description": "PUENTE DE SOLDADURA"},
        {"code": "131", "description": "PUNTOS DE PRUEBA SUCIOS"},
        {"code":"13", "description": "ERROR DE EQUIPO DE PRUEBA"},
        {"code":"132", "description": "PIN DE ICT/U2 NO TOCA TEST POINT"},
        {"code":"200", "description": "DEFECTO DE PROVEEDOR"},
        {"code":"22", "description": "CORTO CIRCUITO"},
        {"code":"3", "description": "FALTANTE NO COLOCADO"},
        {"code":"4", "description": "TERMINAL DOBLADA"},
        {"code":"30", "description": "DAÑADO MANEJO"},
        {"code":"31", "description": "DAÑADO ELECTRICAMENTE"},
        {"code":"54", "description": "CONTAMINACION OBJETO EXTRAÑO"},
        {"code":"70", "description": "PARTE EXTRA"},
        {"code":"9", "description": "UPSIDE-DOWN"},
        {"code":"81", "description": "POLARIDAD EQUIVOCADA"},
        {"code":"92", "description": "TERMINAL LEVANTADA"},
        {"code":"1", "description": "SOLDADURA FALTANTE"},
        {"code":"110","description": "SESGADO DESALINEADO"},
        {"code":"14", "description": "EXCESO DE SOLDADURA"},
        {"code":"147", "description": "SOLDADURA FRIA"},
        {"code":"16", "description": "ABIERTO"},
        {"code":"18", "description": "FUERA DE TOLERANCIA"},
        {"code":"2", "description": "DESALINEADO INCLINADO"},
        {"code":"220", "description": "LUGAR EQUIVOCADO"},
        {"code":"224", "description": "VALOR EQUIVOCADO"},
        {"code":"235", "description": "REQUIERE REPROGRAMACION"},
        {"code":"236", "description": "PROBLEMA DE SOFTWARE"},
        {"code":"40", "description": "QUEMADO ELECTRICAMENTE"},
        {"code":"5", "description": "ERROR DE ENSAMBLE"},
        {"code":"60", "description": "CORROSION"},
        {"code":"61", "description": "COMPONENTE CON FISURA POR GOLPE"},
        {"code":"83", "description": "CON BURBUJAS"},
        {"code":"93", "description": "SCRAP EN FIXTURA DE ICT"},
        {"code":"95", "description": "UNIDAD PARA SCRAP"},
        {"code":"96", "description": "SCRAP EN CORTADOR FANCORT"},
        {"code":"97", "description": "SCRAP EN CORTADOR MAESTRO 4M"},
        {"code":"99", "description": "UNIDAD SIN FALLA"},
        {"code":"OP", "description": "OPERADOR"},
    ])

@app.route("/api/register", methods=["POST"])
def register_repair():
    data = request.get_json()
    print("Datos recibidos (register_repair):", data)
    
    # Verificar si es un registro múltiple
    mas_de_un_registro = data.get('masDeUnRegistro', False)
    numero_registros = int(data.get('numeroRegistros', 1)) if data.get('numeroRegistros') else 1
    
    if mas_de_un_registro:
        # Modo múltiple: generar varios registros
        registros_creados = []
        
        # Parsear el serial original UNA VEZ
        parsed_serial = parse_serial_number(data.get('serialNumber', '').strip())
        if not parsed_serial:
            return jsonify({"ok": False, "error": "Número de serie inválido"}), 400
        
        job = parsed_serial['job']
        ensamble = parsed_serial['ensamble_formateado'] or data.get('item', '')
        fecha_original = data.get('fechaRegistro')
        sequence = data.get('secuencia', 'BOTTOM')
        
        # Mapear secuencia
        sequence_map = {'BOTTOM': '10', 'TOP': '20'}
        mapped_sequence = sequence_map.get(sequence.upper(), sequence)
        
        # Convertir fecha
        try:
            fecha_obj = datetime.strptime(fecha_original, "%Y-%m-%d")
            fecha_formateada = f"{str(fecha_obj.year)[2:]}/{fecha_obj.month}"
        except ValueError:
            return jsonify({"ok": False, "error": "Formato de fecha inválido"}), 400
        
        # Para secuencia 10 (BOTTOM), obtener el siguiente ID disponible e incrementar
        if mapped_sequence == "10":
            # Obtener el siguiente ID disponible basado en el patrón del serial original
            identificador_original = parsed_serial['identificador']
            year_month = serial_manager.format_date(fecha_formateada)
            ensamble_clean = ensamble.replace("003-", "").replace("-", "")
            
            # Generar serial base para encontrar el patrón
            serial_base = f"0{identificador_original}{year_month}{ensamble_clean} {job}"
            
            # Obtener el próximo ID disponible
            next_id = serial_manager.get_next_available_id(
                year_month, ensamble_clean, job, mapped_sequence, serial_base
            )
            
            current_id = next_id
            
            for i in range(numero_registros):
                registro_data = data.copy()
                
                # Generar serial con el ID incrementado
                id_formateado = str(current_id).zfill(4)
                serial = f"0{id_formateado}{year_month}{ensamble_clean} {job}"
                
                # Truncar a 26 caracteres si es necesario
                if len(serial) > 26:
                    serial = serial[:26]
                
                # Verificar que no exista (por seguridad)
                while serial_manager.serial_exists_in_db(serial):
                    current_id += 1
                    id_formateado = str(current_id).zfill(4)
                    serial = f"0{id_formateado}{year_month}{ensamble_clean} {job}"
                    if len(serial) > 26:
                        serial = serial[:26]
                
                registro_data['serialNumber'] = serial
                
                # Guardar en la base de datos
                if not save_register(registro_data):
                    return jsonify({"ok": False, "error": f"Error al guardar registro {i+1}"}), 500
                
                registros_creados.append({
                    "registro": i + 1,
                    "serialNumber": serial,
                    "id_usado": current_id
                })
                
                # Incrementar ID para el siguiente registro
                current_id += 1
        
        else:
            # Para secuencia 20 (TOP), usar la lógica original sin validación
            identificador_original = parsed_serial['identificador']
            
            for i in range(numero_registros):
                registro_data = data.copy()
                
                # Generar serial para modo múltiple sin validación de duplicados
                serial = serial_manager.generate_serial_number(
                    identificador=identificador_original,
                    fecha=fecha_formateada,
                    ensamble=ensamble,
                    job=job,
                    sequence="20"  # Usar "20" para evitar validación de duplicados
                )
                
                if not serial:
                    return jsonify({"ok": False, "error": f"No se pudo generar serial para registro {i+1}"}), 500
                
                registro_data['serialNumber'] = serial
                
                # Guardar en la base de datos
                if not save_register(registro_data):
                    return jsonify({"ok": False, "error": f"Error al guardar registro {i+1}"}), 500
                
                registros_creados.append({
                    "registro": i + 1,
                    "serialNumber": serial
                })
        
        return jsonify({
            "ok": True,
            "message": f"{numero_registros} registros guardados",
            "registros": registros_creados,
            "totalRegistros": numero_registros
        })
    
    else:
        # Modo normal: un solo registro
        parsed_serial = parse_serial_number(data.get('serialNumber', '').strip())
        if not parsed_serial:
            return jsonify({"ok": False, "error": "Número de serie inválido"}), 400
        
        job = parsed_serial['job']
        ensamble = parsed_serial['ensamble_formateado'] or data.get('item', '')
        fecha_original = data.get('fechaRegistro')
        sequence = data.get('secuencia', 'BOTTOM')
        
        # Mapear secuencia
        sequence_map = {'BOTTOM': '10', 'TOP': '20'}
        mapped_sequence = sequence_map.get(sequence.upper(), sequence)
        
        # Convertir fecha
        try:
            fecha_obj = datetime.strptime(fecha_original, "%Y-%m-%d")
            fecha_formateada = f"{str(fecha_obj.year)[2:]}/{fecha_obj.month}"
        except ValueError:
            return jsonify({"ok": False, "error": "Formato de fecha inválido"}), 400
        
        identificador_original = parsed_serial['identificador']
        
        # Generar serial único
        serial = serial_manager.generate_serial_number(
            identificador=identificador_original,
            fecha=fecha_formateada,
            ensamble=ensamble,
            job=job,
            sequence=mapped_sequence
        )
        
        if not serial:
            return jsonify({"ok": False, "error": "No se pudo generar un serial único"}), 500
        
        data['serialNumber'] = serial
        
        # Guardar en la base de datos
        if not save_register(data):
            return jsonify({"ok": False, "error": "Error al guardar en la base de datos"}), 500
        
        return jsonify({
            "ok": True,
            "message": "Registro guardado",
            "serialNumber": serial
        })

@app.route("/api/user-info", methods=["GET"])
def get_user_info():
    try:
        current_user = get_current_user()
        user_data = load_data_user(current_user)
        
        if user_data:
            return jsonify({
                "numeroEmpleado": user_data["Id"],
                "nombreEmpleadoCompleto": user_data["Original_Name"],
                "puesto": user_data["Job Position"],
                "nombreEmpleado": user_data["First_Name"],
                "apellidoEmpleado": user_data["First_Lastname"],
            })
        else:
            return jsonify({"ok": False, "error": "Usuario no encontrado"}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# **************** CONSULTAS BASE DE DATOS ****************
@app.route("/api/consultas", methods=["GET"])
def consultas():
    """Endpoint para consultar registros desde la base de datos"""
    try:
        # Parámetros de paginación y filtros opcionales
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '', type=str)
        
        # Query base
        query = Reparacion.query
        
        # Aplicar filtro de búsqueda si se proporciona
        if search:
            query = query.filter(
                db.or_(
                    Reparacion.serial_number.contains(search),
                    Reparacion.item.contains(search),
                    Reparacion.familia.contains(search),
                    Reparacion.nombre_empleado_completo.contains(search)
                )
            )
        
        # Ordenar por fecha de creación descendente
        query = query.order_by(Reparacion.id.desc())
        
        # Paginación
        reparaciones = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            "registros": [{
                "id": reparacion.id,
                "serial_number": reparacion.serial_number,
                "item": reparacion.item,
                "familia": reparacion.familia,
                "descripcion": reparacion.descripcion,
                "area": reparacion.area,
                "fecha_registro": reparacion.fecha_registro,
                "nombre_empleado": reparacion.nombre_empleado_completo,
                "puesto": reparacion.puesto,
                "codigo_falla": reparacion.codigo_falla,
                "descripcion_falla": reparacion.descripcion_falla,
                "tiempo_reparacion": reparacion.tiempo_reparacion,
                "turno": reparacion.turno,
                "secuencia": reparacion.secuencia
            } for reparacion in reparaciones.items],
            "pagination": {
                "page": reparaciones.page,
                "pages": reparaciones.pages,
                "per_page": reparaciones.per_page,
                "total": reparaciones.total,
                "has_next": reparaciones.has_next,
                "has_prev": reparaciones.has_prev
            }
        })
        
    except Exception as e:
        print(f"Error en consultas: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/export-csv", methods=["GET"])
def export_csv():
    """Endpoint para exportar registros a CSV"""
    try:
        import io
        import csv as csv_module
        from flask import make_response
        
        # Obtener todos los registros
        reparaciones = Reparacion.query.order_by(Reparacion.id.desc()).all()
        
        # Crear archivo CSV en memoria
        output = io.StringIO()
        fieldnames = [
            "S/N", "Item", "Familia", "Descripcion", "Area", "Centro de Costo", 
            "Semana", "Fecha de registro", "No. empleado", "Nombre empleado", 
            "Puesto", "Tiempo de reparacion", "Turno", "Codigo de Falla", 
            "Descripcion de falla", "Descripcion del defecto", "Ref. del esquematico", 
            "Item P/N", "Secuencia"
        ]
        
        writer = csv_module.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for reparacion in reparaciones:
            writer.writerow({
                "S/N": reparacion.serial_number,
                "Item": reparacion.item,
                "Familia": reparacion.familia,
                "Descripcion": reparacion.descripcion,
                "Area": reparacion.area,
                "Centro de Costo": reparacion.centro_costo,
                "Semana": reparacion.semana,
                "Fecha de registro": reparacion.fecha_registro,
                "No. empleado": reparacion.numero_empleado,
                "Nombre empleado": reparacion.nombre_empleado_completo,
                "Puesto": reparacion.puesto,
                "Tiempo de reparacion": reparacion.tiempo_reparacion,
                "Turno": reparacion.turno,
                "Codigo de Falla": reparacion.codigo_falla,
                "Descripcion de falla": reparacion.descripcion_falla,
                "Descripcion del defecto": reparacion.descripcion_defecto,
                "Ref. del esquematico": reparacion.ref_esquematico or "",
                "Item P/N": reparacion.item_pn or "",
                "Secuencia": reparacion.secuencia
            })
        
        # Crear respuesta con el CSV
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename=registros_reparaciones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response.headers["Content-type"] = "text/csv"
        
        return response
        
    except Exception as e:
        print(f"Error exportando CSV: {e}")
        return jsonify({"error": str(e)}), 500

# Crear tablas al inicializar la aplicación
@app.before_first_request
def create_tables():
    """Crear las tablas de la base de datos si no existen"""
    try:
        db.create_all()
        print("Tablas de base de datos verificadas/creadas exitosamente")
    except Exception as e:
        print(f"Error creando tablas: {e}")

if __name__ == "__main__":
    # Crear tablas si la aplicación se ejecuta directamente
    with app.app_context():
        db.create_all()
        print("Aplicación iniciada con SQLite")
    
    app.run(debug=False)

