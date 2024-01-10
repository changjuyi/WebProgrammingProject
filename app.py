#connect
#check login 
#guest info
#admin page

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField,SelectField, PasswordField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text

app = Flask(__name__,static_folder="static", static_url_path="/")
app.config['SECRET_KEY'] = '1234'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost/my_hotel'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

rooms = [
 ('101', 'Single Room'),
 ('102', 'Double Room'),
 ('103', 'Deluxe Room'),
 ('104', 'Homeymoon Suit')
]

class Login(db.Model):
    login_id = db.Column(db.Integer, primary_key=True)
    login_name = db.Column(db.String(255), nullable=False)
    login_password = db.Column(db.String(255), nullable=False)
    #order_id = db.Column(db.Integer, db.ForeignKey('booking.booking_id'))

class LoginForm(FlaskForm):
    username = StringField('User Name', validators=[DataRequired()])
    passwd = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class Room(db.Model):
    room_number = db.Column(db.String(10), primary_key=True)
    room_type = db.Column(db.String(50))
    price_per_night = db.Column(db.Integer)
    max_guests = db.Column(db.Integer) 

class Guest(db.Model):
    guest_id = db.Column(db.Integer, primary_key=True)
    guest_name = db.Column(db.String(255), nullable=False)
    contact_info = db.Column(db.String(255))

class Booking(db.Model):
    booking_id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.guest_id'), nullable=False)
    room_number = db.Column(db.Integer, db.ForeignKey('room.room_number'), nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)

class BookingForm(FlaskForm):
    guest_name = StringField('Guest Name', validators=[DataRequired()])
    room_number = SelectField('Room Number', choices=rooms,validators=[DataRequired()])
    check_in_date = DateField('Check-In Date', format='%Y-%m-%d',validators=[DataRequired()])
    check_out_date = DateField('Check-Out Date', format='%Y-%m-%d', validators=[DataRequired()])
    contact_info = StringField('Contact Information', validators=[DataRequired()])
    submit = SubmitField('Book Now')


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == "admin" and form.passwd.data == "admin":
            return redirect(url_for('admin'))
        else:
            #check if username exist, yes=>check passwd , no=>add new login
            login_data = db.session.execute(text('SELECT login_name, login_passwd FROM login where login_name=:username'),
                {'username': form.username.data}
            ).fetchone()

            if login_data:
                if form.passwd.data == login_data[1]:
                    #print(form.passwd.data)
                    #print(login_data[1])
                    return render_template("home.html")
                else:
                    flash("wrong password")
                    return redirect(url_for('login'))
            else:
                new_login = Login(login_name = form.username.data, login_password = form.passwd.data)
                db.session.add(new_login)
                db.session.flush()
                db.session.commit()
                return redirect(url_for('login'))

    return render_template("login.html", form=form)

@app.route('/admin', methods=['GET','POST'])
def admin():
    #show order,delete order
    if request.method == 'POST':
        # Handle delete action
        booking_id_to_delete = request.form.get('delete_booking_id')
        print(booking_id_to_delete)
        db.session.execute(text('DELETE from booking where booking_id=:delete_id'),{'delete_id': int(booking_id_to_delete)})
        data = db.session.execute(text('SELECT guest_name, room_type, check_in_date, check_out_date, contact_info, booking_id FROM booking FULL JOIN guest ON booking.guest_id = guest.guest_id FULL JOIN room ON booking.room_number = room.room_number WHERE booking.room_number IS NOT NULL'))
        db.session.commit()
        print("Booking deleted successfully.")
        print(data)
        return render_template("admin.html", data=data)
    
    
    data = db.session.execute(text('SELECT guest_name, room_type, check_in_date, check_out_date, contact_info, (check_out_date - check_in_date)*price_per_night AS total_price, booking_id FROM booking FULL JOIN guest ON booking.guest_id = guest.guest_id FULL JOIN room ON booking.room_number = room.room_number WHERE booking.room_number IS NOT NULL'))
    print(data)
    return render_template("admin.html", data=data)

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    form = BookingForm()
    if form.validate_on_submit():
        if form.check_in_date.data > form.check_out_date.data:
            flash('Error: Check-in date cannot be later than check-out date', 'error')
            return render_template('booking.html', form=form)
        new_guest = Guest(guest_name=form.guest_name.data, contact_info=form.contact_info.data)
        db.session.add(new_guest)
        db.session.flush() # Flush to get the ID of the new guest
        new_booking = Booking(
            guest_id = new_guest.guest_id,
            room_number = form.room_number.data,
            check_in_date = form.check_in_date.data,
            check_out_date = form.check_out_date.data
        )
        db.session.add(new_booking)
        db.session.commit()
        return redirect(url_for('confirm'))
    
    return render_template('booking.html', form=form)

@app.route('/confirm', methods=['GET', 'POST'])
def confirm():
    
    booking_data = db.session.execute(text('SELECT guest_name, room_type,check_in_date, check_out_date, contact_info, (check_out_date - check_in_date)*price_per_night AS total_price FROM booking  FULL JOIN guest ON booking.guest_id = guest.guest_id FULL JOIN room ON booking.room_number = room.room_number WHERE booking.room_number IS NOT NULL ORDER BY booking_id DESC LIMIT 1'))      
    return render_template('confirm.html', data = booking_data)

@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    return render_template("contact.html")

@app.route('/gallery', methods=['GET', 'POST'])
def gallery():
    return render_template("gallery.html")

@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template("about.html")

@app.route('/accomodation', methods=['GET', 'POST'])
def accomodation():
    return render_template("accomodation.html")

@app.route('/contact_form_submit', methods=['POST'])
def contact_form_submit():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        # Now you can process the form data as needed (e.g., send emails, save to database, etc.)

        # For now, let's just print the data
        print(f"Name: {name}, Email: {email}, Subject: {subject}, Message: {message}")

        # You might want to add a flash message or a redirect here after processing the form

    return render_template("contact.html")
@app.route('/singleroom', methods=['GET', 'POST'])
def singleroom():
    return render_template("singleroom.html")

@app.route('/doubleroom', methods=['GET', 'POST'])
def doubleroom():
    return render_template("doubleroom.html")

@app.route('/deluxeroom', methods=['GET', 'POST'])
def deluxeroom():
    return render_template("deluxeroom.html")

@app.route('/honeymoon', methods=['GET', 'POST'])
def honeymoon():
    return render_template("honeymoon.html")
if __name__ == '__main__':
    app.run(debug=True)

