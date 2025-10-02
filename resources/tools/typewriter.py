import pandas as pd 
import openpyxl
import os
import shutil
import csv
import sys
from pathlib import Path

# Añadir el directorio padre al path para poder importar data_manager
sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))
from data_manager import get_database_path, get_excel_path

class SerialNumberManager:
    def __init__(self):
        self.serials_by_job = {}
        self.db_path = None
        # Configurar automáticamente la ruta correcta al inicializar
        self.set_db_path()

    def set_db_path(self, path=None):
        """Establece la ruta de la base de datos"""
        if path is None:
            # Si no se proporciona path, usar el gestor de datos
            try:
                self.db_path = get_database_path()
                print(f"Database path configurado automáticamente: {self.db_path}")
            except Exception as e:
                print(f"Error configurando Database path: {e}")
        else:
            self.db_path = path
            print(f"Database path configurado manualmente: {self.db_path}")

    def extract_job_from_serial(self, serial):
        """Extrae el job del número de serial, manejando espacios extras"""
        parts = serial.strip().split()
        if len(parts) >= 2:
            if len(parts[-2]) == 1:
                return f"{parts[-2]} {parts[-1]}"
            return parts[-1]
        return ""
    
    def serial_exists_in_db(self, serial_number):
        """
        Verifica si el serial completo ya existe en la base de datos
        """
        if not self.db_path:
            print("Error: Database path not set")
            return False

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM reparaciones WHERE serial_number = ?", (serial_number,))
            count = cursor.fetchone()[0]
            
            conn.close()
            return count > 0
            
        except Exception as e:
            print(f"Error al verificar si el serial existe en la base de datos: {e}")
            return False

    def get_next_available_id(self, year_month, ensamble_clean, job, sequence, current_serial_base):
        """
        Encuentra el próximo ID disponible para un serial base dado usando la base de datos
        """
        if not self.db_path:
            print("Error: Database path not set")
            return 1

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            used_ids = set()
            
            # Consultar todos los registros con la misma secuencia
            cursor.execute("SELECT serial_number FROM reparaciones WHERE secuencia = ?", (sequence,))
            records = cursor.fetchall()
            
            for record in records:
                existing_serial = record[0].strip()
                row_job = self.extract_job_from_serial(existing_serial)

                # Verificar si es el mismo job
                if row_job.strip() == job.strip():
                    # Extraer la parte del serial sin el job para comparar el patrón
                    serial_parts = existing_serial.split()
                    if len(serial_parts) >= 2:
                        serial_without_job = serial_parts[0]  # Parte antes del job
                        current_serial_without_job = current_serial_base.split()[0]
                        
                        # Si el patrón base es el mismo (mismo año, mes, ensamble)
                        if len(serial_without_job) >= 5 and len(current_serial_without_job) >= 5:
                            existing_pattern = serial_without_job[5:]  # Sin el ID (posiciones 1-4)
                            current_pattern = current_serial_without_job[5:]  # Sin el ID
                            
                            if existing_pattern == current_pattern:
                                # Extraer el ID (posiciones 1-4 del serial)
                                try:
                                    current_id = int(serial_without_job[1:5])
                                    used_ids.add(current_id)
                                except ValueError:
                                    pass
            
            conn.close()
            
            # Si no hay IDs usados, retornar 1
            if not used_ids:
                return 1
            
            # Retornar el máximo ID + 1
            next_id = max(used_ids) + 1
            return next_id
            
        except Exception as e:
            print(f"Error en get_next_available_id: {e}")
            return 1

    def convert_month_to_hex(self, month):
        """Convierte el mes (1-12) a hexadecimal"""
        try:
            month = int(month)
            if month < 1 or month > 12:
                raise ValueError(f"Mes inválido: {month}")
            
            if month <= 9:
                return str(month)
            elif month == 10:
                return "A"
            elif month == 11:
                return "B"
            elif month == 12:
                return "C"
            
        except ValueError as e:
            print(f"Error al convertir mes: {e}")
            return None

    def format_date(self, date_str):
        """Formatea la fecha de AA/M a AAM"""
        try:
            if '/' not in date_str:
                raise ValueError("Formato de fecha incorrecto. Use AA/M")
            
            year, month = date_str.split('/')
            if len(year) != 2:
                raise ValueError("El año debe tener 2 dígitos")
            
            hex_month = self.convert_month_to_hex(month)
            if hex_month is None:
                raise ValueError("Error al convertir el mes")
                
            return f"{year}{hex_month}"
            
        except ValueError as e:
            print(f"Error al formatear fecha: {e}")
            return None
    
    def generate_serial_number(self, identificador, fecha, ensamble, job, sequence):
        """
        Genera un número de serie único, incrementando el ID si ya existe.
        Para secuencia 20, no procesa duplicados, devuelve el serial tal como viene
        """
        try:
            # Formatear año y mes en hexadecimal
            year_month = self.format_date(fecha)
            if not year_month:
                return None

            # Limpiar y formatear el código de ensamble
            ensamble_clean = ensamble.replace("003-", "").replace("-", "")
            job_clean = job.strip()

            # Generar el serial con el identificador original
            current_id = identificador
            serial_number = f"0{current_id}{year_month}{ensamble_clean} {job_clean}"
            
            # Truncar a 26 caracteres si es necesario
            if len(serial_number) > 26:
                serial_number = serial_number[:26]

            # Si la secuencia es 20, no procesar duplicados
            if sequence == "20":
                return serial_number

            # Para otras secuencias, procesar duplicados normalmente
            if self.serial_exists_in_db(serial_number):
                # Obtener el próximo ID disponible para este patrón de serial
                next_id = self.get_next_available_id(year_month, ensamble_clean, job_clean, sequence, serial_number)
                if next_id is None:
                    print("Error: No se pudo obtener el siguiente ID")
                    return None
                
                # Generar nuevo serial con el nuevo ID
                new_identificador = str(next_id).zfill(4)
                serial_number = f"0{new_identificador}{year_month}{ensamble_clean} {job_clean}"
                
                if len(serial_number) > 26:
                    serial_number = serial_number[:26]
                
                # Verificar una vez más si el nuevo serial existe (por seguridad)
                if self.serial_exists_in_db(serial_number):
                    # Recursivamente buscar el siguiente disponible
                    return self.generate_serial_number(str(next_id + 1).zfill(4), fecha, ensamble, job, sequence)
            
            return serial_number

        except Exception as e:
            print(f"Error al generar el número de serie: {e}")
            return None

