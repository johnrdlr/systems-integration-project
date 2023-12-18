var scheduleData = ""; //Predefine a global variable to store schedule data if neededd

//Grab the value of a cookie based on its name
function getCookie(name) {
	const regex = new RegExp(`(^| )${name}=([^;]+)`);
	const match = document.cookie.match(regex);
	if (match) {
		return match[2];
	}
}

//A simple, but effective hasing function that takes in a string
function stringToHash(string) {
	let hash = 0;
	if (string.length == 0) return hash;
	for (i = 0; i < string.length; i++) {
		char = string.charCodeAt(i);
		hash = ((hash << 5) - hash) + char;
		hash = hash & hash;
	}
	return hash;
}

//A function that adds the user's token if it is valid
function makeURL(name) {
	token = getCookie("token");
	if (token == undefined || token == "undefined") {
		return name;
	}
	console.log(name);
	return (name + "?token=" + token);
}

//A function to reset the dropdown options on the schedule webpage
//To make sure that the user doesn't request schedule data when changing semesters
function dropdownChange(dropdown) {
	if (dropdown == "semester") {
		if (document.getElementById("term").value == "Fall2024") {
			alert("Not ready yet");
			document.getElementById("term").value = "Spring2024";
		}
		document.getElementById("date").selectedIndex = 0;
		document.getElementById("building").selectedIndex = 0;
	}
	else if (dropdown == "building") {
		sendUser("scheduleReq");
	}
	else if (dropdown == "date") {
		makeTable();
	}
}

//The function to build and send JSON messages to the messaging server
function sendUser(action) {
	//Grab the user's cookie. If it doesn't exist, create one
	//The user's cookie is used to define the user's temporary queue for their session
	var userID = document.cookie;
	if (getCookie("userid") == "" || getCookie("userid") == undefined) {
		userID = Math.random().toString(16).slice(2);
		document.cookie = "userid=" + userID + ";";
	}

	//Grab the input field's data if they have userInfo as their class name
	var userInfo = document.getElementsByClassName("userinfo");
	userJson = { "body": {} };
	for (var a = 0; a < userInfo.length; a++) {
		let info = userInfo[a].id;
		userJson["body"][info] = userInfo[a].value;
	}

	//An ungodly set of if statements that sets the action of the message
	//If it has to do with the user's password, it will be hashed
	if (action == "login") {
		userJson.action = "loginReq";
		userJson["body"]["password"] = stringToHash(userJson["body"]["password"]);

	} else if (action == "register") {
		userJson.action = "registerReq";
		userJson["body"]["password"] = stringToHash(userJson["body"]["password"]);
		userJson["body"]["confirmpass"] = stringToHash(userJson["body"]["confirmpass"]);
		userJson["body"]["question"] = stringToHash(userJson["body"]["question"]);
		userJson["body"]["questionType"] = document.getElementById("questionSelection").value;

	} else if (action == "auth") {
		userJson.action = "authReq";
		userJson["body"]["password"] = stringToHash(userJson["body"]["password"]);

	} else if (action == "info") {
		userJson.action = "info";

	} else if (action == "scheduleReq") {
		userJson.action = "scheduleReq";
		userJson["body"]["building"] = document.getElementById("building").value;

	} else if (action == "edit") {
		userJson.action = "editReq";
		userJson["body"]["password"] = stringToHash(userJson["body"]["password"]);
		userJson["body"]["newPassword"] = stringToHash(userJson["body"]["newPassword"]);

	} else if (action == "forgot") {
		userJson.action = "forgotReq";
		userJson["body"]["password"] = stringToHash(userJson["body"]["password"]);
		userJson["body"]["confirmpass"] = stringToHash(userJson["body"]["confirmpass"]);
		userJson["body"]["questionType"] = document.getElementById("questionSelection").value;
		userJson["body"]["question"] = stringToHash(userJson["body"]["question"]);
	}

	userJson.userID = getCookie("userid");
	sendPost("/request", userJson); //Send the message
}

//Function to overwrite the token variable in the cookies and redirect the user
//Effectively logging out users
function logout() {
	console.log("attempting logout");
	sendLogout();
}

async function sendLogout() {
	console.log("Sent: logout");
	let message = fetch(makeURL("logout"), {
		method: 'POST',
		headers: { //Header for the request packet
			'Accept': 'application/json', //Tell the server that it accepts JSON as a return message
			'Content-Type': 'application/json' //Make it handle only JSON
		},
		body: JSON.stringify(getCookie("token")) //Store the userdata in the body attribuite of the json message
	}).then(response => response.text()) //When the promise resolves
	.then(object => { //When the previous response is completed and convert the object into JSON
		console.log("Recieved: ", object);
		if(object == "LogoutSuccess") {
			window.location.href = makeURL("index");
			document.cookie = "token=undefined"
			window.location.href = makeURL("index");
		}
	}).catch(function (err) {
		console.log(err); //Error catch
	});
}

