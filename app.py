from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from flask_migrate import Migrate
from sqlalchemy.orm import Session
from hashlib import sha256
from flask_socketio import SocketIO, join_room, leave_room, emit
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime


app = Flask(__name__)
load_dotenv()
room_users = {}
users = {}
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
socket = SocketIO(app, cors_allowed_origins="*")
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class RoomData(db.Model):
    __tablename__ = "room_data"
    room_name = db.Column(db.String(100), primary_key=True)
    password = db.Column(db.String(100), nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False)
    cur_capacity = db.Column(db.Integer, nullable=False)

def log_error(error_message, function):
    with open("error_log.txt", "a") as f:
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M")
        f.write(f"{current_time}--{function}    {error_message}\n")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/create_room", methods=["POST", "GET"])
def create_room():
    if request.method == "POST":
        data = request.json

        # checking if data is provided
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        # extractign the variable from the request the server received

        room_name = data.get('room_name')
        password = data.get('password')

        capacity = data.get('capacity')

        #  checking all the variables is provided or not
        if not room_name or not password or not capacity:
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400


        try:
            # checking that the user is already exists in the database oe not
            # Hash the password
            hashed_password = sha256(password.encode()).hexdigest()
            exist_room = db.session.execute(text("SELECT * FROM user.room_data WHERE room_name= :room_name"), {'room_name': room_name}).fetchall()
            if exist_room:
                return jsonify({'status': 'room_exist'})

            room = RoomData(room_name=room_name, password=hashed_password, max_capacity=capacity, cur_capacity=0)
            db.session.add(room)
            db.session.commit()

            return jsonify({'status': 'room_created'})
        
        except SQLAlchemyError as e:
            db.session.rollback()
            log_error(str(e),"create_room")
            return jsonify({'status': 'error', 'message': str(e)}), 500
        
        except Exception as e:
            log_error(str(e),"createe_room")
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
            log_error(str(e),"login_room")
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
    ssid = request.sid    
    
    if user_id is None or user_id == "null":
        user_id = str(uuid.uuid4())
    
    if room not in room_users:
        room_users[room] = []

    if user_id not in room_users[room]:
        room_users[room].append(user_id)
        users[ssid] = {"room": room, "user_id": user_id}
        
        try:
            with Session(db.engine) as session, session.begin():
                result = session.execute(
                    text("SELECT cur_capacity, max_capacity FROM user.room_data WHERE room_name = :room_name"),
                    {"room_name": room}
                ).fetchone()

                if result.cur_capacity >= result.max_capacity:
                    raise Exception("Room is full")
                    
                
                session.execute(
                    text("UPDATE user.room_data SET cur_capacity = cur_capacity + 1 WHERE room_name = :room_name"),
                    {"room_name": room}
                )
                
                curcapacity = session.execute(
                    text("SELECT cur_capacity, max_capacity FROM user.room_data WHERE room_name = :room_name"),
                    {"room_name": room}
                ).fetchone()[0]
                
            join_room(room)

            emit("set_user_id",{"user_id":user_id},to=request.sid)
            emit("joined_room", {'cur_capacity': curcapacity},include_self=False, to=room)
        except SQLAlchemyError as e:
            db.session.rollback()
            log_error(str(e),"connect1")
            emit("error", {'message': str(e)}, to=ssid), 500
        except Exception as e:
            log_error(e,"connect2")
            return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500
    else:
        print("error message user already in room")
        emit("error", {'message': 'User already in room'}, to=ssid)
@socket.on('join_room')
def handle_join(data):
    ssid = request.sid
    if ssid in users:
        
        room = data["room"]
        try:
            cur_capacity = db.session.execute(
                text("SELECT cur_capacity FROM user.room_data WHERE room_name = :room_name"),
                {"room_name": room}
            ).fetchall()
            emit("self_join", {'cur_capacity': cur_capacity[0][0]}, to=ssid)
        except SQLAlchemyError as e:
            db.session.rollback()
            log_error(str(e),"join_room")
            emit("error", {'message': str(e)}, to=ssid)
        
        except Exception as e:
            log_error(str(e),"join_room")
            return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500
    else:
        emit("error", {'message': 'User already in room'}, to=ssid)

@socket.on("message")
def handle_message(data):
    room = data['room']
    message = data['message']
    emit("message", message, to=room, include_self=False)


@socket.on('disconnect')
def handle_disconnect():
    ssid = request.sid
    if ssid in users:
        room = users[ssid]["room"]
        user_id = users[ssid]["user_id"]

        del users[ssid]
        if user_id in room_users[room]:
            room_users[room].remove(user_id)
        if not room_users[room]:
            del room_users[room]
        try:
            with Session(db.engine) as session, session.begin():
                current_room = session.execute(
                    text("SELECT cur_capacity FROM user.room_data WHERE room_name = :room_name FOR UPDATE"),
                    {"room_name": room}
                ).fetchone()

                if current_room and current_room.cur_capacity > 0:
                    session.execute(
                        text("UPDATE user.room_data SET cur_capacity = cur_capacity - 1 WHERE room_name = :room_name"),
                        {"room_name": room}
                    )
                    updated_room = session.execute(
                        text("SELECT cur_capacity FROM user.room_data WHERE room_name = :room_name"),
                        {"room_name": room}
                    ).fetchone()
                    leave_room(room)
                    emit("lefted_room", {'cur_capacity': updated_room.cur_capacity}, to=room)
        except SQLAlchemyError as e:
            db.session.rollback()
            log_error(str(e),"disconnect")
            emit("error", {'message': str(e)}, to=room)
        except Exception as e:
            log_error(str(e),"disconnect")
            return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500
        leave_room(room)
       

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socket.run(app, host="0.0.0.0", port=5000)
    
