from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    # Add login logic here
    return f"Logged in with email: {email}"

@app.route('/forgot-password')
def forgot_password():
    return "Forgot Password Page (To be implemented)"

@app.route('/signup')
def signup():
    return "Signup Page (To be implemented)"

if __name__ == '__main__':
    app.run(debug=True)

