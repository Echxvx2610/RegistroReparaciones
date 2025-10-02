import os
import sys
from pathlib import Path
import shutil
import sqlite3
from datetime import datetime

def get_app_data_dir():
    """Obtiene el directorio donde guardar los datos de la aplicación"""
    if sys.platform == "win32":
        # Windows: usar AppData/Local
        app_data = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')))
        return app_data / "RegistroReparaciones"
    else:
        # Linux/Mac: usar directorio home
        return Path.home() / ".registro_reparaciones"

def get_network_data_dir():
    """Obtiene el directorio de red donde están los archivos centralizados"""
    return Path("H:/Publico/Ingenieria/PCB/RegistroRetrabajo")

def get_resource_path(relative_path):
    """Obtiene la ruta a un recurso, funciona tanto en desarrollo como en ejecutable"""
    if hasattr(sys, '_MEIPASS'):
        # Ejecutándose desde PyInstaller
        return Path(sys._MEIPASS) / relative_path
    else:
        # Ejecutándose desde código fuente
        return Path(__file__).parent / relative_path

def check_network_files_updated():
    """Verifica si los archivos de red son más recientes que los locales"""
    network_dir = get_network_data_dir()
    local_dir = get_app_data_dir() / "data"
    
    files_to_check = [
        "HeadCount_220125.xlsx", 
        "Lista_Ref_RW_230125.xlsx"
    ]
    
    files_updated = []
    
    for filename in files_to_check:
        network_file = network_dir / filename
        local_file = local_dir / filename
        
        if network_file.exists():
            if not local_file.exists():
                files_updated.append(filename)
            else:
                # Comparar fechas de modificación
                network_mtime = network_file.stat().st_mtime
                local_mtime = local_file.stat().st_mtime
                
                if network_mtime > local_mtime:
                    files_updated.append(filename)
    
    return files_updated

def sync_files_from_network():
    """Sincroniza archivos desde la red a la carpeta local"""
    try:
        network_dir = get_network_data_dir()
        app_data_dir = get_app_data_dir()
        local_data_dir = app_data_dir / "data"
        
        # Crear directorios si no existen
        app_data_dir.mkdir(exist_ok=True)
        local_data_dir.mkdir(exist_ok=True)
        
        # Verificar qué archivos necesitan actualización
        updated_files = check_network_files_updated()
        
        if updated_files:
            print(f"Sincronizando archivos actualizados: {updated_files}")
            
            for filename in updated_files:
                network_file = network_dir / filename
                local_file = local_data_dir / filename
                
                if network_file.exists():
                    try:
                        shutil.copy2(network_file, local_file)
                        print(f"Archivo sincronizado: {filename}")
                    except Exception as e:
                        print(f"Error sincronizando {filename}: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error durante sincronización: {e}")
        return False

def ensure_data_files():
    """Asegura que los archivos de datos existan en el directorio correcto"""
    app_data_dir = get_app_data_dir()
    app_data_dir.mkdir(exist_ok=True)
    
    data_dir = app_data_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Primero intentar sincronizar desde la red
    sync_success = sync_files_from_network()
    
    # Lista de archivos Excel requeridos
    excel_files = [
        "HeadCount_220125.xlsx", 
        "Lista_Ref_RW_230125.xlsx"
    ]
    
    # Si la sincronización falló, copiar desde resources como fallback
    if not sync_success:
        print("Sincronización de red falló, usando archivos locales...")
        for filename in excel_files:
            target_file = data_dir / filename
            
            if not target_file.exists():
                try:
                    source_file = get_resource_path(f"resources/data/{filename}")
                    if source_file.exists():
                        shutil.copy2(source_file, target_file)
                        print(f"Archivo copiado desde resources: {filename}")
                    else:
                        print(f"Archivo fuente no encontrado: {source_file}")
                except Exception as e:
                    print(f"Error al copiar {filename}: {e}")
    
    # Verificar que los archivos Excel existan
    for filename in excel_files:
        target_file = data_dir / filename
        if not target_file.exists():
            print(f"Advertencia: Archivo Excel faltante: {filename}")
    
    return True

def get_database_path():
    """Obtiene la ruta correcta a la base de datos SQLite"""
    network_dir = get_network_data_dir()
    db_path = network_dir / "registros.db"
    
    try:
        # Crear directorio de red si no existe
        network_dir.mkdir(parents=True, exist_ok=True)
        
        # Si la base de datos no existe, crearla
        if not db_path.exists():
            # Crear la base de datos con SQLite
            create_database(db_path)
            
        return str(db_path)
        
    except Exception as e:
        print(f"Error accediendo a la base de datos de red: {e}")
        # Fallback a base de datos local
        local_db = get_app_data_dir() / "registros.db"
        if not local_db.exists():
            create_database(local_db)
        return str(local_db)

def create_database(db_path):
    """Crea la base de datos SQLite con la estructura necesaria"""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Crear tabla de reparaciones
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reparaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_number VARCHAR(50) NOT NULL,
            item VARCHAR(100) NOT NULL,
            familia VARCHAR(100) NOT NULL,
            descripcion VARCHAR(200) NOT NULL,
            area VARCHAR(100) NOT NULL,
            centro_costo VARCHAR(100) NOT NULL,
            semana VARCHAR(20) NOT NULL,
            fecha_registro VARCHAR(20) NOT NULL,
            numero_empleado VARCHAR(50) NOT NULL,
            nombre_empleado_completo VARCHAR(200) NOT NULL,
            nombre_empleado VARCHAR(100) NOT NULL,
            apellido_empleado VARCHAR(100) NOT NULL,
            puesto VARCHAR(100) NOT NULL,
            turno VARCHAR(50) NOT NULL,
            codigo_falla VARCHAR(50) NOT NULL,
            descripcion_falla VARCHAR(200) NOT NULL,
            descripcion_defecto VARCHAR(200) NOT NULL,
            ref_esquematico VARCHAR(100),
            item_pn VARCHAR(100),
            secuencia VARCHAR(10) NOT NULL,
            tiempo_reparacion VARCHAR(20) NOT NULL,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"Base de datos creada exitosamente en: {db_path}")
        return True
        
    except Exception as e:
        print(f"Error creando base de datos: {e}")
        return False

def get_excel_path(filename):
    """Obtiene la ruta correcta a archivos Excel"""
    app_data_dir = get_app_data_dir()
    data_dir = app_data_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    excel_file = data_dir / filename
    
    # Si el archivo no existe localmente, intentar sincronizar desde red
    if not excel_file.exists():
        sync_files_from_network()
    
    # Si aún no existe, copiar desde resources
    if not excel_file.exists():
        try:
            source_excel = get_resource_path(f"resources/data/{filename}")
            if source_excel.exists():
                shutil.copy2(source_excel, excel_file)
                print(f"Archivo Excel copiado desde resources: {filename}")
        except Exception as e:
            print(f"Error al copiar Excel {filename}: {e}")
    
    return excel_file

# Función para mantener compatibilidad con CSV (puede ser removida después)
def get_csv_path():
    """Función de compatibilidad - retorna None ya que usamos SQLite"""
    print("Advertencia: get_csv_path() llamada pero se está usando SQLite")
    return None