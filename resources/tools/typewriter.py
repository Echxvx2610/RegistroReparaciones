import pandas as pd 
import openpyxl
import os
import shutil
import csv
# Importar el gestor de datos
import sys
from pathlib import Path

# Añadir el directorio padre al path para poder importar data_manager
# sys.path.append(str(Path(__file__).parent.parent))
# from data_manager import get_csv_path, get_excel_path

sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))
from data_manager import get_csv_path, get_excel_path

class SerialNumberManager:
    def __init__(self):
        self.serials_by_job = {}
        self.csv_file_path = None
        # Configurar automáticamente la ruta correcta al inicializar
        self.set_csv_path()

    def set_csv_path(self, path=None):
        """Establece la ruta del archivo CSV"""
        if path is None:
            # Si no se proporciona path, usar el gestor de datos
            try:
                self.csv_file_path = str(get_csv_path())
                print(f"CSV path configurado automáticamente: {self.csv_file_path}")
            except Exception as e:
                print(f"Error configurando CSV path: {e}")
                # Fallback a la ruta original
                self.csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'registros.csv')
        else:
            self.csv_file_path = path
            print(f"CSV path configurado manualmente: {self.csv_file_path}")

    def extract_job_from_serial(self, serial):
        """Extrae el job del número de serial, manejando espacios extras"""
        parts = serial.strip().split()
        if len(parts) >= 2:
            if len(parts[-2]) == 1:
                return f"{parts[-2]} {parts[-1]}"
            return parts[-1]
        return ""
    
    def serial_exists_in_csv(self, serial_number):
        """
        Verifica si el serial completo ya existe en el CSV
        """
        if not self.csv_file_path:
            print("Error: CSV path not set")
            return False

        try:
            with open(self.csv_file_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Saltar encabezado
                for row in reader:
                    if len(row) >= 1:
                        existing_serial = row[0].strip()
                        if existing_serial == serial_number:
                            return True
            return False
        except Exception as e:
            print(f"Error al verificar si el serial existe: {e}")
            return False

    def get_next_available_id(self, year_month, ensamble_clean, job, sequence, current_serial_base):
        """
        Encuentra el próximo ID disponible para un serial base dado
        CORREGIDO: Busca seriales que coincidan EXACTAMENTE con el patrón completo (incluyendo secuencia)
        """
        if not self.csv_file_path:
            print("Error: CSV path not set")
            return 1

        try:
            used_ids = set()
            #print(f"DEBUG: Buscando IDs para job='{job}', sequence='{sequence}'")
            #print(f"DEBUG: Serial base a comparar: '{current_serial_base}'")
            
            with open(self.csv_file_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Saltar encabezado
                for row in reader:
                    if len(row) >= 19:  # Necesitamos el serial y la secuencia
                        existing_serial = row[0].strip()
                        row_sequence = row[18].strip() if len(row) > 18 else ""
                        row_job = self.extract_job_from_serial(existing_serial)

                        #print(f"DEBUG: Comparando - existing_job='{row_job}', row_sequence='{row_sequence}'")
                        #print(f"DEBUG: Serial existente: '{existing_serial}'")
                        
                        # CORREGIDO: Verificar si es el mismo job Y la misma secuencia
                        if row_job.strip() == job.strip() and row_sequence == sequence:
                            # Extraer la parte del serial sin el job para comparar el patrón
                            serial_parts = existing_serial.split()
                            if len(serial_parts) >= 2:
                                serial_without_job = serial_parts[0]  # Parte antes del job
                                current_serial_without_job = current_serial_base.split()[0]
                                
                                #print(f"DEBUG: Comparando patrones - existente: '{serial_without_job}', actual: '{current_serial_without_job}'")
                                
                                # Si el patrón base es el mismo (mismo año, mes, ensamble)
                                if len(serial_without_job) >= 5 and len(current_serial_without_job) >= 5:
                                    existing_pattern = serial_without_job[5:]  # Sin el ID (posiciones 1-4)
                                    current_pattern = current_serial_without_job[5:]  # Sin el ID
                                    
                                    if existing_pattern == current_pattern:
                                        # Extraer el ID (posiciones 1-4 del serial)
                                        try:
                                            current_id = int(serial_without_job[1:5])
                                            used_ids.add(current_id)
                                            #print(f"DEBUG: ID usado encontrado: {current_id} del serial: {existing_serial}")
                                        except ValueError as ve:
                                            #print(f"DEBUG: Error al extraer ID de {existing_serial}: {ve}")
                                            pass
            
            #print(f"DEBUG: IDs usados encontrados: {sorted(used_ids)}")
            
            # Si no hay IDs usados, retornar 1
            if not used_ids:
                #print("DEBUG: No hay IDs usados, retornando 1")
                return 1
            
            # Retornar el máximo ID + 1
            next_id = max(used_ids) + 1
            #print(f"DEBUG: IDs usados: {sorted(used_ids)}, siguiente ID: {next_id}")
            
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
            
            #print(f"Año: {year}, Mes: {month}, Mes convertido: {hex_month}")
                
            return f"{year}{hex_month}"
            
        except ValueError as e:
            print(f"Error al formatear fecha: {e}")
            return None
    
    def generate_serial_number(self, identificador, fecha, ensamble, job, sequence):
        """
        Genera un número de serie único, incrementando el ID si ya existe.
        CORREGIDO: Para secuencia 20, no procesa duplicados, devuelve el serial tal como viene
        """
        try:
            # print(f"Generando serial con secuencia: {sequence}")
            # print(f"Job recibido: '{job}'")
            # print(f"Identificador original: '{identificador}'")

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

            #print(f"Serial generado inicialmente: {serial_number}")

            # CORREGIDO: Si la secuencia es 20, no procesar duplicados
            if sequence == "20":
                # print(f"Secuencia 20 detectada - manteniendo serial original sin procesamiento")
                # print(f"SerialNumberManager: Serial number final - {serial_number}")
                # print(f"SerialNumberManager: Serial number length - {len(serial_number)}")
                return serial_number

            # Para otras secuencias, procesar duplicados normalmente
            if self.serial_exists_in_csv(serial_number):
                #print(f"Serial duplicado encontrado: {serial_number}")
                
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
                
                #print(f"Nuevo serial generado con ID {next_id}: {serial_number}")
                
                # Verificar una vez más si el nuevo serial existe (por seguridad)
                if self.serial_exists_in_csv(serial_number):
                    #print(f"ADVERTENCIA: El nuevo serial también existe: {serial_number}")
                    # Recursivamente buscar el siguiente disponible
                    return self.generate_serial_number(str(next_id + 1).zfill(4), fecha, ensamble, job, sequence)
            else:
                print(f"Serial no duplicado, usando el serial original: {serial_number}")
                
            #print(f"SerialNumberManager: Serial number final - {serial_number}")
            #print(f"SerialNumberManager: Serial number length - {len(serial_number)}")

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
        
        #print(f"Cargando datos de personal desde: {headcount_path}")
        #print(f"Cargando datos de ensambles desde: {lista_ref_path}")
        
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


# def formated_user_string(name_string):
#         name_parts = name_string.replace(",", " ").split()[:-1]
#         if len(name_parts) >= 3:
#             formated = (name_parts[2][0] + name_parts[0] + name_parts[1]).upper()
#             return formated, name_string  # Devuelve el nombre formateado y el original
#         return "error", name_string

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
        #print("DEBUG: Error en formated_user_string:", e)
        return "error", name_string


#obtener la cuenta actual del usuario conectado
def get_current_user():
    try:
        current_user = os.getlogin()
        #print(f"!Debug get_current_user(): {current_user} ")
        return current_user
    except Exception as e:
        print(f"Error al obtener el usuario actual: {e}")
        return "UKNOWN_USER"
    
    
def load_data_user(current_username):
    """Cargar datos de usuario desde Excel usando el gestor de datos"""
    try:
        # Usar el gestor de datos para obtener la ruta correcta
        headcount_path = get_excel_path("HeadCount_220125.xlsx")
        
        #print(f"Cargando datos de usuario desde: {headcount_path}")
        
        users = pd.read_excel(str(headcount_path), engine='openpyxl')
        users = users[['Id', 'Name', 'Job Position']]
       
        users[['Formated_Name', 'Original_Name']] = users['Name'].apply(
            lambda x: pd.Series(formated_user_string(x))
        )
        # print("DEBUG: current_username =", current_username.upper())
        # print("DEBUG: Formated_Name list =", users['Formated_Name'].tolist())
        matched_user = users[users['Formated_Name'] == current_username.upper()]
       
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
            #print("DEBUG: load_data_user() - Usuario encontrado:", row)
           
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

# print(load_data_user(("CECHEVARRIAMENDOZA")))
# print(load_data_user("PCOLLINSFISHER"))
#print(load_data_user("LZAZUETAVAZQUEZ"))
# print(load_data_user("CCESENAMALDONADO"))
# #PCOLLINSFISHER
