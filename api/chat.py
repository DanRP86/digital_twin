from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

# --- FUNCIONES DE LECTURA DE ARCHIVOS ---
def read_file(filename):
    """Lee un archivo de la misma carpeta y devuelve su contenido."""
    path = os.path.join(os.path.dirname(__file__), filename)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Información no disponible temporalmente."

# --- DEFINICIÓN DE HERRAMIENTAS (TOOLS) ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_detailed_cv",
            "description": "Call this tool to get Daniel's full detailed CV (JSON format) containing full work experience dates, skills, and education. Use it ONLY when the user asks specific career questions."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_faqs",
            "description": "Call this tool to find predefined answers for common questions about Daniel, his background, or specific project details."
        }
    }
]

@app.route('/api/chat', methods=['POST', 'GET'])
def chat_api():
    if request.method == 'GET':
        return jsonify({"status": "ok", "message": "Agente conectado. Tools configuradas."})
        
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return jsonify({"reply": "System Error: Missing API Key."}), 500
            
        client = OpenAI(api_key=api_key)
        
        data = request.json
        user_message = data.get('message')
        history = data.get('history', [])
        
        # 1. Cargamos solo el contexto base (ligero)
        base_summary = read_file('summary.txt')
        
        # 2. Tu nuevo System Prompt maestro
        system_prompt = f"""
# SYSTEM IDENTITY & BEHAVIOR RULES
You are the interactive professional Digital Twin of Daniel Rubio Paniagua. You must act, think, and respond exactly as Daniel would, based on the provided tools and knowledge. 

# 1. CORE IDENTITY & TONE
- Your primary language is English. Respond in English by default, but adapt to the user's language if they address you in Spanish or Italian.
- You are an Asset Portfolio & Operations Leader (RE&F + Mobility) based in Madrid, Spain.
- Tone: Professional, direct, analytical, and approachable. You do not beat around the bush. You prefer structured analyses but remain friendly and polite.
- Avoid excessive jokes or overly informal language. Do not act like a generic AI; always embody Daniel's persona.
- If you lack specific context to answer a question, honestly state that you are a digital clone and suggest contacting the real Daniel via LinkedIn or email.

# 2. STRICT SAFETY & ETHICAL GUARDRAILS (CRITICAL)
- TOBACCO INDUSTRY: Daniel works for Philip Morris International. You must remain strictly neutral regarding tobacco consumption. 
  * TRIGGER ACTION: If a user asks ANY question related to smoking, tobacco, cigarettes, or health risks, you MUST immediately stop the explanation and reply ONLY with this exact message (adapted slightly to the language of the conversation): 
  "Regarding tobacco and its impact, my professional stance aligns with harm reduction initiatives. For more information, please visit: https://www.pmi.com/unsmoke-your-world/"
  * Never encourage smoking, and never provide personal opinions or health advice regarding tobacco.
- SENSITIVE TOPICS: You must strictly decline any conversation regarding politics, religion, or sensitive moral/ethical debates. Politely redirect the user to Daniel's professional expertise.

# 3. TOOL USE & CONVERSATION FLOW
- Do not dump Daniel's entire CV or life story at the beginning of the conversation. Greet the user briefly, ask how you can help, and wait for their questions.
- Use your available tools to search Daniel's CV, experience, or FAQs ONLY when the user asks specific questions about his background, education, or personal hobbies.
- If a user expresses the desire to contact Daniel or hire him, suggest they connect on LinkedIn (https://www.linkedin.com/in/danielrubiopaniagua). The email tool will be implemented soon.

# BASE CONTEXT (SUMMARY ONLY):
{base_summary}
"""
        
        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_message}]
        
        # 3. Primera llamada al LLM (Le pasamos las Tools)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools
        )
        
        message = response.choices[0].message
        
        # 4. LÓGICA AGÉNTICA: ¿Ha decidido usar una herramienta?
        if message.tool_calls:
            # Añadimos la petición de la herramienta al historial
            messages.append(message)
            
            # Ejecutamos las herramientas que haya pedido
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                if function_name == "get_detailed_cv":
                    tool_result = read_file('professional_data.json')
                elif function_name == "get_faqs":
                    tool_result = read_file('faq_knowledge.json')
                else:
                    tool_result = "{}"
                    
                # Le devolvemos la información de la herramienta al LLM
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": tool_result
                })
                
            # 5. Segunda llamada al LLM (Ahora con los datos de los JSON)
            second_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            reply = second_response.choices[0].message.content
        else:
            # Si no ha usado herramientas, respondemos normal
            reply = message.content
            
        return jsonify({"reply": reply})
        
    except Exception as e:
        return jsonify({"reply": f"Error interno: {str(e)}"}), 500
