from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from hashlib import sha256
from flask_socketio import SocketIO, join_room, leave_room, emit
from dotenv import load_dotenv
import os
import uuid

app = Flask(__name__)
load_dotenv()
room_users = {}
users = {}
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
socket = SocketIO(app, cors_allowed_origins="*")
db = SQLAlchemy(app)

class RoomData(db.Model):
    room_name = db.Column(db.String(100), primary_key=True)
    password = db.Column(db.String(100), nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False)
    cur_capacity = db.Column(db.Integer, nullable=False)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/create_room", methods=["POST", "GET"])
def create_room():
    if request.method == "POST":
        data = request.json
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        room_name = data.get('room_name')
        password = sha256(data.get('password').encode()).hexdigest()
        capacity = data.get('capacity')

        if not room_name or not password or not capacity:
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

        try:
            exist_room = db.session.execute(text("SELECT * FROM user.room_data WHERE room_name= :room_name"), {'room_name': room_name}).fetchall()
            if exist_room:
                return jsonify({'status': 'room_exist'})

            room = RoomData(room_name=room_name, password=password, max_capacity=capacity, cur_capacity=1)
            db.session.add(room)
            db.session.commit()

            return jsonify({'status': 'room_created'})
        
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
        
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500
        
    else:
        return render_template("create_room.html")

@app.route("/login_to_room", methods=["POST", "GET"])
def login_to_room():
    if request.method == "POST":
        data = request.json
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        room_name = data.get('room_name')
        password = sha256(data.get('password').encode()).hexdigest()

        if not room_name or not password:
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

        try:
            user_exists = db.session.execute(text("SELECT * FROM user.room_data WHERE room_name = :room_name AND password = :password"), {'room_name': room_name, 'password': password}).fetchall()
            if user_exists:
                if user_exists[0][2] > user_exists[0][3]:
                    if user_exists[0][1] == password:
                        return jsonify({"status": "success", "room_name": user_exists[0][0]})
                    else:
                        return jsonify({'status': 'error', 'message': 'Incorrect password'})
                else:
                    return jsonify({'status': 'error', 'message': 'Room is full'})
            else:
                return jsonify({'status': 'error', 'message': 'Room does not exist'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500
    else:
        return render_template("login_to_room.html")

@app.route("/chat_room")
def chat_room():
    data = request.args
    return render_template("chat_room.html", data=data)

@app.route("/error")
def error_page():
    message = request.args.get("message", "")
    return render_template("error_page.html", data={"message": message})

@socket.on('connect')
def handle_connect():
    room = request.args.get("room")
    user_id = request.args.get("user_id")
    if user_id is None or user_id == "null":
        user_id = str(uuid.uuid4())
    
    if room not in room_users:
        room_users[room] = []
    if user_id not in room_users[room]:
        room_users[room].append(user_id)
        try:
            db.session.execute(
                text("UPDATE user.room_data SET cur_capacity = cur_capacity + 1 WHERE room_name = :room_name"),
                {'room_name': room}
            )
            db.session.commit()

            result = db.session.execute(
            text("SELECT cur_capacity, max_capacity FROM user.room_data WHERE room_name = :room_name"),
            {"room_name": room}
            ).fetchone()

            cur_capacity, max_capacity = result
            print("cur_capacity",cur_capacity,"max_capacity",max_capacity)
            if cur_capacity >= max_capacity:
                db.session.execute(
                text("UPDATE user.room_data SET cur_capacity = cur_capacity - 1 WHERE room_name = :room_name"),
                {'room_name': room}
                )
                db.session.commit()
                emit("error", {'message': 'Room is full'}, to=request.sid)
                return
            join_room(room)

            emit("set_user_id",{"user_id":user_id},to=request.sid)
            emit("joined_room", {'cur_capacity': cur_capacity},include_self=False, to=room)
        except SQLAlchemyError as e:
            db.session.rollback()
            emit("error", {'message': str(e)}, to=request.sid)
    else:
        emit("error", {'message': 'User already in room'}, to=request.sid)
        
@socket.on('join_room')
def handle_join(data):
    room = data["room"]
    user_id = data["user_id"]
    ssid = request.sid
    print(ssid)
    users[ssid] = {"room": room, "user_id": user_id}
    join_room(room)
    try:
        cur_capacity = db.session.execute(
            text("SELECT cur_capacity FROM user.room_data WHERE room_name = :room_name"),
            {"room_name": room}
        ).fetchall()
        print("cur_capacity", cur_capacity[0][0])
        emit("self_join", {'cur_capacity': cur_capacity[0][0]}, to=ssid)
    except SQLAlchemyError as e:
        db.session.rollback()
        emit("error", {'message': str(e)}, to=ssid)

@socket.on("message")
def handle_message(data):
    room = data['room']
    message = data['message']
    emit("message", message, to=room, include_self=False)


@socket.on('disconnect')
def handle_disconnect():
    ssid = request.sid
    print(ssid)
    if ssid in users:
        room = users[ssid]["room"]
        user_id = users[ssid]["user_id"]
        print("disconnect", ssid)
        print(room_users)
        print(users)

        del users[ssid]
        if user_id in room_users[room]:
            room_users[room].remove(user_id)
        if not room_users[room]:
            del room_users[room]
        try:
            db.session.execute(
                text("UPDATE user.room_data SET cur_capacity = cur_capacity - 1 WHERE room_name = :room_name AND cur_capacity > 0"),
                {'room_name': room}
            )
            db.session.commit()
            cur_capacity = db.session.execute(
                text("SELECT cur_capacity FROM user.room_data WHERE room_name = :room_name"),
                {"room_name": room}
            ).fetchall()
            emit("lefted_room", {'cur_capacity': cur_capacity[0][0]}, to=room)
        except SQLAlchemyError as e:
            db.session.rollback()
            emit("error", {'message': str(e)}, to=room)
        leave_room(room)
        print(room_users)
        print(users)

if __name__ == "__main__":
    socket.run(app, host="0.0.0.0", port=5000)
    with app.app_context():
        db.create_all()
