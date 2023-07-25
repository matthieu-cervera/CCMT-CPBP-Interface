//RESTRICT THE KEYBOARD INPUT
let inputkeyboard = document.getElementById("inputkeyboard")
//let body1 = document.getElementById("bodyID");
let melodyFormPopup = document.getElementById("MelodyFormID");
let sendButton = document.getElementById("sendButtonID");
var stringYMiddle = (window.scrollY + (window.innerHeight * 0.5)).toString() + "px";
melodyFormPopup.style.top = stringYMiddle;
melodyFormPopup.classList.add("open-popup");
//body1.style.overflow = "hidden";

let regexp = /[^0-9]/gi;
if(inputkeyboard){
    inputkeyboard.addEventListener('keyup', acceptCharacter);
    inputkeyboard.addEventListener('keyup', enabDisabSendButton)
}

function acceptCharacter(){
    inputkeyboard.value = inputkeyboard.value.replace(regexp, "");
}

function enabDisabSendButton(){
    if(inputkeyboard.value != ""){
        sendButton.classList.remove("disabled-general");
    }
    else{
        sendButton.classList.add("disabled-general");
    }
}