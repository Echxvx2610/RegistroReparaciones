from flask import Flask, request, jsonify,send_file,send_from_directory
from flask_cors import CORS
import pandas as pd
from models import db, Reparacion
from resources.tools.typewriter import load_excel_data, search_assembly_info, get_current_user, load_data_user,SerialNumberManager
import os 
import webbrowser
import sqlite3
import csv
import os
from datetime import datetime
# Importar el gestor de datos
from data_manager import get_csv_path, get_excel_path


# crear instancia de app
app = Flask(__name__)
# permite cors de cualquier origen (en desarrollo)
CORS(app, origins="*")
# inicializar el manager de numeros de serie
serial_manager = SerialNumberManager()

# Configurar la ruta del CSV usando el gestor de datos
CSV_PATH = get_csv_path()
serial_manager.set_csv_path(CSV_PATH)

print(f"CSV path configurado: {CSV_PATH}")

def parse_serial_number(serial):
    try:
        parts = serial.strip().split()
        if len(parts) != 2:
            return None
        left_part, job = parts[0], parts[1]
        if len(left_part) == 14:
            identificador = left_part[1:5]
            fecha_hex = left_part[5:8]
            ensamble_raw = left_part[8:14]
            ensamble_raw = ensamble_raw[:-2] + '-' + ensamble_raw[-2:]
        elif len(left_part) == 15:
            identificador = left_part[1:5]
            fecha_hex = left_part[5:8]
            ensamble_raw = left_part[8:15]
            ensamble_raw = ensamble_raw[:-2] + '-' + ensamble_raw[-2:]
        else:
            return None
        ensamble_formateado = f"003-{ensamble_raw}" if ensamble_raw else None
        return {
            "identificador": identificador,
            "fecha_hex": fecha_hex,
            "ensamble_formateado": ensamble_formateado,
            "job": job
        }
    except Exception as e:
        print(f"Error al analizar el número de serie: {e}")
        return None

def serial_exists(serial_number, job, sequence, csv_path):
    """
    Función simplificada para verificar si un serial específico ya existe
    """
    try:
        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Saltar encabezado
            for row in reader:
                if len(row) >= 1:
                    existing_serial = row[0].strip()
                    if existing_serial == serial_number:
                        return True
        return False
    except Exception as e:
        print(f"Error al verificar duplicado: {e}")
        return False
 
