from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import http.client
import json

app = Flask(__name__)

# Configuracion de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db =SQLAlchemy(app)

#Modelo de la tabla log
class Log(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    fecha_y_hora = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    remitente = db.Column(db.String)
    datajson = db.Column(db.TEXT)
    texto = db.Column(db.TEXT)
    
    #constructor de la clase Log
    def __init__(self, texto, datajson,remitente):
        self.texto = texto
        self.datajson = datajson
        self.remitente = remitente

#Crear la tabla si no existe
with app.app_context():
    db.create_all()

#Funcion para ordenar registros por fecha y hora
def ordenar_por_fecha_y_hora(registros):
    return sorted(registros, key=lambda x: x.fecha_y_hora, reverse=True)

@app.route('/')
def index():
    # Obtener todos los registros de la base de datos
    registros = Log.query.all()
    registros_ordenados = ordenar_por_fecha_y_hora(registros)
    return render_template('index.html',registros=registros_ordenados)

mensajes_log = []

#Función para agregar mensajes y guardar en la base de datos
def agregar_mensajes_log(texto, datajson, remitente):
    texto = str(texto)
    datajson = json.dumps(datajson) if isinstance(datajson, dict) else str(datajson)
    mensajes_log.append(texto)
    #Guardar el mensaje en la base de datos
    nuevo_registro = Log(texto=texto,datajson=datajson,remitente=remitente)
    db.session.add(nuevo_registro)
    db.session.commit()

#TOKEN DE VERIFICACION PARA LA CONFIGURACION
TOKEN_MPERRO = "MPERRO"

@app.route('/webhook', methods=['GET','POST'])

def webhook():
    if request.method== 'GET':
        challenge = verificar_token(request)
        return challenge
    elif request.method == 'POST':
        reponse = recibir_mensajes(request)
        return reponse

def verificar_token(req):
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')

    if challenge and token == TOKEN_MPERRO:
        return challenge
    else:
        return jsonify({'error':'token invalido'}),401
 
def limpiar_numero_telefono(numero):
    if numero.startswith("549") and len(numero) == 13:  # Si el número empieza con "549" y tiene 13 dígitos
        numero = "54" + numero[3:]  # Remover el dígito "9"
    return numero


def recibir_mensajes(req):
    try:
        req = request.get_json()
        # Obtener el remitente del mensaje
        entry = req.get('entry', [])[0]
        changes = entry.get('changes', [])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
        number = "N/A"  # Valor predeterminado en caso de que no se defina

        if messages:
            message = messages[0]
            numero = message['from']
            # Llama a la función para limpiar el número
            number = limpiar_numero_telefono(numero)

            tipo = message.get('type', '')
            text = "N/A"  # Valor predeterminado en caso de que no se defina


            if tipo == "text":
                text = message['text']['body']
                enviar_mensajes_whatsapp(text, number)

            elif tipo == "interactive":
                tipo_interactivo = message['interactive']['type']

                if tipo_interactivo == "button_reply":
                    text = message['interactive']['button_reply']['id']
                    enviar_mensajes_whatsapp(text, number)

                elif tipo_interactivo == "list_reply":
                    text = message['interactive']['list_reply']['id']
                    enviar_mensajes_whatsapp(text, number)
        
            agregar_mensajes_log(f"Recibido: {text}", datajson=str(req), remitente=number)
            
        return jsonify({'message': 'EVENT_RECEIVED'})

    except Exception as e:
        agregar_mensajes_log("N/A", "Error: " + str(e), number)
        return jsonify({'message': 'EVENT_RECEIVED'})

def enviar_mensajes_whatsapp(texto, number):
    texto = texto.lower()
    number = number
    data = None

    if "hola" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🇦🇷 Hola Argentin@. Bienvenido al chat del Movimiento de Liberación Nacional."
            }
        }
    elif "1" in texto.lower():
        # Obtener la respuesta del usuario (si es necesario)
        respuesta_usuario = input("Te puedo recomendar plataformas como Coursera, edX o Udemy. ¿En qué área te gustaría especializarte? (Ej: programación, diseño, marketing, datos, ciencias de la computación, desarrollo web, diseño gráfico, análisis de datos): ")

        # Diccionario de respuestas predefinidas
        respuestas = {
            "programación": "Genial, la programación es un campo muy amplio. ¿Te interesa más el desarrollo web (front-end, back-end), el desarrollo de aplicaciones móviles (iOS, Android), la programación de videojuegos o la ciencia de datos?",
            "diseño": "El diseño es un mundo creativo. ¿Te gustaría explorar el diseño gráfico, UX/UI, diseño de producto o animación?",
            "datos": "La ciencia de datos es un campo en auge. ¿Te interesa más el aprendizaje automático, el análisis de datos, la visualización de datos o la inteligencia artificial?",
            "default": "¡Interesante! ¿Puedes contarme un poco más sobre lo que te gustaría aprender? ¿Quizás te interesan las humanidades, las ciencias sociales, los negocios o alguna otra área?"
        }

        # Buscar la respuesta correspondiente en el diccionario
        respuesta = respuestas.get(respuesta_usuario.lower(), respuestas["default"])

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": respuesta
            }
        }   
    elif "2" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Actualmente podes acercarte a los grupos de compañeros que están trabajando en las siguientes zonas: General San Martin, Hurlingham, Morón, Merlo, Moreno, Luján, Mercedes, Florencio Varela y La Plata."
            }
        } 
    elif "3" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "document",
            "document": {
                "link": "https://mln.ar/descargas/1154-D-2023-IAPI-XXI.pdf",
                "caption": "IAPI XXI C.E."
            }
        }
    elif "4" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "document",
            "document": {
                "link": "https://mln.ar/descargas/0988-D-2023-ELMA.pdf",
                "caption": "ELMA XXI C.E."
            }
        }
    elif "5" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "document",
            "document": {
                "link": "https://mln.ar/descargas/0989-D-2023-REGIMEN-PARA-LA-ACTIVIDAD-DEL-TRANSPORTE-POR-AGUA.pdf",
                "caption": "Régimen para la actividad del transporte por Agua"
            }
        }
    elif "6" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "document",
            "document": {
                "link": "https://mln.ar/descargas/0987-D-2023-Fondo-para-el-Desarrollo-de-la-Industria-Naval-Nacional.pdf",
                "caption": "Fondo de Desarrollo de la Industria Naval"
            }
        }              
    else:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "¡Hola! Soy tu asistente virtual para la tecnología educativa. ¿En qué puedo ayudarte hoy?\n\nPregunta sobre: (elige un número)\n1️⃣ *Aprendizaje en línea:* Plataformas, cursos, recursos.\n2️⃣ *Herramientas digitales:* Para docentes y estudiantes.\n3️⃣ *Orientación vocacional:* Carreras tecnológicas y educativas.\n4️⃣ *Proyectos educativos:* Ideas y consejos.\n\n¡Estoy aquí para responder a tus dudas!"
                }
            }
    
    # Registro de depuración con el remitente (número)
    if 'text' in data and 'body' in data['text']:
        agregar_mensajes_log(f"Enviado: {data['text']['body']}", data, number)
    else:
        agregar_mensajes_log(f"Enviado: {data['type'].capitalize()}", data, number)

    #Convertir el diccionaria a formato JSON
    data=json.dumps(data)
    
    headers = {
        "Content-Type" : "application/json",
        "Authorization" : "Bearer EAAYhSwsIKiQBO57N4AWgZBbAKXcOc4S26D6SFZC2qbYxGBbLwASNC1LthzTfiKZBUX7RCPZBWZCwgF7PpIWKZBL5oHmpZA09jhM5cFtfXHfeDSqFZANogT1fBOHKB0P0fe8s2Op0wDfzzJ1njdoQQhdsVAd6ZBeGrHy0YtbDXR7ZATyotbG4ZC6hZAHEeMSdRuAVgiq3GSjI8QRsqfspnGKPg9aefjoXE3KP"
    }

    connection = http.client.HTTPSConnection("graph.facebook.com")

    try:
         connection.request("POST","/v20.0/368298853039307/messages", data, headers)
         response = connection.getresponse()
         agregar_mensajes_log("N/A", f"{response.status} - {response.reason}", number)
    except Exception as e:
             agregar_mensajes_log("N/A", f"Error: {str(e)}", number)  
    finally:
         connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80,debug=True)