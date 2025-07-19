import os
from datetime import datetime
from flask import Flask, request, jsonify, abort, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev")

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///local.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    registration_start = db.Column(db.DateTime, nullable=False)
    registration_end = db.Column(db.DateTime, nullable=False)

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    registrant_name = db.Column(db.String(100), nullable=False)
    registrant_email = db.Column(db.String(120), nullable=False)
    paid = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    event = db.relationship('Event', backref=db.backref('registrations', lazy=True))

@app.route("/")
def home():
    events = Event.query.order_by(Event.registration_start).all()
    return render_template("events.html", events=events)

@app.route("/events/<int:event_id>/register", methods=["GET", "POST"])
def register(event_id):
    event = Event.query.get_or_404(event_id)
    now = datetime.utcnow()
    if not (event.registration_start <= now <= event.registration_end):
        flash("Registration is closed for this event.", "danger")
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        if not name or not email:
            flash("Please enter your name and email.", "warning")
            return render_template("register.html", event=event)

        registration = Registration(
            event_id=event.id,
            registrant_name=name,
            registrant_email=email,
            paid=False
        )
        db.session.add(registration)
        db.session.commit()
        flash("Registration successful!", "success")
        return redirect(url_for("registrations", event_id=event.id))

    return render_template("register.html", event=event)

@app.route("/events/<int:event_id>/registrations")
def registrations(event_id):
    event = Event.query.get_or_404(event_id)
    registrations = Registration.query.filter_by(event_id=event.id).order_by(Registration.timestamp.desc()).all()
    return render_template("registrations.html", event=event, registrations=registrations)

@app.route("/api/events", methods=["GET"])
def api_list_events():
    events = Event.query.all()
    return jsonify(events=[{
        "id": e.id,
        "name": e.name,
        "registration_start": e.registration_start.isoformat(),
        "registration_end": e.registration_end.isoformat()
    } for e in events])

@app.route("/api/events", methods=["POST"])
def api_create_event():
    data = request.json
    if not data:
        abort(400, "Request must be JSON")
    try:
        event = Event(
            name=data["name"],
            registration_start=datetime.fromisoformat(data["registration_start"]),
            registration_end=datetime.fromisoformat(data["registration_end"]),
        )
    except (KeyError, ValueError) as e:
        abort(400, f"Missing or invalid data: {e}")
    db.session.add(event)
    db.session.commit()
    return jsonify(message="Event created", event_id=event.id), 201

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)