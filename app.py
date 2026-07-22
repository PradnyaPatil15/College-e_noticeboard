from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3, os, random
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from config import Config
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- Helper: DB Connection ----------
def get_db_connection():
    return sqlite3.connect('noticeboard.db', timeout=10)

# ---------- Initialize Database ----------
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rollno TEXT,
        name TEXT NOT NULL,
        class TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        password TEXT,
        status TEXT DEFAULT 'inactive'
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS notices(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        body TEXT,
        filename TEXT,
        date TEXT
    )''')

    # Default Admin
    cur.execute("SELECT * FROM students WHERE email='admin@college.com'")
    if not cur.fetchone():
        cur.execute("INSERT INTO students(name,class,email,password,phone,status) VALUES (?,?,?,?,?,?)",
                    ('Admin', 'Admin', 'admin@college.com', 'admin123', '0000000000', 'active'))
    conn.commit()
    conn.close()

init_db()

# ---------- Ensure date column exists ----------
def ensure_notice_date_column():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(notices)")
    cols = [r[1] for r in cur.fetchall()]
    if 'date' not in cols:
        try:
            cur.execute("ALTER TABLE notices ADD COLUMN date TEXT")
            conn.commit()
            print("✅ Added 'date' column to notices table.")
        except Exception as e:
            print("❌ Failed to add 'date' column:", e)
    conn.close()

ensure_notice_date_column()

# ---------- Email Function ----------
def send_email(to, subject, body, filename=None):
    try:
        msg = MIMEMultipart()
        msg['From'] = Config.MAIL_USERNAME
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        if filename:
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            with open(filepath, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={filename}")
            msg.attach(part)

        with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
            server.starttls()
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.send_message(msg)
        print(f"✅ Email sent to {to}")
    except Exception as e:
        print(f"❌ Email failed for {to}: {e}")

# ---------- Routes ----------
@app.route('/')
def index():
    return render_template('index.html')

# ---------- Signup ----------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name'].strip().lower()
        cls = request.form['class']
        email = request.form['email'].lower().strip()
        phone = request.form.get('phone', '').strip()
        password = request.form['password']

        excel_path = os.path.join(os.getcwd(), 'list.xlsx')
        if not os.path.exists(excel_path):
            flash("❌ College student database file missing (list.xlsx)", "danger")
            return redirect(url_for('login'))

        df = pd.read_excel(excel_path)
        df.columns = df.columns.str.strip().str.lower()

        if 'name' not in df.columns:
            flash("❌ Invalid Excel format! Must have 'Name' column.", "danger")
            return redirect(url_for('login'))

        matched = df[df['name'].astype(str).str.lower().str.strip() == name]
        if matched.empty:
            flash("🚫 Your name was not found in the college database.", "danger")
            return redirect(url_for('login'))

        rollno = str(matched.iloc[0]['roll no']) if 'roll no' in df.columns else 'N/A'

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE email=? OR phone=?", (email, phone))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE students 
                SET name=?, class=?, password=?, status='active'
                WHERE email=? OR phone=?
            """, (name.title(), cls, password, email, phone))
        else:
            cur.execute("""
                INSERT INTO students(rollno, name, class, email, phone, password, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            """, (rollno, name.title(), cls, email, phone, password))

        conn.commit()
        conn.close()

        flash("✅ Account activated successfully! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

# ---------- Login ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE email=? AND password=?", (email, password))
        user = cur.fetchone()

        if user:
            if user[7] == 'inactive':
                cur.execute("UPDATE students SET status='active' WHERE email=?", (email,))
                conn.commit()

            cur.execute("SELECT * FROM students WHERE email=?", (email,))
            user = cur.fetchone()

            session['student_id'] = user[0]
            session['student_name'] = user[2]

            conn.close()
            return redirect(url_for('student_notices'))
        else:
            conn.close()
            flash("❌ Invalid credentials!", "danger")

    return render_template('login.html')

# ---------- Forgot Password ----------
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].lower()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE email=?", (email,))
        user = cur.fetchone()
        conn.close()

        if user:
            otp = random.randint(100000, 999999)
            session['otp_email'] = email
            session['otp_code'] = otp
            send_email(email, "Password Reset OTP", f"Your OTP for password reset is: {otp}")
            flash("📩 OTP sent to your email!", "success")
            return redirect(url_for('reset_password'))
        else:
            flash("❌ Email not found!", "danger")
    return render_template('forgot_password.html')

# ---------- Reset Password ----------
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        otp_input = request.form.get('otp')
        new_password = request.form.get('new_password')

        if not new_password:
            flash("❌ Please enter a new password.", "danger")
            return redirect(url_for('reset_password'))

        if 'otp_code' in session and int(otp_input) == session['otp_code']:
            email = session['otp_email']
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE students SET password=? WHERE email=?", (new_password, email))
            conn.commit()
            conn.close()

            flash("🔒 Password reset successfully!", "success")
            session.pop('otp_code', None)
            session.pop('otp_email', None)
            return redirect(url_for('login'))
        else:
            flash("❌ Invalid OTP!", "danger")

    return render_template('reset_password.html')

# ---------- Student Notices ----------
@app.route('/notices')
def student_notices():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, body, filename, date FROM notices ORDER BY id DESC")
    notices = cur.fetchall()
    conn.close()
    return render_template('notices.html', notices=notices)

# ---------- Admin Login ----------
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == 'admin@college.com' and password == 'admin123':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials!', 'danger')
    return render_template('admin_login.html')

# ---------- Admin Dashboard ----------
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, class, email, phone 
        FROM students
        WHERE LOWER(TRIM(name)) != 'admin'
        ORDER BY id DESC
    """)
    students = cur.fetchall()

    cur.execute("SELECT id, title, body, filename, date FROM notices ORDER BY id DESC")
    notices = cur.fetchall()

    conn.close()
    return render_template('admin_dashboard.html', students=students, notices=notices)

# ---------- Add Notice ----------
@app.route('/add_notice', methods=['POST'])
def add_notice():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    title = request.form['title']
    description = request.form['description']
    file = request.files['file']
    filename = None

    if file and file.filename != '':
        filename = file.filename
        file.save(os.path.join('static/uploads', filename))

    date_now = datetime.now().strftime("%d %b %Y, %I:%M %p")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO notices (title, body, filename, date) VALUES (?, ?, ?, ?)",
        (title, description, filename, date_now)
    )

    cur.execute("SELECT email FROM students WHERE status='active' AND LOWER(TRIM(name)) != 'admin'")
    students = cur.fetchall()
    conn.commit()
    conn.close()

    for student in students:
        email = student[0]
        send_email(email, f"📢 New Notice: {title}", description, filename)

    flash("📢 Notice added and emailed to all active students successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# ---------- Edit Notice ----------
@app.route('/edit_notice/<int:notice_id>', methods=['GET', 'POST'])
def edit_notice(notice_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files.get('file')
        filename = None

        if file and file.filename != '':
            filename = file.filename
            file.save(os.path.join('static/uploads', filename))
            cur.execute(
                "UPDATE notices SET title=?, body=?, filename=? WHERE id=?",
                (title, description, filename, notice_id)
            )
        else:
            cur.execute(
                "UPDATE notices SET title=?, body=? WHERE id=?",
                (title, description, notice_id)
            )

        conn.commit()
        conn.close()

        flash("📝 Notice updated successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    cur.execute("SELECT * FROM notices WHERE id=?", (notice_id,))
    notice = cur.fetchone()
    conn.close()

    if notice is None:
        flash("⚠️ Notice not found.", "danger")
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_notice.html', notice=notice)

# ---------- Delete Notice ----------
@app.route('/delete_notice/<int:notice_id>')
def delete_notice(notice_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM notices WHERE id=?", (notice_id,))
    conn.commit()
    conn.close()

    flash("🗑️ Notice deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# ---------- Delete Student ----------
@app.route('/delete_student/<int:sid>')
def delete_student(sid):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE id=?", (sid,))
    conn.commit()
    conn.close()
    flash("🗑️ Student record deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# ---------- Logout ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
