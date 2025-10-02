import sqlite3
import pandas as pd
from datetime import datetime
import os

def migrar_csv_a_sqlite(archivo_csv, archivo_bd, tabla_destino):
    """
    Migra datos de CSV a base de datos SQLite
    
    Args:
        archivo_csv (str): Ruta del archivo CSV
        archivo_bd (str): Ruta de la base de datos SQLite
        tabla_destino (str): Nombre de la tabla destino
    """
    
    try:
        # Verificar que el archivo CSV existe
        if not os.path.exists(archivo_csv):
            print(f"Error: El archivo CSV '{archivo_csv}' no existe.")
            return False
        
        # Leer el archivo CSV con detección automática de codificación
        print(f"Leyendo archivo CSV: {archivo_csv}")
        
        # Intentar diferentes codificaciones comunes
        codificaciones = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        df = None
        codificacion_usada = None
        
        for encoding in codificaciones:
            try:
                df = pd.read_csv(archivo_csv, encoding=encoding)
                codificacion_usada = encoding
                print(f"Archivo leído correctamente con codificación: {encoding}")
                break
            except (UnicodeDecodeError, UnicodeError):
                print(f"Falló codificación: {encoding}")
                continue
        
        if df is None:
            raise Exception("No se pudo leer el archivo con ninguna codificación común")
        print(f"Se encontraron {len(df)} registros en el CSV")
        
        # Mostrar las primeras filas para verificación
        print("\nPrimeras 5 filas del CSV:")
        print(df.head())
        print(f"\nColumnas encontradas: {list(df.columns)}")
        
        # Transformar la columna 'semana' si existe
        if 'semana' in df.columns:
            print("\nTransformando formato de semana...")
            
            def convertir_semana(valor):
                if pd.isna(valor) or valor == '' or valor is None:
                    return None
                
                valor_str = str(valor).strip()
                
                # Si ya tiene formato "Wk XX", devolverlo tal como está
                if valor_str.startswith('Wk '):
                    return valor_str
                
                # Si es solo un número, convertirlo a "Wk XX"
                try:
                    numero = int(float(valor_str))  # float primero por si viene como "12.0"
                    return f"Wk {numero}"
                except (ValueError, TypeError):
                    # Si no se puede convertir, mantener el valor original
                    print(f"Advertencia: No se pudo procesar el valor de semana: '{valor}'")
                    return valor_str
            
            df['semana'] = df['semana'].apply(convertir_semana)
            
            # Mostrar ejemplos de transformación
            ejemplos = df['semana'].dropna().head(5).tolist()
            print("Ejemplos de transformación de semana:", ejemplos)
        
        # Agregar columnas que no están en el CSV pero sí en la BD
        if 'nombre_empleado' not in df.columns:
            df['nombre_empleado'] = None  # o '' para string vacío
            print("Columna 'nombre_empleado' agregada con valores NULL")
        
        if 'apellido_empleado' not in df.columns:
            df['apellido_empleado'] = None  # o '' para string vacío
            print("Columna 'apellido_empleado' agregada con valores NULL")
        
        if 'fecha_creacion' not in df.columns:
            df['fecha_creacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print("Columna 'fecha_creacion' agregada con timestamp actual")
        
        # Conectar a la base de datos SQLite
        print(f"\nConectando a la base de datos: {archivo_bd}")
        conn = sqlite3.connect(archivo_bd)
        
        # Mostrar estructura de la tabla (opcional)
        cursor = conn.cursor()
        try:
            cursor.execute(f"PRAGMA table_info({tabla_destino})")
            columnas_bd = cursor.fetchall()
            print(f"\nEstructura de la tabla '{tabla_destino}':")
            columnas_validas = []
            for col in columnas_bd:
                print(f"  - {col[1]} ({col[2]})")
                columnas_validas.append(col[1])
        except sqlite3.OperationalError:
            print(f"Advertencia: La tabla '{tabla_destino}' no existe. Se creará automáticamente.")
            columnas_validas = None
        
        # Filtrar DataFrame para incluir solo columnas que existen en la BD
        if columnas_validas:
            # Encontrar columnas del CSV que están en la BD (excluyendo 'id' si es autoincrement)
            columnas_csv = df.columns.tolist()
            columnas_a_insertar = []
            
            for col in columnas_csv:
                if col in columnas_validas and col.lower() != 'id':  # Excluir ID si es autoincrement
                    columnas_a_insertar.append(col)
            
            # Filtrar DataFrame
            df_filtrado = df[columnas_a_insertar].copy()
            
            print(f"\nColumnas del CSV: {columnas_csv}")
            print(f"Columnas que se insertarán: {columnas_a_insertar}")
            
            # Identificar columnas que están en la BD pero no en el CSV
            columnas_faltantes = [col for col in columnas_validas if col not in columnas_csv and col.lower() != 'id']
            if columnas_faltantes:
                print(f"Columnas de la BD que no están en el CSV: {columnas_faltantes}")
                
                # Agregar columnas faltantes con valores por defecto
                for col in columnas_faltantes:
                    if col in ['nombre_empleado', 'apellido_empleado']:
                        df_filtrado[col] = None
                    elif col == 'fecha_creacion':
                        df_filtrado[col] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        df_filtrado[col] = None
                        
                print(f"Columnas agregadas con valores por defecto: {columnas_faltantes}")
            
            # Reordenar columnas según el orden de la BD (excluyendo ID)
            columnas_ordenadas = [col for col in columnas_validas if col in df_filtrado.columns and col.lower() != 'id']
            df_final = df_filtrado[columnas_ordenadas]
            
            # Limpiar valores NaN, None, y strings vacíos
            print("\nLimpiando valores nulos y vacíos...")
            
            # Reemplazar NaN, None, y strings vacíos con valores apropiados
            for columna in df_final.columns:
                # Contar valores problemáticos antes de limpiar
                nulos_antes = df_final[columna].isna().sum()
                vacios_antes = (df_final[columna] == '').sum() if df_final[columna].dtype == 'object' else 0
                
                if nulos_antes > 0 or vacios_antes > 0:
                    print(f"  - {columna}: {nulos_antes} NaN, {vacios_antes} vacíos")
                    
                    # Para columnas de texto, reemplazar con string vacío o un valor por defecto
                    if df_final[columna].dtype == 'object':
                        # Reemplazar NaN con string vacío
                        df_final[columna] = df_final[columna].fillna('')
                        # Limpiar espacios en blanco
                        df_final[columna] = df_final[columna].astype(str).str.strip()
                        # Si quedó como 'nan' (string), reemplazar con vacío
                        df_final[columna] = df_final[columna].replace(['nan', 'None', 'NaN'], '')
                    else:
                        # Para columnas numéricas, reemplazar con 0 o un valor apropiado
                        df_final[columna] = df_final[columna].fillna(0)
            
            # Verificación final de valores nulos
            print("\nVerificación final de valores nulos por columna:")
            for columna in df_final.columns:
                nulos = df_final[columna].isna().sum()
                vacios = (df_final[columna] == '').sum() if df_final[columna].dtype == 'object' else 0
                if nulos > 0 or vacios > 0:
                    print(f"{columna}: {nulos} nulos, {vacios} vacíos")
                    
            # Mostrar ejemplo de descripcion_defecto para diagnóstico
            print("\nPrimeros 10 valores de 'descripcion_defecto':")
            if 'descripcion_defecto' in df_final.columns:
                for i, val in enumerate(df_final['descripcion_defecto'].head(10), 1):
                    print(f"  {i}. '{val}' (tipo: {type(val).__name__}, len: {len(str(val))})")
            
        else:
            df_final = df
            print("\nAdvertencia: No se pudo obtener estructura de la tabla. Insertando todas las columnas.")
        
        # Insertar datos en la base de datos
        print(f"\nInsertando {len(df_final)} registros en la tabla '{tabla_destino}'...")
        print(f"Columnas finales a insertar: {list(df_final.columns)}")
        
        # Usar if_exists='append' para agregar datos sin eliminar existentes
        # Cambiar a 'replace' si quieres reemplazar toda la tabla
        df_final.to_sql(tabla_destino, conn, if_exists='append', index=False)
        
        # Confirmar cambios
        conn.commit()
        
        # Verificar inserción
        cursor.execute(f"SELECT COUNT(*) FROM {tabla_destino}")
        total_registros = cursor.fetchone()[0]
        print(f"Migración completada exitosamente!")
        print(f"Total de registros en la tabla '{tabla_destino}': {total_registros}")
        
        # Mostrar algunos registros de ejemplo
        print(f"\nÚltimos 3 registros insertados:")
        cursor.execute(f"SELECT * FROM {tabla_destino} ORDER BY id DESC LIMIT 3")
        registros = cursor.fetchall()
        
        # Obtener nombres de columnas
        cursor.execute(f"PRAGMA table_info({tabla_destino})")
        columnas = [col[1] for col in cursor.fetchall()]
        
        for i, registro in enumerate(registros, 1):
            print(f"  Registro {i}: {dict(zip(columnas, registro))}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error durante la migración: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

def main():
    """Función principal para ejecutar la migración"""
    
    # Configuración - MODIFICA ESTOS VALORES SEGÚN TUS ARCHIVOS
    ARCHIVO_CSV = "unificado.csv"  # Cambia por la ruta de tu CSV
    ARCHIVO_BD = "registros.db"  # Cambia por la ruta de tu BD SQLite
    TABLA_DESTINO = "reparaciones"  # Cambia por el nombre de tu tabla
    
    print("=== SCRIPT DE MIGRACIÓN CSV A SQLITE ===\n")
    print(f"Archivo CSV: {ARCHIVO_CSV}")
    print(f"Base de datos: {ARCHIVO_BD}")
    print(f"Tabla destino: {TABLA_DESTINO}")
    print("-" * 50)
    
    # Ejecutar migración
    exito = migrar_csv_a_sqlite(ARCHIVO_CSV, ARCHIVO_BD, TABLA_DESTINO)
    
    if exito:
        print("\nProceso completado exitosamente!")
    else:
        print("\nEl proceso falló. Revisa los errores anteriores.")

if __name__ == "__main__":
    main()