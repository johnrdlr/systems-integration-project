#!/usr/bin/env python
import pika
import time

parameters = pika.URLParameters('amqp://backend:linuser@192.168.194.102:5672/%2F')
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

channel.queue_declare(queue='Backend1', durable=False)
print(' [*] Waiting for messages. To exit press CTRL+C')


def callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")
    time.sleep(body.count(b'.'))
    print(" [x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='Backend1', on_message_callback=callback)

channel.start_consuming()
