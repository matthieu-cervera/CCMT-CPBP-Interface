//MIDI Files checker function - ONLY AVAILABLE IN homepage_logged.js


//MAIN PAGE titles
const titlem1 = document.querySelector("#title-1");
const titlem2 = document.querySelector("#title-2");
const tlmt = new TimelineMax();
tlmt.fromTo(titlem1, 1, {y: -1000}, {y: 0});
tlmt.fromTo(titlem2, 1.5, {x: -1000}, {x: 0});

//MAIN PAGE curtain

const hero = document.querySelector(".hero");
const tlmc = new TimelineMax();
tlmc.fromTo(hero, 3, {height: "40%"}, {height: "100%"});
tlmc.fromTo(hero, 3, {width: "40%"}, {width: "100%"});

//MidiFile aeroplane
aeroplane_bck = document.getElementById("aeroplane_bckg_id");

const tll = new TimelineLite();
const flightPath = {
    curviness: 1,
    type: "thru",
    autoRotate: true,
    values: [
        {x: (window.innerWidth/3), y: -130},
        {x: ((window.innerWidth*2)/3), y: 0},
        {x: window.innerWidth, y: -130}
    ]
};

tll.add(
    TweenLite.to("#aeroplanenote", 1, {
        bezier: flightPath,
        ease: Power1.easeInOut
    })
);
var steplength = 1000;
var navheight = document.getElementById("navid").clientHeight;
var aeroplaneobject = document.getElementById("aeroplanenote");
const controller =  new ScrollMagic.Controller();
const scene = new ScrollMagic.Scene({
    triggerElement: ".noteaeroplane-animation",
    duration: steplength*3,
    offset: (navheight * (-1)),
    triggerHook: 0
})
    .setTween(tll)
    .setPin(".noteaeroplane-animation")
    .addTo(controller)
    .on("progress", callbackLogoChanger);


    function callbackLogoChanger(event){
        if(scene.progress() < (1/3)){
            aeroplaneobject.setAttribute("src", "/static/images/midifile.png");
        } else if((scene.progress() >= (1/3)) && (scene.progress() < (2/3))){
            aeroplaneobject.setAttribute("src", "/static/images/neuralnetwork.png");
        } else if(scene.progress() >= (2/3)){
            aeroplaneobject.setAttribute("src", "/static/images/notes.png");
        }
    }

//Containers that follow MIDIAeroplane
const controller2 =  new ScrollMagic.Controller();
var aeroplaneheight = document.getElementById("aeroplane-sec").clientHeight;
var navPlusAeroplaneHeight = navheight + aeroplaneheight;
var wipeAnimation = new TimelineMax()
    // animate to second panel
    .to("#slideContainer", 0.5, {z: -150, delay: 3})		// move back in 3D space
    .to("#slideContainer", 1,   {x: "-33,33333333333333333333%"})	// change from the first panel to the second panel
    .to("#slideContainer", 0.5, {z: 0})				// move back to origin in 3D space
    // animate to third panel
    .to("#slideContainer", 0.5, {z: -150, delay: 2.5}) // move back in 3D space
    .to("#slideContainer", 1,   {x: "-66,66666666666666666666%"}) // change from the second panel to the third panel
    .to("#slideContainer", 0.5, {z: 0}); // move back to origin in 3D space

