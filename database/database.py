import asyncio
import json
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
import os, sys
import random
import atexit
import mariadb

from aio_pika import Message, connect_robust, Queue, ExchangeType

# CREATE TABLE users(fname varchar(255), lname varchar(255), dob DATE, email varchar(255), phone varchar(255), username varchar(255), password varchar(255), PRIMARY KEY(username));
# INSERT INTO users (fname, lname, dob, email, phone, username, password) VALUES ("boss", "man", "2023-11-30", "bossman@proton.me", "9731234567", "bossman", "password123");
# sudo apt install libmariadb3 libmariadb-dev

#List of messaging servers in a cluster
meServers = [
	"amqp://database:lin67^&User@10.116.0.2:5672",
	"amqp://database:lin67^&User@10.116.0.6:5672",
	"amqp://database:lin67^&User@10.116.0.3:5672"
]

#List of database nodes in a cluster
dbServers = [
	"10.116.0.5",
	"10.116.0.4"
]

#Return a random ip from a cluster denoted by the cluster parameter. Name is just used for logging
def getNode(cluster, name):
	pick = cluster[random.randint(0, len(cluster) - 1)]
	print(name + " Selected: " + pick)
	return pick

#Connect to a database node. Exit if it fails
try:
	dbConn = mariadb.connect(
		user="db_user",
		password="lin67^&User",
		host=getNode(dbServers, "DB"),
		port=3306,
		database="RoomFinder",
		autocommit=True
	)
except mariadb.Error as err:
	print(err)
	sys.exit(1)

#Create a cursor that will be running queries and pulling data from
cur = dbConn.cursor()

# Create UpdateLog Table
termTable = "CREATE TABLE IF NOT EXISTS {0} (room varchar(255), data LONGTEXT, PRIMARY KEY(room)) ENGINE=InnoDB;"
updateTable = "CREATE TABLE IF NOT EXISTS updatelog (term varchar(255) UNIQUE, date DATETIME, PRIMARY KEY(term)) ENGINE=InnoDB;"
userTable = "CREATE TABLE IF NOT EXISTS users(fname varchar(255), lname varchar(255), dob DATE, email varchar(255), phone varchar(255), username varchar(255) UNIQUE, password varchar(255), question varchar(255), questionType varchar(255), PRIMARY KEY(username)) ENGINE=InnoDB;"

#Intialize the tables for the database. If it doesn't exist or has a different schema, create it. MariaDB will ignore the command if it already exists.
try:
	cur.execute(updateTable)
	cur.execute(userTable)
except mariadb.Error as err:
	print(err)

#Add a user into the users table by taking in a json object of the user information
def addUser(entry):
	#Check if the user already exists. If so, don't do anything and return "duplicate"
	query = "SELECT username from users WHERE username='{0}'".format(entry["username"])
	cur.execute(query)
	if len(cur.fetchall()) > 0: #If there is one or more result, then return
		return "RegisterUserDuplicate"

	#Template of a command needed to add a user that is populated with a format method using the data from the argument given
	query = """INSERT INTO users (fname, lname, dob, email, phone, username, password, question, questionType)
			   VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}');	
	""".format(entry["fname"], entry["lname"], entry["dob"], entry["email"], entry["phone"], entry["username"], entry["password"], entry["question"], entry["questionType"])
	try:
		cur.execute(query)
		return "RegisterUserSuccess" #Tells users a successful creation
	except mariadb.Error as err:
		print(err)
		return err
	return "RegisterUserFailure"
# addUser({"fname":"asd","lname":"das","dob":"2010-01-12","email":"lol","phone":"12331241","username":"te","password":"et"})

#Finds and returns everything about the user from the users table
def getUser(entry): #Enter username as string
	query = "SELECT * FROM users WHERE username = '{0}'".format(entry)
	try:
		cur.execute(query)
		data = cur.fetchall()
		return data[0]
	except mariadb.Error as err:
		print(err)
		return err
# print(getUser("te"))

#Validates whether or not a given username or password is matching in the users table
def loginUser(username, password): #Enter user and pass as strings
	query = "SELECT password FROM users WHERE username='{0}';".format(username)
	try:
		cur.execute(query)
		data = cur.fetchall()
		if len(data) > 0: #If there is a result. It matches
			if data[0][0] == str(password):
				return "LoginUserSuccess"
	except mariadb.Error as err:
		print(err)
		return "error"
	return "LoginUserFailure"
# print(loginUser("bossman", "pas"))
# print(loginUser("bossman", "password123"))

#Edits a user information using a JSON object given by the argument
def editUser(entry):
	query = "SELECT password FROM users WHERE username='{0}';".format(entry["username"])
	try:
		cur.execute(query)
		data = cur.fetchall()
		if len(data) > 0:
			if data[0][0] == str(entry["password"]): #If the username-password is valid, then update the user info
				query = """UPDATE users SET fname='{0}', lname='{1}', dob='{2}', email='{3}', phone='{4}', password='{5}'
						WHERE username='{6}' and password='{7}';
				""".format(entry["fname"], entry["lname"], entry["dob"], entry["email"], entry["phone"], entry["newPassword"], entry["username"], entry["password"])
				cur.execute(query)
				return "EditUserSuccess"
	except mariadb.Error as err:
		print(err)
		return err
	return "EditUserFailure"

