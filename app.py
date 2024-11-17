import datetime
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.utils import secure_filename
from math import ceil
import hashlib 
import smtplib  # For sending email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import json
import datetime
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management



NOTIFICATIONS_FILE = 'notifications.json'

def add_notification_to_json(user_id, message):
    """Adds a notification to the JSON file."""
    try:
        with open(NOTIFICATIONS_FILE, 'r') as file:
            notifications = json.load(file)
    except FileNotFoundError:
        notifications = {}

    # Ensure user ID exists in notifications
    if str(user_id) not in notifications:
        notifications[str(user_id)] = []

    # Add the notification
    notifications[str(user_id)].append({
        'message': message,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'is_read': False
    })

    # Save the updated notifications
    with open(NOTIFICATIONS_FILE, 'w') as file:
        json.dump(notifications, file, indent=4)

def mark_notifications_as_read(user_id):
    """Marks all notifications for a user as read."""
    try:
        with open(NOTIFICATIONS_FILE, 'r') as file:
            notifications = json.load(file)

        # Mark all notifications as read for the user
        if str(user_id) in notifications:
            for notification in notifications[str(user_id)]:
                notification['is_read'] = True

        # Save updated notifications
        with open(NOTIFICATIONS_FILE, 'w') as file:
            json.dump(notifications, file, indent=4)

    except FileNotFoundError:
        pass

def get_notifications_from_json(user_id):
    """Fetch notifications for a specific user from the JSON file."""
    try:
        with open(NOTIFICATIONS_FILE, 'r') as file:
            notifications = json.load(file)
        return notifications.get(str(user_id), [])
    except FileNotFoundError:
        return []

NOTIFICATIONS_FILE = 'notifications.json'

def add_notification_to_json(user_id, message):
    """Adds a notification to a JSON file."""
    try:
        with open(NOTIFICATIONS_FILE, 'r') as file:
            notifications = json.load(file)
    except FileNotFoundError:
        notifications = {}

    if str(user_id) not in notifications:
        notifications[str(user_id)] = []

    notifications[str(user_id)].append({
        'message': message,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'is_read': False
    })

    with open(NOTIFICATIONS_FILE, 'w') as file:
        json.dump(notifications, file, indent=4)

def get_notifications_from_json(user_id):
    """Fetches notifications for a specific user from a JSON file."""
    try:
        with open(NOTIFICATIONS_FILE, 'r') as file:
            notifications = json.load(file)
        return notifications.get(str(user_id), [])
    except FileNotFoundError:
        return []




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
 # Use hashlib for hashing passwords

# Route for user signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        location = request.form['location']  # Fetch location from the form

        # Hash the password
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

        # Handle profile image
        profile_image = None
        if 'profile_image' in request.files:
            image_file = request.files['profile_image']
            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                profile_image = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(profile_image)

        # Insert data into the database
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO Users (name, email, password, location, profile_image) VALUES (?, ?, ?, ?, ?)',
                (name, email, hashed_password, location, profile_image)
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
        password = request.form['password']  # Get the plain-text password from the form

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user:
            # Hash the input password
            hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

            # Compare the stored hash with the hashed input
            if user['password'] == hashed_password:
                session['user_id'] = user['user_id']
                session['user_name'] = user['name']
                flash("Login successful!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid email or password.", "error")
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

    user_id = session['user_id']

    conn = get_db_connection()

    # Fetch top-rated users
    top_rated_users = conn.execute(
        """
        SELECT user_id, name, profile_image, 
               (SELECT AVG(rating) FROM Reviews WHERE user_id = u.user_id) AS rating
        FROM Users u
        ORDER BY rating DESC
        LIMIT 4
        """
    ).fetchall()

    # Fetch most recent listings
    recent_listings = conn.execute(
        """
        SELECT resource_id, title, images, category, date_posted
        FROM Resources
        ORDER BY date_posted DESC
        LIMIT 4
        """
    ).fetchall()

    conn.close()

    # Fetch notifications for the user
    notifications = get_notifications_from_json(user_id)

    return render_template(
        'dashboard.html',
        top_rated_users=top_rated_users,
        recent_listings=recent_listings,
        notifications=notifications
    )


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

