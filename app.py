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
    texto = db.Column(db.TEXT)
    
    #constructor de la clase Log
    def __init__(self, texto):
        self.texto = texto

#Crear la tabla si no existe
with app.app_context():
    db.create_all()

    # prueba1 = Log("hola")
    # prueba2 = Log("holaaa")
    # db.session.add(prueba1)
    # db.session.add(prueba2)
    # db.session.commit()

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
        entry = req['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        objeto_mensaje = value['messages']

        if objeto_mensaje:
            messages = objeto_mensaje[0]

            if "type" in messages:
                tipo = messages["type"]

                if tipo == "interactive":
                    return 0
                if "text" in messages:
                    text = messages["text"]["body"]
                    numero  = messages["from"]
                    #agregar_mensajes_log(text)
                    #agregar_mensajes_log(numero)
                    enviar_mensajes_whatsapp(text,numero)

        return jsonify({'message':'EVENT_RECEIVED'})
    except Exception as e:
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
                    "body": "Primero se saluda, capo. Buen dia, no?"
                }
        }
    #Convertir el diccionario a formato json
    data = json.dumps(data)

    headers = {
        "Contente-Type" : "application/json",
        "Authorization" : "Bearer EAAYhSwsIKiQBOZBctJylOZBNjaJeNoevfHrKbuHsvY0HaWmQmQ2nRNQZAZCDAxhuxIpZC6kkj4drpxJA2EnX4oCkGhT2mz7ZAYyE85Qze9qlqUk2bYXIPOGiPDXF7xLOivAhX755Wc2Ys3wXZCbvpKoyf5rEavkFXVfjTaxmZAk9RI1gXMkFQeBaojhTNLgregIsrAMU4Ip1iofmjDmAVawZD"
    }

    connection = http.client.HTTPConnection("graph.facebook.com")

    try:
        connection.request("POST","/v20.0/368298853039307/messages", data, headers)
        response = connection.getresponse()
        print(response.status, response.reason)
    except Exception as e:
        agregar_mensajes_log(e)
    finally:
        connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80,debug=True)