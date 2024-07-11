from flask import Flask, render_template, request,jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:VenuNan5142M_@localhost/user"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Room_data(db.Model):
    room_name = db.Column(db.String(100),primary_key=True)
    password = db.Column(db.String(100),nullable=False)
    max_capacity = db.Column(db.Integer,nullable= False)
    cur_capacity = db.Column(db.Integer,nullable=False,default=1)

    def __repr__(self) -> str:
        return f"<Room_data(room_name={self.room_name}, password={self.password}, max_capacity={self.max_capacity}, cur_capacity={self.cur_capacity})>"

@app.route("/")
def home():
    return render_template("index.html")

# to render the create room page 
@app.route("/to_create_room_page")
def create_room_page():
    return render_template("create_room.html")

#  to render the login to room page
@app.route("/to_login_to_room_page")
def login_to_room_page():
    return render_template("login_to_room.html")


# to create a room based on the details given by the user
@app.route("/create_room", methods=["POST"])
def create_room():
    data = request.json
    exist_room = Room_data.query.filter_by(room_name=data['room_name'])
    print(exist_room)
    if exist_room > 0:
        return jsonify({'status':'room_exists'})
    print(data)
    return jsonify(data)
    
# to login into an existing room
@app.route("/login_to_room")
def login_to_room():
    return render_template("login_to_room.html")

if __name__ == "__main__":
    app.run()
    with app.app_context():
        db.create_all()
