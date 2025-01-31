import asyncio
from .message_broker import AMQPBroker
from .email_sender import send_email
from fastapi import FastAPI
import os

# Initialisation de FastAPI
app = FastAPI()

# Configuration du RABBITMQ
RABBITMQ_DEFAULT_USER = os.getenv("RABBITMQ_DEFAULT_USER")
RABBITMQ_DEFAULT_PASS = os.getenv("RABBITMQ_DEFAULT_PASS")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")

# Initialize the broker
broker = AMQPBroker(host=RABBITMQ_HOST, user=RABBITMQ_DEFAULT_USER, password=RABBITMQ_DEFAULT_PASS)
broker.connect()

def consume_messages(queue_name):
    broker.declare_queue(queue_name)

    def process_message(message):
        email = message.get("email")
        message_type = message.get("type")  # Renommé pour éviter le conflit avec `type`
        subject = message.get("subject")

        if message_type == "optIn":
            token = message.get("token")
            if not (email and token and subject):
                print("❌ Invalid message format:", message)
                return

            body_html = generate_email_body(message_type, token)
            send_email(email, subject, body_html)

        elif message_type == "doubleOptIn":
            if not (email and subject):
                print("❌ Invalid message format:", message)
                return

            body_html = generate_email_body(message_type)
            send_email(email, subject, body_html)

        else:
            print("❌ Unknown message type:", message_type)

    broker.consume_messages(queue_name, process_message)

def generate_email_body(message_type, token=None):
    if message_type == "optIn":
        content = f"""
            <p>You're almost there! Verify the registration token below to verify your email address.</p>
            <p><b>{token}</b></p>
            <p>If you didn't create an account, ignore this email.</p>
        """
    elif message_type == "doubleOptIn":
        content = "<p>Congratulations! Your email address has been verified.</p>"
    else:
        return ""

    return f"""
    <html>
    <head>
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                background-color: #f4f4f4;
                color: #333333;
                text-align: center;
            }}
            .email-container {{
                max-width: 600px;
                margin: 20px auto;
                background: #ffffff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                font-size: 24px;
                font-weight: bold;
                color: #007bff;
            }}
            .content {{
                font-size: 16px;
            }}
            .footer {{
                margin-top: 20px;
                font-size: 12px;
                color: #888888;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">🚀 Welcome to The Real Deal!</div>
            <div class="content">{content}</div>
            <div class="footer">
                <p>⚡ The Real Deal Team</p>
            </div>
        </div>
    </body>
    </html>
    """
@app.get("/")
def read_root():
    return {"message": "Welcome to notification Service"}

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consume_messages("notification_queue"))
