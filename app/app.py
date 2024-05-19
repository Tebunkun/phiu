import json
import sys
from flask import request
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
from http import HTTPStatus
from flask import Flask
from marshmallow import Schema, fields
from initialise import Initialise
# import built-in validators
from marshmallow.validate import Length, Range
from flask import jsonify
from flask import render_template
from flask_cors import CORS

# Creates the Flask app
app = Flask(__name__, template_folder="templates")
init = Initialise()
app = init.db(app)

# Creates the db connection
db = SQLAlchemy(app)

CORS(app)
# @app.route('/index/')
# def home():
#         return render_template("index.html") 
class UserSchema(Schema):
    # Required value shorter than 50 characters
    name = fields.Str(required=True, validate=Length(max=50))
    # Required value shorter than 50 characters
    surname = fields.Str(required=True, validate=Length(max=50))
    # Required value shorter than 12 characters
    identity_number = fields.Int(required=True, validate=Range(min=1))
    
class IDSchema(Schema):
    identity_number = fields.Int(required=True, validate=Range(min=1))
    
user_schema = UserSchema()

def execute(sql, data):
    result = db.engine.execute(
        sql,
        data
    )
    db.session.commit()
    return result

class ClubMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    sisi = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    about = db.Column(db.Text, nullable=True)
    major = db.Column(db.String(100), nullable=True)
    joined_at = db.Column(db.DateTime, nullable=True, default=db.func.current_timestamp())

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    message = db.Column(db.String(100), nullable=True)
    sisi = db.Column(db.Text, nullable=True)
    
@app.route('/api/clubs', methods=['GET'])
def get_clubs():
    search = request.args.get('find', '')
    try:
        if search:
            sql = text('SELECT * FROM club WHERE name LIKE :search OR description LIKE :search')
            result = db.engine.execute(sql, search=f'%{search}%').fetchall()
        else:
            sql = text('SELECT * FROM club')
            result = db.engine.execute(sql).fetchall()
        clubs = [
            {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "img": row.img,
                "leader": row.leader,
                "goal": row.goal,
                "joinable": bool(row.joinable)
            }
            for row in result
        ]
        return jsonify(clubs), HTTPStatus.OK
    except Exception as e:
        return jsonify({"error": 'Failed. ' + str(e)}), HTTPStatus.NOT_FOUND
    
@app.route('/api/events', methods=['GET'])
def get_events():
    club = request.args.get('club', '')
    try:
        if club:
            sql = text('''
            SELECT event.id, event.club_id, event.name AS event_name, event.img, event.description, event.shortly, event.location, event.start_date, event.status, club.name AS club_name
            FROM event
            JOIN club ON event.club_id = club.id 
            WHERE  club.id = :club 
        ''')
            result = db.engine.execute(sql, club=club).fetchall()
        else:
            sql = text('''
            SELECT event.id, event.club_id, event.name AS event_name, event.img, event.description, event.shortly, event.location, event.start_date, event.status, club.name AS club_name
            FROM event
            JOIN club ON event.club_id = club.id 
            WHERE status = 'ACTIVE' 
        ''')
            result = db.engine.execute(sql).fetchall()
        events = [
            {
                "id": row.id,
                "club_id": row.club_id,
                "event_name": row.event_name,
                "img": row.img,
                "description": row.description,
                
                "shortly": row.shortly,
                "start_date": row.start_date.strftime('%Y-%m-%d %H:%M'),
                "status": row.status,
                "club_name": row.club_name,
                "location": row.location
            }
            for row in result
        ]
        return jsonify(events), HTTPStatus.OK
    except Exception as e:
        return jsonify({"error": 'Failed. ' + str(e)}), HTTPStatus.NOT_FOUND
    
