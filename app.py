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
    elif "1" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "El Movimiento de Liberación Nacional (MLN) encarna la continuidad histórica en el siglo XXI del Modelo Argentino de Desarrollo. Nuestras bases son sólidas, perdurables, y se encuentran en el corazón de cada argentino.\n\n Somos los hombres y mujeres de San Martín, Rosas, Yrigoyen y Perón. Somos el pueblo que durante más de 200 años, pugnó por la Liberación Nacional por medio del poder determinante del trabajo y la fuerza de la comunidad organizada. Así José de San Martín construyó las fábricas militares como brazo industrial de la gesta libertadora. De esa manera, Juan Manuel de Rosas nacionalizó la banca y el comercio exterior poniendo límites a los imperialismos europeos. Bajo el mismo modelo Hipólito Yrigoyen creó la primera petrolera estatal del planeta tierra, YPF.\n\n La obra de Juan Perón, puso a tope al Estado Empresario argentino, mediante la conducción nacional de los sectores industriales estratégicos: más de 300 empresas estatales determinantes para la producción, los servicios, la cultura y todo lo que hace a la vida nacional. En su última etapa, legó para la posteridad, dos instrumentos invaluables para el pueblo argentino y adoptados en el mundo: las Leyes 20.705 y 20.558 de Sociedades y Corporaciones del Estado. Vectores que coronan el Modelo Argentino de Desarrollo, porque integran en su seno a las firmas estatales y a las PyMEs privadas asociadas de manera complementaria, con el sólo objetivo de abandonar el rol de semicolonia en el concierto de la “división internacional del trabajo”, y tomar las riendas de la soberanía política, la independencia económica y la justicia social.\n\n El MLN afirma que existe una forma de ser nacional y eso es el Estado empresario, como forma de organización, que permite lograr el pleno empleo y es la única concepción de justicia social posible, sustentado en dos principios fundamentales: 1) cada argentino debe producir, al menos, aquello que consume y 2) donde hay una necesidad hay un derecho, porque todos tenemos derecho a trabajar. Por eso, el Estado Empresario es el centro del proceso económico y de la vida Nacional. Esa es la concepción del Modelo Argentino de Desarrollo. La Liberación Nacional será con la organización de la comunidad, de la familia y el despliegue espiritual del individuo. Argentina será libre por su pueblo y para su pueblo."
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
                "body": "🇦🇷 Hola Argentin@, visita la web del movimiento https://mln.ar/ para más información, allí también podrás afiliarte.\n\n📌Por favor, ingresa un número #️⃣ para recibir información.\n\n1️⃣. Información del Proyecto. ❔\n2️⃣. Ubicación de los grupos de militancia en el AMBA. 📍\n3️⃣. Enviar proyecto de ley IAPI XXI C.E. 📄 📍\n4️⃣. Enviar proyecto de ley ELMA XXI C.E. 📄\n5️⃣. Enviar proyecto de ley Régimen Transporte por Agua. 📄\n6️⃣. Enviar proyecto de ley Fondo de Desarrollo de la Ind. Naval. 📄\n7️⃣. Audio explicando el proyecto. 🎧\n8️⃣. Video de Introducción. ⏯️\n8️⃣. Hablar con algún compañero. 🙋‍♂️\n9️⃣. Próximas actividades. 🕜\n0️⃣. Regresar al Menú. ☑️"
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
        "Authorization" : "Bearer EAAYhSwsIKiQBO3iNIX3yDe4ZAXjBXUJYs3oxyF6DTJDBc6XjSMXjI2RZBGbKH1zb39j3nGwXNReT6GRAaVk0LZBPPNiBFdekyeWr1fuYvnMMapGXGgzZAgQjs35ZAmaLhqOxN3ryudVajCRI2MOQMbZA8NRTqO2JaXUpLR1d6f7ZC3XJ6lyThV121YpKw361TtrXC8lLf4ooYe7vZCQCSHgZD"
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