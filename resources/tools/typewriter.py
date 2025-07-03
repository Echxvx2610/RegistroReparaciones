import pandas as pd 
import openpyxl
import os
import shutil
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

def load_excel_data():
    """Cargar datos de Excel para búsqueda de empleados y ensambles"""
    try:
        # Cargar datos de personal
        df_personal = pd.read_excel("resources/data/HeadCount_220125.xlsx")
        df_personal_filter = df_personal[["Id", "Name", "Job Position"]]
        
        # Cargar datos de ensambles
        df_ensamble = pd.read_excel("resources/data/Lista_Ref_RW_230125.xlsx")
        df_ensamble_filter = df_ensamble[["Item", "Description", "Family Code"]]
        
        return df_personal_filter, df_ensamble_filter , None
    
    except Exception as e:
        return None, None, f"Error cargando los archivos Excel: {e}"

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
        name_parts = name_string.replace(",", " ").split()[:-1]
        if len(name_parts) >= 3:
            formated = (name_parts[2][0] + name_parts[0] + name_parts[1]).upper()
            return formated, name_string  # Devuelve el nombre formateado y el original
        return "error", name_string

#obtener la cuenta actual del usuario conectado
def get_current_user():
    try:
        current_user = os.getlogin()
        return current_user
    except Exception as e:
        print(f"Error al obtener el usuario actual: {e}")
        return "UKNOWN_USER"
    
    
def load_data_user(current_username):
    users = pd.read_excel('resources/data/HeadCount_220125.xlsx', engine='openpyxl')
    users = users[['Id', 'Name', 'Job Position']]
    users[['Formated_Name', 'Original_Name']] = users['Name'].apply(
        lambda x: pd.Series(formated_user_string(x))
    )
    matched_user = users[users['Formated_Name'] == current_username.upper()]
    if not matched_user.empty:
        row = matched_user.iloc[0]
        return {
            "Id": str(row['Id']),
            "Original_Name": row['Original_Name'],
            "Job Position": row['Job Position']
        }
    else:
        return None
    
    
# print(load_data_user(get_current_user()))