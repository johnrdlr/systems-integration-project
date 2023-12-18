import asyncio
import json
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
import os
import random

from aio_pika import Message, connect_robust, Queue, ExchangeType, connect

# IP addresses for servers in the messaging cluster
servers = [
	"amqp://backend:lin67^&User@10.116.0.2:5672",
	"amqp://backend:lin67^&User@10.116.0.6:5672",
	"amqp://backend:lin67^&User@10.116.0.3:5672"
]

#Grab a random ip address from the servers list
def getNode():
	server = servers[random.randint(0, len(servers) - 1)]
	print("Selected: ", server)
	return server

#A function used to send messages to the messaging cluster taking a channel object, message, and target queue name
async def pubMessage(channel, body, route):
	print("Sent To: ", route)
	await channel.default_exchange.publish(
		Message(body=json.dumps(body).encode()),
		routing_key = route
	)

#Function to run when the backend recieves a message
async def onMessage(message: AbstractIncomingMessage) -> None:
	async with message.process():
		messageBody = message.body.decode("utf-8")
		
		
		messJson = json.loads(messageBody) #Parses the message it recieved
		if type(messJson) == str:
			messJson = json.loads(messJson) #Parses it again because the same method can do multiple things. In this case it goes from """" to "" to the JSON object

		userConnection = await connect_robust(getNode()) #Create a new connection to the messaging cluster
		channel2 = await userConnection.channel() #Creates a new channel for that connection

		action = messJson["action"]

		#Ungodly set of if statements that redirect the messages to their respective destinations basedd
		#If it has Req, send to database. If it has Res, send to user's temporary queue
		if "loginReq" == action:
			await pubMessage(channel2, messJson, "Database")
		elif "loginRes" == action:
			await pubMessage(channel2, messJson, messJson["userID"])

		elif "registerReq" == action:
			await pubMessage(channel2, messJson, "Database")
		elif "registerRes" == action:
			await pubMessage(channel2, messJson, messJson["userID"])

		elif "scheduleReq" == action:
			await pubMessage(channel2, messJson, "Database")
		elif "scheduleRes" == action:
			await pubMessage(channel2, messJson, messJson["userID"])

		elif "editReq" == action:
			await pubMessage(channel2, messJson, "Database")
		elif "editRes" == action:
			await pubMessage(channel2, messJson, messJson["userID"])

		elif "forgotReq" == action:
			await pubMessage(channel2, messJson, "Database")
		elif "forgotRes" == action:
			await pubMessage(channel2, messJson, messJson["userID"])
			
		#If the action is not known, catch it and do nothing
		else:
			print("Bad Action: ", action)

		await userConnection.close() #Close connection
		await asyncio.sleep(1) #Delay becuase it doesn't work without it

#Main Function
async def main() -> None:
	flag = True #Connect flag. Used to decide if program should reconnect to another another node
	while flag:
		try:
			connection = await connect_robust(getNode()) #Create a connection of type, robust, and select a random node
			channel1 = await connection.channel() #Create a channel for that connection
			databaseQ = await channel1.declare_queue("Database", durable=True, arguments={"x-queue-type": "quorum"}) #Create a database queue
			backendQ = await channel1.declare_queue("Backend", durable=True, arguments={"x-queue-type": "quorum"}) #Create a backend queue
			await backendQ.consume(onMessage) #Assign behavior to the channel
			flag = False #If all goes, well, then there is no need to replay this. Allowing normal crashes to occur else where
		except:
			print("Error, connecting to new node")
	
	#Used to run the asynchronous flow for the program to follow
	try:
		await asyncio.Future()
	finally:
		await connection.close()
		

#Start
if __name__ == "__main__":
	asyncio.run(main())