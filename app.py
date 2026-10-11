from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'corex_solutions_secret_key_2026'

# Upload folder configuration for media files
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'webm', 'ogg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Supabase Database Configuration
SUPABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres.zlquamdyrewvwjbnalpz:Corex.10.10.@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres'
)

# Helper function to get PostgreSQL connection
def get_db_connection():
    connection = psycopg2.connect(SUPABASE_URL, cursor_factory=RealDictCursor)
    return connection

# Database tables setup and default data insertion
def setup_database():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Admins table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            )
        ''')
        
        # Contact table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contact (
                id INT PRIMARY KEY,
                phone VARCHAR(50),
                whatsapp VARCHAR(50),
                email VARCHAR(100),
                address TEXT
            )
        ''')
        
        # Posts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                media_file VARCHAR(255),
                media_type VARCHAR(50)
            )
        ''')
        
        # Default admin if not exists
        cursor.execute('SELECT * FROM admins WHERE username = %s', ('admin',))
        if not cursor.fetchone():
            hashed_pw = generate_password_hash('password123')
            cursor.execute('INSERT INTO admins (username, password) VALUES (%s, %s)', ('admin', hashed_pw))
            
        # Default contact details if not exists
        cursor.execute('SELECT * FROM contact WHERE id = 1')
        if not cursor.fetchone():
            cursor.execute('INSERT INTO contact (id, phone, whatsapp, email, address) VALUES (1, %s, %s, %s, %s)', 
                           ('+94 7X XXX XXXX', '+94 7X XXX XXXX', 'support@corex.com', 'Sri Lanka'))
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database Connection Error: {e}")

setup_database()

# 1. Home / Root Page Route
@app.route('/')
def home():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contact WHERE id = 1')
    contact = cursor.fetchone()
    cursor.execute('SELECT * FROM posts ORDER BY id DESC')
    posts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', contact=contact, posts=posts)

# 2. Services Route
@app.route('/services')
def services():
    return home()

@app.route('/services/pos')
def pos_service():
    return render_template('pos_service.html', title="POS Systems")

@app.route('/services/custom-software')
def custom_software_service():
    return render_template('custom_software.html', title="Custom Software")

@app.route('/services/company-solutions')
def company_solutions_service():
    return render_template('company_solutions.html', title="Company Solutions")

# 3. Contact Route
@app.route('/contact')
def contact():
    return home()

# 3.1 Dedicated Announcements Page Route
@app.route('/announcements')
def announcements():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contact WHERE id = 1')
    contact = cursor.fetchone()
    cursor.execute('SELECT * FROM posts ORDER BY id DESC')
    posts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('announcements.html', contact=contact, posts=posts)

# 4. Admin Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admins WHERE username = %s', (username,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if admin and admin['password'] == password:
            session['admin_logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid username or password!"
            
    return render_template('login.html', error=error)

# 5. Admin Dashboard Route
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    error = None
    success = None
    current_username = session.get('username')
    
    if request.method == 'POST':
        action = request.form.get('action')
        cursor = conn.cursor()
        try:
            if action == 'add_post':
                title = request.form.get('title')
                content = request.form.get('content')
                file = request.files.get('media_file')
                
                media_filename = None
                media_type = None
                
                if file and file.filename != '':
                    if allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        media_filename = filename
                        
                        ext = filename.rsplit('.', 1)[1].lower()
                        if ext in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
                            media_type = 'image'
                        elif ext in {'mp4', 'webm', 'ogg'}:
                            media_type = 'video'
                    else:
                        error = "Invalid file extension!"
                
                if title and content and not error:
                    cursor.execute('INSERT INTO posts (title, content, media_file, media_type) VALUES (%s, %s, %s, %s)', 
                                   (title, content, media_filename, media_type))
                    conn.commit()
                    success = "Post published successfully!"
            
            elif action == 'delete_post':
                post_id = request.form.get('post_id')
                cursor.execute('SELECT media_file FROM posts WHERE id = %s', (post_id,))
                post_to_delete = cursor.fetchone()
                if post_to_delete and post_to_delete['media_file']:
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], post_to_delete['media_file'])
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                cursor.execute('DELETE FROM posts WHERE id = %s', (post_id,))
                conn.commit()
                success = "Post deleted successfully!"

            elif action == 'update_contact':
                phone = request.form.get('phone')
                whatsapp = request.form.get('whatsapp')
                email = request.form.get('email')
                address = request.form.get('address')
                cursor.execute('UPDATE contact SET phone = %s, whatsapp = %s, email = %s, address = %s WHERE id = 1', 
                               (phone, whatsapp, email, address))
                conn.commit()
                success = "Contact information updated successfully!"
            
            elif action == 'update_admin':
                new_username = request.form.get('new_username')
                new_password = request.form.get('new_password')
                
                if new_username and new_password:
                    hashed_pw = generate_password_hash(new_password)
                    try:
                        cursor.execute('UPDATE admins SET username = %s, password = %s WHERE username = %s', 
                                       (new_username, hashed_pw, current_username))
                        conn.commit()
                        session['username'] = new_username
                        success = "Admin credentials updated successfully!"
                    except Exception:
                        conn.rollback()
                        error = "Username already exists or update failed!"
        finally:
            cursor.close()
            
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contact WHERE id = 1')
    contact = cursor.fetchone()
    cursor.execute('SELECT * FROM posts ORDER BY id DESC')
    posts = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('admin_dashboard.html', contact=contact, posts=posts, error=error, success=success)

# 6. Add New Admin Route
@app.route('/add-admin', methods=['GET', 'POST'])
def add_admin():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username and password:
            hashed_pw = generate_password_hash(password)
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('INSERT INTO admins (username, password) VALUES (%s, %s)', (username, hashed_pw))
                conn.commit()
                cursor.close()
                conn.close()
                return redirect(url_for('login'))
            except Exception:
                error = "Username already exists!"
                
    return render_template('add_admin.html', error=error)

# 7. Logout Route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)