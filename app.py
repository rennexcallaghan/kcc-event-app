
from flask import Flask, render_template, request, redirect, url_for
from models import db, Event, Field, Registration
from datetime import datetime
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret123'
db.init_app(app)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    today = datetime.today().date()
    events = Event.query.filter(Event.reg_start <= today, Event.reg_end >= today).all()
    return render_template('index.html', events=events)

@app.route('/event/new', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        name = request.form['name']
        reg_start = request.form['reg_start']
        reg_end = request.form['reg_end']
        field_names = request.form.getlist('field_name[]')
        event = Event(name=name, reg_start=reg_start, reg_end=reg_end)
        db.session.add(event)
        db.session.commit()
        for field in field_names:
            db.session.add(Field(event_id=event.id, name=field))
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create_event.html')

@app.route('/event/<int:event_id>/register', methods=['GET', 'POST'])
def register(event_id):
    event = Event.query.get_or_404(event_id)
    fields = Field.query.filter_by(event_id=event.id).all()
    if request.method == 'POST':
        data = {field.name: request.form.get(field.name) for field in fields}
        registration = Registration(event_id=event.id, data=json.dumps(data), paid=False)
        db.session.add(registration)
        db.session.commit()
        return "Registration submitted!"
    return render_template('register.html', event=event, fields=fields)

@app.route('/event/<int:event_id>/registrations')
def view_registrations(event_id):
    event = Event.query.get_or_404(event_id)
    registrations = Registration.query.filter_by(event_id=event.id).all()
    fields = Field.query.filter_by(event_id=event.id).all()
    return render_template('view_registrations.html', event=event, fields=fields, registrations=registrations)

@app.route('/payment/<int:reg_id>/toggle')
def toggle_payment(reg_id):
    reg = Registration.query.get_or_404(reg_id)
    reg.paid = not reg.paid
    db.session.commit()
    return redirect(url_for('view_registrations', event_id=reg.event_id))

if __name__ == '__main__':
    app.run(debug=True)