//Generate the HTML to splice into the wepbage
function makeTable() {
	//If the scheduleData is empty, don't run the rest
	if (scheduleData == "") {
		console.log("Missing schedule data");
		return;
	}

	//Create the first part of the table before the data is generated
	document.getElementById("scheduleTable").innerHTML = "<tr><th>&nbsp;</td><th id='widthRef'>8</th><th>9</th><th>10</th><th>11</th><th>12</th><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th><th>6</th><th>7</th><th>8</th><th>9</th><th>10</th><th>11</th></tr>";
	
	//Get what day to present to the user
	//And get the width of the cells by taking one of the existing cell's width
	var day = document.getElementById("date").selectedIndex;
	var cellWidth = document.getElementById("widthRef").offsetWidth;

	//Iterative loop that goes through the schedule data and generates each row based on the day selected and building name
	for (var a = 0; a < scheduleData.length; a++) {
		var room = scheduleData[a][0];
		var schedule = JSON.parse(scheduleData[a][1]);
		var row = "<tr class='" + room + "'><td>" + room + "</td><td class='8am'>";

		//Another iterative loop to generate each section that is meant to displayed
		for (var b = 0; b < schedule.length; b++) {
			if (schedule[b][2] > day * 1440 && schedule[b][2] < (day + 1) * 1440) { //Checks if the start time of the class is within the time needed to display. 1440 is 24 hours * 60 minutes.
				
				//This creates a div element for every section in the first td element, then pushing it to the write using the class's start time and cells per pixel
				//Pixels to move to the left = [(classStart % minutes in a day) - (Time in minuts the school day starts)] * (The ratio of minutes to pixels)
				//Pixels for the width = (classEnd - classStart) * (The ratio of minutes to pixels)
				row += ("<div class='course' style='left:" + ((((schedule[b][2] % 1440) - (7 * 60)) * (cellWidth / 60))) + "px;width:" + ((schedule[b][3] - schedule[b][2]) * (cellWidth / 60)) + "px;'>" + schedule[b][0] + "</div>");
			}
		}

		//Creates the last part of the table after the data is generated
		row += "</td><td class='9am'></td><td class='10am'></td><td class='11am'></td><td class='12am'></td><td class='1pm'></td><td class='2pm'></td><td class='3pm'></td><td class='4pm'></td><td class='5pm'></td><td class='6pm'></td><td class='7pm'></td><td class='8pm'></td><td class='9pm'></td><td class='10pm'></td><td class='11pm'></td></tr>"
		
		//Add the table data generated to the table in the webpage
		document.getElementById("scheduleTable").innerHTML += row;
	}
}

//The function to send requests to the webserver
//Uses asynchronous promises in order to prevent statements from executing before needing and to prevent page freezing
async function sendPost(url, userJson) {
	console.log("Sent: ", userJson);
	let message = fetch(url, {
		method: 'POST',
		headers: { //Header for the request packet
			'Accept': 'application/json', //Tell the server that it accepts JSON as a return message
			'Content-Type': 'application/json' //Make it handle only JSON
		},
		body: JSON.stringify(userJson) //Store the userdata in the body attribuite of the json message
	}).then(response => response.json()) //When the promise resolves
		.then(object => { //When the previous response is completed and convert the object into JSON
			console.log("Recieved: ", object);
			var action = object["action"];

			if (action == "scheduleRes") { //If the action of the message is a response to the schedule request, create the table
				scheduleData = object["body"];
				makeTable();
			}
			else if (action == "loginRes") { //If the action of the message is a response to the login request, check the status and do what needs to be done
				if (object["body"] == "LoginUserSuccess") {
					document.cookie = ("token=" + object["token"] + ";")
					console.log(getCookie("token"));
					window.location.href = makeURL("landing");
				}
				else {
					alert("Incorrect Username or Password!");
				}
			}
			else if (action == "registerRes") { //If the action of the message is a response to the login request, check the status and do what needs to be done
				if (object["body"] == "RegisterUserSuccess") {
					window.location.href = makeURL("login");
				}
				else if(object["body" == "AddUserDuplicate"]){
					alert("User already exists!");
				}
				else {
					alert("Failed to create user!\nUser may already exist");
				}
			}
			else if (action == "editRes") { //If the action of the message is a response to the login request, check the status and do what needs to be done
				if (object["body"] == "EditUserSuccess") {
					window.location.href = makeURL("login");
				}
				else {
					alert("Incorrect username or password");
				}
			}
			else if (action == "forgetRes") { //If the action of the message is a response to the login request, check the status and do what needs to be done
				if (object["body"] == "PasswordUserSucess") {
					window.location.href = makeURL("login");
				}
				else {
					alert("Incorrect username or question response!");
				}
			}
		}).catch(function (err) {
			console.log(err); //Error catch
		});
}