#update reservation
@app.route('/update_reservation/<int:reservation_id>', methods=['GET'])
def update_reservation(reservation_id):
    if 'user_id' not in session:
        flash("Please log in to update a reservation.", "error")
        return redirect(url_for('login'))

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        flash("Both 'From' and 'To' dates are required to update the reservation.", "error")
        return redirect(url_for('reserved_items'))

    user_id = session['user_id']

    conn = get_db_connection()
    try:
        # Fetch the current reservation to get the item ID
        reservation = conn.execute("SELECT * FROM Reservations WHERE reservation_id = ?", (reservation_id,)).fetchone()
        if not reservation or reservation['user_id'] != user_id:
            flash("Invalid reservation.", "error")
            return redirect(url_for('reserved_items'))

        item_id = reservation['item_id']

        # Check for conflicting reservations during the updated date range
        conflicts = conn.execute('''
            SELECT * FROM Reservations
            WHERE item_id = ? AND reservation_id != ? AND (
                (start_date <= ? AND end_date >= ?) OR
                (start_date <= ? AND end_date >= ?) OR
                (start_date >= ? AND end_date <= ?)
            )
        ''', (item_id, reservation_id, start_date, start_date, end_date, end_date, start_date, end_date)).fetchall()

        if conflicts:
            flash("The selected dates are unavailable. Please choose a different range.", "error")
            return redirect(url_for('reserved_items'))

        # Update the reservation dates in the database
        conn.execute('''
            UPDATE Reservations
            SET start_date = ?, end_date = ?
            WHERE reservation_id = ?
        ''', (start_date, end_date, reservation_id))
        conn.commit()

        flash("Reservation updated successfully!", "success")
    except Exception as e:
        flash(f"An error occurred while updating the reservation: {e}", "error")
    finally:
        conn.close()

    return redirect(url_for('reserved_items'))



# Route to show details for a specific item
@app.route('/item/<int:item_id>', methods=['GET'])
def item_details(item_id):
    # Retrieve item_type from the query parameter
    item_type = request.args.get('item_type')
    
    conn = get_db_connection()

    # Fetch the item details based on item_type
    if item_type == 'resource':
        item = conn.execute("SELECT * FROM Resources WHERE resource_id = ?", (item_id,)).fetchone()
    elif item_type == 'community':
        item = conn.execute("SELECT * FROM Community WHERE community_id = ?", (item_id,)).fetchone()
    else:
        conn.close()
        flash("Invalid item type specified.", "error")
        return redirect(url_for('rent_item'))

    # If item is not found
    if not item:
        conn.close()
        flash("Item not found. Please check the ID and try again.", "error")
        return redirect(url_for('rent_item'))

    # Fetch the owner details
    owner = conn.execute("SELECT * FROM Users WHERE user_id = ?", (item['user_id'],)).fetchone()
    if not owner:
        owner = {"name": "Unknown", "location": "Unknown", "user_id": None}

    # Fetch reviews associated with the owner
    reviews = conn.execute("SELECT * FROM Reviews WHERE owner_id = ?", (owner['user_id'],)).fetchall()
    average_rating = conn.execute("SELECT AVG(rating) FROM Reviews WHERE owner_id = ?", (owner['user_id'],)).fetchone()
    average_rating = average_rating[0] if average_rating[0] else None

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
        # Check for conflicts
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

        # Insert the reservation
        conn.execute(
            "INSERT INTO Reservations (user_id, item_id, start_date, end_date) VALUES (?, ?, ?, ?)",
            (user_id, item_id, start_date, end_date)
        )

        # Fetch the resource and notify the owner
        resource = conn.execute("SELECT * FROM Resources WHERE resource_id = ?", (item_id,)).fetchone()
        if resource:
            owner_id = resource['user_id']
            message = f"Your resource '{resource['title']}' has been reserved from {start_date} to {end_date}."
            add_notification_to_json(owner_id, message)

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

    # Fetch reserved resources and community spaces with their type
    reserved_resources = conn.execute('''
        SELECT r.reservation_id, r.start_date, r.end_date, res.title, res.images, 'resource' AS item_type
        FROM Reservations r
        JOIN Resources res ON r.item_id = res.resource_id
        WHERE r.user_id = ?
    ''', (user_id,)).fetchall()

    reserved_communities = conn.execute('''
        SELECT r.reservation_id, r.start_date, r.end_date, com.title, com.images, 'community' AS item_type
        FROM Reservations r
        JOIN Community com ON r.item_id = com.community_id
        WHERE r.user_id = ?
    ''', (user_id,)).fetchall()

    # Combine both resources and communities into one list
    reserved_items = reserved_resources + reserved_communities

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

