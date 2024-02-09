import paramiko
import os
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configura la conexión SFTP
hostname = 'Server'
port = 22  # Puerto SFTP predeterminado
username = 'tu-usuario'
password = 'tu-clave'
remote_directory = 'tu-ruta-remota'  # Ruta a la carpeta remota
local_directory = 'tu-ruta-en-red-o-local'  # Ruta donde se guardarán los archivos descargados

# Configuración de correo electrónico
email_sender = 'correo-electronico'
email_password = 'contraseña'
smtp_server = 'servidor-smtp'
smtp_port = 587

def send_email(subject, body, recipients):
    msg = MIMEMultipart()
    msg['From'] = email_sender
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(email_sender, email_password)
        server.sendmail(email_sender, recipients, msg.as_string())

try:
    # Inicia la conexión SSH
    transport = paramiko.Transport((hostname, port))
    transport.connect(username=username, password=password)

    # Crea un objeto SFTP utilizando la conexión SSH
    sftp = paramiko.SFTPClient.from_transport(transport)

    # Obtener lista de carpetas en el directorio remoto con sus fechas de modificación
    folder_list = []
    for foldername in sftp.listdir_attr(remote_directory):
        folder_path = os.path.join(remote_directory, foldername.filename)
        folder_modification_time = datetime.datetime.fromtimestamp(foldername.st_mtime)
        folder_list.append((folder_path, folder_modification_time))

    # Ordenar la lista de carpetas por fecha de modificación
    folder_list.sort(key=lambda x: x[1], reverse=True)

    if folder_list:
        # Carpeta más reciente en el servidor remoto
        latest_remote_folder_path, _ = folder_list[0]
        latest_remote_folder_name = os.path.basename(latest_remote_folder_path)

        print(f"Carpeta más reciente en el servidor remoto: {latest_remote_folder_path}")

        # Obtener año y mes actual
        now = datetime.datetime.now()
        year = str(now.year)
        month = str(now.month).zfill(2)  # Zfill para asegurarnos de que siempre tenga 2 dígitos

        # Crear la estructura de carpetas en la ruta local si no existen
        local_year_folder_path = os.path.join(local_directory, year)
        local_month_folder_path = os.path.join(local_year_folder_path, month)

        if not os.path.exists(local_year_folder_path):
            os.makedirs(local_year_folder_path)
            print(f"Carpeta del año creada: {local_year_folder_path}")

        if not os.path.exists(local_month_folder_path):
            os.makedirs(local_month_folder_path)
            print(f"Carpeta del mes creada: {local_month_folder_path}")

        # Obtener lista de archivos en la carpeta más reciente
        file_list = sftp.listdir(latest_remote_folder_path)

        if file_list:
            # Archivo más reciente en la carpeta más reciente
            latest_remote_file = file_list[0]
            print(f"Archivo más reciente en la carpeta: {latest_remote_file}")

            # Corregir la diagonal invertida después de la carpeta
            latest_remote_folder_path = latest_remote_folder_path.rstrip('\\')  # Eliminar la diagonal invertida al final

            # Unir latest_remote_folder_path y latest_remote_file para formar la ruta completa del archivo remoto
            if latest_remote_folder_path.endswith('/'):
                remote_filepath = latest_remote_folder_path + latest_remote_file  # Unir con una barra diagonal normal
            else:
                remote_filepath = latest_remote_folder_path + '/' + latest_remote_file  # Agregar una barra diagonal normal

            # Obtener la fecha de creación del archivo más reciente
            latest_file_creation_time = datetime.datetime.fromtimestamp(sftp.stat(remote_filepath).st_mtime)

            # Formatear la fecha de creación en el formato deseado
            formatted_creation_date = latest_file_creation_time.strftime("%Y-%m-%d")

            # Descargar el archivo
            local_filepath = os.path.join(local_month_folder_path, latest_remote_file)
            sftp.get(remote_filepath, local_filepath)
            print(f"Archivo descargado: {latest_remote_file}")

            # Enviar correo electrónico de éxito con la fecha de creación en el asunto
            success_subject = f'Copia de seguridad realizada correctamente ({formatted_creation_date})'
            success_body = f'La copia de seguridad de fecha ({formatted_creation_date}) se realizó correctamente.'
            send_email(success_subject, success_body, ['correo1', 'correo2'])

        else:
            print("No se encontraron archivos en la carpeta más reciente.")

            # Enviar correo electrónico de error
            error_subject = 'Error al realizar la copia de seguridad'
            error_body = 'No se encontraron archivos en la carpeta más reciente.'
            send_email(error_subject, error_body, ['correo1', 'correo2'])

    else:
        print("No se encontraron carpetas en la ruta remota.")

        # Enviar correo electrónico de error
        error_subject = 'Error al realizar la copia de seguridad'
        error_body = 'No se encontraron carpetas en la ruta remota.'
        send_email(error_subject, error_body, ['correo1', 'correo2'])

except OSError as e:
    print(f"Error: {e}")

    # Enviar correo electrónico de error
    error_subject = 'Error al realizar la copia de seguridad'
    error_body = f'Hubo un error al realizar la copia de seguridad del dia ({formatted_creation_date}) \n\n{str(e)}'
    send_email(error_subject, error_body, ['correo1', 'correo2'])

finally:
    # Cierra la conexión SFTP y SSH
    if sftp:
        sftp.close()
    if transport:
        transport.close()





















