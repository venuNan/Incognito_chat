from flask import Flask, render_template, request, jsonify, redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from hashlib import sha256
from flask_socketio import SocketIO,join_room,leave_room,send
from time import sleep
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.config['METHOD_OVERRIDE'] = False

load_dotenv()

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET"] = os.environ.get("SECRET_KEY")

socket = SocketIO(app,cors_allowed_origins="*")

db = SQLAlchemy(app)

class RoomData(db.Model):
    room_name = db.Column(db.String(100), primary_key=True)
    password = db.Column(db.String(100), nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False)
    cur_capacity = db.Column(db.Integer, nullable=False, default=1)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/create_room", methods=["POST","GET"])
def create_room():
    if request.method == "POST":
        data = request.json
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        room_name = data.get('room_name')
        password = sha256((data.get('password')).encode()).hexdigest()
        capacity = data.get('capacity')

        if room_name == "" or password == " " or capacity == "":
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

        try:
            exist_room = db.session.execute(text("select * from user.room_data where room_name= :room_name"),{'room_name':room_name}).fetchall()
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
    

@app.route("/login_to_room",methods=["POST", "GET"])
def login_to_room():
    print(request.method)
    if request.method == "POST":
        
        data = request.json
        print(data)
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        room_name = data.get('room_name')
        password = sha256((data.get('password')).encode()).hexdigest()

        if room_name == "" or password == " ":
            print("missing required fields")
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

        try:
            user_exists = db.session.execute(text("SELECT * FROM user.room_data WHERE room_name = :room_name AND password = :password"), {'room_name': room_name, 'password': password}).fetchall()
    
            if user_exists:
                if user_exists[0][2] > user_exists[0][3]:
                    if user_exists[0][1] == password:
                        try:
                            db.session.execute(text("UPDATE user.room_data SET cur_capacity = cur_capacity + 1 WHERE room_name = :room_name"), {'room_name': room_name})
                            db.session.commit()
                            return jsonify({"status": "success", "room_name": user_exists[0][0], "max_capacity": user_exists[0][2], "cur_capacity": user_exists[0][3] + 1})
                        except SQLAlchemyError as e:
                            db.session.rollback()
                            return jsonify({'status': 'error', 'message': str(e)}), 500
                    else:
                        return jsonify({'status': 'error', 'message': 'Incorrect password'})
                else:
                    return jsonify({'status': 'error', 'message': 'Room is full'})
            else:
                return jsonify({'status': 'error', 'message': 'Room does not exist'})
        except Exception as e:
            print(f"Exception occurred: {e}") 
            return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500

    else:
        return render_template("login_to_room.html")


@app.route("/chat_room")
def chat_room():
    data = request.args
    return render_template("chat_room.html",data=data)

@socket.on('join')
def handle_join(data):
    room = data['room']
    join_room(room)
    send(f'someone has entered the room.', to=room)

@socket.on('leave')
def handle_leave(data):
    room = data['room']
    leave_room(room)
    try:
        db.session.execute(text("UPDATE user.room_data SET cur_capacity = cur_capacity + 1 WHERE room_name = :room_name"), {'room_name': room})
        db.session.commit()
        send(f'someone has left the room.', to=room)
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@socket.on("message")
def handle_message(data):
    room = data['room']
    message = data['message']
    send(message, to=room)

if __name__ == "__main__":
    socket.run(app,host="localhost",port=6589)
