import asyncio
import json
import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from aio_pika import Message, connect, Queue, ExchangeType


async def onMessage(message: AbstractIncomingMessage) -> None:
    async with message.process():
        messageBody = message.body.decode("utf-8")
        print(messageBody)
        userJson = json.loads(messageBody)

        userConnection = await connect("amqp://backend:linuser@192.168.194.102:5672")
        userChannel = await userConnection.channel()
        
        if "Req" in userJson["action"]:
            databaseExchange = await userChannel.declare_exchange("Database", ExchangeType.DIRECT)
            await databaseExchange.publish(
                Message(body=json.dumps(userJson).encode()),
                routing_key = "Database1",
            )
        elif "Res" in userJson["action"]:
            await userChannel.default_exchange.publish(
                Message(body=json.dumps(userJson).encode()),
                routing_key = userJson["userID"],
            )

        await userConnection.close()
        await asyncio.sleep(1)


async def main() -> None:
    connection = await connect("amqp://backend:linuser@192.168.194.102:5672")

    #Check if the name of the exchange exists, if so, assign it to this var
    queueName = "Backend1"
    channel = await connection.channel()

    exchange = await channel.declare_exchange("Backend", ExchangeType.DIRECT)
    queue = await channel.declare_queue(queueName)
    await queue.bind(exchange)
    
    await queue.consume(onMessage)

    try:
        await asyncio.Future()
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())