from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3, os, random
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from config import Config
from datetime import datetime
from ai.chatbot import search_notices
import openpyxl

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

EXCEL_FILE = 'list.xlsx'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# ---------------- DB CONNECTION ----------------
def get_db_connection():
    conn = sqlite3.connect('noticeboard.db', timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- INIT DATABASE ----------------
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # ✅ FIXED: inside function
    try:
        cur.execute("ALTER TABLE students ADD COLUMN last_login TEXT")
    except:
        pass

    cur.execute('''
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rollno TEXT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        password TEXT,
        status TEXT DEFAULT 'active',
        department TEXT,
        year TEXT,
        division TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS notices(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        body TEXT,
        filename TEXT,
        date TEXT,
        department TEXT,
        year TEXT,
        division TEXT,
        target_type TEXT,
        target_id INTEGER
    )
    ''')

    # Create Admin
    cur.execute("SELECT * FROM students WHERE email='admin@college.com'")
    if not cur.fetchone():
        cur.execute("""
        INSERT INTO students
        (name,email,password,status,department,year,division)
        VALUES (?,?,?,?,?,?,?)
        """, (
            'Admin',
            'admin@college.com',
            generate_password_hash('admin123'),
            'active',
            'ADMIN','ADMIN','ADMIN'
        ))

    conn.commit()
    conn.close()

init_db()


# ---------------- NORMALIZE ----------------
def normalize(value):
    return str(value).strip().lower()


# ---------------- EXCEL VALIDATION ----------------
def validate_student_from_excel(email, department, year, division):
    if not os.path.exists(EXCEL_FILE):
        return False

    wb = openpyxl.load_workbook(EXCEL_FILE)
    sheet = wb.active

    email = normalize(email)
    department = normalize(department)
    year = normalize(year)
    division = normalize(division)

    for row in sheet.iter_rows(min_row=2, values_only=True):
        if not row or len(row) < 6:
            continue

        rollno, name, e, dept, yr, div = row

        if (
            normalize(e) == email and
            normalize(dept) == department and
            normalize(yr) == year and
            normalize(div) == division
        ):
            return True

    return False


# ---------------- EMAIL FUNCTION ----------------
def send_email(to, subject, body, filename=None):
    try:
        msg = MIMEMultipart()
        msg['From'] = Config.MAIL_USERNAME
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        if filename:
            path = os.path.join(UPLOAD_FOLDER, filename)
            with open(path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={filename}')
            msg.attach(part)

        with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
            server.starttls()
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.send_message(msg)

    except Exception as e:
        print("Email error:", e)


# ---------------- HOME ----------------
@app.route('/')
def index():
    return render_template('index.html')


# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email'].lower()
        phone = request.form['phone']
        password = generate_password_hash(request.form['password'])
        department = request.form['department']
        year = request.form['year']
        division = request.form['division']

        if not validate_student_from_excel(email, department, year, division):
            flash("Unauthorized signup! Details not found in Excel.", "danger")
            return redirect(url_for('signup'))

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
            INSERT INTO students
            (name,department,year,division,email,phone,password,status)
            VALUES (?,?,?,?,?,?,?,'active')
            """,(
                name, department, year, division,
                email, phone, password
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Email already registered", "danger")
            conn.close()
            return redirect(url_for('signup'))

        conn.close()
        flash("Signup successful. Please login.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        conn = get_db_connection()
        cur = conn.cursor()

        email = request.form['email'].lower()
        password = request.form['password']

        cur.execute("SELECT * FROM students WHERE email=?", (email,))
        user = cur.fetchone()

        if user and check_password_hash(user['password'], password):

            # update last login
            cur.execute("UPDATE students SET last_login=? WHERE id=?",
                        (datetime.now().strftime("%d %b %Y %I:%M %p"), user['id']))
            conn.commit()

            if email == "admin@college.com":
                session.clear()
                session['admin'] = True
                conn.close()
                return redirect(url_for('admin_dashboard'))

            session.clear()
            session['student_id'] = user['id']
            session['student_name'] = user['name']

            conn.close()
            return redirect(url_for('student_notices'))

        conn.close()
        flash("Invalid login", "danger")

    return render_template('login.html')



# ---------------- STUDENT NOTICES ----------------
@app.route('/notices')
def student_notices():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT department,year,division FROM students WHERE id=?",
                (session['student_id'],))
    dept, year, div = cur.fetchone()

    cur.execute("""
    SELECT title, body, filename, date
    FROM notices
    WHERE
        target_type='all'
        OR (target_type='student' AND target_id=?)
        OR (department LIKE ? AND year LIKE ? AND division LIKE ?)
    ORDER BY id DESC
    """,(
        session['student_id'],
        f"%{dept}%",
        f"%{year}%",
        f"%{div}%"
    ))

    notices = cur.fetchall()
    conn.close()

    return render_template('notices.html', notices=notices)


# ---------------- FORGOT PASSWORD ----------------
# ---------------- FORGOT PASSWORD (OTP SEND) ----------------
@app.route('/forgot_password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].lower()

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM students WHERE email=?", (email,))
        user = cur.fetchone()
        conn.close()

        if user:
            otp = random.randint(100000, 999999)
            session['otp'] = str(otp)
            session['otp_email'] = email

            send_email(
                email,
                "Password Reset OTP - eNoticeBoard",
                f"Your OTP for password reset is: {otp}"
            )

            flash("OTP sent to your email", "success")
            return redirect(url_for('reset_password'))
        else:
            flash("Email not registered", "danger")

    return render_template('forgot_password.html')


# ---------------- RESET PASSWORD ----------------
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'otp' not in session or 'otp_email' not in session:
        flash("Please request OTP first", "danger")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        entered_otp = request.form['otp']
        new_password = generate_password_hash(request.form['new_password'])

        if str(session['otp']) == entered_otp:
            email = session['otp_email']
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE students SET password=? WHERE email=?",
                        (new_password, email))
            conn.commit()
            conn.close()

            session.pop('otp', None)
            session.pop('otp_email', None)

            flash("Password reset successfully.", "success")
            return redirect(url_for('login'))
        else:
            flash("Invalid OTP.", "danger")

    return render_template('reset_password.html')


# ---------------- ADMIN LOGIN ----------------
@app.route('/admin_login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE email=?", (email,))
        admin = cur.fetchone()
        conn.close()

        # Check email is admin + password match
        if admin and email == "admin@college.com" and check_password_hash(admin[5], password):
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))

        flash("Invalid admin login", "danger")

    return render_template('admin_login.html')


# ---------------- ADD NOTICE (MULTI TARGET) ----------------
@app.route('/add_notice', methods=['POST'])
def add_notice():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    file = request.files.get('file')
    filename = None

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    departments = request.form.getlist('department')
    years = request.form.getlist('year')
    divisions = request.form.getlist('division')
    target_type = request.form['target_type']
    student_id = request.form.get('student_id')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO notices
    (title,body,filename,date,department,year,division,target_type,target_id)
    VALUES (?,?,?,?,?,?,?,?,?)
    """,(
        request.form['title'],
        request.form['description'],
        filename,
        datetime.now().strftime("%d %b %Y, %I:%M %p"),
        ",".join(departments),
        ",".join(years),
        ",".join(divisions),
        target_type,
        student_id
    ))

    # Email selection
    if target_type == 'student' and student_id:
        cur.execute("SELECT email FROM students WHERE id=?", (student_id,))
    else:
        query = "SELECT email FROM students WHERE status='active'"
        conditions = []
        params = []

        if departments:
            conditions.append("department IN ({})".format(",".join("?"*len(departments))))
            params.extend(departments)

        if years:
            conditions.append("year IN ({})".format(",".join("?"*len(years))))
            params.extend(years)

        if divisions:
            conditions.append("division IN ({})".format(",".join("?"*len(divisions))))
            params.extend(divisions)

        if conditions:
            query += " AND " + " AND ".join(conditions)

        cur.execute(query, params)

    emails = cur.fetchall()
    conn.commit()
    conn.close()

    for e in emails:
        send_email(e[0],
                   f"New Notice: {request.form['title']}",
                   request.form['description'],
                   filename)

    flash("Notice sent successfully","success")
    return redirect(url_for('admin_dashboard'))


@app.route('/delete_notice/<int:notice_id>')
def delete_notice(notice_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM notices WHERE id=?", (notice_id,))
    conn.commit()
    conn.close()

    flash("Notice deleted successfully", "success")
    return redirect(url_for('admin_dashboard'))    

@app.route('/edit_notice/<int:notice_id>', methods=['GET', 'POST'])
def edit_notice(notice_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # GET: show existing data
    if request.method == 'GET':
        cur.execute("SELECT * FROM notices WHERE id=?", (notice_id,))
        notice = cur.fetchone()
        conn.close()
        return render_template('edit_notice.html', notice=notice)

    # POST: update notice
    title = request.form['title']
    description = request.form['description']

    cur.execute("""
        UPDATE notices
        SET title=?, body=?
        WHERE id=?
    """, (title, description, notice_id))

    conn.commit()
    conn.close()

    flash("Notice updated successfully", "success")
    return redirect(url_for('admin_dashboard'))

# ---------------- admin dashboard ----------------

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM students WHERE email != ?", ("admin@college.com",))
    students = cur.fetchall()

    cur.execute("SELECT * FROM notices ORDER BY id DESC")
    notices = cur.fetchall()

    conn.close()

    return render_template('admin_dashboard.html', students=students, notices=notices)

#----------------ai---------------

@app.route('/ai_chat', methods=['GET', 'POST'])
def ai_chat():

    if 'student_id' not in session:
        return redirect(url_for('login'))

    answer = None
    results = []

    if request.method == 'POST':

        question = request.form['question']

        results = search_notices(question)

        if results:

            best_score, best_notice = results[0]

            answer = (
                f"Based on the available notices, "
                f"the most relevant notice is: "
                f"{best_notice['title']}"
            )

        else:
            answer = "Sorry, I could not find any relevant notice."

    return render_template(
        'ai_chat.html',
        answer=answer,
        results=results
    )
    
    
# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
