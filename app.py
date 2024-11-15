import datetime
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.utils import secure_filename
from math import ceil


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management

# Configuration for file uploads
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create the upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('smart_neighborhood_exchange.db')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key support
    return conn

# Route for user signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']  # Store as plain text temporarily

        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO Users (name, email, password) VALUES (?, ?, ?)',
                (name, email, password)
            )
            conn.commit()
            flash("Signup successful! You can now log in.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already exists. Please use a different email.", "error")
        finally:
            conn.close()

    return render_template('signup.html')

# Route for user login
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Users WHERE email = ? AND password = ?', (email, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))  # Redirect to dashboard after login
        else:
            flash("Invalid email or password.", "error")

    return render_template('login.html')

# Route for user logout
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# Route for dashboard
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.", "error")
        return redirect(url_for('login'))

    # Fetch some community feed or other data to show on the dashboard
    conn = get_db_connection()
    community_feed = conn.execute(
        "SELECT * FROM Community ORDER BY date_posted DESC LIMIT 5"
    ).fetchall()
    resources_feed = conn.execute(
        "SELECT * FROM Resources ORDER BY date_posted DESC LIMIT 5"
    ).fetchall()
    conn.close()

    return render_template('dashboard.html', community_feed=community_feed, resources_feed=resources_feed)

# Route for resources page with search functionality
@app.route('/resources')
def resources():
    conn = get_db_connection()
    search_query = request.args.get('search', '')
    if search_query:
        resources = conn.execute(
            "SELECT * FROM Resources WHERE title LIKE ? OR category LIKE ?",
            ('%' + search_query + '%', '%' + search_query + '%')
        ).fetchall()
    else:
        resources = conn.execute("SELECT * FROM Resources").fetchall()
    conn.close()
    return render_template('resources.html', resources=resources)

# Route for adding a new resource
@app.route('/add_resource', methods=['GET', 'POST'])
def add_resource():
    if 'user_id' not in session:
        flash("Please log in to list a resource.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        availability = 'available'
        date_posted = datetime.datetime.now().strftime('%Y-%m-%d')
        user_id = session['user_id']

        image_filename = None
        if 'images' in request.files:
            images = request.files['images']
            if images and allowed_file(images.filename):
                image_filename = f"images/{secure_filename(images.filename)}"
                images.save(os.path.join('static', image_filename))

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO Resources (title, description, category, availability, date_posted, user_id, images) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (title, description, category, availability, date_posted, user_id, image_filename)
        )
        conn.commit()
        conn.close()
        flash("Resource listed successfully!", "success")
        return redirect(url_for('resources'))

    return render_template('add_resource.html')

# Route for community events page
@app.route('/community_events', methods=['GET'])
def community_events():
    conn = get_db_connection()
    search_query = request.args.get('search', '')
    if search_query:
        community_entries = conn.execute(
            "SELECT * FROM Community WHERE title LIKE ? OR location LIKE ?",
            ('%' + search_query + '%', '%' + search_query + '%')
        ).fetchall()
    else:
        community_entries = conn.execute("SELECT * FROM Community ORDER BY date_posted DESC").fetchall()
    conn.close()
    return render_template('community_events.html', community_entries=community_entries)

# Route for creating a new community event or space
@app.route('/community/create', methods=['GET', 'POST'])
def create_community():
    if 'user_id' not in session:
        flash("Please log in to create a community space.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        location = request.form['location']
        availability = 'available'
        date_posted = datetime.datetime.now().strftime('%Y-%m-%d')
        user_id = session['user_id']

        image_filename = None
        if 'images' in request.files:
            images = request.files['images']
            if images and allowed_file(images.filename):
                image_filename = f"images/{secure_filename(images.filename)}"
                images.save(os.path.join('static', image_filename))

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO Community (user_id, title, description, images, location, availability, date_posted)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, title, description, image_filename, location, availability, date_posted))
        conn.commit()
        conn.close()

        flash("Community space created successfully!", "success")
        return redirect(url_for('community_events'))

    return render_template('create_community.html')

# Route to render the list item page
@app.route('/list_item', methods=['GET'])
def list_item():
    return render_template('list_item.html')

# Route for rent item page
@app.route('/rent_item', methods=['GET'])
def rent_item():
    conn = get_db_connection()
    # Fetch all resources and community spaces
    resources = conn.execute("SELECT * FROM Resources").fetchall()
    community_spaces = conn.execute("SELECT * FROM Community").fetchall()
    conn.close()
    return render_template('rent_item.html', resources=resources, community_spaces=community_spaces)


