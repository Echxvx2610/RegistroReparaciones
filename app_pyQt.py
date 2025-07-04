# @author: Cristian Echevarria 
# @version: 1.0
# @description: Sistema de Registro de Defectos
# @fecha: 2023-08-30
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QFormLayout, QLabel, QLineEdit, QComboBox, QSpinBox, 
    QTextEdit, QPushButton, QGroupBox, QFileDialog, QMessageBox, QDialog, QListWidget,QMenuBar,QToolBar,QInputDialog,QDialog,QInputDialog,QGridLayout)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QPixmap,QAction,QIcon
import sys
import os
from datetime import datetime
import csv
from pathlib import Path
import shutil
from resources.tools import typewriter,qr_code
import pandas as pd 
import re

class SerialNumberManager:
    def __init__(self):
        self.serials_by_job = {}
        # Usar la ruta del CSV desde la aplicación principal
        self.csv_file_path = None

    def set_csv_path(self, path):
        """Establece la ruta del archivo CSV"""
        self.csv_file_path = path
        print(f"CSV path set to: {self.csv_file_path}")

    def extract_job_from_serial(self, serial):
        """Extrae el job del número de serial, manejando espacios extras --> 00001252250251A 1800012345"""
        parts = serial.strip().split()
        #print("extract_job_from_serial - parts:", parts)
        if len(parts) >= 2:
            # Si hay una letra sola seguida de espacio (como 'D 18000451')
            if len(parts[-2]) == 1:
                return f"{parts[-2]} {parts[-1]}"
            return parts[-1]
        return ""

    def get_last_id_for_job(self, job, sequence):
        """
        Busca el último ID usado para un job específico con secuencia 'BOTTOM'
        y devuelve el siguiente ID
        """
        if not self.csv_file_path:
            print("Error: CSV path not set")
            return 1  # Cambiado de 2 a 1 para el primer registro

        try:
            ids = []
            print(f"get_last_id_for_job - IDs: {ids}")
            with open(self.csv_file_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Saltar el encabezado
                for row in reader:
                    if len(row) >= 18:
                        serial = row[0].strip()  # Columna del número de serie
                        print("get_last_id_for_job - Serial:", serial)
                        row_sequence = row[17].strip()  # Columna de secuencia
                        row_job = self.extract_job_from_serial(serial)
                        print(f"Comparando - Job actual: '{job}', Job en fila: '{row_job}', Secuencia en fila: '{row_sequence}'")
                        
                        # Verificar si es el mismo job y secuencia
                        if row_job.strip() == job.strip() and row_sequence.upper() == sequence.upper():
                            try:
                                current_id = int(serial[1:5])
                                print("get_last_id_for_job - Current_id:", current_id)
                                ids.append(current_id)
                                print(f"ID encontrado: {current_id}")
                            except ValueError as e:
                                print(f"Error al convertir ID: {e}")
            
            if ids:
                # Obtener el siguiente ID: max(ids) + 1
                next_id = max(ids) + 1  # Cambiado de -1 a +1 para incrementar
                print(f"Próximo ID a usar: {next_id}")
                return next_id
            
            print("No se encontraron IDs previos, usando ID inicial 1")
            return 1  # Cambiado de 2 a 1 para el primer registro

        except Exception as e:
            print(f"Error al leer el CSV: {e}")
            return 1  # Cambiado de 2 a 1 para el primer registro

    
    def convert_month_to_hex(self, month):
        """
        Convierte el mes (1-12) a hexadecimal usando condicionales
        1-9 -> "1"-"9"
        10 -> "A"
        11 -> "B"
        12 -> "C"
        """
        try:
            month = int(month)
            if month < 1 or month > 12:
                raise ValueError(f"Mes inválido: {month}")
            
            # Conversión usando condicionales
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
        """
        Formatea la fecha de AA/M a AAM
        Ejemplo: 25/2 -> 252, 25/10 -> 25A
        """
        try:
            if '/' not in date_str:
                raise ValueError("Formato de fecha incorrecto. Use AA/M")
            
            year, month = date_str.split('/')
            if len(year) != 2:
                raise ValueError("El año debe tener 2 dígitos")
            
            hex_month = self.convert_month_to_hex(month)
            if hex_month is None:
                raise ValueError("Error al convertir el mes")
            
            # Imprimir para debug
            print(f"Año: {year}, Mes: {month}, Mes convertido: {hex_month}")
                
            return f"{year}{hex_month}"
            
        except ValueError as e:
            print(f"Error al formatear fecha: {e}")
            return None
    
    def generate_serial_number(self, identificador, fecha, ensamble, job, sequence):
        """
        Genera un número de serie, incrementando el ID si es necesario.
        Asegura que el número de serie tenga exactamente 26 caracteres.
        """
        try:
            print(f"Generando serial con secuencia: {sequence}")
            print(f"Job recibido: '{job}'")

            # Formatear año y mes en hexadecimal
            year_month = self.format_date(fecha)
            if not year_month:
                return None

            # Incrementar ID si es secuencia BOTTOM
            if sequence and sequence.upper() == "BOTTOM":
                new_id = self.get_last_id_for_job(job, "BOTTOM")
                identificador = str(new_id).zfill(4)
                print(f"Nuevo ID generado para BOTTOM: {identificador}")

            # Limpiar y formatear el código de ensamble
            ensamble = ensamble.replace("003-", "").replace("-", "")

            # Eliminar espacios extras del job
            job = job.strip()

            # Generar el número de serie
            serial_number = f"0{identificador}{year_month}{ensamble} {job}"

            # Asegurar que la longitud del número de serie sea de 26 caracteres
            if len(serial_number) > 26:
                serial_number = serial_number[:26]
            
            print(f"SerialNumberManager: Serial number generated - {serial_number}")
            print("SerialNumberManager: Serial number length -", len(serial_number))

            # Asegurarse de que el serial tiene exactamente 26 caracteres
            return serial_number[:26]  # Recortar o ajustar a 26 caracteres.

        except Exception as e:
            print(f"Error al generar el número de serie: {e}")
            return None

    
class ViewRecordDialog(QDialog):
    def __init__(self, record_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ver Registro")
        self.setMinimumSize(600, 400)
        self.setWindowIcon(QIcon(r"resources/img/carpetas.png")) 
        
        layout = QHBoxLayout(self)
        
        # Área de texto para mostrar la información
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setStyleSheet("width: 200px;")
        
        # Cargar y mostrar el texto
        with open(record_path / "registro.txt", "r", encoding='utf-8') as f:
            formatted_content = self.format_content(f.read())
            self.text_display.setText(formatted_content)
        
        # Imagen del esquemático
        self.image_label = QLabel()
        image_files = list(record_path.glob("esquematico.*"))
        if image_files:
            pixmap = QPixmap(str(image_files[0]))
            scaled_pixmap = pixmap.scaled(500, 500, Qt.KeepAspectRatio)
            self.image_label.setPixmap(scaled_pixmap)
        
        # Botón de cerrar
        # self.close_button = QPushButton("Cerrar")
        # self.close_button.clicked.connect(self.close)
        
        layout.addWidget(self.text_display)
        layout.addWidget(self.image_label)
        #layout.addWidget(self.close_button)
        
    def format_content(self, content):
        """Formatea el contenido para mostrar las categorías en negrita."""
        formatted_lines = []
        for line in content.split('\n'):
            if ':' in line:
                category, value = line.split(':', 1)
                formatted_lines.append(f"<b>{category}:</b>{value}")
            else:
                formatted_lines.append(line)
        
        return '<br>'.join(formatted_lines)
    
class LabelShow(QDialog):
    """ Ventana flotante para mostrar el código QR """
    def __init__(self, serial_number, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Etiqueta Generada")
        self.setGeometry(150, 250, 250, 100)
        self.setWindowIcon(QIcon(r"resources/img/carpetas.png"))
        self.setFixedSize(self.size())  
        # mostrar un texto en la ventana flotante ( serial number )
        self.line_edit = QLineEdit(self)
        self.line_edit.setReadOnly(True)
        self.line_edit.setText(serial_number)
        layout = QVBoxLayout(self)
        layout.addWidget(self.line_edit)
        self.setLayout(layout)
        
class QRInputDialog(QDialog):
    """ Diálogo para introducir la fecha, ensamble y job """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generar Etiqueta QR")
        self.setGeometry(200, 200, 350, 100)

        # Crear un layout de formulario
        layout = QFormLayout()

        # Crear los widgets
        self.identificador = "0001"      
        self.fecha_input = QLineEdit(self)
        self.ensamble_input = QLineEdit(self)
        self.job_input = QLineEdit(self)

        # Agregar etiquetas y campos de entrada al layout
        layout.addRow("Fecha (AA/M):", self.fecha_input)
        layout.addRow("Ensamble (003-XXXXX-XX):", self.ensamble_input)
        layout.addRow("Job (XXXXXXXXXX):", self.job_input)

        # Crear botón de aceptar
        self.accept_button = QPushButton("Generar Etiqueta", self)
        self.accept_button.clicked.connect(self.accept)

        # Agregar botón al layout
        layout.addWidget(self.accept_button)
        self.setLayout(layout)

    def convert_month_to_hex(self, month):
        """
        Convierte el mes (1-12) a hexadecimal usando condicionales
        1-9 -> "1"-"9"
        10 -> "A"
        11 -> "B"
        12 -> "C"
        """
        try:
            month = int(month)
            if month < 1 or month > 12:
                raise ValueError(f"Mes inválido: {month}")
            
            # Conversión usando condicionales
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
        """
        Formatea la fecha de AA/M a AAM
        Ejemplo: 25/2 -> 252, 25/10 -> 25A
        """
        try:
            if '/' not in date_str:
                raise ValueError("Formato de fecha incorrecto. Use AA/M")
            
            year, month = date_str.split('/')
            if len(year) != 2:
                raise ValueError("El año debe tener 2 dígitos")
            
            hex_month = self.convert_month_to_hex(month)
            if hex_month is None:
                raise ValueError("Error al convertir el mes")
            
            # Imprimir para debug
            print(f"Año: {year}, Mes: {month}, Mes convertido: {hex_month}")
                
            return f"{year}/{hex_month}"
            
        except ValueError as e:
            print(f"Error al formatear fecha: {e}")
            return None

    def get_input_values(self):
        """ Devuelve los valores de los campos de texto con la fecha formateada """
        try:
            # Obtener los valores
            fecha_str = self.fecha_input.text().strip()
            ensamble = self.ensamble_input.text().strip().upper()
            print(ensamble)
            job = self.job_input.text().strip()
            
            errores = []
            
            # Validar formato de fecha (AA/M)
            if not fecha_str:
                errores.append("La fecha es requerida")
            elif '/' not in fecha_str:
                errores.append("La fecha debe tener el formato AA/M (ejemplo: 24/3)")
            else:
                try:
                    year, month = fecha_str.split('/')
                    if len(year) != 2:
                        errores.append("El año debe tener 2 dígitos")
                    if not month.isdigit() or int(month) < 1 or int(month) > 12:
                        errores.append("El mes debe ser un número entre 1 y 12")
                except:
                    errores.append("Formato de fecha inválido")
            
            # Validar formato de ensamble (003-XXXXX-XA)
            if not ensamble:
                errores.append("El ensamble es requerido")
            elif not re.match(r'^003-\d{4,5}-[0-9][A-Z]$', ensamble):
                errores.append("El ensamble debe tener el formato 003-XXXXX-XA (ejemplo: 003-25025-1A)")
                
            # Validar formato de job (10 caracteres)
            if not job:
                errores.append("El job es requerido")
            elif len(job) != 10:
                errores.append("El job debe tener exactamente 10 caracteres")
            elif not job.replace('-', '').isalnum():  # Permitir alfanumérico y guiones
                errores.append("El job solo puede contener letras, números y guiones")
                
            if errores:
                # Mostrar todos los errores en un solo mensaje
                QMessageBox.warning(self, "Formato Inválido", 
                                "Por favor corrija los siguientes errores:\n- " + "\n- ".join(errores))
                return None, None, None, None
                
            # Si pasa todas las validaciones, formatear la fecha
            fecha_formateada = self.format_date(fecha_str)
            if fecha_formateada is None:
                QMessageBox.warning(self, "Error", "Error al formatear la fecha")
                return None, None, None, None
                
            return (
                self.identificador,
                fecha_formateada,
                ensamble,
                job
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error inesperado: {str(e)}")
            return None, None, None, None
        

class DefectRegistrationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Registro de Defectos")
        self.setMinimumWidth(800)
        self.setWindowIcon(QIcon(r"resources/img/carpetas.ico"))

        self.load_stylesheet()
        self.create_menubar()
        self.create_toolbar()
        self.load_excel_data()

        self.registros_dir = Path("registros")
        self.registros_dir.mkdir(exist_ok=True)
        self.csv_file_path = Path(r"registros\registros.csv")
        if not self.csv_file_path.exists():
            self.create_csv_file()

        self.serial_manager = SerialNumberManager()
        self.serial_manager.set_csv_path(self.csv_file_path)
        self.serials_by_job = {}

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(10, 10, 10, 10)
        grid_layout.setSpacing(15)
        main_widget.setLayout(grid_layout)

        # Información Básica
        basic_group = QGroupBox("Información Básica")
        basic_layout = QFormLayout()
        self.date_time = QLabel(QDateTime.currentDateTime().toString("dd/MM/yyyy"))
        self.week = QLabel(str(datetime.now().isocalendar()[1]))
        self.serial_number = QLineEdit()
        self.serial_number.setPlaceholderText("Número de serie (25-26 caracteres) 00000AAMENSAMBLE JOB")
        self.serial_number.textChanged.connect(self.check_serial_length)
        self.sequence = "N/A"
        basic_layout.addRow("Fecha de registro:", self.date_time)
        basic_layout.addRow("Semana:", self.week)
        basic_layout.addRow("S/N:", self.serial_number)
        basic_group.setLayout(basic_layout)

        # Ubicación y Clasificación
        location_group = QGroupBox("Ubicación y Clasificación")
        location_layout = QFormLayout()
        self.cost_center = QComboBox()
        self.cost_center.addItems(["8942", "8943", "8944"])
        self.cost_center.currentTextChanged.connect(self.update_area)
        self.area = QLabel("SMT")
        self.item = QLineEdit()
        self.item.textChanged.connect(self.search_assembly_info)
        self.description = QLineEdit()
        self.description.setReadOnly(True)
        self.family = QLineEdit()
        self.family.setReadOnly(True)
        self.model = QLineEdit()
        # self.model.setReadOnly(True)
        location_layout.addRow("Centro de Costo:", self.cost_center)
        location_layout.addRow("Área:", self.area)
        location_layout.addRow("Item:", self.item)
        location_layout.addRow("Descripción:", self.description)
        location_layout.addRow("Familia:", self.family)
        # location_layout.addRow("Modelo:", self.model)
        location_group.setLayout(location_layout)

        # Información de Reparación
        repair_group = QGroupBox("Información de Reparación")
        repair_layout = QFormLayout()
        self.employee_number = QLineEdit()
        self.employee_number.textChanged.connect(self.search_employee_info)
        self.employee_name = QLineEdit()
        self.employee_name.setReadOnly(True)
        self.shift = QLabel(self.calculate_shift())
        repair_layout.addRow("No. empleado:", self.employee_number)
        repair_layout.addRow("Nombre:", self.employee_name)
        repair_layout.addRow("Turno:", self.shift)
        repair_group.setLayout(repair_layout)

        # Información del Defecto
        defect_group = QGroupBox("Información del Defecto")
        defect_layout = QFormLayout()
        self.fault_code = QComboBox()
        self.fault_code.addItems([
            "DESALINEADO INCLINADO", "FALTANTE NO COLOCADO", "UPSIDE-DOWN",
            "TIPO EQUIVOCADO", "PUENTE DE SOLDADURA", "DAÑADO MANEJO",
            "DAÑO ELECTRICO", "DAÑADO MÁQUINA", "QUEMADO OPERADOR",
            "PARTE EXTRA", "DEMASIADA GOMA", "TERMINAL LEVANTADA",
            "SOLDADURA FALTANTE", "SESGADO DESALINEADO", "EXCESO DE SOLDADURA",
            "SOLDADURA INSUFICIENTE", "VALOR EQUIVOCADO",
            "REEMPLAZAR COMPONENTE POR CAMBIO EN ECO", "SOLDADURA FRIA",
            "SOLDADURA NO ADHIERE AL PAD", "COMPONENTE CON FISURA POR GOLPE",
            "POLARIDAD EQUIVOCADA", "LUGAR EQUIVOCADO", "TERMINAL DOBLADA"
        ])
        self.defect_description = QTextEdit()
        self.defect_description.setMinimumHeight(70)
        self.schematic_ref = QLineEdit()
        self.component_pn = QLineEdit()
        defect_layout.addRow("Código de Falla:", self.fault_code)
        defect_layout.addRow("Descripción del defecto:", self.defect_description)
        defect_layout.addRow("Ref. del esquemático:", self.schematic_ref)
        defect_layout.addRow("Item P/N:", self.component_pn)
        defect_group.setLayout(defect_layout)

        # Agregar widgets al grid_layout (2x2)
        grid_layout.addWidget(basic_group, 0, 0)
        grid_layout.addWidget(repair_group, 0, 1)
        grid_layout.addWidget(location_group, 1, 0)
        grid_layout.addWidget(defect_group, 1, 1)

        self.selected_image_path = None
        self.load_data_user(self.get_current_user())
        self.create_actions()

    
    def generar_qr_dialog(self):
        """
        Abre un diálogo personalizado para ingresar datos y generar un código QR
        """
        try:
            dialog = QRInputDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                identificador, fecha, ensamble, job = dialog.get_input_values()
                print(f"Datos ingresados: Identificador: {identificador}, Fecha: {fecha}, Ensamble: {ensamble}, Job: {job}")
                
                # Validar que todos los campos requeridos estén completos
                errores = []
                if not fecha:
                    errores.append("La fecha es requerida")
                if not ensamble:
                    errores.append("El ensamble es requerido")
                if not job:
                    errores.append("El job es requerido")
                
                if errores:
                    # Si hay errores, mostrar un mensaje con todos los campos faltantes
                    mensaje_error = "Por favor complete los siguientes campos:\n- " + "\n- ".join(errores)
                    QMessageBox.warning(self, "Campos Requeridos", mensaje_error)
                    return None
                
                # Si todos los campos están completos, continuar con la generación
                if job not in self.serials_by_job:
                    serial_number = self.serial_manager.generate_serial_number(
                        identificador, 
                        fecha, 
                        ensamble, 
                        job,
                        self.sequence # Usar la secuencia almacenada en la clase
                    )
                    if serial_number:
                        self.serials_by_job[job] = serial_number
                else:
                    serial_number = self.serials_by_job[job]
                
                self.mostrar_serial_en_ventana_flotante(serial_number)
                return serial_number
            
            return None
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar el código QR: {str(e)}")
            return None
            
                
    def mostrar_serial_en_ventana_flotante(self, serial_number):
        """ Muestra el código QR en una ventana flotante no modal """
        self.label_show = LabelShow(serial_number)
        self.label_show.show()
    
    def load_stylesheet(self):
        """ Carga la hoja de estilos desde un archivo.qss para posteriormente aplicarla a la app """
        # Obtener la ruta al archivo style.qss
        style_path = Path("resources/tools/styles.qss")
        
        if style_path.exists():
            # Leer el archivo .qss
            with open(style_path, "r", encoding="utf-8") as file:
                stylesheet = file.read()
            
            # Aplicar el estilo a la aplicación
            QApplication.instance().setStyleSheet(stylesheet)
        else:
            print("El archivo style.qss no se encuentra.")

    def formated_user_string(self,name_string):
        name_parts = name_string.replace(",", " ").split()[:-1]
        if len(name_parts) >= 3:
            formated = (name_parts[2][0] + name_parts[0] + name_parts[1]).upper()
            return formated, name_string  # Devuelve el nombre formateado y el original
        return "error", name_string

    def load_data_user(self,current_username):
        users = pd.read_excel('resources/data/HeadCount_220125.xlsx', engine='openpyxl')
        users = users[['Id', 'Name', 'Job Position']]

        # Crear nuevas columnas con el nombre formateado y el original
        users[['Formated_Name', 'Original_Name']] = users['Name'].apply(
            lambda x: pd.Series(self.formated_user_string(x))
        )

        # Buscar coincidencias entre el usuario actual (OS) y los nombres formateados
        matched_user = users[users['Formated_Name'] == current_username.upper()]

        if not matched_user.empty:
            row = matched_user.iloc[0]
            self.employee_number.setText(str(row['Id']))
            self.employee_name.setText(row['Original_Name'])
            # print(f"Usuario original: {row['Original_Name']}")
            # print(f"Usuario formateado: {row['Formated_Name']}")
            # print(f"ID del usuario: {row['Id']}")
            # print(f"Posición del trabajo: {row['Job Position']}")
        else:
            QMessageBox.critical(self, "Error", "Usuario no encontrado en la base de datos.")


    #obtener la cuenta actual del usuario conectado
    def get_current_user(self):
        try:
            current_user = os.getlogin()
            return current_user
        except Exception as e:
            print(f"Error al obtener el usuario actual: {e}")
            return "UKNOWN_USER"
    
    def upload_image(self):
        """ Permite cargar una imagen desde el explorador de archivos """
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg)"
        )
        if file_name:
            self.selected_image_path = file_name
            self.upload_button.setText(f"Imagen seleccionada: {Path(file_name).name}")
    
    def create_menubar(self):
        """ Inicializa el menú de la app """
        menubar = self.menuBar()
        # File menu
        file_menu = menubar.addMenu("Archivo")
        file_menu.addAction(self.create_action("Guardar", "save", self.save_record, "Ctrl+S"))
        file_menu.addAction(self.create_action("Limpiar", "clear", self.clear_form, "Ctrl+N"))
        file_menu.addSeparator()
        file_menu.addAction(self.create_action("Salir", "exit", self.close, "Ctrl+Q"))
        
        # View menu
        view_menu = menubar.addMenu("Ver")
        view_menu.addAction(self.create_action("Ver Registros", "list", self.show_records, "Ctrl+L"))
    
    def create_toolbar(self):
        """ Inicializa la barra de herramientas de la app """
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)
        # Cambiar orientación de la barra
        self.toolbar.setOrientation(Qt.Vertical)
        self.addToolBar(Qt.LeftToolBarArea, self.toolbar)
        # Add actions to toolbar
        self.toolbar.addAction(self.create_action("Guardar Registro", "guardar", self.save_record))
        self.toolbar.addAction(self.create_action("Limpiar", "recargar", self.clear_form))
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.create_action("Ver Registros", "archivos", self.show_records))
        # Agregar acción para generar QR
        self.toolbar.addAction(self.create_action("Generar Serial", "escaner", self.generar_qr_dialog))

    def create_action(self, text, icon_name, slot, shortcut=None):
        """ Crea acciones para la barra de herramientas y el menú (conectadas a los slots correspondientes) """
        action = QAction(text, self)
        # You would typically set icons like this:
        # action.setIcon(QIcon(f"icons/{icon_name}.png"))
        action.setIcon(QIcon(f"resources/img/{icon_name}.png"))
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        return action
    
    def create_actions(self):
        """ Crea acciones para la barra de herramientas y el menú """
        # These could be class attributes if needed elsewhere
        self.save_action = self.create_action("Guardar", "save", self.save_record, "Ctrl+S")
        self.clear_action = self.create_action("Limpiar", "clear", self.clear_form, "Ctrl+N")
        self.view_records_action = self.create_action("Ver Registros", "list", self.show_records, "Ctrl+L")
        self.generate_qr_action = self.create_action("Generar QR", "qr", self.generar_qr_dialog)
        
    def load_excel_data(self):
        """Cargar datos de Excel para búsqueda de empleados y ensambles"""
        self.df_personal_filter, self.df_ensamble_filter, error_message = typewriter.load_excel_data()
        if error_message:
            QMessageBox.warning(self, "Error", error_message)
            
    def search_employee_info(self):
        """Buscar información del empleado al ingresar su número"""
        no_empleado = self.employee_number.text()
        if no_empleado:
            name, position = typewriter.search_employee_info(no_empleado, self.df_personal_filter)
            self.employee_name.setText(name)
            self.employee_position = position
        else:
            self.employee_name.clear()
            self.employee_position = ""

    def search_assembly_info(self):
        """Buscar información del ensamble al ingresar el item"""
        no_ensamble = self.item.text()
        if no_ensamble:
            description, family_code = typewriter.search_assembly_info(no_ensamble, self.df_ensamble_filter)
            self.description.setText(description)
            self.family.setText(family_code)
            self.model.setText(description)
        else:
            self.description.clear()
            self.family.clear()
            self.model.clear()

    def check_serial_length(self):
        """Verifica la longitud del S/N y muestra el popup si tiene 26 caracteres."""
        serial_number = self.serial_number.text()
        if len(serial_number) == 26:  # Si el S/N tiene 26 caracteres
            sequence = self.ask_for_sequence()  # Mostrar popup para seleccionar la secuencia
            if sequence:
                self.sequence = sequence  # Guardar la secuencia seleccionada
            # Si el usuario omite la selección, no cambiamos self.sequence
            
        elif len(serial_number) == 25:
            sequence = self.ask_for_sequence()  # Mostrar popup para seleccionar la secuencia
            if sequence:
                self.sequence = sequence  # Guardar la secuencia seleccionada
            # Si el usuario omite la selección, no cambiamos self.sequence
            
    def ask_for_sequence(self):
        """Muestra un popup para preguntar por la secuencia (10 o 20, bottom o top)"""
        options = ["Bottom","Top"]
        sequence, ok = QInputDialog.getItem(
            self,
            "Seleccionar Secuencia",
            "Elija la secuencia a registrar:",
            options,
            0,  # Índice predeterminado
            False  # No editable
        )

        if ok and sequence:
            return sequence
        else:
            return None
    
    def create_csv_file(self):
        """ Crea el archivo CSV con los encabezados si no existe """
        headers = [
            "S/N", "Item", "Familia", "Descripcion", "Area", "Centro de Costo", 
            "Semana", "Fecha de registro", "No. empleado", "Nombre empleado", 
            "Puesto","Turno", "Codigo de Falla", 
            "Descripcion del defecto", "Ref. del esquematico", "Item P/N", 
            "Secuencia", "Ruta de Imagen"
        ]
        
        with open(self.csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
    
    #___________________________________________________________________________________________________________
     
    def save_record(self):
        """ Guarda los datos del registro en un archivo CSV """
        # Lista para almacenar errores
        validation_errors = []
        
        # Validar campos obligatorios
        if not self.serial_number.text():
            validation_errors.append("El número de serie es obligatorio")
        
        # Validar otros campos obligatorios
        if not self.item.text():
            validation_errors.append("El Item es obligatorio")
        
        if not self.family.text():
            validation_errors.append("La Familia es obligatoria")
        
        if not self.description.text():
            validation_errors.append("La Descripción es obligatoria")
        
        if not self.area.text():
            validation_errors.append("El Área es obligatoria")
        
        if not self.cost_center.currentText() or self.cost_center.currentText() == "Seleccione":
            validation_errors.append("Debe seleccionar un Centro de Costo")
        
        if not self.week.text():
            validation_errors.append("La Semana es obligatoria")
        
        if not self.employee_number.text():
            validation_errors.append("El Número de empleado es obligatorio")
        
        if not self.employee_name.text():
            validation_errors.append("El Nombre del empleado es obligatorio")
        
        if not self.shift.text():
            validation_errors.append("El Turno es obligatorio")
        
        if self.fault_code.currentText() == "Seleccione":
            validation_errors.append("Debe seleccionar un Código de Falla")
        
        if not self.defect_description.toPlainText():
            validation_errors.append("La Descripción del defecto es obligatoria")
            
        if not self.schematic_ref.text():
            validation_errors.append("La Referencia del esquematico es obligatoria")
        
        if not self.component_pn.text():
            validation_errors.append("El Item P/N es obligatorio")
        
        # Si hay errores, mostrar todos juntos y terminar la función
        if validation_errors:
            QMessageBox.warning(self, "Error de Validación", "\n".join(validation_errors))
            return
        
        # Validar la secuencia si el S/N tiene 26 o 25 caracteres
        current_serial = self.serial_number.text()
        if (len(current_serial) == 26 or len(current_serial) == 25) and self.sequence == "N/A":
            sequence = self.ask_for_sequence()
            if not sequence:
                QMessageBox.warning(self, "Error", "Debe seleccionar una secuencia (10 o 20, bottom o top)")
                return
            self.sequence = sequence  # Guardar la secuencia seleccionada
        
        
        # Obtener el número de serie actual
        if len(current_serial) == 26:
            job = current_serial[16::]
            year = current_serial[5:7] 
            month = current_serial[8] 
            formated_date = f'{year}/{month}'
            print("save_to_csv = job: ", job)
            serial_components = {
                'identificador': current_serial[1:5],
                'fecha': formated_date,
                'ensamble': current_serial[8:15],
                'job': job
            }
            print("serial_components:", serial_components)
        elif len(current_serial) == 25:
            job = current_serial[15::]
            year = current_serial[5:7]
            month = current_serial[7] 
            formated_date = f'{year}/{month}'
            print("save_to_csv = job: ", job)
            serial_components = {
                'identificador': current_serial[1:5],
                'fecha': formated_date,
                'ensamble': current_serial[8:14],
                'job': job
            }
            print("serial_components:", serial_components)
        
        # Validar que serial_components tiene todos los componentes necesarios
        if not all(serial_components.values()):
            QMessageBox.warning(self, "Error", "Número de serie inválido o incompleto")
            return
        
        # Generar nuevo número de serie usando los componentes
        serial_number = self.serial_manager.generate_serial_number(
            serial_components['identificador'],
            serial_components['fecha'],
            serial_components['ensamble'],
            serial_components['job'],
            self.sequence
        )
        
        if not serial_number:
            QMessageBox.warning(self, "Error", "No se pudo generar el número de serie")
            return

        # Validar el tiempo de reparación (debe ser mayor que cero)
        # if self.repair_time.value() <= 0:
        #     QMessageBox.warning(self, "Error", "El tiempo de reparación debe ser mayor que cero")
        #     return
        
        # Fecha exacta para el registro
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        record_data = [
            serial_number,  # S/N
            self.item.text().upper(),  # Item
            self.family.text().upper(),  # Familia
            self.description.text().upper(),  # Descripcion
            self.area.text().upper(),  # Area
            self.cost_center.currentText(),  # Centro de Costo
            self.week.text(),  # Semana
            date,  # Fecha de registro
            self.employee_number.text(),  # No. empleado
            self.employee_name.text().upper(),  # Nombre empleado
            getattr(self, 'employee_position', ''),  # Puesto
            #self.repair_time.value(),  # Tiempo de reparacion
            self.shift.text(),  # Turno
            self.fault_code.currentText(),  # Codigo de Falla
            self.defect_description.toPlainText().upper(),  # Descripcion del defecto
            self.schematic_ref.text().upper(),  # Ref. del esquematico
            self.component_pn.text().upper(),  # Item P/N
            self.sequence.upper(),  # Secuencia
            self.selected_image_path if self.selected_image_path else ''  # Ruta de Imagen
        ]

        # Validar que todos los elementos de record_data están presentes
        if any(item is None for item in record_data):
            QMessageBox.warning(self, "Error", "Hay campos requeridos que están vacíos")
            return
        
        try:
            with open(self.csv_file_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(record_data)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar el registro: {str(e)}")
            print(f"Error al guardar: {str(e)}")
            return

        print("Registro guardado en CSV.") 
        QMessageBox.information(self, "Éxito", "Registro guardado correctamente")
        self.clear_form()
    #____________________________________________________________________________________________________________
    
    
    def show_records(self):
        """ Abre Excel con los registros guardados """
        try:
            os.startfile(self.csv_file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al abrir el archivo: {str(e)}")
            print(f"Error al abrir el archivo: {str(e)}")
            return
    
    def clear_form(self):
        """ Limpia los campos del formulario """
        # Limpiar todos los campos excepto fecha, semana y turno
        self.serial_number.clear()
        self.item.clear()
        self.description.clear()
        self.family.clear()
        self.model.clear()
        self.employee_number.clear()
        #self.repair_time.setValue(1)
        self.defect_description.clear()
        self.schematic_ref.clear()
        self.component_pn.clear()
        #self.upload_button.setText("Agregue foto del defecto (Si posee una foto del defecto)")
        self.selected_image_path = None
        self.sequence = "N/A"  # Resetear la secuencia
    
    def update_area(self, cost_center):
        """ Actualizacion en tiempo real del area segun el centro de costo """
        area_mapping = {
            "8942": "SMT",
            "8943": "THT",
            "8944": "TNT"
        }
        self.area.setText(area_mapping.get(cost_center, ""))

    def calculate_shift(self):
        """ Calcula el turno segun la hora actual """
        # hora en formato 24 horas
        hour = QDateTime.currentDateTime().time().hour()
        #print(hour)
        if 7 <= hour < 17:
            return "1er Turno"
        elif 17 <= hour < 1:
            return "2do Turno"
        else:
            return "3er Turno"
        

        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DefectRegistrationApp()
    window.show()
    sys.exit(app.exec())
