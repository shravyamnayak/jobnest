from flask import Flask, render_template, session, redirect
from flask_mail import Mail, Message
from flask_dance.contrib.google import make_google_blueprint, google

from auth import auth
from jobs import jobs
from db import get_db_connection

app = Flask(__name__)
app.secret_key = "dev_secret_key"

# ================= MAIL CONFIG =================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'yourgmail@gmail.com'
app.config['MAIL_PASSWORD'] = 'APP_PASSWORD'

mail = Mail(app)

# ================= GOOGLE OAUTH =================
google_bp = make_google_blueprint(
    client_id="GOOGLE_CLIENT_ID",
    client_secret="GOOGLE_CLIENT_SECRET",
    scope=["profile", "email"]
)
app.register_blueprint(google_bp, url_prefix="/login")

# ================= BLUEPRINTS =================
app.register_blueprint(auth)
app.register_blueprint(jobs)

# ================= ROUTES =================
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/jobs')
    return render_template('home.html')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/register')
def register_page():
    return render_template('register.html')


@app.route('/google-login')
def google_login():
    if not google.authorized:
        return redirect('/login/google')

    resp = google.get("/oauth2/v2/userinfo")
    info = resp.json()

    email = info["email"]
    name = info["name"]

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("""
            INSERT INTO users (name, email, role, is_verified)
            VALUES (%s, %s, 'job_seeker', TRUE)
        """, (name, email))
        db.commit()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

    session.clear()
    session['user_id'] = user['id']
    session['role'] = user['role']

    return redirect('/jobs')


if __name__ == "__main__":
    app.run(debug=True)
