"""
Tool para actualizar el campo "Numero de contacto usuario" en un lead de Kommo.
Usa el endpoint PATCH /api/v4/leads/{id}
Docs: https://developers.kommo.com/reference/updating-single-lead
"""

import os
import requests

def update_data_Telefono_Cliente(lead_id: int, telefono: str) -> bool:
    """
    Actualiza el campo "Nombre del usuario" del lead.

    Args:
        lead_id: ID del lead.
        telefono: Telefono del usuario indicado por el cliente.

    Returns:
        True si se actualizó correctamente, False en caso de error.
    """
    subdomain = os.getenv("KOMMO_SUBDOMAIN")
    access_token = os.getenv("KOMMO_ACCESS_TOKEN")
    pipeline_id = int(os.getenv("KOMMO_PIPELINE_ID"))
    telefono_custom_field = int(os.getenv("KOMMO_TELEFONO_FIELD_ID"))

    url = f"https://{subdomain}.kommo.com/api/v4/leads/{lead_id}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "pipeline_id": pipeline_id,
        "custom_fields_values": [
            {
                "field_id": telefono_custom_field,
                "values": [{ "value": telefono }]
            }
        ]
    }

    response = requests.patch(url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"💳 Lead {lead_id}: Valor de telefono del usuario actualizado a {telefono}")
        return True
    else:
        print(f"❌ Error actualizando datos de contrato y entrega de cliente: {response.status_code}")
        print(f"   Detalle: {response.text}")
        return False