import pika

RABBITMQ_HOST = "rabbitmq"
USERNAME = "user"
PASSWORD = "password"

EXCHANGE_NAME = "topic_logs"
QUEUE_NAME = "service1_queue"
BINDING_KEYS = ["warning.*", "error.*"]  # Listens for any warning or error messages

def callback(ch, method, properties, body):
    print(f" [Service 1] Received {body.decode()} with key {method.routing_key}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def consume():
    credentials = pika.PlainCredentials(USERNAME, PASSWORD)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    )
    channel = connection.channel()

    # Declare exchange and queue
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    # Bind queue to multiple patterns
    for key in BINDING_KEYS:
        channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=key)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    print(" [Service 1] Waiting for messages...")
    channel.start_consuming()

if __name__ == "__main__":
    consume()
