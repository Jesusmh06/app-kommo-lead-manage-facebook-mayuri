# Para generar el entorno virtual
conda create --name LlamaIndex-proj-Kommo python=3.11

# Para activar el entorno virtual
conda activate LlamaIndex-proj-Kommo

# Instalar dependencias
pip install -r requirements.txt

# Con este levantamos el endpoint
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Comando para el forwarding (Para testeo local)
ngrok http 8000

# Dockerfile:
docker login
docker buildx build --platform linux/amd64 -t jemayuh157/app-kommo-lead-manage-facebook-mayuri:latest --push .

