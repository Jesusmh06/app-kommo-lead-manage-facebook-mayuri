"""
Tool de envío de email por SMTP (Gmail).
Usa APP_PASSWORD_GMAIL para autenticación.

Variables de entorno para la firma (opcionales, tienen valores por defecto):
    FIRMA_EMPRESA   → nombre de la empresa
    FIRMA_EMAIL     → email visible en la firma (por defecto usa EMAIL_REMITENTE)
"""

import os
import base64
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


# --- Constantes OAuth2 ---
TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


def _get_access_token() -> tuple[str, str]:
    """
    Obtiene un access token fresco usando el refresh token.
    Retorna (access_token, error_message). Si hay error, access_token es "".
    """
    client_id     = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        return "", "Error: Variables GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET o GMAIL_REFRESH_TOKEN no configuradas en .env"

    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type":    "refresh_token",
            "client_id":     client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        },
        timeout=10,
    )

    if response.status_code != 200:
        return "", f"Error obteniendo access token: {response.text}"

    return response.json().get("access_token", ""), ""


def _build_body(nro_lead: int, nombre: str, marca: str, telefono: str, direccion: str) -> str:

    fecha = datetime.now().strftime("%d-%m-%Y")

    """Construye el body del correo"""
    return (
        "\n\n¡Pedido generado con exito!\n\n"
        f"Estimado(a):{nombre}\n"
        f"Lead: #{nro_lead}\n"
        f"Fecha: {fecha}\n"
        f"Agradecemos su confianza, su orden de {marca} se genero para entrega en {direccion}\n"
        f"Numero de contacto registrado: {telefono}, nos comunicaremos para el recojo, se le avisara el dia de la entrega por el numero registrado en la orden de compra\n"
    )

def _build_signature() -> str:
    """Construye la firma del correo desde variables de entorno con valores por defecto."""
    empresa  = os.getenv("FIRMA_EMPRESA",  "Nombre de tu Empresa")
    email    = os.getenv("FIRMA_EMAIL",    os.getenv("EMAIL_REMITENTE", "Tu Email"))

    return (
        "\n\nAtentamente.\n\n"
        f"{empresa}\n"
        f"{email}"
    )

def _build_raw_message(sender: str, recipient: str, subject: str, body: str) -> str:
    """Construye el mensaje MIME y lo codifica en base64 para la Gmail API."""
    msg = MIMEMultipart()
    msg["From"]    = sender
    msg["To"]      = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    return raw


def send_email(recipient_email: str, subject: str, datos_cliente: list) -> str:
    """Envía un email via Gmail API al destinatario indicado.

    Args:
        recipient_email: Dirección de correo del destinatario.
        subject: Asunto del email.
        body: Cuerpo del email en texto plano (sin firma, se añade automáticamente).
    """
    sender_email = os.getenv("EMAIL_REMITENTE")
    if not sender_email:
        return "Error: Variable EMAIL_REMITENTE no configurada en .env"

    # 1. Obtener access token fresco
    access_token, error = _get_access_token()
    if error:
        return error

    # 2. Construir mensaje
    body = _build_body(datos_cliente[0], datos_cliente[1], datos_cliente[2], datos_cliente[3], datos_cliente[4])
    full_body = body + _build_signature()
    raw_message = _build_raw_message(sender_email, recipient_email, subject, full_body)

    # 3. Enviar via Gmail API
    try:
        response = requests.post(
            GMAIL_SEND_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type":  "application/json",
            },
            json={"raw": raw_message},
            timeout=15,
        )

        if response.status_code == 200:
            return f"Email enviado exitosamente a {recipient_email}"
        else:
            return f"Error Gmail API {response.status_code}: {response.text}"

    except requests.exceptions.Timeout:
        return "Error: Timeout al conectar con Gmail API"
    except Exception as e:
        return f"Error al enviar email: {str(e)}"

