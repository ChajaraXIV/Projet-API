import time
import amqp
import json

class AMQPBroker:
    def __init__(self, host='message-broker', port=5672, user='user', password='password', vhost='/'):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.vhost = vhost
        self.connection = None
        self.channel = None

    def connect(self):
        while True:    
            try:
                self.connection = amqp.Connection(
                    host=f"{self.host}:{self.port}", 
                    userid=self.user, 
                    password=self.password, 
                    virtual_host=self.vhost
                )
                self.channel = self.connection.channel()
                print("Connected to AMQP broker.")
                break
            except Exception as e:
                print(f"Failed to connect: {e}")
                time.sleep(5)

    def declare_queue(self, queue_name, durable=True):
        if self.channel:
            self.channel.queue_declare(queue=queue_name, durable=durable)
            print(f"Queue '{queue_name}' declared.")
        else:
            print("Channel is not initialized. Call connect() first.")

    def publish_message(self, queue_name, message):
        if self.channel:
            msg = amqp.Message(json.dumps(message))
            self.channel.basic_publish(msg, routing_key=queue_name)
            print(f"Message sent to queue '{queue_name}'.")
        else:
            print("Channel is not initialized. Call connect() first.")

    def consume_messages(self, queue_name, callback):
        if self.channel:
            def wrapper(msg):
                try:
                    message_body = json.loads(msg.body)
                    callback(message_body)
                    # ✅ Explicitly acknowledge the message
                    self.channel.basic_ack(msg.delivery_tag)
                except Exception as e:
                    print(f"Error processing message: {e}")

            self.channel.basic_consume(queue=queue_name, callback=wrapper)
            print(f"Consuming messages from queue '{queue_name}'. Press Ctrl+C to stop.")

            try:
                while True:
                    self.connection.drain_events()  # ✅ Correct message handling
            except KeyboardInterrupt:
                print("Stopped consuming messages.")
        else:
            print("Channel is not initialized. Call connect() first.")


    def close_connection(self):
        if self.connection:
            self.connection.close()
            print("Connection closed.")
        else:
            print("No active connection to close.")

# Example usage
if __name__ == "__main__":
    broker = AMQPBroker(host='message-broker', user='user', password='password')
    broker.connect()
    broker.declare_queue("test_queue")
    broker.publish_message("test_queue", {"message": "Hello, AMQP!"})
    
    def process_message(msg):
        print("Received:", msg)
    
    broker.consume_messages("test_queue", process_message)
