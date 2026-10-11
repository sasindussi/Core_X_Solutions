import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Posts table (Photos, Videos saha captions walata)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            media_file TEXT
        )
    ''')
    
    # Contact details table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            email TEXT,
            address TEXT
        )
    ''')
    
    # Admin table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Default admin user create karamu (Username: admin, Password: password123)
    hashed_pw = generate_password_hash('password123')
    try:
        cursor.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ('admin', hashed_pw))
    except sqlite3.IntegrityError:
        pass # Already exists unoth error eka skip karai
        
    # Default contact info
    cursor.execute("SELECT COUNT(*) FROM contact_info")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO contact_info (phone, email, address) VALUES (?, ?, ?)", 
                       ('+94 77 123 4567', 'info@posproject.lk', 'Colombo, Sri Lanka'))
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()