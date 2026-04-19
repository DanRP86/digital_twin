from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

# Vercel leerá la API Key de sus variables de entorno de forma segura
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    history = data.get('history', [])
    
    # 1. Leer el archivo con tu cuestionario prealimentado
    # En Vercel, hay que usar rutas absolutas basadas en el directorio actual
    base_dir = os.path.dirname(os.path.dirname(__file__))
    summary_path = os.path.join(base_dir, 'data', 'summary.txt')
    
    with open(summary_path, 'r', encoding='utf-8') as f:
        knowledge = f.read()
        
    # 2. Construir las instrucciones de la IA
    system_prompt = f"""
    Eres el gemelo digital interactivo de Daniel Rubio Paniagua.
    Debes actuar y responder como él. Aquí tienes toda su información 
    y un cuestionario de cómo responder a ciertas preguntas:
    
    {knowledge}
    
    Nunca digas que eres una IA de OpenAI, di que eres el clon digital de Daniel.
    """
    
    # 3. Montar la conversación
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_message}]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        reply = response.choices[0].message.content
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": "Vaya, ha habido un cruce de cables en mi sistema virtual. ¿Puedes repetirlo?"}), 500