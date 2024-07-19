from flask import Flask, render_template, request, jsonify, redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from hashlib import sha256
from flask_socketio import SocketIO,send
from time import sleep

app = Flask(__name__)
app.config['METHOD_OVERRIDE'] = False


app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:VenuNan5142M_@localhost/user"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET"] = "dhagumativenumadhavreddy"

socket = SocketIO(app)

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
            user_exists = db.session.execute(text("select * from user.room_data where room_name= :room_name and password= :password"),{'room_name':room_name,"password":password}).fetchall()
            print(user_exists)
            if user_exists:
                return jsonify({"status":"success", "room_name":user_exists[0][0],"max_capacity":user_exists[0][2],"cur_capacity":user_exists[0][3]})
            else:
                return jsonify({'status': 'error', 'mesage':'Room does not exist'})
        
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500
    else:
        return render_template("login_to_room.html")


@app.route("/chat_room")
def chat_room():
    data = request.args
    return render_template("chat_room.html",data=data)

# @app.route("/send")
# def send():
#     message = request.form.get("message")
#     return jsonify({"message":"helloworld"})

def func():
    while True:
        sleep(1)
        socket.emit("hello world")

@socket.on("message")
def send_to_frontend(msg):
    if msg == "user_connected":
            print(msg)
            socket.start_background_task(func)


if __name__ == "__main__":
    socket.run(app,host="localhost",port=6589)
