#!/usr/bin/env python
import pika
import sys

#credentials = pika.PlainCredentials('messenger', 'linuser')
#hostname='message1.home.arpa'
parameters = pika.URLParameters('amqp://backend:linuser@192.168.194.102:5672/%2F')
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

channel.queue_declare(queue='Backend1', durable=False)

message = ' '.join(sys.argv[1:]) or "Hello World!"
channel.basic_publish(
    exchange='',
    routing_key='Backend1',
    body=message
)
print(f" [x] Sent {message}")
connection.close()
