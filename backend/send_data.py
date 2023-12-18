import asyncio
import json
import aio_pika
import os
from aio_pika.abc import AbstractIncomingMessage
import random

from aio_pika import Message, connect, Queue, ExchangeType

#Run the script to download the data if it doesn't exist
if not os.path.isfile("courses_processed,json"):
	os.system("python3 download_data.py")

#Open and parse the course schedule data
fileJson = json.load(open("courses_processed.json"))
	

messJson = {"action": "buildingDataUpdate", "body": json.dumps(fileJson)} #Cram the course data in a message JSON object the schedule data from the file

# IP addresses for servers in the messaging cluster
servers = [
	"amqp://backend:lin67^&User@10.116.0.2:5672",
	"amqp://backend:lin67^&User@10.116.0.6:5672",
	"amqp://backend:lin67^&User@10.116.0.3:5672"
]

#Get a random ip address from the messaging server list
def getNode():
	server = servers[random.randint(0, len(servers) - 1)]
	print("Selected: ", server)
	return server

#A function used to send messages to the messaging cluster taking a channel object, message, and target queue name
async def pubMessage(channel, body, route):
	print("Sent: ", route)
	await channel.default_exchange.publish(
		Message(body=json.dumps(body).encode()),
		routing_key = route
	)

#Main Function
async def main() -> None:
	flag = True #Connect flag. Used to decide if program should reconnect to another another node
	while flag:
		try:
			userConnection = await connect(getNode()) #Create a connection of type, robust, and select a random node
			userChannel = await userConnection.channel() #Create a channel for that connection
			backendQ = await userChannel.declare_queue("Backend", durable=True, arguments={"x-queue-type": "quorum"}) #Create a database queue
			databaseQ = await userChannel.declare_queue("Database", durable=True, arguments={"x-queue-type": "quorum"}) #Create a backend queue

			await pubMessage(userChannel, messJson, "Database") #Send the data loaded from the file to the database
			await userConnection.close() #Close the connection
			flag = False #If all goes, well, then there is no need to replay this. Allowing normal crashes to occur else where
		except:
			print("Error, connecting to new node")
	
	#Used to run the asynchronous flow for the program to follow
	try:
		await asyncio.Future()
	finally:
		await userConnection.close()


if __name__ == "__main__":
	asyncio.run(main())