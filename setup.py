import sqlite3
import hashlib

def setup_database():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('smart_neighborhood_exchange.db')
    cursor = conn.cursor()
    
    # Create Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        profile_image TEXT,
        location TEXT
    )
    ''')
    
    # Create Resources Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Resources (
        resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        images TEXT,
        category TEXT,
        availability TEXT,
        date_posted TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES Users (user_id)
    )
    ''')
    
    # Create Messages Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Messages (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        content TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (sender_id) REFERENCES Users (user_id),
        FOREIGN KEY (receiver_id) REFERENCES Users (user_id)
    )
    ''')

    # Create Reviews Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Reviews (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        reviewer_id INTEGER,
        rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
        comment TEXT,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES Users (user_id),
        FOREIGN KEY (reviewer_id) REFERENCES Users (user_id)
    )
    ''')

    # Create Reservations Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Reservations (
        reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES Users(user_id),
        FOREIGN KEY (item_id) REFERENCES Resources(resource_id) ON DELETE CASCADE
    )
    ''')

    # Create Community Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Community (
        community_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        images TEXT,
        location TEXT,
        availability TEXT,
        date_posted TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES Users(user_id)
    )
    ''')
    
    # Commit and close connection
    conn.commit()
    conn.close()
    print("Database setup complete.")

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(name, email, password, profile_image=None, location=None):
    """Registers a new user in the database."""
    conn = sqlite3.connect('smart_neighborhood_exchange.db')
    cursor = conn.cursor()
    
    try:
        # Hash the password before storing it
        hashed_password = hash_password(password)
        
        # Insert user data into Users table
        cursor.execute('''
        INSERT INTO Users (name, email, password, profile_image, location)
        VALUES (?, ?, ?, ?, ?)
        ''', (name, email, hashed_password, profile_image, location))
        
        # Commit the transaction
        conn.commit()
        print("User registered successfully.")
        
    except sqlite3.IntegrityError:
        print("Error: A user with that email already exists.")
    
    finally:
        # Close the database connection
        conn.close()

if __name__ == '__main__':
    setup_database()
    # Example user registration
    register_user("John Doe", "john@example.com", "password123", "john_profile.jpg", "New York")
