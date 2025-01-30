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
        subject = message.get("subject")

        if email and subject:
            verification_link = f"http://localhost:4000/auth/verify-email/{email}"

            body_html = f"""
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
                    .button {{
                        display: inline-block;
                        background-color: #007bff;
                        color: white;
                        padding: 12px 24px;
                        border-radius: 5px;
                        text-decoration: none;
                        font-weight: bold;
                        margin-top: 20px;
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
                    <div class="content">
                        <p>You're almost there! Click the button below to verify your email address.</p>
                        <a href="{verification_link}" class="button">Verify My Email</a>
                        <p>If you didn't create an account, ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>⚡ The Real Deal Team</p>
                    </div>
                </div>
            </body>
            </html>
            """

            send_email(email, subject, body_html)
        else:
            print("❌ Invalid message format:", message)

    broker.consume_messages(queue_name, process_message)


@app.get("/")
def read_root():
    return {"message": "Welcome to notification Service"}

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, consume_messages, "notification_queue")
