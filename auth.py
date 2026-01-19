from flask import Blueprint, request, session, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection
import mysql.connector
import uuid

auth = Blueprint('auth', __name__)

# ================= REGISTER =================
@auth.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = generate_password_hash(request.form['password'])
    role = request.form['role']
    token = str(uuid.uuid4())

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (name, email, password, role, verification_token)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, email, password, role, token))
        db.commit()

        # Email sending handled in app.py via Flask-Mail
        flash("Registration successful. Please verify your email.", "success")
        return redirect('/login')

    except mysql.connector.errors.IntegrityError:
        flash("Email already exists.", "error")
        return redirect('/register')


# ================= LOGIN =================
@auth.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if not user or not check_password_hash(user['password'], password):
        flash("Invalid email or password.", "error")
        return redirect('/login')

    if not user['is_verified']:
        flash("Please verify your email before logging in.", "error")
        return redirect('/login')

    session.clear()
    session['user_id'] = user['id']
    session['role'] = user['role']

    flash("Welcome back!", "success")
    return redirect('/jobs')


# ================= EMAIL VERIFY =================
@auth.route('/verify/<token>')
def verify_email(token):
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE verification_token=%s",
        (token,)
    )
    user = cursor.fetchone()

    if not user:
        return "Invalid or expired verification link."

    cursor.execute("""
        UPDATE users
        SET is_verified = TRUE, verification_token = NULL
        WHERE id = %s
    """, (user[0],))
    db.commit()

    flash("Email verified successfully. You can now login.", "success")
    return redirect('/login')


# ================= LOGOUT =================
@auth.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect('/login')