# Route to show details for a specific item
@app.route('/item/<int:item_id>', methods=['GET'])
def item_details(item_id):
    conn = get_db_connection()

    # Fetch the item details (resource or community space)
    resource = conn.execute("SELECT * FROM Resources WHERE resource_id = ?", (item_id,)).fetchone()
    community_space = conn.execute("SELECT * FROM Community WHERE community_id = ?", (item_id,)).fetchone()
    if resource:
        item = resource
        item_type = 'resource'
    elif community_space:
        item = community_space
        item_type = 'community'
    else:
        conn.close()
        return "Item not found", 404

    # Fetch the owner details
    owner = conn.execute("SELECT * FROM Users WHERE user_id = ?", (item['user_id'],)).fetchone()
    if not owner:
        owner = {"name": "Unknown", "location": "Unknown", "user_id": None}

    # Fetch reviews
    reviews = conn.execute("SELECT * FROM Reviews WHERE user_id = ?", (owner['user_id'],)).fetchall()
    average_rating = conn.execute("SELECT AVG(rating) FROM Reviews WHERE user_id = ?", (owner['user_id'],)).fetchone()[0]

    # Fetch reservations for this item
    reservations = conn.execute("SELECT * FROM Reservations WHERE item_id = ?", (item_id,)).fetchall()
    user_reserved = any(reservation['user_id'] == session.get('user_id') for reservation in reservations)

    conn.close()

    return render_template(
        'item_details.html',
        item=item,
        item_type=item_type,
        owner=owner,
        reviews=reviews,
        average_rating=average_rating,
        reservations=reservations,
        user_reserved=user_reserved
    )


# Route to send a message to the owner
@app.route('/send_message/<int:receiver_id>', methods=['POST'])
def send_message(receiver_id):
    if 'user_id' not in session:
        flash("Please log in to send a message.", "error")
        return redirect(url_for('login'))

    sender_id = session['user_id']
    content = request.form['message_content']
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO Messages (sender_id, receiver_id, content, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (sender_id, receiver_id, content, timestamp))
    conn.commit()
    conn.close()
    flash("Message sent successfully!", "success")
    return redirect(url_for('item_details', item_id=receiver_id))

# Route to reserve an item
# @app.route('/reserve_item/<int:item_id>', methods=['POST'])
# def reserve_item(item_id):
#     if 'user_id' not in session:
#         flash("Please log in to reserve an item.", "error")
#         return redirect(url_for('login'))

#     # Check for start_date and end_date in the form
#     start_date = request.form.get('start_date')
#     end_date = request.form.get('end_date')

#     if not start_date or not end_date:
#         flash("Invalid reservation dates. Please try again.", "error")
#         return redirect(url_for('item_details', item_id=item_id))

#     user_id = session['user_id']

#     conn = get_db_connection()
#     conn.execute('''
#         INSERT INTO Reservations (item_id, user_id, start_date, end_date)
#         VALUES (?, ?, ?, ?)
#     ''', (item_id, user_id, start_date, end_date))
#     conn.commit()
#     conn.close()

#     flash(f"Item reserved successfully from {start_date} to {end_date}!", "success")
#     return redirect(url_for('item_details', item_id=item_id))

#   Route to handle reservation
@app.route('/reserve/<int:item_id>', methods=['POST'])
def reserve_item(item_id):
    if 'user_id' not in session:
        flash("Please log in to reserve an item.", "error")
        return redirect(url_for('login'))

    user_id = session['user_id']
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    conn = get_db_connection()
    try:
        # Check if the item is already reserved during the selected date range
        conflicts = conn.execute('''
            SELECT * FROM Reservations
            WHERE item_id = ? AND (
                (start_date <= ? AND end_date >= ?) OR
                (start_date <= ? AND end_date >= ?) OR
                (start_date >= ? AND end_date <= ?)
            )
        ''', (item_id, start_date, start_date, end_date, end_date, start_date, end_date)).fetchall()

        if conflicts:
            flash("The selected dates are unavailable. Please choose a different range.", "error")
            return redirect(url_for('item_details', item_id=item_id))

        # Insert the reservation if no conflicts exist
        conn.execute(
            "INSERT INTO Reservations (user_id, item_id, start_date, end_date) VALUES (?, ?, ?, ?)",
            (user_id, item_id, start_date, end_date)
        )

        # Mark the item as unavailable
        if conn.execute("SELECT * FROM Resources WHERE resource_id = ?", (item_id,)).fetchone():
            conn.execute("UPDATE Resources SET availability = 'unavailable' WHERE resource_id = ?", (item_id,))
        elif conn.execute("SELECT * FROM Community WHERE community_id = ?", (item_id,)).fetchone():
            conn.execute("UPDATE Community SET availability = 'unavailable' WHERE community_id = ?", (item_id,))

        conn.commit()
        flash("Item reserved successfully!", "success")
    except Exception as e:
        flash(f"Error reserving item: {str(e)}", "error")
    finally:
        conn.close()

    return redirect(url_for('reserved_items'))


#   Route for displaying reserved items
@app.route('/reserved_items', methods=['GET'])
def reserved_items():
    if 'user_id' not in session:
        flash("Please log in to view reserved items.", "error")
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    reserved_items = conn.execute('''
        SELECT r.reservation_id, r.start_date, r.end_date, i.title, i.images
        FROM Reservations r
        JOIN Resources i ON r.item_id = i.resource_id
        WHERE r.user_id = ?
    ''', (user_id,)).fetchall()
    conn.close()

    return render_template('reserved_items.html', reserved_items=reserved_items)

#   Route for cancelling reservations

