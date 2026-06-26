from flask import Flask
from models import db, User

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():

    users = User.query.all()

    print("\n===== USERS IN DATABASE =====\n")

    for user in users:
        print(
            f"ID: {user.id} | "
            f"Email: {user.email} | "
            f"Credits: {user.credits}"
        )

    print("\n=============================\n")