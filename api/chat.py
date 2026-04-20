from flask import Flask, request, jsonify
from openai import OpenAI
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# --- FUNCIONES DE LECTURA DE ARCHIVOS ---
def read_file(filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Información no disponible temporalmente."

# --- FUNCIÓN DE ENVÍO DE EMAIL (LA NOVEDAD) ---
def send_contact_email(name, surname, user_email, message_to_daniel):
    # Estas variables las pondremos en Vercel por seguridad
    my_email = os.environ.get("GMAIL_ADDRESS")
    password = os.environ.get("GMAIL_APP_PASSWORD")

    if not my_email or not password:
        return "Error interno: Credenciales de email no configuradas."

    try:
        # 1. Email para ti (El aviso)
        msg_daniel = MIMEMultipart()
        msg_daniel['From'] = my_email
        msg_daniel['To'] = my_email
        msg_daniel['Subject'] = f"Digital Twin Contacto: {name} {surname}"
        
        body_daniel = f"Tu Gemelo Digital ha captado un lead:\n\nNombre: {name} {surname}\nEmail: {user_email}\n\nMensaje:\n{message_to_daniel}"
        msg_daniel.attach(MIMEText(body_daniel, 'plain'))

        # 2. Email para el Usuario (Acuse de recibo)
        msg_user = MIMEMultipart()
        msg_user['From'] = my_email
        msg_user['To'] = user_email
        msg_user['Subject'] = "Acuse de recibo - Daniel Rubio Paniagua"
        
        body_user = f"Hello {name},\n\nI am Daniel Rubio's digital twin. This is an automated message to confirm that I have received your request:\n\n\"{message_to_daniel}\"\n\nI have securely forwarded your information to Daniel, and he will get back to you at this email address ({user_email}) as soon as possible.\n\nBest regards,\nDaniel's Digital Twin"
        msg_user.attach(MIMEText(body_user, 'plain'))

        # 3. Conexión con Gmail y envío
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(my_email, password)
        server.send_message(msg_daniel)
        server.send_message(msg_user)
        server.quit()

        return "SUCCESS: Emails enviados correctamente. Dile al usuario que revise su bandeja de entrada."
    except Exception as e:
        return f"FAILED: Error enviando los emails. Motivo: {str(e)}"

# --- DEFINICIÓN DE HERRAMIENTAS (TOOLS) ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_detailed_cv",
            "description": "Call this tool to get Daniel's full detailed CV (JSON format). Use it ONLY when the user asks specific career questions."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_faqs",
            "description": "Call this tool if the user asks about specific technologies (like n8n, Microsoft, AI agents), personal projects, or any 'What are you doing/studying' type of questions."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_contact_email",
            "description": "Call this tool ONLY when the user explicitly wants to leave a message, contact Daniel, or hire him, AND you have already collected their Name, Surname, Email, and Message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The user's first name."},
                    "surname": {"type": "string", "description": "The user's last name."},
                    "user_email": {"type": "string", "description": "The user's email address."},
                    "message_to_daniel": {"type": "string", "description": "The message the user wants to send to Daniel."}
                },
                "required": ["name", "surname", "user_email", "message_to_daniel"],
                "additionalProperties": False
            }
        }
    }
]

@app.route('/api/chat', methods=['POST', 'GET'])
def chat_api():
    if request.method == 'GET':
        return jsonify({"status": "ok", "message": "Agente conectado con función de Email activa."})
        
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return jsonify({"reply": "System Error: Missing API Key."}), 500
            
        client = OpenAI(api_key=api_key)
        data = request.json
        user_message = data.get('message')
        history = data.get('history', [])
        
        base_summary = read_file('summary.txt')
        
        # --- PROMPT MEJORADO CON REGLAS DE EMAIL ---
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
- If the user mentions specific software or tools (e.g., n8n, Microsoft Copilot, etc.), ALWAYS check the get_faqs or get_detailed_cv tools before providing a generic answer. Daniel's personal experience with these tools is more important than general definitions.
- CONTACT PROCEDURE (CRITICAL): If a user expresses the desire to contact Daniel or hire him, suggest they connect on LinkedIn (https://www.linkedin.com/in/danielrubiopaniagua) OR offer to send him a direct message right now through this chat.
  * If they choose to send a message here, ask them conversationally for their First Name, Last Name, Email address, and the specific message they want to send. 
  * DO NOT call the 'send_contact_email' tool until you have collected ALL 4 pieces of information.
  * Once the tool returns SUCCESS, inform the user that an acknowledgment receipt has been sent to their email.

# BASE CONTEXT (SUMMARY ONLY):
{base_summary}
"""
        
        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_message}]
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools
        )
        
        message = response.choices[0].message
        
        if message.tool_calls:
            messages.append(message)
            
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                arguments = eval(tool_call.function.arguments) # Convertimos el JSON string a diccionario de Python
                
                if function_name == "get_detailed_cv":
                    tool_result = read_file('professional_data.json')
                elif function_name == "get_faqs":
                    tool_result = read_file('faq_knowledge.json')
                elif function_name == "send_contact_email":
                    tool_result = send_contact_email(
                        arguments.get('name'), 
                        arguments.get('surname'), 
                        arguments.get('user_email'), 
                        arguments.get('message_to_daniel')
                    )
                else:
                    tool_result = "{}"
                    
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": tool_result
                })
                
            second_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            reply = second_response.choices[0].message.content
        else:
            reply = message.content
            
        return jsonify({"reply": reply})
        
    except Exception as e:
        return jsonify({"reply": f"Error interno: {str(e)}"}), 500