@app.route('/cancel_reservation/<int:reservation_id>', methods=['POST'])
def cancel_reservation(reservation_id):
    if 'user_id' not in session:
        flash("Please log in to cancel a reservation.", "error")
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM Reservations WHERE reservation_id = ?", (reservation_id,))
        conn.commit()
        flash("Reservation canceled successfully!", "success")
    except Exception as e:
        flash(f"Error canceling reservation: {str(e)}", "error")
    finally:
        conn.close()

    return redirect(url_for('reserved_items'))

#  New route to fetch reserved dates dynamically 
@app.route('/fetch_reserved_dates/<int:item_id>', methods=['GET'])
def fetch_reserved_dates(item_id):
    conn = get_db_connection()
    reserved_dates = conn.execute('''
        SELECT start_date, end_date FROM Reservations WHERE item_id = ?
    ''', (item_id,)).fetchall()
    conn.close()

    return jsonify([{"start": row["start_date"], "end": row["end_date"]} for row in reserved_dates])

@app.route('/messages', methods=['GET'])
def messages():
    if 'user_id' not in session:
        flash("Please log in to view your messages.", "error")
        return redirect(url_for('login'))
    logged_in_user_id = session['user_id']
    conn = get_db_connection()
    # Fetch conversations with last message
    conversations = conn.execute('''
        SELECT u.user_id, u.name,
               (SELECT content FROM Messages m
                WHERE (m.sender_id = u.user_id AND m.receiver_id = ?)
                   OR (m.receiver_id = u.user_id AND m.sender_id = ?)
                ORDER BY timestamp DESC
                LIMIT 1) as last_message
        FROM Users u
        JOIN Messages m
          ON (u.user_id = m.sender_id AND m.receiver_id = ?)
          OR (u.user_id = m.receiver_id AND m.sender_id = ?)
        WHERE u.user_id != ?
        GROUP BY u.user_id, u.name
    ''', (logged_in_user_id, logged_in_user_id, logged_in_user_id, logged_in_user_id, logged_in_user_id)).fetchall()
    conn.close()
    # Transform conversations to list of dicts
    conversations = [{'user_id': conv['user_id'], 'name': conv['name'], 'last_message': conv['last_message']} for conv in conversations]
    return render_template('messages.html', conversations=conversations, recipient=None, messages=[])


@app.route('/start_conversation', methods=['GET', 'POST'])
def start_conversation():
    if 'user_id' not in session:
        flash("Please log in to start a conversation.", "error")
        return redirect(url_for('login'))
    logged_in_user_id = session['user_id']
    conn = get_db_connection()
    # Fetch all users except the logged-in user
    users = conn.execute('''
        SELECT user_id, name
        FROM Users
        WHERE user_id != ?
    ''', (logged_in_user_id,)).fetchall()
    conn.close()
    if request.method == 'POST':
        selected_user_id = request.form['selected_user']
        return redirect(url_for('chat', user_id=selected_user_id))
    return render_template('start_conversation.html', users=users)
@app.route('/chat/<int:user_id>', methods=['GET', 'POST'])
def chat(user_id):
    if 'user_id' not in session:
        flash("Please log in to chat.", "error")
        return redirect(url_for('login'))
    logged_in_user_id = session['user_id']
    conn = get_db_connection()
    # Handle sending a message
    if request.method == 'POST':
        content = request.form['message_content']
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute('''
            INSERT INTO Messages (sender_id, receiver_id, content, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (logged_in_user_id, user_id, content, timestamp))
        conn.commit()
        flash("Message sent successfully!", "success")
    # Fetch all messages between the logged-in user and the selected user
    messages = conn.execute('''
        SELECT *
        FROM Messages
        WHERE (sender_id = ? AND receiver_id = ?)
           OR (sender_id = ? AND receiver_id = ?)
        ORDER BY timestamp ASC
    ''', (logged_in_user_id, user_id, user_id, logged_in_user_id)).fetchall()
    # Fetch the recipient's details
    recipient = conn.execute('SELECT * FROM Users WHERE user_id = ?', (user_id,)).fetchone()
    # Fetch conversations with last message
    conversations = conn.execute('''
        SELECT u.user_id, u.name,
               (SELECT content FROM Messages m
                WHERE (m.sender_id = u.user_id AND m.receiver_id = ?)
                   OR (m.receiver_id = u.user_id AND m.sender_id = ?)
                ORDER BY timestamp DESC
                LIMIT 1) as last_message
        FROM Users u
        JOIN Messages m
          ON (u.user_id = m.sender_id AND m.receiver_id = ?)
          OR (u.user_id = m.receiver_id AND m.sender_id = ?)
        WHERE u.user_id != ?
        GROUP BY u.user_id, u.name
    ''', (logged_in_user_id, logged_in_user_id, logged_in_user_id, logged_in_user_id, logged_in_user_id)).fetchall()
    conn.close()
    # Transform conversations to list of dicts
    conversations = [{'user_id': conv['user_id'], 'name': conv['name'], 'last_message': conv['last_message']} for conv in conversations]

    return render_template('messages.html', conversations=conversations, recipient=recipient, messages=messages)


if __name__ == '__main__':
    app.run(debug=True)
