function sendUser(action) {
    var userID = document.cookie;
    if (userID == "") {
        userID = Math.random().toString(16).slice(2);
        document.cookie = userID;
    }

    var userInfo = document.getElementsByClassName("userinfo");
    userJson = {};
    for (var a = 0; a < userInfo.length; a++) {
        let info = userInfo[a].id;
        userJson[info] = userInfo[a].value;
    }

    if (action == "login") {
        userJson.action = "loginReq";
    } else if (action == "register") {
        userJson.action = "registerReq";
    } else if (action == "auth") {
        userJson.action = "authReq";
    } else if (action == "info") {
        userJson.action = "info";
    }
    userJson.returnQueue = userID;
    userJson.userID = document.cookie;
    console.log(action);
    sendPost("/app", userJson);
    
}

function sendPost(url, userJson) {
    (async () => {
        console.log("sending" + userJson);
        const rawResponse = await fetch(url, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userJson)
        });
        const content = await rawResponse;
        if(content.body == "success") {
            localStorage.setItem("username", userJson.username);
            window.location.href="landing.html";
        }
        console.log(content);
    })();
}

function validateLogin()
{
    let username = document.getElementById("username").value;
    let password = document.getElementById("password").value;
    if (username == "") 
    {
        alert("Username must be filled out");
        return false;
    }
    else if (password = "")
    {
        alert("Password must be filled out");
        return false;
    }
}

function loginFunctions()
{
    
}  