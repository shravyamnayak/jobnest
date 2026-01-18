from flask import Blueprint, request, render_template, redirect, session, flash
from db import get_db_connection
import mysql.connector

jobs = Blueprint('jobs', __name__)

# ---------------- LIST ALL JOBS ----------------
@jobs.route('/jobs')
def list_jobs():
    if 'user_id' not in session:
        flash("Please login to view jobs.", "error")
        return redirect('/login')

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
    jobs_list = cursor.fetchall()

    return render_template('jobs.html', jobs=jobs_list)


# ---------------- POST JOB (RECRUITER ONLY) ----------------
@jobs.route('/post-job', methods=['POST'])
def post_job():
    if 'user_id' not in session or session.get('role') != 'recruiter':
        flash("Unauthorized access.", "error")
        return redirect('/jobs')

    title = request.form['title']
    description = request.form['description']
    location = request.form['location']

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO jobs (recruiter_id, title, description, location)
        VALUES (%s, %s, %s, %s)
        """,
        (session['user_id'], title, description, location)
    )
    db.commit()

    flash("Job posted successfully!", "success")
    return redirect('/jobs')


# ---------------- APPLY FOR JOB (JOB SEEKER ONLY) ----------------
@jobs.route('/apply/<int:job_id>')
def apply_job(job_id):
    if 'user_id' not in session or session.get('role') != 'job_seeker':
        flash("Only job seekers can apply for jobs.", "error")
        return redirect('/jobs')

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute(
            "INSERT INTO applications (job_id, user_id) VALUES (%s, %s)",
            (job_id, session['user_id'])
        )
        db.commit()

        flash("Application submitted successfully!", "success")
        return redirect('/my-applications')

    except mysql.connector.errors.IntegrityError:
        flash("You have already applied for this job.", "error")
        return redirect('/jobs')


# ---------------- JOB SEEKER: MY APPLICATIONS ----------------
@jobs.route('/my-applications')
def my_applications():
    if 'user_id' not in session or session.get('role') != 'job_seeker':
        flash("Unauthorized access.", "error")
        return redirect('/jobs')

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT jobs.title, jobs.location, applications.applied_at
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        WHERE applications.user_id = %s
        ORDER BY applications.applied_at DESC
    """, (session['user_id'],))

    applications = cursor.fetchall()
    return render_template('my_applications.html', applications=applications)


# ---------------- RECRUITER DASHBOARD: THEIR JOBS ----------------
@jobs.route('/recruiter/jobs')
def recruiter_jobs():
    if 'user_id' not in session or session.get('role') != 'recruiter':
        flash("Unauthorized access.", "error")
        return redirect('/jobs')

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, title, created_at
        FROM jobs
        WHERE recruiter_id = %s
        ORDER BY created_at DESC
    """, (session['user_id'],))

    jobs_list = cursor.fetchall()
    return render_template('recruiter_jobs.html', jobs=jobs_list)


# ---------------- RECRUITER: VIEW APPLICANTS ----------------
@jobs.route('/recruiter/jobs/<int:job_id>/applicants')
def view_applicants(job_id):
    if 'user_id' not in session or session.get('role') != 'recruiter':
        flash("Unauthorized access.", "error")
        return redirect('/jobs')

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # 🔒 Ownership check
    cursor.execute(
        "SELECT id, title FROM jobs WHERE id = %s AND recruiter_id = %s",
        (job_id, session['user_id'])
    )
    job = cursor.fetchone()

    if not job:
        flash("You are not allowed to view applicants for this job.", "error")
        return redirect('/recruiter/jobs')

    cursor.execute("""
        SELECT users.name, users.email, applications.applied_at
        FROM applications
        JOIN users ON applications.user_id = users.id
        WHERE applications.job_id = %s
        ORDER BY applications.applied_at DESC
    """, (job_id,))

    applicants = cursor.fetchall()

    return render_template(
        'applicants.html',
        applicants=applicants,
        job=job
    )
