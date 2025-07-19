
import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# SQLite-only configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///local.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)

@app.route("/")
def index():
    return jsonify(message="Welcome to your Flask + SQLite app!")

@app.route("/add-user/<username>")
def add_user(username):
    if User.query.filter_by(username=username).first():
        return jsonify(message="User already exists."), 409

    new_user = User(username=username)
    db.session.add(new_user)
    db.session.commit()
    return jsonify(message=f"User '{username}' added.")

@app.route("/users")
def list_users():
    users = User.query.all()
    return jsonify(users=[u.username for u in users])

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
