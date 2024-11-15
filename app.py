import datetime
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.utils import secure_filename

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
    resources = conn.execute("SELECT * FROM Resources WHERE availability = 'available'").fetchall()
    community_spaces = conn.execute("SELECT * FROM Community WHERE availability = 'available'").fetchall()
    conn.close()
    return render_template('rent_item.html', resources=resources, community_spaces=community_spaces)

# Route to show details for a specific item
@app.route('/item/<int:item_id>', methods=['GET'])
def item_details(item_id):
    conn = get_db_connection()
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

    owner = conn.execute("SELECT * FROM Users WHERE user_id = ?", (item['user_id'],)).fetchone()
    if not owner:
        owner = {"name": "Unknown", "location": "Unknown", "user_id": None}

    reviews = conn.execute("SELECT * FROM Reviews WHERE user_id = ?", (owner['user_id'],)).fetchall()
    average_rating = conn.execute("SELECT AVG(rating) FROM Reviews WHERE user_id = ?", (owner['user_id'],)).fetchone()[0]
    conn.close()
    return render_template('item_details.html', item=item, item_type=item_type, owner=owner, reviews=reviews, average_rating=average_rating)

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
@app.route('/reserve_item/<int:item_id>', methods=['POST'])
def reserve_item(item_id):
    if 'user_id' not in session:
        flash("Please log in to reserve an item.", "error")
        return redirect(url_for('login'))

    reservation_date = request.form['reservation_date']
    user_id = session['user_id']

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO Reservations (item_id, user_id, reservation_date)
        VALUES (?, ?, ?)
    ''', (item_id, user_id, reservation_date))
    conn.commit()
    conn.close()

    flash(f"Item reserved successfully for {reservation_date}!", "success")
    return redirect(url_for('item_details', item_id=item_id))


if __name__ == '__main__':
    app.run(debug=True)
