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
    if "hola" in texto:
            data={
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": number,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": "🚀 Hola, ¿Cómo estás? Bienvenido."
                }
            }
    elif "1" in texto:
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": number,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": "El Movimiento de Liberación Nacional (MLN) encarna la continuidad histórica en el siglo XXI del Modelo Argentino de Desarrollo. Nuestras bases son sólidas, perdurables, y se encuentran en el corazón de cada argentino. Somos los hombres y mujeres de San Martín, Rosas, Yrigoyen y Perón. Somos el pueblo que durante más de 200 años, pugnó por la Liberación Nacional por medio del poder determinante del trabajo y la fuerza de la comunidad organizada. Así José de San Martín construyó las fábricas militares como brazo industrial de la gesta libertadora. De esa manera, Juan Manuel de Rosas nacionalizó la banca y el comercio exterior poniendo límites a los imperialismos europeos. Bajo el mismo modelo Hipólito Yrigoyen creó la primera petrolera estatal del planeta tierra, YPF."
                }
            }
    elif "2" in texto:
            data = {
                "messaging_product": "whatsapp",
                "to": number,
                "type": "location",
                "location": {
                    "latitude": "-12.067158831865067",
                    "longitude": "-77.03377940839486",
                    "name": "Estadio Nacional del Perú",
                    "address": "Cercado de Lima"
                }
            }
    elif "3" in texto:
            data={
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": number,
                "type": "document",
                "document": {
                        "link": "https://www.turnerlibros.com/wp-content/uploads/2021/02/ejemplo.pdf",
                        "caption": "Temario del Curso #001"
                    }
                }
    elif "4" in texto:
            data={
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": number,
                "type": "audio",
                "audio": {
                    "link": "https://filesamples.com/samples/audio/mp3/sample1.mp3"
                }
            }
    elif "5" in texto:
            data = {
                "messaging_product": "whatsapp",
                "to": number,
                "text": {
                    "preview_url": True,
                    "body": "Introduccion al curso! https://youtu.be/6ULOE2tGlBM"
                }
            }
    elif "6" in texto:
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": number,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": "🤝 En breve me pondre en contacto contigo. 🤓"
                }
            }
    elif "7" in texto:
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": number,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": "📅 Horario de Atención : Lunes a Viernes. \n🕜 Horario : 9:00 am a 5:00 pm 🤓"
                }
            }
    elif "0" in texto:
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": number,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": "🚀 Hola, visita mi web https://mln.ar/ para más información.\n \n📌Por favor, ingresa un número #️⃣ para recibir información.\n \n1️⃣. Información del Proyecto. ❔\n2️⃣. Ubicación del local. 📍\n3️⃣. Enviar temario en PDF. 📄\n4️⃣. Audio explicando curso. 🎧\n5️⃣. Video de Introducción. ⏯️\n6️⃣. Hablar con AnderCode. 🙋‍♂️\n7️⃣. Horario de Atención. 🕜 \n0️⃣. Regresar al Menú. 🕜"
                }
            }
    elif "boton" in texto:
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": number,
                "type": "interactive",
                "interactive":{
                    "type":"button",
                    "body": {
                        "text": "¿Confirmas tu registro?"
                    },
                    "footer": {
                        "text": "Selecciona una de las opciones"
                    },
                    "action": {
                        "buttons":[
                            {
                                "type": "reply",
                                "reply":{
                                    "id":"btnsi",
                                    "title":"Si"
                                }
                            },{
                                "type": "reply",
                                "reply":{
                                    "id":"btnno",
                                    "title":"No"
                                }
                            },{
                                "type": "reply",
                                "reply":{
                                    "id":"btntalvez",
                                    "title":"Tal Vez"
                                }
                            }
                        ]
                    }
                }
            }
    elif "btnsi" in texto:
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": number,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": "Muchas Gracias por Aceptar."
                }
            }
    elif "btnno" in texto:
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": number,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": "Es una Lastima."
                }
            }
    elif "btntalvez" in texto:
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": number,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": "Estare a la espera."
                }
            }
    elif "lista" in texto:
            data ={
                "messaging_product": "whatsapp",
                "to": number,
                "type": "interactive",
                "interactive":{
                    "type" : "list",
                    "body": {
                        "text": "Selecciona Alguna Opción"
                    },
                    "footer": {
                        "text": "Selecciona una de las opciones para poder ayudarte"
                    },
                    "action":{
                        "button":"Ver Opciones",
                        "sections":[
                            {
                                "title":"Compra y Venta",
                                "rows":[
                                    {
                                        "id":"btncompra",
                                        "title" : "Comprar",
                                        "description": "Compra los mejores articulos de tecnologia"
                                    },
                                    {
                                        "id":"btnvender",
                                        "title" : "Vender",
                                        "description": "Vende lo que ya no estes usando"
                                    }
                                ]
                            },{
                                "title":"Distribución y Entrega",
                                "rows":[
                                    {
                                        "id":"btndireccion",
                                        "title" : "Local",
                                        "description": "Puedes visitar nuestro local."
                                    },
                                    {
                                        "id":"btnentrega",
                                        "title" : "Entrega",
                                        "description": "La entrega se realiza todos los dias."
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
    elif "btncompra" in texto:
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": number,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": "Los mejos articulos top en ofertas."
                }
            }
    elif "btnvender" in texto:
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": number,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": "Excelente elección."
                }
            }
    else:
            data={
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": number,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": "🚀 Hola, visita mi web anderson-bastidas.com para más información.\n \n📌Por favor, ingresa un número #️⃣ para recibir información.\n \n1️⃣. Información del Curso. ❔\n2️⃣. Ubicación del local. 📍\n3️⃣. Enviar temario en PDF. 📄\n4️⃣. Audio explicando curso. 🎧\n5️⃣. Video de Introducción. ⏯️\n6️⃣. Hablar con AnderCode. 🙋‍♂️\n7️⃣. Horario de Atención. 🕜 \n0️⃣. Regresar al Menú. 🕜"
                }
        }
    
    # Registro de depuración con el remitente (número)
    agregar_mensajes_log(f"Enviado: {data['text']['body']}", data, number)

    #Convertir el diccionaria a formato JSON
    data=json.dumps(data)
    
    headers = {
        "Content-Type" : "application/json",
        "Authorization" : "Bearer EAAYhSwsIKiQBOwVE1mViKlQYCRWqwl2oMvda0Pp0aqZAoDxHIatDIX0unn4mDhV7MuKGusJfRBjDCm1uuvcbXZCy2ZCBzZBf2m74ueSaZB5YZCc54c4cC0Midd6FDH1q8WSsj1cLZC2rGBFvuxLZCw5ZCqwTn0Jpk8ZBV20hDAesPuvzOWLivy3JAxvNqMam3T7TFjAx1GgmsogqpHFkMMh8EZD"
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