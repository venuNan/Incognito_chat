from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:VenuNan5142M_@localhost/user"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class RoomData(db.Model):
    
    room_name = db.Column(db.String(100), primary_key=True)
    password = db.Column(db.String(100), nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False)
    cur_capacity = db.Column(db.Integer, nullable=False, default=1)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/to_create_room_page")
def to_create_room_page():
    return render_template("create_room.html")


@app.route("/create_room", methods=["POST"])
def create_room():
    
    data = request.json
    print(data)
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400

    room_name = data.get('room_name')
    password = data.get('password')
    capacity = data.get('capacity')

    if not room_name or not password or not capacity:
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

    try:
        exist_room = db.session.execute(text("select * from user.room_data where room_name= :room_name"),{'room_name':room_name}).fetchall()
        if exist_room:
            print("room_exist")
            return jsonify({'status': 'room_exist'})

        room = RoomData(room_name=room_name, password=password, max_capacity=capacity, cur_capacity=1)
        db.session.add(room)
        db.session.commit()

        print("room_created")
        return jsonify({'status': 'room_created'})
    
    except SQLAlchemyError as e:
        print(e)
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500
    
    
@app.route("/login_to_room")
def login_to_room():
    return render_template("login_to_room.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()
