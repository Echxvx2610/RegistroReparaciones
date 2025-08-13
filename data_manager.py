import os
import sys
from pathlib import Path
import shutil

def get_app_data_dir():
    """Obtiene el directorio donde guardar los datos de la aplicación"""
    if sys.platform == "win32":
        # Windows: usar AppData/Local
        app_data = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')))
        return app_data / "RegistroReparaciones"
    else:
        # Linux/Mac: usar directorio home
        return Path.home() / ".registro_reparaciones"

def get_resource_path(relative_path):
    """Obtiene la ruta a un recurso, funciona tanto en desarrollo como en ejecutable"""
    if hasattr(sys, '_MEIPASS'):
        # Ejecutándose desde PyInstaller
        return Path(sys._MEIPASS) / relative_path
    else:
        # Ejecutándose desde código fuente
        return Path(__file__).parent / relative_path

def ensure_data_files():
    """Asegura que los archivos de datos existan en el directorio correcto"""
    app_data_dir = get_app_data_dir()
    app_data_dir.mkdir(exist_ok=True)
    
    data_dir = app_data_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Lista de archivos que deben copiarse
    required_files = [
        "registros.csv",
        "HeadCount_220125.xlsx", 
        "Lista_Ref_RW_230125.xlsx"
    ]
    
    # Copiar todos los archivos necesarios
    for filename in required_files:
        target_file = data_dir / filename
        
        if not target_file.exists():
            try:
                source_file = get_resource_path(f"resources/data/{filename}")
                if source_file.exists():
                    shutil.copy2(source_file, target_file)
                    #print(f"Archivo copiado: {filename}")
                else:
                    # Solo crear CSV vacío si es el archivo de registros
                    if filename == "registros.csv":
                        create_empty_csv(target_file)
                        #print(f"Archivo CSV creado vacío: {filename}")
                    else:
                        print(f"Archivo fuente no encontrado: {source_file}")
            except Exception as e:
                print(f"Error al copiar {filename}: {e}")
                if filename == "registros.csv":
                    create_empty_csv(target_file)
    
    # Retornar la ruta del CSV principal
    csv_file = data_dir / "registros.csv"
    return csv_file

def create_empty_csv(csv_path):
    """Crea un archivo CSV vacío con headers básicos"""
    headers = ["serial", "job", "timestamp", "user"]  # Ajusta según tus headers reales
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
        #print(f"Archivo CSV vacío creado en: {csv_path}")
    except Exception as e:
        print(f"Error al crear CSV vacío: {e}")

def get_csv_path():
    """Obtiene la ruta correcta al archivo CSV de registros"""
    return ensure_data_files()

def get_excel_path(filename):
    """Obtiene la ruta correcta a archivos Excel en resources/data"""
    app_data_dir = get_app_data_dir()
    data_dir = app_data_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    excel_file = data_dir / filename
    
    # Si el archivo no existe, copiarlo desde resources
    if not excel_file.exists():
        try:
            source_excel = get_resource_path(f"resources/data/{filename}")
            if source_excel.exists():
                shutil.copy2(source_excel, excel_file)
                #print(f"Archivo Excel copiado: {filename}")
        except Exception as e:
            print(f"Error al copiar Excel {filename}: {e}")
    
    return excel_file

# Para importar desde cualquier lugar
import csv