#   Reviews 
@app.route('/submit_review/<int:owner_id>', methods=['POST'])
def submit_review(owner_id):
    if 'user_id' not in session:
        flash("Please log in to submit a review.", "error")
        return redirect(url_for('login'))
    
    # Get the form data
    rating = request.form.get('rating')
    review_comment = request.form.get('review_comment')
    user_id = session['user_id']
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if not rating or not review_comment:
        flash("Please provide both a rating and a review comment.", "error")
        return redirect(request.referrer)

    conn = get_db_connection()
    try:
        # Save the review in the Reviews table
        conn.execute('''
            INSERT INTO Reviews (user_id, owner_id, rating, comment, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, owner_id, rating, review_comment, timestamp))
        conn.commit()
        flash("Your review has been submitted successfully!", "success")
    except Exception as e:
        flash(f"An error occurred while submitting your review: {str(e)}", "error")
    finally:
        conn.close()

    return redirect(request.referrer)  # Redirect back to the item details page


@app.route('/profile', methods=['GET'])
def profile():
    if 'user_id' not in session:
        flash("Please log in to access your profile.", "error")
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM Users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()

    return render_template('profile.html', user=user)

# Delete a resource 
@app.route('/delete_resource/<int:resource_id>', methods=['POST'])
def delete_resource(resource_id):
    if 'user_id' not in session:
        flash("Please log in to delete a resource.", "error")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    try:
        # Ensure only the owner can delete the resource
        resource = conn.execute("SELECT * FROM Resources WHERE resource_id = ? AND user_id = ?", (resource_id, user_id)).fetchone()
        if not resource:
            flash("You are not authorized to delete this resource.", "error")
            return redirect(url_for('my_listings'))

        conn.execute("DELETE FROM Resources WHERE resource_id = ?", (resource_id,))
        conn.commit()
        flash("Resource deleted successfully!", "success")
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
    finally:
        conn.close()

    return redirect(url_for('my_listings'))

# Deleting community events 
@app.route('/delete_community/<int:community_id>', methods=['POST'])
def delete_community(community_id):
    if 'user_id' not in session:
        flash("Please log in to delete a community event.", "error")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    try:
        # Ensure only the owner can delete the community event
        community = conn.execute("SELECT * FROM Community WHERE community_id = ? AND user_id = ?", (community_id, user_id)).fetchone()
        if not community:
            flash("You are not authorized to delete this community event.", "error")
            return redirect(url_for('my_listings'))

        conn.execute("DELETE FROM Community WHERE community_id = ?", (community_id,))
        conn.commit()
        flash("Community event deleted successfully!", "success")
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
    finally:
        conn.close()

    return redirect(url_for('my_listings'))

# route for updating a resource 
@app.route('/edit_resource/<int:resource_id>', methods=['GET', 'POST'])
def edit_resource(resource_id):
    if 'user_id' not in session:
        flash("Please log in to edit a resource.", "error")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    resource = conn.execute("SELECT * FROM Resources WHERE resource_id = ? AND user_id = ?", (resource_id, user_id)).fetchone()

    if not resource:
        flash("You are not authorized to edit this resource.", "error")
        return redirect(url_for('my_listings'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        availability = request.form['availability']
        
        conn.execute('''
            UPDATE Resources 
            SET title = ?, description = ?, category = ?, availability = ?
            WHERE resource_id = ? AND user_id = ?
        ''', (title, description, category, availability, resource_id, user_id))
        conn.commit()
        conn.close()
        flash("Resource updated successfully!", "success")
        return redirect(url_for('my_listings'))

    conn.close()
    return render_template('edit_resource.html', resource=resource)

# Route for updating a community
@app.route('/edit_community/<int:community_id>', methods=['GET', 'POST'])
def edit_community(community_id):
    if 'user_id' not in session:
        flash("Please log in to edit a community event.", "error")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    community = conn.execute("SELECT * FROM Community WHERE community_id = ? AND user_id = ?", (community_id, user_id)).fetchone()

    if not community:
        flash("You are not authorized to edit this community event.", "error")
        return redirect(url_for('my_listings'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        location = request.form['location']
        availability = request.form['availability']
        
        conn.execute('''
            UPDATE Community 
            SET title = ?, description = ?, location = ?, availability = ?
            WHERE community_id = ? AND user_id = ?
        ''', (title, description, location, availability, community_id, user_id))
        conn.commit()
        conn.close()
        flash("Community event updated successfully!", "success")
        return redirect(url_for('my_listings'))

    conn.close()
    return render_template('edit_community.html', community=community)

# functionality for my_listings
@app.route('/my_listings', methods=['GET', 'POST'])
def my_listings():
    if 'user_id' not in session:
        flash("Please log in to view your listings.", "error")
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    # Fetch resources and community events created by the logged-in user
    resources = conn.execute("SELECT * FROM Resources WHERE user_id = ?", (user_id,)).fetchall()
    community_events = conn.execute("SELECT * FROM Community WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()

    return render_template('my_listings.html', resources=resources, community_events=community_events)

# organize event confirmation
@app.route('/organize_event/<int:community_id>', methods=['GET', 'POST'])
def organize_event(community_id):
    if 'user_id' not in session:
        flash("Please log in to organize an event.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        event_name = request.form['event_name']
        event_details = request.form['event_details']
        event_date = request.form['event_date']
        event_time = request.form['event_time']

        conn = get_db_connection()
        try:
            # Save the event details in the database
            conn.execute('''
                INSERT INTO Events (community_id, event_name, event_details, event_date, event_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (community_id, event_name, event_details, event_date, event_time))
            conn.commit()
        except Exception as e:
            flash(f"Failed to create event: {str(e)}", "error")
        finally:
            conn.close()

        # Show success message and redirect to dashboard
        return '''
        <script>
            alert('Event created successfully!');
            window.location.href = '/dashboard';
        </script>
        '''

    return render_template('organize_event.html', community_id=community_id)

@app.route('/edit_profile', methods=['POST'])
def edit_profile():
    if 'user_id' not in session:
        flash("Please log in to edit your profile.", "error")
        return redirect(url_for('login'))

    user_id = session['user_id']
    name = request.form['name']
    email = request.form['email']
    location = request.form['location']

    # Handle profile image upload
    profile_image = None
    if 'profile_image' in request.files:
        image_file = request.files['profile_image']
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            profile_image = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(profile_image)

    conn = get_db_connection()
    try:
        # Check if the email is already in use by another user
        existing_email_user = conn.execute(
            "SELECT * FROM Users WHERE email = ? AND user_id != ?",
            (email, user_id)
        ).fetchone()

        if existing_email_user:
            flash("This email is already in use by another user. Please choose a different email.", "error")
            return redirect(url_for('profile'))

        # Update the user's profile
        if profile_image:
            conn.execute(
                '''
                UPDATE Users 
                SET name = ?, email = ?, location = ?, profile_image = ?
                WHERE user_id = ?
                ''',
                (name, email, location, profile_image, user_id)
            )
        else:
            conn.execute(
                '''
                UPDATE Users 
                SET name = ?, email = ?, location = ?
                WHERE user_id = ?
                ''',
                (name, email, location, user_id)
            )

        conn.commit()
        flash("Profile updated successfully!", "success")
    except Exception as e:
        flash(f"An error occurred while updating your profile: {str(e)}", "error")
    finally:
        conn.close()

    return redirect(url_for('profile'))


                



if __name__ == '__main__':
    app.run(debug=True)
