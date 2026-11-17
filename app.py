import os
from flask import Flask, request
from openai import OpenAI
import requests

app = Flask(__name__)

# Variables de entorno que configurarás en Render
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "mi_token_secreto_2026")

# Cliente conectado a DeepSeek
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://deepseek.com")

@app.route("/", methods=["GET"])
def home():
    return "Bot de WhatsApp con DeepSeek activo.", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # 1. Verificación del Webhook por parte de Meta
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Token inválido", 403

    # 2. Recepción de mensajes entrantes
    data = request.get_json()
    try:
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            message = messages[0]
            # Solo procesar mensajes de texto
            if message.get("type") == "text":
                sender_id = message["from"]
                user_text = message["text"]["body"]

                # Consultar a DeepSeek
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "Eres un asistente virtual útil y conciso en WhatsApp."},
                        {"role": "user", "content": user_text}
                    ]
                )
                reply_text = response.choices[0].message.content

                # Enviar respuesta de vuelta a WhatsApp
                url = f"https://facebook.com{PHONE_NUMBER_ID}/messages"
                headers = {
                    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "to": sender_id,
                    "type": "text",
                    "text": {"body": reply_text}
                }
                requests.post(url, json=payload, headers=headers)

    except Exception as e:
        print("Error procesando el mensaje:", e)

    # Siempre responder 200 OK a Meta para evitar reenvíos infinitos
    return "EVENT_RECEIVED", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
