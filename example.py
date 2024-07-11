from app import db,app,Room_data


with app.app_context():
    rooms = Room_data.query.filter_by(room_name="RoomA").all()
    print(len(rooms))
    