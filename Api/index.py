from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route('/api/chat', methods=['POST', 'GET'])
def chat_api():
    # El test del navegador
    if request.method == 'GET':
        return jsonify({"status": "ok", "message": "¡El cerebro de Python por fin ha despertado!"})
        
    try:
        data = request.json
        user_message = data.get('message')
        history = data.get('history', [])
        
        # Leer la chuleta
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
        return jsonify({"reply": f"Error interno real capturado: {str(e)}"}), 500
