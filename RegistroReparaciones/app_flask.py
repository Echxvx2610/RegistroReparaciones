from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from resources.tools.typewriter import load_excel_data, search_assembly_info, get_current_user, load_data_user
app = Flask(__name__)
CORS(app, origins="*")  # durante desarrollo permite todos

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

@app.route("/api/serial_info", methods=["POST"])
def scan_sn():
    data = request.get_json(force=True, silent=True)
    print("Datos recibidos:", data)
    sn = data.get("serialNumber", "")

    # Usar la función para extraer el ensamble formateado
    sn_info = parse_serial_number(sn)
    if not sn_info or not sn_info["ensamble_formateado"]:
        return jsonify({"ok": False, "error": "Serial inválido"}), 400

    item_code = sn_info["ensamble_formateado"]
    print("Item code extraído:", item_code)

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
    payload = request.json
    # Aquí puedes validar, persistir en CSV, DB o Excel
    # persistor.save(payload)
    return jsonify({"ok": True, "message": "Registro guardado"})

@app.route("/api/user-info", methods=["GET"])
def get_user_info():
    try:
        current_user = get_current_user()
        # load_data_user debe devolver los datos, modifícala para retornar en vez de setText
        user_data = load_data_user(current_user)
        if user_data:
            return jsonify({
                "numeroEmpleado": user_data["Id"],
                "nombreEmpleado": user_data["Original_Name"],
                "puesto": user_data["Job Position"]
            })
        else:
            return jsonify({"ok": False, "error": "Usuario no encontrado"}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
