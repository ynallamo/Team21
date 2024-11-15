import sqlite3

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

    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS Reservations (
    #     reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     item_id INTEGER NOT NULL,
    #     user_id INTEGER NOT NULL,
    #     start_date DATE NOT NULL,
    #     end_date DATE NOT NULL,
    #     FOREIGN KEY (item_id) REFERENCES Resources (resource_id),
    #     FOREIGN KEY (user_id) REFERENCES Users (user_id)
    # )
    # ''')

    cursor.execute('''
CREATE TABLE IF NOT EXISTS Community (
    community_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    images TEXT,
    location TEXT,  -- Changed from category to location
    availability TEXT,
    date_posted TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
)
''')
    
    # Commit and close connection
    conn.commit()
    conn.close()
    print("Database setup complete.")

if __name__ == '__main__':
    setup_database()
