import qrcode

def generar_qr(texto, nombre_archivo="resources/img/codigo_qr.png"):
    # Crear un objeto QRCode
    qr = qrcode.QRCode(
        version=1,  # Controla el tamaño del código QR (1 es el más pequeño)
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # Controla el nivel de corrección de errores
        box_size=3,  # Tamaño de cada "caja" del código QR
        border=1,  # Tamaño del borde (en cajas)
        
    )
    
    # Añadir el texto al código QR
    qr.add_data(texto)
    qr.make(fit=True)
    
    # Crear una imagen del código QR
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Guardar la imagen en un archivo
    img.save(nombre_archivo)
    
    return texto

def decodificar_ensamble(codigo_qr):
    """
    Función para decodificar el ensamble a su formato original "003-XXXXX-XX"
    a partir de la cadena contenida en el código QR.
    """
    if len(codigo_qr) == 27:
        codigo_qr = codigo_qr[9:17]
        parte_revision = codigo_qr[-3::]
        parte_informacion = codigo_qr[0:-3]
        ensamble_original = f"003-{parte_informacion}-{parte_revision}"
        return ensamble_original
    elif len(codigo_qr) == 26:
        codigo_qr = codigo_qr[9:15]
        parte_revision = codigo_qr[-2::]
        parte_informacion = codigo_qr[0:-2]
        ensamble_original = f"003-{parte_informacion}-{parte_revision}"
        return ensamble_original
    else:
        return "Formato incorrecto"
    

generar_qr("001012025265081A 1800563629")