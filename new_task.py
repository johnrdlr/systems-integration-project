#!/usr/bin/env python
import pika
import sys

parameters = pika.URLParameters('amqp://username:password@message1.home.arpa:5672/%2F')
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)

message = ' '.join(sys.argv[1:]) or "Hello World!"
channel.basic_publish(
    exchange='',
    routing_key='task_queue',
    body=message
)
print(f" [x] Sent {message}")
connection.close()
