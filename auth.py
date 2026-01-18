from flask import Blueprint, request, session, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection
import mysql.connector

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = generate_password_hash(request.form['password'])
    role = request.form['role']

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,%s)",
            (name, email, password, role)
        )
        db.commit()
        flash("Registration successful. Please login.", "success")
        return redirect('/login')

    except mysql.connector.errors.IntegrityError:
        flash("Email already exists.", "error")
        return redirect('/register')


@auth.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if user and check_password_hash(user['password'], password):
        session.clear()
        session['user_id'] = user['id']
        session['role'] = user['role']
        flash("Welcome back!", "success")
        return redirect('/jobs')

    flash("Invalid email or password.", "error")
    return redirect('/login')


@auth.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect('/login')