@app.route('/api/clubs/<int:club_id>', methods=['GET'])
def get_club_by_id(club_id):
    try:
        sql = text('SELECT * FROM club WHERE id = :club_id')
        result = db.engine.execute(sql, club_id=club_id).fetchone()

        if result:
            club = {
                "id": result.id,
                "name": result.name,
                "description": result.description,
                "img": result.img,
                "leader": result.leader,
                "goal": result.goal,
                "joinable": bool(result.joinable)
            }
            return jsonify(club), HTTPStatus.OK
        else:
            return jsonify({"error": "Club not found"}), HTTPStatus.NOT_FOUND
    except Exception as e:
        return jsonify({"error": 'Failed. ' + str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR
    
@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_event_by_id(event_id):
    try:
        sql = text('''
            SELECT event.id, event.club_id, event.name AS event_name, event.img, event.description, event.shortly, event.location, event.start_date, event.status, club.name AS club_name
            FROM event
            JOIN club ON event.club_id = club.id 
            WHERE event.id = :event_id
        ''')
        row = db.engine.execute(sql, event_id=event_id).fetchone()

        if row:
            event = {
                "id": row.id,
                "club_id": row.club_id,
                "event_name": row.event_name,
                "img": row.img,
                "description": row.description,
                "shortly": row.shortly,
                "start_date": row.start_date.strftime('%Y-%m-%d %H:%M'),
                "status": row.status,
                "club_name": row.club_name,
                "location": row.location
            }
            return jsonify(event), HTTPStatus.OK
        else:
            return jsonify({"error": "Club not found"}), HTTPStatus.NOT_FOUND
    except Exception as e:
        return jsonify({"error": 'Failed. ' + str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route('/api/clubs/<int:club_id>/members', methods=['GET'])
def get_club_members(club_id):
    try:
        # Query club members by club_id
        members = ClubMember.query.filter_by(club_id=club_id).all()
        
        # Serialize members to JSON
        serialized_members = []
        for member in members:
            serialized_member = {
                "id": member.id,
                "club_id": member.club_id,
                "first_name": member.first_name,
                "last_name": member.last_name,
                "sisi": member.sisi,
                "email": member.email,
                "about": member.about,
                "major": member.major,
                "joined_at": member.joined_at.strftime('%Y-%m-%d %H:%M:%S') if member.joined_at else None
            }
            serialized_members.append(serialized_member)
        
        return jsonify(serialized_members), HTTPStatus.OK
    except Exception as e:
        return jsonify({"error": 'Failed. ' + str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route('/api/members/<int:club_id>', methods=['POST'])
def add_member(club_id):
    try:
        data = request.get_json()

        # Validate the incoming data
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        sisi = data.get('sisi')
        email = data.get('email')
        about = data.get('about')
        major = data.get('major')
        joined_at = data.get('joined_at')

        if not club_id or not first_name or not last_name:
            return jsonify({"error": "club_id, first_name, and last_name are required"}), 400

        if joined_at:
            joined_at = datetime.strptime(joined_at, '%Y-%m-%d %H:%M:%S')
        
        # Create a new member instance
        new_member = ClubMember(
            club_id=club_id,
            first_name=first_name,
            last_name=last_name,
            sisi=sisi,
            email=email,
            about=about,
            major=major
        )

        # Add and commit the new member to the database
        db.session.add(new_member)
        db.session.commit()

        return jsonify({"message": "Member added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
class Item(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    img = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    phone = db.Column(db.Text, nullable=False)
    
@app.route('/api/products', methods=['GET'])
def get_items():
    try:
        items = Item.query.all()
        result = []
        for item in items:
            item_data = {
                "id": item.id,
                "img": item.img,
                "name": item.name,
                "price": item.price,
                "description": item.description,
                "phone": item.phone
            }
            result.append(item_data)

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/feedback', methods=['POST'])
def add_feedback():
    try:
        data = request.get_json()

        # Validate the incoming data
        name = data.get('name')
        sisi = data.get('sisi')
        message = data.get('message')

        if not sisi or not name:
            return jsonify({"error": "name and sisi are required"}), 400
        
        # Create a new member instance
        feedback = Feedback(
            name=name,
            sisi=sisi,
            message=message,
        )

        # Add and commit the new member to the database
        db.session.add(feedback)
        db.session.commit()

        return jsonify({"message": "Member added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500