#Edits a user information using a JSON object given by the argument
#entry = {username:, question:, questionType:, password:, confirmpass}
#Find result for username and question matches. Update password with ["password"]
def forgotUser(entry):
	query = "SELECT question FROM users WHERE username='{0}' and questionType='{1}';".format(entry["username"], entry["questionType"])
	print(query)
	try:
		cur.execute(query)
		data = cur.fetchall()
		if len(data) > 0:
			print(data[0][0], str(entry["question"]))
			if data[0][0] == str(entry["question"]): #If the username-question is valid, then update the user info
				query = """UPDATE users SET password='{0}'
						WHERE username='{1}';
				""".format(entry["password"], entry["username"])
				cur.execute(query)
				return "PasswordResetSuccess"
	except mariadb.Error as err:
		print(err)
		return err
	return "PasswordResetFailure"

#Creates a table in the database that is about a certain term and its data
def createTermTable(term, data): #Term is name of new table and data is the json of the semester
	query = termTable.format(term)
	print(query)
	try:
		cur.execute(query)
	except mariadb.Error as err:
		print(err)
		return err
	try:
		#Inserts the room and every class that's in that room into the table
		#Ex: INSERT INTO Spring2024 (room, ddata) VALUES (ex1, ex1),(ex1, ex1),(ex1, ex1)...
		addEntry = "INSERT INTO {0} (room, data) VALUES ".format(term)
		for room in data:
			addEntry += "('{0}','{1}'), ".format(room, json.dumps(data[room]))
		addEntry = addEntry.rstrip(", ") + ";"
		cur.execute(addEntry)
	except mariadb.Error as err:
		print(err)
		return err
	return False
# createTermTable("Spring2024", {"kupfhtdfr112305":{"123":[1, 2]}, "kuhtrpf3hd105":{"123":[1, 2]}})

#Function that updates a term table
def updateCourses(entry): #Enter as json
	createTermTable(entry["term"], entry["data"])

#Get information about a building from a term table
def getBuilding(term, building):
	#A query that uses the wildcard, '%', to fetch information. Since we store building rooms as CKB1233 or the such. We use CKB%
	query = "SELECT * FROM {0} WHERE room LIKE '{1}%'".format(term, building)
	try:
		cur.execute(query)
		data = cur.fetchall()
		print(term, building)
		return data
	except mariadb.Error as err:
		print(err)
		return err
	return "GetBuildingFailure"

#Function used to send messages to a server in the messaging cluster
async def pubMessage(channel, body, route):
	print("Sent To: ", route)
	await channel.default_exchange.publish(
		Message(body=json.dumps(body).encode()),
		routing_key = route
	)

#A function that takes request messages and converts them to response messages
async def onMessage(message: AbstractIncomingMessage) -> None:
	async with message.process():
		messageBody = message.body.decode("utf-8")
		
		#Parses the message twice to remove the two layers of encapsulation
		messJson = json.loads(messageBody)
		if type(messJson) == str:
			messJson = json.loads(messJson)

		#Create connection object and a channel for it
		userConnection = await connect_robust(getNode(meServers, "ME"))
		channel2 = await userConnection.channel()

		body = messJson["body"]

		#An ungodly abomination of if statements that try to complete an action based on the message's requet
		action = messJson["action"]
		if "loginReq" == action:
			messJson["action"] = "loginRes"
			messJson["body"] = loginUser(body["username"], body["password"])
			await pubMessage(channel2, messJson, "Backend")

		elif "registerReq" == action:
			messJson["action"] = "registerRes"
			messJson["body"] = addUser(body)
			await pubMessage(channel2, messJson, "Backend")

		elif "scheduleReq" == action:
			messJson["action"] = "scheduleRes"
			messJson["body"] = getBuilding(body["term"], body["building"])
			await pubMessage(channel2, messJson, "Backend")

		elif "editReq" == action:
			messJson["action"] = "editRes"
			messJson["body"] = editUser(body)
			await pubMessage(channel2, messJson, "Backend")

		elif "forgotReq" == action:
			messJson["action"] = "forgotRes"
			messJson["body"] = forgotUser(body)
			await pubMessage(channel2, messJson, "Backend")

		elif "buildingDataUpdate" == action:
			updateCourses(json.loads(body))

		else:
			print("Bad Action")
		
		await userConnection.close()
		await asyncio.sleep(1)

#A function run as the python script is closing to ensure that the database connection properly terminates
def exitCode():
	try:
		dbConn.close()
		print("Exit Success")
	except:
		print("Exit Error")

#Main function
async def main() -> None:
	flag = True
	#Loop until it finds a stable server to connect to
	while flag:
		try:
			connection = await connect_robust(getNode(meServers, "ME")) #Create a robust connection
			channel1 = await connection.channel() #Create a channel for that channel
			backendQ = await channel1.declare_queue("Database", durable=True, arguments={"x-queue-type": "quorum"}) #Create a Database queue on the messaging server
			await backendQ.consume(onMessage) #Assign an onMessage behavior whenever this script gets a message in its queue
		except:
			print("Failed, reconnecting to new node")
		flag = False

	#Code to keep the script running when there is an error
	try:
		await asyncio.Future()
	finally:
		await connection.close()
		
#Start
if __name__ == "__main__":
	atexit.register(exitCode)
	asyncio.run(main())