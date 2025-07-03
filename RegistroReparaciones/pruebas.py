def parse_serial_number(serial):
        """
        Extrae los componentes del número de serie.
        Ejemplo de serial: '00128256328431B 1800056627'
        Devuelve:
            {
                "identificador": "0128",
                "fecha_hex": "2563",
                "ensamble_formateado": "003-28431-B",
                "job": "1800056627"
            }
        """
        try:
            # Separar por espacio
            parts = serial.strip().split()
            if len(parts) != 2:
                return None

    
            left_part, job = parts[0], parts[1]
            print(f"Partes del serial: {len(left_part)}, Job: {len(job)}")

            if len(left_part) == 14:
                identificador = left_part[1:5]  # '1282'
                fecha_hex = left_part[5:8]      # '569'
                ensamble_raw = left_part[8:14]  # '91541D'
                ensamble_raw = ensamble_raw[:-2] + '-' + ensamble_raw[-2:]  # '9154-1D'
            elif len(left_part) == 15:
                identificador = left_part[1:5]  # '1282'
                fecha_hex = left_part[5:8]      # '562'
                ensamble_raw = left_part[8:15]  # '283431G'
                ensamble_raw = ensamble_raw[:-2] + '-' + ensamble_raw[-2:]  # '28343-1G'
            
            # Formatear ensamble: ejemplo de '28431B' a '003-28431-B'
            if ensamble_raw:
                ensamble_formateado = f"003-{ensamble_raw}"
                print(f"Ensamble formateado: {ensamble_formateado}")
            else:
                ensamble_formateado = None
            return {
                "identificador": identificador,
                "fecha_hex": fecha_hex,
                "ensamble_formateado": ensamble_formateado,
                "job": job
            }

        except Exception as e:
            print(f"Error al analizar el número de serie: {e}")
            return None

serial = "00128256250251A 1800056627"
resultado = parse_serial_number(serial)
print(resultado)