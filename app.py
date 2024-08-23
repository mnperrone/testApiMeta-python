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
    remitente = db.Column(db.String)
    texto = db.Column(db.TEXT)
    
    #constructor de la clase Log
    def __init__(self, texto, remitente):
        self.texto = texto
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
def agregar_mensajes_log(texto, remitente):
    texto = str(texto)
    mensajes_log.append(texto)
    #Guardar el mensaje en la base de datos
    nuevo_registro = Log(texto=texto,remitente=remitente)
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
        
        agregar_mensajes_log("Mensaje recibido: " + str(req), number)  # Log de depuración
        return jsonify({'message': 'EVENT_RECEIVED'})

    except Exception as e:
        agregar_mensajes_log("Error: " + str(e), number)
        return jsonify({'message': 'EVENT_RECEIVED'})

def enviar_mensajes_whatsapp(texto, number):
    texto = texto.lower()
    number = number
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
    
    # Registro de depuración con el remitente (número)
    agregar_mensajes_log(f"Data Sent: {json.dumps(data, indent=2)}", number)

    headers = {
        "Content-Type" : "application/json",
        "Authorization" : "Bearer EAAYhSwsIKiQBO3sPDAHaUIiOjfOsOp4BdbvrVmklTxxlCcr98U6Y0u8YboPrn4XwbRiTPRnZAa4ibIyWZBZAxHHJRJ7wSkUCzx8cdEXXL4437lBFxr2YTgX0YG1TscSOdTHSIcyDwEqrlX8b8oPc4UC3NMqZA4xvXxY8j10d55WbwTWmXgYc5q0586h65o2ZAIu02lWnxtDkYDPGxUWgZD"
    }

    connection = http.client.HTTPSConnection("graph.facebook.com")

    try:
         connection.request("POST","/v20.0/368298853039307/messages", data, headers)
         response = connection.getresponse()
         #agregar_mensajes_log(response.status)
         #agregar_mensajes_log(response.status)
         agregar_mensajes_log(f"{response.status} - {response.reason}", number)
    except Exception as e:
             agregar_mensajes_log(f"Error: {str(e)}", number)  # Asegurarse de pasar el remitente
    finally:
         connection.close()
    
    # URL de la API de WhatsApp
    #url = "https://graph.facebook.com/v20.0/368298853039307/messages"
    # connection = http.client.HTTPSConnection("graph.facebook.com")

    # try:
    #     # Enviar la solicitud POST
    #     connection.request("POST","/v20.0/368298853039307/messages", data, headers)
    #     response = connection.getresponse()
    #     #response = requests.post(url, headers=headers, data=json.dumps(data))
    #     agregar_mensajes_log(response.status)
    #     agregar_mensajes_log(response.reason)
    # except Exception as e:
    #     # Manejar errores de conexión o de la solicitud
    #     agregar_mensajes_log("Error en enviar_mensajes_whatsapp: " + str(e))
    # finally:
    #     connection.close()
        
    # URL de la API de WhatsApp
    # url = "https://graph.facebook.com/v20.0/368298853039307/messages"

    # try:
    #     # Enviar la solicitud POST con requests sin json.dumps(data)
    #     response = requests.post(url, headers=headers, json=data)

    #     # Registrar el estado de la respuesta y el contenido completo de la respuesta
    #     agregar_mensajes_log(f"Status Code: {response.status_code}", number)
    #     agregar_mensajes_log(f"Response Text: {response.text}", number)

    #     # Revisar si la respuesta incluye un JSON con detalles del error
    #     try:
    #         response_json = response.json()
    #         agregar_mensajes_log(f"Response JSON: {json.dumps(response_json, indent=2)}", number)
    #     except ValueError:
    #         agregar_mensajes_log("No JSON response received.", number)

    #     if response.status_code == 200:
    #         print("Mensaje enviado exitosamente")
    #     else:
    #         print(f"Error al enviar mensaje: {response.status_code}, {response.reason}")

    # except Exception as e:
    #     # Manejar errores de conexión o de la solicitud
    #     agregar_mensajes_log(f"Error: {str(e)}", number)


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80,debug=True)