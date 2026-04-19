from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

@app.route('/api/chat', methods=['POST', 'GET'])
def chat_api():
    # 1. El test rápido desde el navegador
    if request.method == 'GET':
        return jsonify({"status": "ok", "message": "¡El cerebro de Python está conectado y funcionando al 100%!"})
        
    # 2. El chat real
    try:
        # Inicializamos OpenAI DENTRO de la función para evitar el "Crash" del servidor
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return jsonify({"reply": "Error: Vercel no está leyendo la API Key."}), 500
            
        client = OpenAI(api_key=api_key)
        
        data = request.json
        user_message = data.get('message')
        history = data.get('history', [])
        
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
        
    except FileNotFoundError:
        return jsonify({"reply": "Error: No encuentro el archivo summary.txt"}), 500
    except Exception as e:
        return jsonify({"reply": f"Error interno real: {str(e)}"}), 500
