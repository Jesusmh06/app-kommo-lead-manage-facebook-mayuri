  📊 Niveles del Embudo de Ventas en Kommo                                                                                                                
  El sistema está diseñado para manejar 4 etapas principales:                                                                                          
  
  1. 📥 Contacto Inicial (implícito)
    - Estado inicial del lead
    - No tiene movimiento automático
  2. 🎯 Toma de Decisión
    - Activa con la etiqueta [INTERESADO]
    - Cliente muestra intención clara de compra
    - Usa KOMMO_LEAD_INTERESADO_STATUS_ID
  3. 📝 Discusión de Contrato
    - Activa con la etiqueta [CONTRATO]
    - Cliente pregunta detalles de pago, envío, garantías
    - Usa KOMMO_LEAD_CALIFICADO_STATUS_ID
  4. 💰 Cerrar Venta
    - Activa con la etiqueta [VENDIDO]
    - Etapa final (pago confirmado), da datos de su nombre, telefono, correo y direccion
    - Usa KOMMO_LEAD_VENDIDO_STATUS_ID

  🔄 Traza de Manejo de Estados

  Flujo Automático:

  Mensaje Cliente → Agente IA → Parseo Etiquetas → Acciones Automáticas

  Proceso Detallado:

  1. Recepción Webhook (app.py)
    - Kommo envía mensaje del cliente
    - Validación de duplicados y switch IA
  2. Procesamiento IA (agent.py)
    - Agente "Andrea" responde usando knowledge_base
    - Genera respuesta con etiquetas según intención
  3. Parseo de Etiquetas (agent.py)
    - Extrae: is_interested, is_contract, marca, pago
    - Limpia respuesta para el cliente
  4. Acciones Automáticas (app.py)
  if tags["is_contract"]:
      move_lead_to_Discusion_de_Contrato()  # → Cambio de estado de lead Discusión de Contrato
  elif tags["is_interested"]:
      move_lead_to_Toma_de_Decision()       # → Cambio de estado de lead Toma de Decisión
  elif tags["is_sold"]:
      move_lead_to_Cerrar_Venta()           # → Cambio de estado de lead Cerrar Venta
      send_email()                          # → Enviar un correo de confirmacion de pedido

  if tags["marca"]:
      update_data_Marca_de_Interes()     # Actualiza campo personalizado
  if tags["pago"]:
      update_data_Metodo_de_Pago()       # Actualiza campo personalizado
  if tags["nombre"]:
      update_data_Nombre_Cliente()       # Actualiza campo personalizado
  if tags["telefono"]:
      update_data_Telefono_Cliente()     # Actualiza campo personalizado
  if tags["correo"]:
      update_data_Correo_Cliente()       # Actualiza campo personalizado
  if tags["direccion"]:
      update_data_Direccion_Cliente()    # Actualiza campo personalizado

  5. Actualización Final (app.py)
    - Guarda respuesta en historial
    - Actualiza lead en Kommo
    - Ejecuta launch_salesbot()

  🎯 Campos Personalizados Rastreados

  ┌──────────────────┬─────────────┬──────────────────┬────────────────────────────────────┐
  │      Campo       │  Etiqueta   │     Ejemplo      │             Archivo                │
  ├──────────────────┼─────────────┼──────────────────┼────────────────────────────────────┤
  │ Marca de Interés │ [MARCA:...] │ [MARCA:VitaCalm] │ update_data_Marca_de_Interes.py    │
  ├──────────────────┼─────────────┼──────────────────┼────────────────────────────────────┤
  │ Método de Pago   │ [PAGO:...]  │ [PAGO:tarjeta]   │ update_data_Metodo_de_Pago.py      │
  ├──────────────────┼─────────────┼──────────────────┼────────────────────────────────────┤
  │ Nombre           │ [NOMBRE:..] │ [NOMBRE:Jesus]   │ update_data_Nombre_de_cliente.py   │  
  ├──────────────────┼─────────────┼──────────────────┼────────────────────────────────────┤
  │ Telefono         │ [TELEFONO:.]│ [TELEFONO:9XXXX] │ update_data_Telefono_de_cliente.py │  
  ├──────────────────┼─────────────┼──────────────────┼────────────────────────────────────┤
  │ Correo           │ [CORREO:.]  │ [CORREO:@]       │ update_data_Correo_de_cliente.py   │  
  ├──────────────────┼─────────────┼──────────────────┼────────────────────────────────────┤
  │ Direccion        │[DIRECCION:.]│ [DIRECCION:Av..] │ update_data_Direccion_de_cliente.py│  
  ├──────────────────┼─────────────┼──────────────────┼────────────────────────────────────┤
