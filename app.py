from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import http.client
import requests
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
    texto = db.Column(db.TEXT)
    
    #constructor de la clase Log
    def __init__(self, texto):
        self.texto = texto

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
def agregar_mensajes_log(texto):
    texto = str(texto)
    mensajes_log.append(texto)
    #Guardar el mensaje en la base de datos
    nuevo_registro = Log(texto=texto)
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
 
def recibir_mensajes(req):
    try:
        req = request.get_json()
        agregar_mensajes_log("Mensaje recibido: " + str(req))  # Registro de depuración
        entry = req['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        objeto_mensaje = value['messages']

        if objeto_mensaje:
            messages = objeto_mensaje[0]

            if "type" in messages:
                tipo = messages["type"]

                #Guardar Log en la BD
                agregar_mensajes_log(messages)

                if tipo == "interactive":
                    tipo_interactivo = messages["interactive"]["type"]

                    if tipo_interactivo == "button_reply":
                        text = messages["interactive"]["button_reply"]["id"]
                        numero = messages["from"]

                        enviar_mensajes_whatsapp(text,numero)

                    elif tipo_interactivo == "list_reply":
                        text = messages["interactive"]["list_reply"]["id"]
                        numero = messages["from"]

                        enviar_mensajes_whatsapp(text,numero)    

                if "text" in messages:
                    text = messages["text"]["body"]
                    numero = messages["from"]
                    #agregar_mensajes_log("Texto del mensaje: " + text)  # Registro de depuración
                    #agregar_mensajes_log("Número de teléfono: " + numero)  # Registro de depuración
                    enviar_mensajes_whatsapp(text,numero)

                    #Guardar Log en la BD
                    agregar_mensajes_log(messages)

        return jsonify({'message':'EVENT_RECEIVED'})
    except Exception as e:
        agregar_mensajes_log("Error: " + str(e))  # Registro de depuración
        return jsonify({'message':'EVENT_RECEIVED'})     

def enviar_mensajes_whatsapp(texto,number):
    texto = texto.lower()
    if "hola" in texto:
        data = {
                    "messaging_product": "whatsapp",    
                    "recipient_type": "individual",
                    "to": number,
                    "type": "text",
                    "text": {
                        "preview_url": False,
                        "body": "Hola Gatienzoo"
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
                        "body": "Primero se saluda, buen dia capo, no?"
                    }
                }
    agregar_mensajes_log("Enviando mensaje de respuesta: " + str(data))  # Registro de depuración

    #Convertir el diccionario a formato json
    data = json.dumps(data)

    headers = {
        "Content-Type" : "application/json",
        "Authorization" : "Bearer EAAYhSwsIKiQBOZCtLw8rmCnCKsfSRs0qiP2lKLOxnL02esZAxbidew9xLHc2ksHPDsPE54Kpl0y5CfntcQN0Qx8aDdnK3ByqvjetnlwoAKIatjevZAXEfakk9KQYcVp0NOzNR2ytquE3BgAhHfG8iBqucYroU7WRYv1bbfI9IPp940W9gtrLf0lyuwrAowvOp9tLMZBkrghS3QEUZBmZCJ"
    }

    #connection = http.client.HTTPSConnection("graph.facebook.com")

    # try:
    #     connection.request("POST","/v20.0/368298853039307/messages", data, headers)
    #     response = connection.getresponse()
    #     agregar_mensajes_log(response.status)
    #     agregar_mensajes_log(response.reason)
    #     if response.status == 200:
    #         print("Mensaje enviado exitosamente")
    #     else:
    #         print("Error al enviar mensaje:", response.status, response.reason)
    # except Exception as e:
    #     agregar_mensajes_log(e)
    # finally:
    #     connection.close()
    
    # URL de la API de WhatsApp
    #url = "https://graph.facebook.com/v20.0/368298853039307/messages"
    connection = http.client.HTTPSConnection("graph.facebook.com")

    try:
        # Enviar la solicitud POST
        connection.request("POST","https://graph.facebook.com/v20.0/368298853039307/messages", data, headers)
        response = connection.getresponse()
        #response = requests.post(url, headers=headers, data=json.dumps(data))
        agregar_mensajes_log(response.status)
        agregar_mensajes_log(response.reason)
        # Verificar el código de estado de la respuesta
        if response.status == 200:
            print("Mensaje enviado correctamente.")
        else:
            print(f"Error al enviar el mensaje: {response.status} - {response.reason}")

    except Exception as e:
        # Manejar errores de conexión o de la solicitud
        agregar_mensajes_log(e)
    finally:
        connection.close()    

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80,debug=True)