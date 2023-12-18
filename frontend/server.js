const express = require("express"); //Framework
var amqp = require('amqp-connection-manager'); //Connection Manager for Rabbitmq
const IP = require("ip"); //Access to server's IP
const dotenv = require("dotenv"); //Allow access to environment variables
const jwt = require('jsonwebtoken'); //User tokenization
const redis = require('redis');

const app = express();
app.set("view engine", "ejs"); //Template engine for building webpages

dotenv.config(); //Initialize environment variables
process.env.TOKEN_SECRET; //Import token secret from environment variables to generate secure tokens

//Generate a token for the user based on datagiven
function generateAccessToken(data) {
	return jwt.sign(data, process.env.TOKEN_SECRET, { expiresIn: '1800s' });
}

//Verify a given token. True if valud. False if not
function verifyToken(token) {

	return (async () => {
		if (token == "undefined") {
			console.log("undefined");
			return false
		}
		const inDenyList = await redisClient.get(`bl_${token}`);

		if (inDenyList) {
			console.log("denied");
			return false
		}
		return jwt.verify(token, process.env.TOKEN_SECRET, function (err, decoded) {
			if (err) {
				console.log(token);
				console.log("error");
				return false;
			}
			console.log("good");
			return true;
		});
	})();
}

//Decode a given token
function decodeToken(token) {
	return jwt.verify(token, process.env.TOKEN_SECRET, function (err, decoded) {
		if (err) {
			console.log("Error: ", err);
			return "Unauthorized";
		}
		else if (decoded) {
			return decoded["username"];
		}
	});
}

function getTokenExp(token) {
	return jwt.verify(token, process.env.TOKEN_SECRET, function (err, decoded) {
		if (err) {
			return "Unauthorized";
		}
		else if (decoded) {
			return decoded["exp"];
		}
	});
}

//List of messaging servers
servers = [
	"amqp://frontend:lin67^&User@10.116.0.2:5672",
	"amqp://frontend:lin67^&User@10.116.0.3:5672",
	"amqp://frontend:lin67^&User@10.116.0.6:5672"
];

expressServer = [
	"192.168.194.50:7009",
	"192.168.194.51:7009"
]

function sendBlackList() {

}



(async () => {
	redisClient = redis.createClient();

	redisClient.on("error", (error) => {
		console.log(error);
	});
	redisClient.on("connect", () => {
		console.log("Redis connected!");
	});

	await redisClient.connect();
})();


//Create the connection object
var connection = amqp.connect(servers, {
	heartbeatIntervalInSeconds: 0, //How long to wait before closing a connection
	reconnectTimeInSeconds: 0 //How long to wait before moving onto another connection
});
connection.on('connect', function () {
	console.log('Connected!');
});
connection.on('disconnect', function (err) {
	console.log('Disconnected.', err.stack);
});

//Create a sending channel for the connection
var ch1Wrapper = connection.createChannel({
	setup: function (ch1) {
		return Promise.all([
			ch1.assertQueue("Backend", { arguments: { "x-queue-type": "quorum" } }), //Tell the messaging server to create a queue for Backendd
		]);
	},
});

//Handle POST requests from the user going to /request
app.post("/request", (req, res, next) => {
	var body = "";
	res.set({ 'Content-Type': 'application/json' }); //Set respond header to handle JSON
	if (req.method == "POST") {
		req.on("readable", function () { //Read the entire message sent from the user
			body += req.read();
		});
		req.on("end", function () { //When fully read, do this
			body = body.replace("null", "");
			var userJson = JSON.parse(body); //Parse the request
			var queueName = userJson["userID"]; //Define the queue name to use for user's temporary queue
			console.log("To Send: ", userJson["action"]);

			//Create the user's temporary queue
			ch1Wrapper.assertQueue(queueName, { arguments: { "x-expires": 5000, "x-queue-type": "quorum" } })
				.then(function () {
					//Send the user data to the Backend queue
					ch1Wrapper.sendToQueue("Backend", Buffer.from(JSON.stringify(userJson)))
				}).then(function () {
					//Create the second channel for recieving data
					var ch2Wrapper = connection.createChannel({
						setup: function (ch2) {
							return Promise.all([
								//When there is a message in the user's queue, run this
								ch2.consume(queueName, function (msg) {
									ch2.ack(msg); //Tell the messaging server that the message has been recieved
									var message = JSON.parse(msg.content.toString()); //Parse the recieved message
									console.log("Recieved", message["action"]);

									//If one of the recieved messages' action happens to verify the user's login
									//Capture it and send back the user's newly generated token that stores their username
									if (message["action"] == "loginRes" && message["body"] == "LoginUserSuccess") {
										const token = generateAccessToken({ "username": userJson["body"]["username"] }); //Generate the user's token
										message["token"] = token; //Replace the body of the JSON object with the token
									}
									res.send(message); //Send the recieved JSON to the user
									res.end(); //End the response message
									ch2Wrapper.close(); //Close the secondary channel
								}),
							]);
						}
					})
				});

		});
	}
});

