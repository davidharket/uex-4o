from flask import Flask, render_template, request, jsonify, session
from flask_mail import Mail, Message
from flask_session import Session
from chatbot_logic import get_response
from datetime import timedelta
import os

app = Flask(__name__)

# Secret key for session management. You can set this to any random string.
app.secret_key = os.urandom(24)

# Configure server-side sessions
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True  # Session will persist across browser restarts
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Sessions will persist for 7 days
app.config['SESSION_USE_SIGNER'] = True  # Encrypt the session cookies
app.config['SESSION_FILE_DIR'] = './flask_session/'  # Directory to store session files
Session(app)

# Ensure the session file directory exists
if not os.path.exists(app.config['SESSION_FILE_DIR']):
    os.makedirs(app.config['SESSION_FILE_DIR'])

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'mail.uex.no'  # Replace with your email provider's SMTP server
app.config['MAIL_PORT'] = 465  # Correct port for SSL
app.config['MAIL_USE_SSL'] = True  # Use SSL instead of TLS
app.config['MAIL_USERNAME'] = 'messages@uex.no'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'Mario123456Sodefjed179!'  # Replace with your email password
app.config['MAIL_DEFAULT_SENDER'] = 'messages@uex.no'  # Replace with your email
mail = Mail(app)

@app.route('/')
def index():
    if 'initial_message_shown' not in session:
        session['initial_message_shown'] = False
    return render_template('index.html')

@app.route('/initial_message_status', methods=['GET'])
def initial_message_status():
    return jsonify({"initial_message_shown": session.get('initial_message_shown', False)})

@app.route('/set_initial_message_shown', methods=['POST'])
def set_initial_message_shown():
    session['initial_message_shown'] = True
    session.modified = True
    return jsonify({"status": "success"})

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'chat_history' not in session:
        session['chat_history'] = []

    data = request.json
    message = data.get('message')
    if not message:
        return jsonify({"message": "No message provided"}), 400

    session['chat_history'].append({"role": "user", "content": message})
    response_message, buttons = get_response(message)
    session['chat_history'].append({"role": "assistant", "content": response_message})

    return jsonify({"message": response_message, "buttons": buttons})

@app.route('/submit_form', methods=['POST'])
def submit_form():
    data = request.json
    email = data.get('email')
    message = data.get('message')

    if not email or not message:
        return jsonify({"message": "Email and message are required"}), 400

    try:
        msg = Message("New Contact Form Submission",
                      recipients=['david@harket.no'])  # Replace with your recipient email
        msg.body = f"Email: {email}\n\nMessage:\n{message}"
        mail.send(msg)
        return jsonify({"message": "Email sent successfully"})
    except Exception as e:
        error_message = str(e)
        return jsonify({"message": f"Failed to send email: {error_message}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
