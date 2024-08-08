from flask import Flask, render_template, request, jsonify, session
from flask_mail import Mail, Message
from flask_session import Session
from chatbot_logic import get_response
from datetime import timedelta
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Secret key for session management. Loaded from environment variable.
app.secret_key = os.getenv('SECRET_KEY')

# Configure server-side sessions
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_FILE_DIR'] = './flask_session/'
Session(app)

# Ensure the session file directory exists
if not os.path.exists(app.config['SESSION_FILE_DIR']):
    os.makedirs(app.config['SESSION_FILE_DIR'])

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
mail = Mail(app)

@app.route('/')
def index():
    if 'initial_message_shown' not in session:
        session['initial_message_shown'] = False
    return render_template('index.html')

@app.route('/initial_message_status', methods=['GET'])
def initial_message_status():
    initial_message_shown = session.get('initial_message_shown', False)
    return jsonify({"initial_message_shown": initial_message_shown})

@app.route('/set_initial_message_shown', methods=['POST'])
def set_initial_message_shown():
    if not session.get('initial_message_shown'):
        session['initial_message_shown'] = True
        if 'chat_history' not in session:
            session['chat_history'] = []
        initial_message = {"role": "assistant", "content": "Hei, mitt navn er Mia! Hvordan kan jeg hjelpe deg i dag?"}
        session['chat_history'].append(initial_message)
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
    assistant_message = {"role": "assistant", "content": response_message}
    if buttons:
        assistant_message["buttons"] = buttons
    session['chat_history'].append(assistant_message)

    session.modified = True  # Ensure session changes are saved

    return jsonify({"message": response_message, "buttons": buttons})

@app.route('/get_chat_history', methods=['GET'])
def get_chat_history():
    chat_history = session.get('chat_history', [])
    return jsonify(chat_history)

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
