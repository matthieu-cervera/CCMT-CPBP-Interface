//JAVASCRIPT RELATED TO THE USER STATUS

//display Login Form - we use the class name instead of the ID (bc we have multiple login buttons)
let userStatusButton = document.getElementById("userstatusButton");
let overlayCollection = document.getElementsByClassName("overlayPopUp");
let userstatusFormPopup = document.getElementById("UserStatusID");
let closeuserstatusColl = document.getElementsByClassName("closeUserStatusForm");
let logoutButton = document.getElementById("logoutButton");
let body = document.getElementById("bodyID");
let click = false;

if(userStatusButton){
    userStatusButton.addEventListener('click', openUserStatus);
    userStatusButton.addEventListener('click', clicked);
}


if(closeuserstatusColl){
    for(var i = 0; i < closeuserstatusColl.length; i++){
        closeuserstatusColl[i].addEventListener('click', crossbar);
        closeuserstatusColl[i].addEventListener('click', closeTheUserStatusForm);
    }
}

if(logoutButton){
    logoutButton.addEventListener('click', logout);
}

function logout(){
    //Simply go to the homepage_not_logged
    window.location.href = "http://127.0.0.1:5014/";
}

function clicked() {
    click = true;
}

function crossbar(){
    click = false;
}
function openUserStatus(){
        var stringYMiddle = (window.scrollY + (window.innerHeight * 0.5)).toString() + "px";
        userstatusFormPopup.style.top = stringYMiddle;
        for (var i = 0; i < overlayCollection.length; i++){
            overlayCollection[i].classList.add("active");
        }
        userstatusFormPopup.classList.add("open-popup");
        body.style.overflow = "hidden";
}

function closeTheUserStatusForm(){
    for (var i = 0; i < overlayCollection.length; i++){
        overlayCollection[i].classList.remove("active");
    }
    userstatusFormPopup.classList.remove("open-popup");
    if(!click){
        body.style.overflow = "visible";
    }
}

//delete account
let deleteButton = document.getElementById("deleteButton")
if(deleteButton){
    deleteButton.addEventListener('click', deleteAccount)
}

function deleteAccount(){
    //First Retrieve the user data from FLask(session) and delete the account from the API
    xmlhttpRetrUser = new XMLHttpRequest();
    xmlhttpRetrUser.responseType = 'json';
    xmlhttpRetrUser.open("GET", "http://localhost:5014/getuserdata");
    xmlhttpRetrUser.onreadystatechange = () => {
        if(xmlhttpRetrUser.readyState === XMLHttpRequest.DONE){
            if(xmlhttpRetrUser.status === 200){
                //once we retrieve the data we can send the DELETE request to the API
                var jsonResponse = xmlhttpRetrUser.response;
                urlUser = "http://localhost:5000/api/users/byparameters?username=" + jsonResponse['username'] + "&password=" + jsonResponse['password']
                xmlhttpDeleteUser = new XMLHttpRequest();
                xmlhttpDeleteUser.open("DELETE", urlUser);
                xmlhttpDeleteUser.onreadystatechange = () => {
                    if(xmlhttpDeleteUser.readyState === XMLHttpRequest.DONE){
                        if(xmlhttpDeleteUser.status === 204){
                            //when the request to the API has succeded, it returns a 204 No Content, because it has been deleted
                            //Only when it has been deleted we can come back to the Main Page
                            window.location.href = "http://127.0.0.1:5014/";    
                        }
                    }
                };
                xmlhttpDeleteUser.send();
            }
        }
    };
    xmlhttpRetrUser.send();
}