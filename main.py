
#IMPORT PACKAGES AND IMPORT DATABASE
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management
conn = sqlite3.connect('railway.db', check_same_thread=False)
c = conn.cursor()


def create_DB_if_Not_available():
    # Create a table to store user information
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    # Create a table to store employee information
    c.execute('''CREATE TABLE IF NOT EXISTS employees (employee_id TEXT, password TEXT, designation TEXT)''')
    # Create a table to store train details
    c.execute('''CREATE TABLE IF NOT EXISTS trains (train_number TEXT, train_name TEXT, departure_date TEXT, starting_destination TEXT, ending_destination TEXT)''')
    conn.commit()

def add_train(train_number, train_name, departure_date, starting_destination, ending_destination):
    c.execute("INSERT INTO trains (train_number, train_name, departure_date, starting_destination, ending_destination) VALUES (?, ?, ?, ?, ?)",
              (train_number, train_name, departure_date, starting_destination, ending_destination))
    conn.commit()
    create_seat_table(train_number)

# def delete_train(train_number, departure_date):
#     train_query = c.execute("SELECT * FROM trains WHERE train_number = ?", (train_number,))
#     train_data = train_query.fetchone()
#     if train_data:
#         c.execute("DELETE FROM trains WHERE train_number = ? AND departure_date=?", (train_number, departure_date))
#         conn.commit()
#         flash(f"Train with Train Number {train_number} has been deleted.")
#     else:
#         flash(f"No such Train with Number {train_number} is available")

def create_seat_table(train_number):
    c.execute(f'''
        CREATE TABLE IF NOT EXISTS seats_{train_number} (
            seat_number INTEGER PRIMARY KEY,
            seat_type TEXT,
            booked INTEGER,
            passenger_name TEXT,
            passenger_age INTEGER,
            passenger_gender TEXT
        )
    ''')
    for i in range(1, 51):
        val = categorize_seat(i)
        c.execute(f'''INSERT INTO seats_{train_number}(seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender) VALUES (?,?,?,?,?,?);''', (
            i, val, 0, "", "", ""))
    conn.commit()

def categorize_seat(seat_number):
    if (seat_number % 10) in [0, 4, 5, 9]:
        return "Window"
    elif (seat_number % 10) in [2, 3, 6, 7]:
        return "Aisle"
    else:
        return "Middle"

def allocate_next_available_seat(train_number, seat_type):
    seat_query = c.execute(f"SELECT seat_number FROM seats_{train_number} WHERE booked=0 and seat_type=? ORDER BY seat_number asc", (seat_type,))
    result = seat_query.fetchall()
    if result:
        return result[0][0]
    return None

# def book_ticket(train_number, passenger_name, passenger_age, passenger_gender, seat_type):
#     train_query = c.execute("SELECT * FROM trains WHERE train_number = ?", (train_number,))
#     train_data = train_query.fetchone()
#     if train_data:
#         seat_number = allocate_next_available_seat(train_number, seat_type)
#         if seat_number:
#             c.execute(f"UPDATE seats_{train_number} SET booked=1, seat_type=?, passenger_name=?, passenger_age=?, passenger_gender=? WHERE seat_number=?", (
#                 seat_type, passenger_name, passenger_age, passenger_gender, seat_number))
#             conn.commit()
#             flash(f"Successfully booked seat {seat_number} ({seat_type}) for {passenger_name}.")
#         else:
#             flash("No available seats for booking in this train.")
#     else:
#         flash(f"No such Train with Number {train_number} is available")

# def cancel_tickets(train_number, seat_number):
#     train_query = c.execute("SELECT * FROM trains WHERE train_number = ?", (train_number,))
#     train_data = train_query.fetchone()
#     if train_data:
#         c.execute(f'''UPDATE seats_{train_number} SET booked=0, passenger_name='', passenger_age='', passenger_gender='' WHERE seat_number=?''', (seat_number,))
#         conn.commit()
#         flash(f"Successfully canceled seat {seat_number} from {train_number}.")
#     else:
#         flash(f"No such Train with Number {train_number} is available")

def search_train_by_train_number(train_number):
    train_query = c.execute("SELECT * FROM trains WHERE train_number = ?", (train_number,))
    train_data = train_query.fetchone()
    return train_data

def search_trains_by_destinations(starting_destination, ending_destination):
    train_query = c.execute("SELECT * FROM trains WHERE starting_destination = ? AND ending_destination = ?", (starting_destination, ending_destination))
    train_data = train_query.fetchall()
    return train_data

# def view_seats(train_number):
#     train_query = c.execute("SELECT * FROM trains WHERE train_number = ?", (train_number,))
#     train_data = train_query.fetchone()
#     if train_data:
#         seat_query = c.execute(f'''SELECT seat_number, seat_type, passenger_name, passenger_age, passenger_gender, booked FROM seats_{train_number} ORDER BY seat_number asc''')
#         result = seat_query.fetchall()
#         return result
#     else:
#         flash(f"No such Train with Number {train_number} is available")
#         return []

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_query = c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = user_query.fetchone()
        if user:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!')
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        flash('Registration successful! Please log in.')
    except sqlite3.IntegrityError:
        flash('Username already exists!')
    return redirect(url_for('login'))

