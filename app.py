import random
from flask import Flask, request
from flask import render_template
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

socket_pairs = {}

waiting_sockets = []

connectionNumber = 10

@app.route('/')
def index():
    return render_template("index.html")

@socketio.on('connect')
def handle_connect():
    print(f'Cliente conectado: {request.sid}')
    waiting_sockets.append(request.sid) 

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in waiting_sockets:
        waiting_sockets.remove(request.sid)
    else:
        partner = socket_pairs.pop(request.sid, None)
        if partner:
            waiting_sockets.append(partner) 
            emit('message', f'El socket {request.sid} se ha desconectado. Ahora estás en espera.', room=partner)

    print(f'Cliente desconectado: {request.sid}')
    emit("message", str(len(waiting_sockets))) 

@socketio.on('create_random_pair')
def handle_create_random_pair():
    if len(waiting_sockets) < 2:
        emit('message', 'No hay suficientes clientes en espera para crear una pareja.')
        return

    selected_sockets = random.sample(waiting_sockets, 2)
    room_name = f'room_{selected_sockets[0]}_{selected_sockets[1]}'

    for socket_id in selected_sockets:
        join_room(room_name)
        socket_pairs[socket_id] = selected_sockets[1] if socket_id == selected_sockets[0] else selected_sockets[0]
        waiting_sockets.remove(socket_id)
        emit('message', f'Has sido unido a la sala: {room_name}', room=socket_id)

    print(f'Sockets {selected_sockets} se unieron a la sala: {room_name}')

@socketio.on('leave_room')
def handle_leave_room():
    partner = socket_pairs.pop(request.sid, None)
    if partner:
        leave_room(f'room_{request.sid}_{partner}')
        waiting_sockets.append(partner)
        emit('message', f'Has salido de la sala. Tu compañero {partner} ahora está en espera.', room=partner)
        if waiting_sockets:
            new_partner = waiting_sockets.pop(0) 
            room_name = f'room_{request.sid}_{new_partner}'
            join_room(room_name)
            socket_pairs[request.sid] = new_partner
            socket_pairs[new_partner] = request.sid
            emit('message', f'Has sido emparejado con {new_partner} en la sala: {room_name}', room=request.sid)
            emit('message', f"Has sido emparejado")# con {request.sid} en la sala: {room_name}, room=new_partner)
            print(f'Socket {request.sid} se ha emparejado con {new_partner} en la sala: {room_name}')
    else:
        emit('message', 'No estás en una sala.')

@socketio.on('send_message')
def handle_send_message(data):
    if isinstance(data, dict) and 'message' in data:
        message = data['message']
    else:
        message = str(data)  
    partner = socket_pairs.get(request.sid)
    if partner:
        emit('message', f'{message}', room=partner)
        #emit('message', f'Tú: {message}', room=request.sid)
        #print(f'Mensaje de {request.sid} a {partner}: {message}')
    else:
        emit('message', 'No tienes pareja para enviar un mensaje.')


@socketio.on('number')
def handle_number():
    print(connectionNumber)
    emit("message", str(connectionNumber))


if __name__ == '__main__':
    socketio.run(app)
