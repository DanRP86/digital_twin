from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Este enrutador atrapa CUALQUIER petición que Vercel le mande a este archivo
@app.route('/', defaults={'path': ''}, methods=['POST', 'GET'])
@app.route('/<path:path>', methods=['POST', 'GET'])
def chat_api(path):
    # TRUCO DE DIAGNÓSTICO: Si entras desde el navegador (GET), verás este mensaje
    if request.method == 'GET':
        return jsonify({"status": "ok", "message": "¡El cerebro de Python está vivo y conectado!"})
        
    # Si es el chat (POST), ejecutamos la IA
    try:
        data = request.json
        user_message = data.get('message')
        history = data.get('history', [])
        
        # Leemos el summary.txt asumiendo que están en la misma carpeta "api"
        current_dir = os.path.dirname(__file__)
        summary_path = os.path.join(current_dir, 'summary.txt')
        
        with open(summary_path, 'r', encoding='utf-8') as f:
            knowledge = f.read()
            
        system_prompt = f"""
        Eres el gemelo digital interactivo de Daniel Rubio Paniagua.
        Debes actuar y responder como él. Aquí tienes toda su información:
        {knowledge}
        Nunca digas que eres una IA de OpenAI, di que eres el clon digital de Daniel.
        """
        
        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_message}]
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        reply = response.choices[0].message.content
        return jsonify({"reply": reply})
        
    except Exception as e:
        # Si algo falla dentro de Python, ahora sí nos lo devolverá a la pantalla
        return jsonify({"reply": f"Error interno: {str(e)}"}), 500