@app.route('/index')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/add_train', methods=['GET', 'POST'])
def add_train_route():
    if request.method == 'POST':
        train_number = request.form['train_number']
        train_name = request.form['train_name']
        departure_date = request.form['departure_date']
        starting_destination = request.form['starting_destination']
        ending_destination = request.form['ending_destination']
        
        if train_number and train_name and starting_destination and ending_destination:
            add_train(train_number, train_name, departure_date, starting_destination, ending_destination)
            flash("Train Added Successfully!")
            return redirect(url_for('index'))
    return render_template('add_train.html')

@app.route('/view_trains')
def view_trains():
    train_query = c.execute("SELECT * FROM trains")
    trains = train_query.fetchall()
    return render_template('view_trains.html', trains=trains)

@app.route('/search_train', methods=['GET', 'POST'])
def search_train():
    train_data = None
    if request.method == 'POST':
        train_number = request.form.get('train_number')
        starting_destination = request.form.get('starting_destination')
        ending_destination = request.form.get('ending_destination')
            
        print(f"Searching for Train Number: {train_number}")
        print(f"Searching from {starting_destination} to {ending_destination}")

        if train_number:
            train_data = search_train_by_train_number(train_number)
            if train_data:  # Wrap in a list if a single train is found
                train_data = [train_data]
        elif starting_destination and ending_destination:
            train_data = search_trains_by_destinations(starting_destination, ending_destination)
            print(f"Train Data: {train_data}")
            
        return render_template('search_train.html', train_data=train_data)
    return render_template('search_train.html')
@app.route('/book_ticket', methods=['GET', 'POST'])
def book_ticket():
    if request.method == 'POST':
        train_number = request.form['train_number']
        passenger_name = request.form['passenger_name']
        passenger_age = request.form['passenger_age']
        passenger_gender = request.form['passenger_gender']
        seat_type = request.form['seat_type']

        # Check if train exists
        train = search_train_by_train_number(train_number)
        if not train:
            flash("Train not found!")
            return redirect(url_for('book_ticket'))

        # Find available seat of requested type
        seat_number = allocate_next_available_seat(train_number, seat_type)
        
        if not seat_number:
            flash(f"No {seat_type} seats available!")
            return redirect(url_for('book_ticket'))

        # Book the seat
        c.execute(f"""
            UPDATE seats_{train_number} 
            SET booked = 1, 
                passenger_name = ?, 
                passenger_age = ?, 
                passenger_gender = ?
            WHERE seat_number = ?
        """, (passenger_name, passenger_age, passenger_gender, seat_number))
        conn.commit()

        flash(f"Ticket booked successfully! Your seat number is {seat_number}")
        # Instead of redirecting to view_seats, redirect back to index
        return redirect(url_for('index'))

    return render_template('book_ticket.html')

@app.route('/cancel_ticket', methods=['GET', 'POST'])
def cancel_ticket():
    if request.method == 'POST':
        train_number = request.form['train_number']
        seat_number = request.form['seat_number']

        try:
            # Check if the seat is actually booked
            seat_query = c.execute(f"""
                SELECT booked, passenger_name FROM seats_{train_number}
                WHERE seat_number = ?
            """, (seat_number,))
            seat = seat_query.fetchone()

            if not seat:
                flash("Invalid seat number!")
                return redirect(url_for('cancel_ticket'))

            if not seat[0]:  # if not booked
                flash("This seat is not booked!")
                return redirect(url_for('cancel_ticket'))

            # Cancel the ticket
            c.execute(f"""
                UPDATE seats_{train_number}
                SET booked = 0,
                    passenger_name = NULL,
                    passenger_age = NULL,
                    passenger_gender = NULL
                WHERE seat_number = ?
            """, (seat_number,))
            conn.commit()

            flash(f"Ticket cancelled successfully for seat {seat_number}!")
            return redirect(url_for('view_seats'))

        except sqlite3.OperationalError:
            flash(f"Train {train_number} not found!")
            return redirect(url_for('cancel_ticket'))

    return render_template('cancel_ticket.html')
@app.route('/view_seats', methods=['GET', 'POST'])
def view_seats():
    seats = None
    train_number = None
    
    if request.method == 'POST':
        train_number = request.form['train_number']
        
        try:
            # Get all seats for the train
            seats_query = c.execute(f"""
                SELECT seat_number, seat_type, passenger_name, 
                       passenger_age, passenger_gender, booked 
                FROM seats_{train_number}
                ORDER BY seat_number
            """)
            seats = seats_query.fetchall()
            
            if not seats:
                flash(f"No seats found for train {train_number}")
            
        except sqlite3.OperationalError:
            flash(f"Train {train_number} not found!")
            return redirect(url_for('view_seats'))

    return render_template('view_seats.html', seats=seats, train_number=train_number)

@app.route('/delete_train/<train_number>')
def delete_train(train_number):
    # Delete associated seats first (foreign key constraint)
    c.execute("DELETE FROM seats WHERE train_number = ?", (train_number,))
    
    # Then delete the train
    c.execute("DELETE FROM trains WHERE train_number = ?", (train_number,))
    conn.commit()
    
    flash("Train deleted successfully!")
    return redirect(url_for('view_trains'))

# ... other routes for delete_train, book_ticket, cancel_tickets, view_seats ...

if __name__ == '__main__':
    create_DB_if_Not_available()  # Ensure DB is created
    app.run(debug=True)