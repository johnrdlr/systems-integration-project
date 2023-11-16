import asyncio
import json
import aio_pika
import os
from aio_pika.abc import AbstractIncomingMessage

from aio_pika import Message, connect, Queue, ExchangeType

if not os.path.isfile("courses_processed,json"):
	os.system("python3 get_resources.py")
fileJson = json.load(open("courses_processed.json"))
	

messJson = {"action": "courseUpdateReq", "body": json.dumps(fileJson)}

async def main() -> None:
	userConnection = await connect("amqp://backend:linuser@192.168.194.2:5672")
	userChannel = await userConnection.channel()
	databaseExchange = await userChannel.declare_exchange("Database", ExchangeType.DIRECT)
	await databaseExchange.publish(
		Message(body=json.dumps(messJson).encode()),
		routing_key = "Database1",
	)
	await userConnection.close()


if __name__ == "__main__":
	asyncio.run(main())