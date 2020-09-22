from flask import jsonify
import json
import traceback
from flask_bcrypt import check_password_hash
from UserMicroservice.user_db import UserAccess

db_access = UserAccess()


class UserAction:
    def __init__(self, app):
        self.app = app

    def signup(self, data):
        # Get data from AJAX request

        email = data['email']
        password = data['password']
        name = data['name']

        message, status_code = db_access.create_user(email=email,
                                                     password=password,
                                                     name=name)

        return message, status_code

    def login(self, data):
        try:
            email = data['email']
            password = data['password']

            # Find user
            user = db_access.get_user(email=email)

            return self._check_user_data(user, password, email)
        except Exception as ex:
            stacktrace = traceback.format_exc()
            print(stacktrace)
            return json.dumps({'message': 'Erreur inconnue, nous nous excusons'}), 500

    def get_user_by_user_id(self, user_id):
        user = db_access.get_user(id=user_id, as_dict=True)

        if user is not None:
            return jsonify(user), 200
        else:
            return json.dumps({'message': 'L''utilisateur n''a pas été trouvé'}), 401

    def get_user_by_email(self, email):
        user = db_access.get_user(email=email, as_dict=True)

        if user is not None:
            return jsonify(user), 200
        else:
            return json.dumps({'message': 'L''utilisateur n''a pas été trouvé'}), 401

    def _check_user_data(self, user, password, email):
        # If user exists, check if email and password matches
        if user is not None:
            check_pw = check_password_hash(user.password_hash, password)
            if user.email == email and check_pw:
                return json.dumps({'message': '/dashboard'}), 200
            else:
                return json.dumps({'message': 'Données utilisateur incorrectes'}), 401
        else:
            return json.dumps({'message': 'Email non enregistré'}), 401
