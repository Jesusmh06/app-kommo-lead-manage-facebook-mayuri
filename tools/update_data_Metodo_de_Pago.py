"""
Tool para actualizar el campo "Método de Pago" en un lead de Kommo.
Usa el endpoint PATCH /api/v4/leads/{id}
Docs: https://developers.kommo.com/reference/updating-single-lead
"""

import os
import requests

def update_data_Metodo_de_Pago(lead_id: int, metodo: str) -> bool:
    """
    Actualiza el campo "Método de Pago" del lead.

    Args:
        lead_id: ID del lead.
        metodo: Método de pago indicado por el cliente.

    Returns:
        True si se actualizó correctamente, False en caso de error.
    """
    subdomain = os.getenv("KOMMO_SUBDOMAIN")
    access_token = os.getenv("KOMMO_ACCESS_TOKEN")
    pipeline_id = int(os.getenv("KOMMO_PIPELINE_ID"))
    metodo_pago_custom_field = int(os.getenv("KOMMO_METODO_PAGO_FIELD_ID"))

    url = f"https://{subdomain}.kommo.com/api/v4/leads/{lead_id}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "pipeline_id": pipeline_id,
        "custom_fields_values": [
            {
                "field_id": metodo_pago_custom_field,
                "values": [{"value": metodo}]
            }
        ]
    }

    response = requests.patch(url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"💳 Lead {lead_id}: Método de Pago actualizado a '{metodo}'")
        return True
    else:
        print(f"❌ Error actualizando Método de Pago: {response.status_code}")
        print(f"   Detalle: {response.text}")
        return False