def save_register(data):
    # Pendiente de implementar bd compartida para analisis
    # try:
    #     # === Guardar en la base de datos (pendiente de evaluar) ===
    #     nueva_reparacion = Reparacion(
    #         serial_number=data.get('serialNumber', ''),
    #         item=data.get('item', ''),
    #         familia=data.get('familia', ''),
    #         descripcion=data.get('descripcion', ''),
    #         area=data.get('area', ''),
    #         centro_costo=data.get('centroCosto', ''),
    #         semana=data.get('semana', ''),
    #         fecha_registro=data.get('fechaRegistro', ''),
    #         numero_empleado=data.get('numeroEmpleado', ''),
    #         nombre_empleado_completo=data.get('nombreEmpleadoCompleto', ''),
    #         nombre_empleado=data.get('nombreEmpleado', ''),
    #         apellido_empleado=data.get('apellidoEmpleado', ''),
    #         puesto=data.get('puesto', ''),
    #         turno=data.get('turno', ''),
    #         codigo_falla=data.get('codigoFalla', ''),
    #         descripcion_falla=data.get('descripcionFalla', ''),
    #         descripcion_defecto=data.get('descripcionDefecto', ''),
    #         ref_esquematico=data.get('refEsquematico', ''),
    #         item_pn=data.get('itemPN', ''),
    #         secuencia=data.get('secuencia', ''),
    #         tiempo_reparacion=data.get('tiempoReparacion', '')
    #     )

    #     db.session.add(nueva_reparacion)
    #     db.session.commit()
    #     print("Registro guardado en la base de datos!")
    # except Exception as e:
    #     print(f"Error al guardar en la base de datos: {e}")

    try:
        # === Guardar en CSV ===
        # ejemplo de datos:
        """ 
        Datos recibidos (register_repair): {'serialNumber': '00625256311781c 1800045682', 'item': '003-31178-1c', 'familia': 'GOOSE', 'descripcion': '@PCB TST ASSY RECON HEAD', 'area': 'SMT', 'centroCosto': '8942', 'semana': 'Wk 27', 'fechaRegistro': '2025-07-07', 'numeroEmpleado': '15310', 'nombreEmpleadoCompleto': 'ECHEVARRIA MENDOZA,CRISTIAN ALFONSO', 'nombreEmpleado': 'CRISTIAN', 'apellidoEmpleado': 'ECHEVARRIA', 'puesto': 'TECNICO SMT I', 'turno': '1er Turno', 'codigoFalla': '10', 'descripcionFalla': 'PUENTE DE SOLDADURA', 'descripcionDefecto': 'N/A', 'refEsquematico': 'R123', 'itemPN': '114-0100-c4', 'secuencia': '10'}
        """
        csv_filename = get_csv_path()
        file_exists = os.path.isfile(csv_filename)

        with open(csv_filename, mode='a', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                "S/N", "Item", "Familia", "Descripcion", "Area", "Centro de Costo", "Semana", "Fecha de registro", "No. empleado", "Nombre empleado", "Puesto", "Tiempo de reparacion", "Turno", "Codigo de Falla", "Descripcion de falla", "Descripcion del defecto", "Ref. del esquematico", "Item P/N", "Secuencia"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            # Extraer los campos necesarios del diccionario data
            row_data = {
                "S/N": data.get('serialNumber', '').upper(),
                "Item": data.get('item', '').upper(),
                "Familia": data.get('familia', '').upper(),
                "Descripcion": data.get('descripcion', '').upper(),
                "Area": data.get('area', '').upper(),
                "Centro de Costo": data.get('centroCosto', ''),
                "Semana": data.get('semana', ''),
                "Fecha de registro": data.get('fechaRegistro', ''),
                "No. empleado": data.get('numeroEmpleado', ''),
                "Nombre empleado": data.get('nombreEmpleadoCompleto', '').upper(),
                "Puesto": data.get('puesto', '').upper(),
                "Tiempo de reparacion": data.get('tiempoReparacion', ''),
                "Turno": data.get('turno', ''),
                "Codigo de Falla": data.get('codigoFalla', ''),
                "Descripcion de falla": data.get('descripcionFalla', '').upper(),
                "Descripcion del defecto": data.get('descripcionDefecto', '').upper(),
                "Ref. del esquematico": data.get('refEsquematico', '').upper(),
                "Item P/N": data.get('itemPN', '').upper(),
                "Secuencia": data.get('secuencia', '')
            }

            writer.writerow(row_data)
            print("Registro guardado en el archivo CSV!")
    except Exception as e:
        print(f"Error al guardar en el archivo CSV: {e}")

    return None

@app.route("/")
def index():
    return send_from_directory("templates", "reparaciones.html")

@app.route('/api/generate-serial', methods=['POST'])
def generate_serial():
    """
    Endpoint para generar números de serie
    Esperado JSON: {
        "identificador": "1234",
        "fecha": "25/2",
        "ensamble": "003-12345-01",
        "job": "18000451",
        "sequence": "BOTTOM"
    }
    """
    try:
        data = request.get_json()
        print("!DEBUG: Datos recibidos (generate_serial):", data)
        # cambiar secuencia a un valor numérico
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
    Endpoint para obtener el último ID usado para un job específico
    """
    try:
        data = request.get_json()
        #print("Datos recibidos (get_last_id):", data)
        job = data.get('job')
        sequence = data.get('sequence', 'BOTTOM')
        
        if not job:
            return jsonify({
                'success': False,
                'error': 'Job es requerido'
            }), 400

        # Mapeo de secuencia legible a valor numérico del CSV
        sequence_map = {
            'BOTTOM': '10',
            'TOP': '20'
        }
        sequence_mapped = sequence_map.get(sequence.upper(), sequence)

        # Obtener todos los IDs para este job/secuencia
        try:
            ids = []
            with open(serial_manager.csv_file_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)
                for row in reader:
                    if len(row) >= 18:
                        serial = row[0].strip()
                        row_sequence = row[18].strip()
                        row_job = serial_manager.extract_job_from_serial(serial)
                        #print(f"Debug: Serial: {serial}, row_sequence: {row_sequence}, row_job: {row_job}")

                        if row_job.strip() == job.strip() and row_sequence.upper() == sequence_mapped.upper():
                            try:
                                current_id = int(serial[1:5])
                                ids.append(current_id)
                            except ValueError:
                                pass
            
            last_id = max(ids) if ids else 0
            next_id = last_id + 1
            
        except Exception as e:
            print(f"Error al obtener último ID: {e}")
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
    #print("!DEBUG: Datos recibidos (scan_sn):", data)
    sn = data.get("serialNumber", "")

    # Usar la función para extraer el ensamble formateado
    sn_info = parse_serial_number(sn)
    if not sn_info or not sn_info["ensamble_formateado"]:
        return jsonify({"ok": False, "error": "Serial inválido"}), 400

    item_code = sn_info["ensamble_formateado"]
    #print("Item code extraído:", item_code)

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
        return jsonify({"ok": False, "error": "S/N no encontrado"}), 404

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
    #print("Datos recibidos (register_repair):", data)
    
    # Verificar si es un registro múltiple
    mas_de_un_registro = data.get('masDeUnRegistro', False)
    # Convertir numeroRegistros a int si viene como string
    numero_registros = int(data.get('numeroRegistros', 1)) if data.get('numeroRegistros') else 1
    
    if mas_de_un_registro:
        # Modo múltiple: generar varios registros sin validar SN únicos
        registros_creados = []
        
        for i in range(numero_registros):
            # Crear una copia de los datos para cada registro
            registro_data = data.copy()
            
            # Paso 1: Usar parse_serial_number para extraer datos reales
            parsed_serial = parse_serial_number(data.get('serialNumber', '').strip())
            if not parsed_serial:
                return jsonify({"ok": False, "error": "Número de serie inválido"}), 400
            
            job = parsed_serial['job']
            ensamble = parsed_serial['ensamble_formateado'] or data.get('item', '')
            fecha_original = data.get('fechaRegistro')  # '2025-07-08'
            sequence = data.get('secuencia', 'BOTTOM')
            
            # Mapear secuencia (BOTTOM/TOP -> 10/20)
            sequence_map = {'BOTTOM': '10', 'TOP': '20'}
            mapped_sequence = sequence_map.get(sequence.upper(), sequence)
            
            # Convertir fecha a 'AA/M' desde 'YYYY-MM-DD'
            try:
                fecha_obj = datetime.strptime(fecha_original, "%Y-%m-%d")
                fecha_formateada = f"{str(fecha_obj.year)[2:]}/{fecha_obj.month}"
            except ValueError:
                return jsonify({"ok": False, "error": "Formato de fecha inválido"}), 400
            
            # Usar el identificador original del serial parseado
            identificador_original = parsed_serial['identificador']
            
            # En modo múltiple, generar serial sin validar duplicados
            # Forzamos sequence="20" para evitar procesamiento de duplicados
            serial = serial_manager.generate_serial_number(
                identificador=identificador_original,
                fecha=fecha_formateada,
                ensamble=ensamble,
                job=job,
                sequence="20"  # Usar "20" para evitar validación de duplicados
            )
            
            if not serial:
                return jsonify({"ok": False, "error": f"No se pudo generar serial para registro {i+1}"}), 500
            
            # Actualizar data con el nuevo serial
            registro_data['serialNumber'] = serial
            
            # Guardar en CSV
            save_register(registro_data)
            
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
        # Modo normal: un solo registro con validación de SN único
        # Paso 1: Usar parse_serial_number para extraer datos reales
        parsed_serial = parse_serial_number(data.get('serialNumber', '').strip())
        if not parsed_serial:
            return jsonify({"ok": False, "error": "Número de serie inválido"}), 400
        
        job = parsed_serial['job']
        ensamble = parsed_serial['ensamble_formateado'] or data.get('item', '')
        fecha_original = data.get('fechaRegistro')  # '2025-07-08'
        sequence = data.get('secuencia', 'BOTTOM')
        
        # Mapear secuencia (BOTTOM/TOP -> 10/20)
        sequence_map = {'BOTTOM': '10', 'TOP': '20'}
        mapped_sequence = sequence_map.get(sequence.upper(), sequence)
        
        # Convertir fecha a 'AA/M' desde 'YYYY-MM-DD'
        try:
            fecha_obj = datetime.strptime(fecha_original, "%Y-%m-%d")
            fecha_formateada = f"{str(fecha_obj.year)[2:]}/{fecha_obj.month}"
        except ValueError:
            return jsonify({"ok": False, "error": "Formato de fecha inválido"}), 400
        
        # Usar el identificador original del serial parseado
        identificador_original = parsed_serial['identificador']
        
        # Paso 2: Generar el serial usando el identificador original (con validación única)
        serial = serial_manager.generate_serial_number(
            identificador=identificador_original,
            fecha=fecha_formateada,
            ensamble=ensamble,
            job=job,
            sequence=mapped_sequence
        )
        
        if not serial:
            return jsonify({"ok": False, "error": "No se pudo generar un serial único"}), 500
        
        # Paso 4: Actualizar data con el nuevo serial
        data['serialNumber'] = serial
        
        # Paso 5: Guardar en CSV
        save_register(data)
        
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
        #print("!DEBUG: Datos del usuario actual:", user_data)
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


#**************** consultas base de datos ****************
# @app.route("/api/consultas", methods=["GET"])
# def consultas():
#     reparaciones = Reparacion.query.all()
#     return jsonify([{
#         "id": reparacion.id,
#         "serial_number": reparacion.serial_number,
#         "item": reparacion.item,
#         "fecha_registro": reparacion.fecha_registro,
#         "nombre_empleado": reparacion.nombre_empleado_completo,
#         "tiempo_de_reparacion":reparacion.tiempo_reparacion
#     } for reparacion in reparaciones])

if __name__ == "__main__":
    app.run(debug=False)
