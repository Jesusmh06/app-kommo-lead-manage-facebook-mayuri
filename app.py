import os
import sys
import time
from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks

sys.path.append(os.path.join(os.path.dirname(__file__), "Kommo Functions"))
from kommo import parse_kommo_webhook, update_lead_with_response, launch_salesbot, get_switch_status

sys.path.append(os.path.join(os.path.dirname(__file__), "tools"))
from tools.move_lead_to_Toma_de_Decision import move_lead_to_Toma_de_Decision
from tools.move_lead_to_Discusion_de_Contrato import move_lead_to_Discusion_de_Contrato
from tools.move_lead_to_Cerrar_Venta import move_lead_to_Cerrar_Venta
from tools.update_data_Marca_de_Interes import update_data_Marca_de_Interes
from tools.update_data_Metodo_de_Pago import update_data_Metodo_de_Pago
from tools.update_data_Nombre_de_cliente import update_data_Nombre_Cliente
from tools.update_data_Telefono_de_cliente import update_data_Telefono_Cliente
from tools.update_data_Correo_de_cliente import update_data_Correo_Cliente
from tools.update_data_Direccion_de_cliente import update_data_Direccion_Cliente
from tools.send_notification_by_email import send_email

from conversation_history import init_chat_store, save_message, format_history_for_prompt
from agent import init_agent, ask_agent, parse_and_clean_tags

load_dotenv()

# Deduplicación: evita procesar el mismo mensaje si Kommo reenvía el webhook
processed_messages: dict[str, float] = {}
DEDUP_WINDOW_SECONDS = 300  # 5 minutos

print("💾 Inicializando historial de conversación (PostgreSQL/Supabase)...")
init_chat_store()

llm, retrieval_tool = init_agent()

app = FastAPI(title="Kommo AI Chatbot")


def is_duplicate(lead_id: str, text: str) -> bool:
    """Verifica si este mensaje ya fue procesado recientemente (deduplicación)."""
    now = time.time()

    expired = [k for k, v in processed_messages.items() if now - v > DEDUP_WINDOW_SECONDS]
    for k in expired:
        del processed_messages[k]

    key = f"{lead_id}:{text}"
    if key in processed_messages:
        return True

    processed_messages[key] = now
    return False


async def process_message(message_text: str, lead_id: str):
    """Procesa el mensaje en segundo plano: genera respuesta con el agente, actualiza lead, lanza salesbot."""
    try:
        # 1. Guardar mensaje del usuario en el historial
        save_message(lead_id, "user", message_text)

        # 2. Obtener historial y consultar al agente
        history_str = format_history_for_prompt(lead_id)
        response_text = await ask_agent(llm, retrieval_tool, message_text, history_str)

        # 3. Parsear tags y limpiar respuesta
        tags = parse_and_clean_tags(response_text)
        clean_response = tags["clean_response"]

        print(f"🤖 Respuesta: {clean_response[:80]}...")

        # 4. Guardar respuesta del asistente en el historial
        save_message(lead_id, "assistant", clean_response)

        # 5. Ejecutar acciones según tags detectados
        if tags["is_contract"]:
            print(f"📝 DISCUSIÓN DE CONTRATO detectada para lead {lead_id}")
            move_lead_to_Discusion_de_Contrato(int(lead_id))
        elif tags["is_interested"]:
            print(f"🎯 INTERÉS DE COMPRA detectado para lead {lead_id}")
            move_lead_to_Toma_de_Decision(int(lead_id))
        elif tags["is_sold"]:
            print(f"💰 CIERRE DE VENTA detectado para lead {lead_id}")
            move_lead_to_Cerrar_Venta(int(lead_id))
            # Enviar email de confirmación si hay correo
            recipient_email = tags.get("correo")
            if recipient_email:
                subject = f"Confirmación de pedido #{lead_id}"
                datos_cliente = [
                    int(lead_id),
                    tags.get("nombre", ""),
                    tags.get("marca", ""),
                    tags.get("telefono", ""),
                    tags.get("direccion", "")
                ]
                result = send_email(recipient_email, subject, datos_cliente)
                print(f"📧 {result}")
            else:
                print(f"⚠️ No se puede enviar email: correo no proporcionado para lead {lead_id}")

        if tags["marca"]:
            update_data_Marca_de_Interes(int(lead_id), tags["marca"])

        if tags["pago"]:
            update_data_Metodo_de_Pago(int(lead_id), tags["pago"])

        if tags["nombre"]:
            update_data_Nombre_Cliente(int(lead_id), tags["nombre"])

        if tags["telefono"]:
            update_data_Telefono_Cliente(int(lead_id), tags["telefono"])

        if tags["correo"]:
            update_data_Correo_Cliente(int(lead_id), tags["correo"])

        if tags["direccion"]:
            update_data_Direccion_Cliente(int(lead_id), tags["direccion"])

        # 6. Actualizar lead en Kommo y lanzar salesbot
        update_lead_with_response(lead_id, clean_response)
        print(f"✅ Lead {lead_id} actualizado: respuesta guardada + switch activado")

        launch_salesbot(lead_id)

    except Exception as e:
        print(f"❌ Error procesando mensaje: {str(e)}")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Kommo AI Chatbot activo"}


@app.post("/webhook/kommo")
async def kommo_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()

    data = parse_kommo_webhook(body)

    message_text = data.get("text", "")
    lead_id = data.get("lead_id")
    message_type = data.get("type", "")
    created_by = data.get("created_by")

    if message_type and message_type == "outgoing":
        return {"status": "ignored", "reason": "outgoing message"}

    if created_by and str(created_by) != "0":
        return {"status": "ignored", "reason": "system message"}

    if not message_text or not lead_id:
        return {"status": "ignored", "reason": "missing data"}

    if len(message_text.strip()) < 1:
        return {"status": "ignored", "reason": "empty message"}

    if is_duplicate(lead_id, message_text):
        print(f"⏭️ Webhook duplicado ignorado (lead {lead_id})")
        return {"status": "ignored", "reason": "duplicate webhook"}

    if not get_switch_status(lead_id):
        print(f"🔴 Switch IA DESACTIVADO para lead {lead_id}")
        return {"status": "ignored", "reason": "AI switch off"}

    print(f"📩 Webhook recibido de Kommo!")
    print(f"💬 Mensaje: '{message_text[:50]}...' | Lead ID: {lead_id}")

    background_tasks.add_task(process_message, message_text, lead_id)

    return {"status": "ok", "message": "processing"}

