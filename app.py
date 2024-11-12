from flask import Flask, render_template, request, redirect, url_for
import calendar
from datetime import datetime
import sqlite3

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    # Add login logic here
    return f"Logged in with email: {email}"

@app.route('/forgot-password')
def forgot_password():
    return "Forgot Password Page (To be implemented)"

@app.route('/signup')
def signup():
    return "Signup Page (To be implemented)"

@app.route('/feed')
def feed():
    return render_template('feed.html')

@app.route('/calendar')
def default_calendar():
    # Redirect to the current month and year for a general calendar
    today = datetime.today()
    return redirect(url_for('calendar_view', year=today.year, month=today.month))

@app.route('/calendar/<int:year>/<int:month>')
def calendar_view(year, month):
    # Generate a calendar without resource-specific reservations
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)
    return render_template('calendar.html', month_days=month_days, year=year, month=month, reservations={})

@app.route('/calendar/<int:year>/<int:month>/<int:resource_id>')
def calendar_view_with_resource(year, month, resource_id):
    conn = sqlite3.connect('test.db')
    reservations_query = """
        SELECT start_date, end_date FROM Reservations
        WHERE resource_id = ?
    """
    reservations = conn.execute(reservations_query, (resource_id,)).fetchall()
    conn.close()

    reserved_dates = []
    for reservation in reservations:
        reserved_dates.extend(generate_date_range(reservation[0], reservation[1]))

    # Generate calendar and highlight reserved dates
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)
    return render_template(
        'calendar.html', 
        month_days=month_days, 
        year=year, 
        month=month, 
        reservations=reserved_dates
    )

@app.route('/add-resource', methods=['GET', 'POST'])
def add_resource():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        owner_id = 1  # Replace with logged-in user ID
        availability = 'available'
        # Insert resource into the database
        query = """
            INSERT INTO Resources (title, description, owner_id, category, availability)
            VALUES (?, ?, ?, ?, ?)
        """
        conn = sqlite3.connect('test.db')
        conn.execute(query, (title, description, owner_id, category, availability))
        conn.commit()
        conn.close()
        return redirect('/resources')  # Redirect to resource listing page
    return render_template('add_resource.html')

@app.route('/resources', methods=['GET'])
def resources():
    query = request.args.get('query')  # Get search query
    category = request.args.get('category')  # Get category filter
    conn = sqlite3.connect('test.db')
    sql_query = "SELECT * FROM Resources WHERE 1=1"
    params = []
    if query:
        sql_query += " AND title LIKE ?"
        params.append(f"%{query}%")
    if category:
        sql_query += " AND category = ?"
        params.append(category)
    resources = conn.execute(sql_query, params).fetchall()
    conn.close()
    return render_template('resources.html', resources=resources)

@app.route('/reserve/<int:resource_id>', methods=['POST'])
def reserve(resource_id):
    user_id = 1  # Replace with logged-in user ID
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    
    # Check for conflicts
    conn = sqlite3.connect('test.db')
    conflict_query = """
        SELECT * FROM Reservations
        WHERE resource_id = ?
          AND end_date >= ?
          AND start_date <= ?
    """
    conflicts = conn.execute(conflict_query, (resource_id, start_date, end_date)).fetchall()
    if conflicts:
        return "Conflict with an existing reservation.", 400

    # Add reservation to the database
    insert_query = """
        INSERT INTO Reservations (resource_id, user_id, start_date, end_date)
        VALUES (?, ?, ?, ?)
    """
    conn.execute(insert_query, (resource_id, user_id, start_date, end_date))
    conn.commit()
    conn.close()
    return redirect('/calendar')  # Redirect to the calendar page

def generate_date_range(start_date, end_date):
    """Generate a list of dates between start_date and end_date."""
    from datetime import timedelta
    date_list = []
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    while current_date <= end_date:
        date_list.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    return date_list

if __name__ == '__main__':
    app.run(debug=True)


