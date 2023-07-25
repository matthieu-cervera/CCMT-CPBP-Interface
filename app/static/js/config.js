const address = "http://localhost:5001/";

//CODE TO MAKE THE USER SCROLL TO THE TOP OF THE DOCUMENT

let bcktop = document.getElementById("btn-back-to-top");

if (bcktop) {
    bcktop.addEventListener("click", backToTop);
}

function backToTop() {
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
}