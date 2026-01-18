from flask import Flask, render_template, session, redirect
from auth import auth
from jobs import jobs

app = Flask(__name__)
app.secret_key = "dev_secret_key"

# Register blueprints
app.register_blueprint(auth)
app.register_blueprint(jobs)

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/jobs')
    return render_template('home.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/post-job')
def post_job_page():
    if 'user_id' not in session or session.get('role') != 'recruiter':
        return "Unauthorized"
    return render_template('post_job.html')

if __name__ == "__main__":
    app.run(debug=True)