// create scene to pin and link animation
new ScrollMagic.Scene({
    triggerElement: "#pinContainer",
    triggerHook: "onLeave",
    offset: (navPlusAeroplaneHeight)*(-1),
    duration: "300%"
    })
    .setPin("#pinContainer")
    .setTween(wipeAnimation)
    .addTo(controller2)
    .on("start", callbackContainer);

    function callbackContainer(event){
        document.getElementById("textFCont").style.color = "#Eff0f5";
        var styleTextFirstCont = document.createElement('style');
        styleTextFirstCont.innerHTML = `
        .typewriter p {

            overflow: hidden; /* Ensures the content is not revealed until the animation */
            border-right: 2px solid white; /* The typwriter cursor, how big is it */
            white-space: nowrap; /* Keeps the content on a single line */
            margin: 0 auto; /* Gives that scrolling effect as the typing happens */
            letter-spacing: 2px; /* Adjust as needed */
            animation: 
              typing 4s steps(40, end),
              blink-caret .5s step-end infinite;
          }
          
          /* The typing effect */
          @keyframes typing {
              from { width: 0% }
              to { width: 100% }
            }
          
            @keyframes blink-caret {
              from, to { border-color: transparent }
              50% { border-color: white }
            }
        `;
        document.head.appendChild(styleTextFirstCont);

    }

    //MAIN PAGE PopUp Forms

    //display Login Form - we use the class name instead of the ID (bc we have multiple login buttons)
    let loginButton = document.getElementsByClassName("loginButton");
    let signupButton = document.getElementById("signupButton");
    let loginFormPopup = document.getElementById("LoginFormID");
    let signupFormPopup = document.getElementById("SignupFormID");
    let closebuttonLogIn = document.getElementById("closeLogInForm");
    let closebuttonSignUp = document.getElementById("closeSignUpForm");
    let overlayCollection = document.getElementsByClassName("overlayPopUp");
    let body = document.getElementById("bodyID");
    let click = false;

    if(loginButton){
        for(var i = 0; i < loginButton.length; i++){
            loginButton[i].addEventListener('click', clicked);
            loginButton[i].addEventListener('click', openTheLoginForm);
        }
    }
    if(signupButton){
        signupButton.addEventListener('click', openTheSignUpForm);
    }

    if(closebuttonSignUp){
        closebuttonSignUp.addEventListener("click", crossbar);
        closebuttonSignUp.addEventListener("click", closeTheSignUpForm);
    }

    if(closebuttonLogIn){
        closebuttonLogIn.addEventListener("click", crossbar);
        closebuttonLogIn.addEventListener("click", closeTheLogInForm);
    }

    function clicked() {
        click = true;
    }

    function crossbar(){
        click = false;
    }


    function openTheLoginForm() {

            closeTheSignUpForm();
            var stringYMiddle = (window.scrollY + (window.innerHeight * 0.5)).toString() + "px";
            loginFormPopup.style.top = stringYMiddle;
            for (var i = 0; i < overlayCollection.length; i++){
                overlayCollection[i].classList.add("active");
            }
            loginFormPopup.classList.add("open-popup");
            body.style.overflow = "hidden";
        
    }
    
    function closeTheLogInForm(){
        for (var i = 0; i < overlayCollection.length; i++){
            overlayCollection[i].classList.remove("active");
        }
        loginFormPopup.classList.remove("open-popup");
        if(!click){
            body.style.overflow = "visible";
        }
    }

    function openTheSignUpForm(){
            closeTheLogInForm();
            var stringYMiddle = (window.scrollY + (window.innerHeight * 0.5)).toString() + "px";
            signupFormPopup.style.top = stringYMiddle;
            for (var i = 0; i < overlayCollection.length; i++){
                overlayCollection[i].classList.add("active");
            }
            signupFormPopup.classList.add("open-popup");    
    }

    function closeTheSignUpForm(){
        for (var i = 0; i < overlayCollection.length; i++){
            overlayCollection[i].classList.remove("active");
        }
        signupFormPopup.classList.remove("open-popup");
        if(!click){
            body.style.overflow = "visible";
        }
    }

    //RESTRICT THE KEYBOARD INPUT
    let inputs = document.getElementsByClassName("keyboardconst");
    let feedbckCollection = document.getElementsByClassName("feedbck");
    // SIGN UP FORM
    // 0 -> Username 
    // 1 -> Email 
    // 2 -> Password
    // 3 -> Repeated Password
    // LOGIN FORM
    // 4 -> Username Login
    // 5 -> Password Login
    let regexp = /[^a-z0-9.@\-_ñ]/gi;
    if(inputs){
        for (let j = 0; j < inputs.length; j++){
            inputs[j].addEventListener('keyup', (e) => {
                inputs[j].value = inputs[j].value.replace(regexp, "");
            });
        }
    }


    //SIGNUP AND LOGIN BUTTONS THAT CALL THE API
    //the inputs fields are contained in the inputs Collection
    let signupAPIbutton = document.getElementById("signupAPI");
    let loginAPIbutton = document.getElementById("loginAPI");
    let urlUsername = "http://127.0.0.1:5000/api/users/byparameters/usr?username=";
    let urlEmail = "http://127.0.0.1:5000/api/users/byparameters/eml?email=";


    if(signupAPIbutton && loginAPIbutton) {
        signupAPIbutton.addEventListener('click', signup);
        loginAPIbutton.addEventListener('click', login);
    }

    function signup(){
        let anyEmpties = false;
        for (let i = 0; i < 4; i++){
            if(inputEmpty(i)){
                anyEmpties = true;
            }
        }
        if(!anyEmpties) {
            //we check if the passwords are equal
            if((inputs[2].value === inputs[3].value) && (inputs[2].value != "")){
                inputs[2].classList.remove("is-invalid");
                inputs[2].classList.add("is-valid");
                inputs[3].classList.remove("is-invalid");
                inputs[3].classList.add("is-valid");

                xhr = new XMLHttpRequest();
                xhr.open("POST", address + "register");
                const formData = new FormData();
                formData.append('username', inputs[0].value);
                formData.append('email', inputs[1].value);
                formData.append('password', inputs[2].value);
                xhr.onload = function() {
                      if (xhr.status === 200) {
                        // Handle the successful response
                        inputs[0].classList.add("is-valid");
                        inputs[1].classList.add("is-valid");
                        window.location.href = address + "homepage_logged";
                        }
                      else {
                        // Handle the error response
                        const response = JSON.parse(xhr.responseText);
                        if (xhr.status === 400) {
                          inputs[1].classList.remove("is-valid");
                          inputs[1].classList.add("is-invalid");
                          inputs[0].classList.add("is-valid");
                          feedbckCollection[1].innerHTML= "Email exists already";
                        }
                        if (xhr.status == 409) {
                            inputs[0].classList.remove("is-valid");
                            inputs[0].classList.add("is-invalid");
                            feedbckCollection[0].innerHTML= "Username already taken";
                        }
                      }
                };
                xhr.send(formData);

                }
             }
            else
            {
                inputs[2].classList.remove("is-valid");
                inputs[2].classList.add("is-invalid");
                feedbckCollection[2].innerHTML= "Passwords must match";
                inputs[3].classList.remove("is-valid");
                inputs[3].classList.add("is-invalid");
                feedbckCollection[3].innerHTML= "Passwords must match";
            }
    }

    function login(){
    let anyEmpties = false;
    for (let i = 4; i < 6; i++){
        if(inputEmpty(i)){
            anyEmpties = true;
            }
        }
    if(!anyEmpties) {
            xhr = new XMLHttpRequest();
            xhr.open("POST", address + "login");
            const formData = new FormData();
            formData.append('username', inputs[4].value);
            formData.append('password', inputs[5].value);
            xhr.onload = function() {
                  if (xhr.status === 200) {
                    // Handle the successful response
                    window.location.href = address + "homepage_logged";
                    }
                  else {
                    // Handle the error response
                    const response = JSON.parse(xhr.responseText);
                    if (xhr.status === 400) {
                        inputs[4].classList.remove("is-valid");
                        inputs[4].classList.add("is-invalid");
                        inputs[5].classList.remove("is-valid");
                        inputs[5].classList.add("is-invalid");
                        feedbckCollection[4].innerHTML= "User might not exist";
                        feedbckCollection[5].innerHTML= "Password might be wrong";
                    }
                  }
                };
            xhr.send(formData);
            }
    }


    function inputEmpty(index){
        let empty = false; 
        if(inputs[index].value === ""){
            empty = true;
            inputs[index].classList.remove("is-valid");
            inputs[index].classList.add("is-invalid");
            feedbckCollection[index].innerHTML= "Cannot be empty";
        }
        else {
            inputs[index].classList.remove("is-invalid");
            feedbckCollection[index].innerHTML= "";
        }
        return empty;
    }

    
    /*
    loginbutton[0] = navbar login button
    loginbutton[1] = login button in the carousel
    loginbutton[2] = login button inside of the SignUp form
    */

 


      
    

   
    

   

	