def load_excel_data():
    """Cargar datos de Excel para búsqueda de empleados y ensambles"""
    try:
        # Usar el gestor de datos para obtener las rutas correctas
        headcount_path = get_excel_path("HeadCount_220125.xlsx")
        lista_ref_path = get_excel_path("Lista_Ref_RW_230125.xlsx")
        
        print(f"Cargando datos de personal desde: {headcount_path}")
        print(f"Cargando datos de ensambles desde: {lista_ref_path}")
        
        # Cargar datos de personal
        df_personal = pd.read_excel(str(headcount_path))
        df_personal_filter = df_personal[["Id", "Name", "Job Position"]]
        
        # Cargar datos de ensambles
        df_ensamble = pd.read_excel(str(lista_ref_path))
        df_ensamble_filter = df_ensamble[["Item", "Description", "Family Code"]]
        
        return df_personal_filter, df_ensamble_filter, None
    
    except Exception as e:
        error_msg = f"Error cargando los archivos Excel: {e}"
        print(error_msg)
        return None, None, error_msg

def search_assembly_info(item_code, df_ensamble_filter):
    """Buscar información del ensamble al ingresar el item"""
    item_code = item_code.upper()
    if item_code:
        if item_code in df_ensamble_filter["Item"].values:
            assembly_data = df_ensamble_filter.loc[
                df_ensamble_filter["Item"] == item_code, 
                ["Description", "Family Code"]
            ].values[0]
            
            return assembly_data[0], assembly_data[1]  # Descripción, Familia
    return "", ""

