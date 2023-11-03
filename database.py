import asyncio
import json
import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from aio_pika import Message, connect, Queue, ExchangeType

import mysql.connector

mydb = mysql.connector.connect(
	host="localhost",
	database="RoomFinder",
	user="backend",
	password="password"
)

mycursor = mydb.cursor(buffered=True)
# sql = "SELECT * FROM Users"
# mycursor.execute(sql)
# print(mycursor.fetchall)



async def registerUser(userJson) -> None:
	addUser = ("INSERT INTO Users (username, password, email, firstname, lastname, phone, dob) VALUES (%s, %s, %s, %s, %s, %s, %s)")
	userData = (userJson["username"], userJson["password"], userJson["email"], userJson["firstname"], userJson["lastname"], userJson["phone"], userJson["dob"])
	try:
		mycursor.execute(addUser, userData)
		mydb.commit()
		return "success"
	except Exception as error:
		print(error)
		return "failure"

def addQuote(str):
	return '"{0}"'.format(str)

async def authUser(username) -> None:
	getPass = "SELECT password FROM Users WHERE username =" + addQuote(username)
	print("What i put in ", getPass)
	try:
		mycursor.execute(getPass)
		# print(mycursor.fetchall()[0][0])
		return "success"
	except Exception as error:
		print(error)
		return "failure"

async def loginUser(userJson) -> None:
	checkCred = "SELECT * FROM Users WHERE username='{0}' AND password='{1}'".format(userJson["username"], userJson["password"])
	try:
		mycursor.execute(checkCred)
		return "success"
	except Exception as error:
		print(error)
		return "failure"

		

async def sendMessage(messageBody, dest) -> None:
	userConnection = await connect("amqp://backend:linuser@192.168.194.102:5672")
	userChannel = await userConnection.channel()
	await userChannel.default_exchange.publish(
		Message(body=messageBody.encode()),
		routing_key = dest
	)
	await userConnection.close()
	await asyncio.sleep(1)

async def onMessage(message: AbstractIncomingMessage) -> None:
	async with message.process():
		messageBody = message.body.decode("utf-8")
		print(messageBody)
		userJson = json.loads(messageBody)

		action = userJson["action"]
		if action == "registerReq":
			res = await registerUser(userJson)
			await sendMessage(
				json.dumps({'action':'registerRes','returnQueue':userJson["returnQueue"],'body':res}),
				userJson["returnQueue"]
			)
		elif action == "loginReq":
			res = await loginUser(userJson)
			print(res)
			await sendMessage(
				json.dumps({'action':'loginRes','returnQueue':userJson["returnQueue"],'body':res}),
				userJson["returnQueue"]
			)

async def main() -> None:
	connection = await connect("amqp://database:linuser@192.168.194.102:5672")

	queueName = "Database1"
	channel = await connection.channel()

	exchange = await channel.declare_exchange("Database", ExchangeType.DIRECT)
	queue = await channel.declare_queue(queueName)
	await queue.bind(exchange)
	
	await queue.consume(onMessage)

	try:
		await asyncio.Future()
	finally:
		await connection.close()


if __name__ == "__main__":
	asyncio.run(main())