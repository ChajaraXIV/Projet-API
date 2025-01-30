import asyncio
import os
from fastapi import FastAPI
from .message_broker import AMQPBroker

# Initialize FastAPI
app = FastAPI()

# Configuration du RABBITMQ
RABBITMQ_DEFAULT_USER = os.getenv("RABBITMQ_DEFAULT_USER")
RABBITMQ_DEFAULT_PASS = os.getenv("RABBITMQ_DEFAULT_PASS")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")

# Initialize the broker
broker = AMQPBroker(host=RABBITMQ_HOST, user=RABBITMQ_DEFAULT_USER, password=RABBITMQ_DEFAULT_PASS)
broker.connect()

# Store the latest received message
latest_message = {"message": "No messages received yet."}

def consume_messages(queue_name):
    broker.declare_queue(queue_name)
    def process_message(msg):
        global latest_message
        latest_message = msg  
        print("Received:", msg) 
    broker.consume_messages(queue_name, process_message)

@app.get("/")
def read_root():
    return {"message": "Welcome to Customer Service"}

@app.get("/customer")
def get_latest_message():
    return {"latest_message": latest_message}  

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, consume_messages, "customer_queue")
