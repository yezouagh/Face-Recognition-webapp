from flask_bcrypt import generate_password_hash
import json
from sqlalchemy.exc import IntegrityError
import traceback

from setup_app import db
from UserMicroservice.user import User


class UserAccess:

    def __init__(self):
        self.db = db
        self.User = User

    def get_user(self, id=None, email=None, as_dict=False):
        if id is not None:
            user = self.User.query.filter_by(id=id).first()
        elif email is not None:
            user = self.User.query.filter_by(email=email).first()

        if as_dict:
            return self.User.as_dict(user)
        else:
            return user

    def create_user(self, email, password, name):
        try:
            # Hash the password (store only the hash)
            pw_hash = generate_password_hash(password, 10)

            # Save user in database
            new_user = self.User(name=name, email=email, password_hash=pw_hash)

            # Take the row spot
            self.db.session.add(new_user)
            self.db.session.flush()

            # Commit changes
            self.db.session.commit()

            return json.dumps({'message': '/login_page'}), 200
        except IntegrityError as ex:
            stacktrace = traceback.format_exc()
            print(stacktrace)
            self.db.session.rollback()
            return json.dumps({'message': 'Email déjà enregistré'}), 403
        except Exception as ex:
            stacktrace = traceback.format_exc()
            print(stacktrace)
            return json.dumps({'message': 'Un problème est survenu'}), 401
