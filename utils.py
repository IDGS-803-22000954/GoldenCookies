import os
from flask import flash, session
import pyotp
from models import db
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

Secret_key = pyotp.random_base32()

def generar_codigo_2fa(user):
    """Genera un código 2FA, lo guarda en la base de datos y envía el correo."""
    totp = pyotp.TOTP(Secret_key)
    codigo_2fa = totp.now()
    
    user.codigo_2fa = codigo_2fa
    db.session.commit()

    if enviar_correo(user.email, codigo_2fa):
        flash('Código de autenticación enviado por correo.', 'info')
    else:
        flash('Error al enviar el código.', 'danger')
    
    session["codigo_2fa"] = user.codigo_2fa


def enviar_correo(destinatario, codigo_2fa):
    """Función para enviar el código 2FA por correo electrónico usando Gmail API."""
    mensaje = f'Tu código de autenticación es: {codigo_2fa}'
    
    creds = None
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('Credentials.json', SCOPES)
            creds = flow.run_local_server(port=38699)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    msg = MIMEMultipart()
    msg['From'] = 'ian.aquinoflores@gmail.com'
    msg['To'] = destinatario
    msg['Subject'] = 'Código de Autenticación 2FA'
    msg.attach(MIMEText(mensaje, 'plain'))

    try:
        service = build('gmail', 'v1', credentials=creds)
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode().replace("=", "")
        message = {'raw': raw_message}
        service.users().messages().send(userId='me', body=message).execute()
        return True
    except Exception as e:
        print(f'Error al enviar el correo: {e}')
        return False