def search_employee_info(employee_number, df_personal_filter):
    """Buscar información del empleado al ingresar su número"""
    try:
        if employee_number:
            employee_number = int(employee_number)
            if employee_number in df_personal_filter["Id"].values:
                personal_data = df_personal_filter.loc[
                    df_personal_filter["Id"] == employee_number, 
                    ["Name", "Job Position"]
                ].values[0]
                
                return personal_data[0], personal_data[1]  # Nombre, Puesto
        return "", ""
    
    except ValueError:
        return "", ""

def formated_user_string(name_string):
    try:
        # Separar por coma
        lastnames, firstnames = name_string.split(',')

        lastnames_parts = lastnames.strip().split()
        firstnames_parts = firstnames.strip().split()

        if not firstnames_parts or not lastnames_parts:
            return "error", name_string

        # Usar la inicial del primer nombre
        first_initial = firstnames_parts[0][0]

        # Concatenar apellidos
        full_lastname = ''.join(lastnames_parts)

        formated = (first_initial + full_lastname).upper()
        return formated, name_string
    except Exception as e:
        return "error", name_string

def get_current_user():
    """Obtener la cuenta actual del usuario conectado"""
    try:
        current_user = os.getlogin()
        print(current_user)
        return current_user
    except Exception as e:
        print(f"Error al obtener el usuario actual: {e}")
        return "UNKNOWN_USER"
    
def load_data_user(current_username):
    """Cargar datos de usuario desde Excel usando el gestor de datos"""
    try:
        # Usar el gestor de datos para obtener la ruta correcta
        headcount_path = get_excel_path("HeadCount_220125.xlsx")
        users = pd.read_excel(str(headcount_path), engine='openpyxl')
        users = users[['Id', 'Name', 'Job Position']]
       
        # Crear columnas con el nombre formateado
        users[['Formated_Name', 'Original_Name']] = users['Name'].apply(
            lambda x: pd.Series(formated_user_string(x))
        )

        # --- EXCEPCIÓN PARA JHERNA86 ---
        if current_username.upper() == "JHERNA86":
            exception_name = "HERNANDEZ MARTIN DEL CAMPO, JENNIFER ADA"
            matched_user = users[users['Original_Name'].str.upper() == exception_name.upper()]
        else:
            matched_user = users[users['Formated_Name'] == current_username.upper()]
        # --------------------------------

        if not matched_user.empty:
            row = matched_user.iloc[0]
           
            # Extraer el primer apellido y el primer nombre
            try:
                last_name_part, name_part = row['Original_Name'].split(',')
                first_lastname = last_name_part.strip().split()[0]  # Primer apellido
                first_name = name_part.strip().split()[0]           # Primer nombre
            except Exception as e:
                first_lastname = ""
                first_name = ""
                print("DEBUG: Error parsing names:", e)

            return {
                "Id": str(row['Id']),
                "Original_Name": row['Original_Name'],
                "Job Position": row['Job Position'],
                "First_Lastname": first_lastname,
                "First_Name": first_name
            }
        else:
            return None
            
    except Exception as e:
        print(f"Error cargando datos de usuario: {e}")
        return None

#print(load_data_user(("CECHEVARRIAMENDOZA")))
#print(load_data_user("PCOLLINSFISHER"))
#print(load_data_user("LZAZUETAVAZQUEZ"))
# print(load_data_user("CCESEÑAMALDONADO"))
#print(load_data_user("JHERNA86"))
# print(load_data_user("ASOTOCOTA"))
#print(load_data_user("AFRANCOREYES"))
