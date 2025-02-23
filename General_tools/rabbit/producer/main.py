import pika
import time

RABBITMQ_HOST = "rabbitmq"
USERNAME = "user"
PASSWORD = "password"

EXCHANGE_NAME = "topic_logs"

messages = [
    ("info.system", "System is running smoothly"),
    ("error.db", "Database connection failed"),
    ("warning.memory", "Memory usage is high"),
    ("error.system", "System encountered a critical error"),
    ("info.app", "Application started successfully"),
    ("warning.disk", "Disk space is running low"),
]

def send_message():
    credentials = pika.PlainCredentials(USERNAME, PASSWORD)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    )
    channel = connection.channel()

    try:
        while True:
            # Declare topic exchange
            channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')

            for routing_key, message in messages:
                channel.basic_publish(
                    exchange=EXCHANGE_NAME,
                    routing_key=routing_key,
                    body=message
                )
                print(f" [x] Sent '{message}' with routing key '{routing_key}'")
            time.sleep(0.001)
    finally:
        connection.close()

if __name__ == "__main__":
    send_message()
