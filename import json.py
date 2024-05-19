import json
from flask import request
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
from http import HTTPStatus
from initialise import Initialise
from flask import Flask
from marshmallow import Schema, fields
# import built-in validators
from marshmallow.validate import Length, Range


# Creates the Flask app
app = Flask(__name__)
init = Initialise()
app = init.db(app)

# Creates the db connection
db = SQLAlchemy(app)

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

def hateoas(id):
    return [
                {
                    "rel": "self",
                    "resource": "http://127.0.0.1:8000/v1/users/" + str(id),
                    "method": "GET"
                },
                {
                    "rel": "update",
                    "resource": "http://127.0.0.1:8000/v1/users/" + str(id),
                    "method": "PATCH"
                },
                {
                    "rel": "update",
                    "resource": "http://127.0.0.1:8000/v1/users/" + str(id),
                    "method": "DELETE"
                }
            ]

@app.route('/v1/users', methods=['POST'])
def post_user_details():
    try:
        data = request.get_json()
        errors = user_schema.validate(data)
        if errors:
            return json.dumps(str(errors)), HTTPStatus.BAD_REQUEST
        sql = text('INSERT INTO users (name, surname, identity_number) values (:name, :surname, :id_num)')
        result = db.engine.execute(
            sql,
            name=data['name'],
            surname=data['surname'],
            id_num = data['identity_number']
        )
        return json.dumps({"id": result.lastrowid,"links": hateoas(result.lastrowid)})
    except Exception as e:
        return json.dumps('Failed. ' + str(e)), HTTPStatus.NOT_FOUND

@app.route('/v1/users/<user_id>', methods=['GET'])
def get_user_details(user_id):
    try:
        sql = text('SELECT * FROM users WHERE id=:id_num')
        result = db.engine.execute(sql, id_num=user_id).fetchone()
        return json.dumps({"name": result.name, "surname": result.surname, "identity_number": result.identity_number, "links": hateoas(user_id)}), HTTPStatus.OK
    except Exception as e:
        return json.dumps('Failed. ' + str(e)), HTTPStatus.NOT_FOUND


@app.route('/v1/users/<user_id>', methods=['DELETE'])
def delete_user_details(user_id):
    try:
        sql = text('DELETE FROM users WHERE id=:id_num')
        result = db.engine.execute(sql, id_num=user_id)
        return json.dumps('Deleted'), HTTPStatus.OK
    except Exception as e:
        return json.dumps('Failed. ' + str(e)), HTTPStatus.NOT_FOUND

@app.route('/v1/users/<user_id>', methods=['PATCH'])
def patch_user_details(user_id):
    data = request.get_json()
    """
    An update query has a portion where you specify which values to  update. Because we are  sending through a variable amount of columns to change, we need to build the clause in the  SQL that states what must change, programmatically
    """
    for key in data:
        update_string = key + '=:' + key + ','
        # Remove the last comma in the update portion
        update_string = update_string[:-1]
    try:
        data['id'] = user_id
        sql = text('UPDATE users SET ' + update_string + ' WHERE id = :id')
        result = db.engine.execute(sql, data)
        return json.dumps(
            {
                "id": user_id,
                "links": hateoas(user_id)
            }
        )
    except Exception as e:
        return json.dumps('Failed. ' + str(e)), HTTPStatus.NOT_FOUND
    
@app.route('/v1/user', methods=['POST'])
def post_user_details_v1():
    try:
        data = request.get_json()
        # Assuming user_schema is defined elsewhere for validation
        # errors = user_schema.validate(data)
        # if errors:
        #     return json.dumps(str(errors)), HTTPStatus.BAD_REQUEST
        sql = text('INSERT INTO users (name, surname, identity_number) values (:name, :surname, :id_num)')
        result = db.engine.execute(sql, name=data['name'], surname=data['surname'], id_num=data['identity_number'])
        return json.dumps('Added'), HTTPStatus.OK
    except Exception as e:
        return json.dumps('Failed to add record. ' + str(e)), HTTPStatus.NOT_FOUND
    
        