//Serve the user public, static files like images and css
app.use(express.static("public"));

//A function to decide if the user should see a certain header based if they're logged in or not
function chooseHeader(name, token) {
	if (verifyToken(token)) return '../partials/header_priv';
	return '../partials/header';
}

//If the user tries to open up an unknown webpage, they'll be redireceted to the index
app.get("/", (req, res) => {
	res.redirect("/index");
});

//THE REST OF THE MIDDLE WARES ARE NEARLY IDENTICAL, BUT NOT ENOUGH TO BE USE ROUTERS.
//SO THEY ARE THEIR OWN CODE BLOCKS. COMMENTS FOR ONE ARE THE SAME FOR THE REST.

app.use("/test", (req, res) => {
	res.send(req.headers.host);
})

app.use("/logout*", (req, res) => {
	(async () => {
		myIp = req.headers.host;
		token = req.query.token;

		const token_key = `bl_${token}`;
		await redisClient.set(token_key, token);
		redisClient.expireAt(token_key, getTokenExp(token));

		res.send("LogoutSuccess");
	})();
})

app.get("/index*", (req, res) => {
	routeName = req.route.path.slice(1, -1); //Get the route's name, like index in this case
	res.render("pages/" + routeName, { //Use routeName to get the webpage to load for the user
		title: "Home", //Define the title of the webpage
		headFile: '../partials/head', //Define the file location for the head element
		headerFile: chooseHeader(routeName, req.query.token), //Define the file location for the headerFile
		username: decodeToken(req.query.token), //Decode and define the username to be used if the headerFile is privleged
	});
});

//THESE TWO middlewares redirect the user to unprivleged webpages. ie if they're not logged in
app.get("/register*", (req, res) => {
	routeName = req.route.path.slice(1, -1);
	res.render("pages/" + routeName, {
		title: "Register",
		headFile: '../partials/head',
		headerFile: chooseHeader(routeName, req.query.token),
	});
});
app.get("/login*", (req, res) => {
	routeName = req.route.path.slice(1, -1);
	res.render("pages/" + routeName, {
		title: "Login",
		headFile: '../partials/head',
		headerFile: chooseHeader(routeName, req.query.token),
	});
});
app.get("/forgot*", (req, res) => {
	routeName = req.route.path.slice(1, -1);
	res.render("pages/" + routeName, {
		title: "Forget Password",
		headFile: '../partials/head',
		headerFile: chooseHeader(routeName, req.query.token),
	});
});

//A middleware guard to prevent any user with no or bad token from accessing privleged webpages
app.use(async function (req, res, next) {
	console.log("Dtr", verifyToken(req.query.token));
	console.log("token");
	if (token != "undefined" && verifyToken(req.query.token)) {
		console.log("Went Through Guard");
		next();
	}
	else {
		res.redirect("/index");
	}
})

//THESE THREE middlewares redirect the user to privleged webpages
app.get("/landing*", (req, res) => {
	routeName = req.route.path.slice(1, -1);
	res.render("pages/" + routeName, {
		title: "Landing",
		headFile: '../partials/head',
		headerFile: chooseHeader(routeName, req.query.token),
		username: decodeToken(req.query.token),
	});
});
app.get("/schedule*", (req, res) => {
	routeName = req.route.path.slice(1, -1);
	res.render("pages/" + routeName, {
		title: "Schedule",
		headFile: '../partials/head',
		headerFile: chooseHeader(routeName, req.query.token),
		username: decodeToken(req.query.token),
	});
});
app.get("/account*", (req, res) => {
	routeName = req.route.path.slice(1, -1);
	res.render("pages/" + routeName, {
		title: "Account",
		headFile: '../partials/head',
		headerFile: chooseHeader(routeName, req.query.token),
		username: decodeToken(req.query.token),
	});
});


//Start the server on port, 7009
app.listen(7009, function () {
	console.log("Listening on 7009");
});