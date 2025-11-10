import smtplib
from email.mime.text import MIMEText

def enviar_notificacion(email, mensaje):
    # cuerpo del correo
    msg = MIMEText(mensaje)
    msg["Subject"] = "Confirmación de pedido"
    msg["From"] = "tienda@only.com"
    msg["To"] = email

    try:
        with smtplib.SMTP("localhost", 1025) as server:
            server.send_message(msg)
        print(f"✅ Notificación enviada a {email}")
        return True
    except Exception as e:
        print(f"❌ Error al enviar notificación: {e}")
        return False
