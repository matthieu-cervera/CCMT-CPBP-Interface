//CUSTOMIZE YOUR NEW MELODY part
let measurebck = document.getElementsByClassName("meas-backg");
let firstGroupSepMes = []; //Dynamic array where we will store the first group in the Separated measures
//code for the consecutive measures
if (measurebck) {
    for (let i = 0; i < measurebck.length; i++) {
        measurebck[i].addEventListener('click', () => {
            if(consCarItem.classList.contains("active")){ //the measures will perform as Continuous only (red color)
                switch (i) {
                    case 0:
                        if (measurebck[(i + 1)].classList.contains("ActiveContinuous")) {
                            changeBckColor(i);
                        }
                        else {
                            if (measurebck[(i)].classList.contains("ActiveContinuous") && activeMeasureCounter() == 1) {
                                changeBckColor(i);
                            }
                            else {
                                disappearAllMeasures();
                                changeBckColor(i);
                            }
                        }
                        break;
    
                    case 31:
                        if (measurebck[(i - 1)].classList.contains("ActiveContinuous")) {
                            changeBckColor(i);
                        }
                        else {
                            if (measurebck[(i)].classList.contains("ActiveContinuous") && activeMeasureCounter() == 1) {
                                changeBckColor(i);
                            }
                            else {
                                disappearAllMeasures();
                                changeBckColor(i);
                            }
                        }
                        break;
                    default:
                        if (measurebck[(i - 1)].classList.contains("ActiveContinuous") || measurebck[(i + 1)].classList.contains("ActiveContinuous")) {
                            if (measurebck[(i - 1)].classList.contains("ActiveContinuous") && measurebck[(i + 1)].classList.contains("ActiveContinuous")) {
                                disappearAllMeasures();
                            }
                            else {
                                changeBckColor(i);
                            }
                        }
                        else {
                            if (measurebck[(i)].classList.contains("ActiveContinuous") && activeMeasureCounter() == 1) {
                                changeBckColor(i);
                            }
                            else {
                                disappearAllMeasures();
                                changeBckColor(i);
                            }
                        }
                }
            }
            else { //the measures will perform as Separated only (blue color)
                if(!switchSepMeasure.checked){ //if we are selecting the first group of measures performs like continuous
                    switch (i) {
                        case 0:
                            if (measurebck[(i + 1)].classList.contains("ActiveSeparated")) {
                                changeBckColor(i);
                            }
                            else {
                                if (measurebck[(i)].classList.contains("ActiveSeparated") && activeMeasureCounter() == 1) {
                                    changeBckColor(i);
                                }
                                else {
                                    disappearAllMeasures();
                                    changeBckColor(i);
                                }
                            }
                            break;
        
                        case 31:
                            if (measurebck[(i - 1)].classList.contains("ActiveSeparated")) {
                                changeBckColor(i);
                            }
                            else {
                                if (measurebck[(i)].classList.contains("ActiveSeparated") && activeMeasureCounter() == 1) {
                                    changeBckColor(i);
                                }
                                else {
                                    disappearAllMeasures();
                                    changeBckColor(i);
                                }
                            }
                            break;
                        default:
                            if (measurebck[(i - 1)].classList.contains("ActiveSeparated") || measurebck[(i + 1)].classList.contains("ActiveSeparated")) {
                                if (measurebck[(i - 1)].classList.contains("ActiveSeparated") && measurebck[(i + 1)].classList.contains("ActiveSeparated")) {
                                    disappearAllMeasures();
                                }
                                else {
                                    changeBckColor(i);
                                }
                            }
                            else {
                                if (measurebck[(i)].classList.contains("ActiveSeparated") && activeMeasureCounter() == 1) {
                                    changeBckColor(i);
                                }
                                else {
                                    disappearAllMeasures();
                                    changeBckColor(i);
                                }
                            }
                    }
                }
                else { //when we select the second group of measurements directly select the group of measurements where the constraint it's applied
                    //when we mark the checkbox (switchSeparatedMeasure) we store in the checkbox the activeMeasureCounter() value
                    let measuresFirstGroupLength = parseInt(switchSepMeasure.value);
                    let measuresSecondGroupLenght;
                    switch (durSepSelector.selectedIndex) {
                        case 2: //Double up each duration
                            measuresSecondGroupLenght = 2 * measuresFirstGroupLength;
                            break;
                        case 3: //Halve each duration
                            measuresSecondGroupLenght = Math.round((measuresFirstGroupLength/2));
                            break;
                        default: 
                        measuresSecondGroupLenght = measuresFirstGroupLength;
                    }
                    if((i > firstGroupSepMes[(firstGroupSepMes.length - 1)]) && (i + measuresSecondGroupLenght) <= numberMeasuresDisplayed()){
                        activeSecondGroupMeasures(i, measuresSecondGroupLenght);
                    }
                }   
            }
            
            activeMeasureCounter(); //we just recall this function to activate the Proxy Object and control the Save Button
        });
    }
}

//FUNCTION THAT CHECKS WHAT NUMBER OF MEASURES ARE DISPLAYED
function numberMeasuresDisplayed(){
    if(measures32row[0].classList.contains("active")){
        return 32;
    }
    else if(measures16row[0].classList.contains("active")){
        return 16;
    }
    return 8;
}

//FUNCTION THAT CHECKS IF ALL OF THE CONSECUTIVE MEASURES AREN'T ACTIVE & ACTIVATES THEM (this is for the second group of measures)
function activeSecondGroupMeasures(index, length){
    let activeClass = currentActiveClass();
    let measuresActive = false;
    let finalindex = index + length;
    let musicScoreLength = numberMeasuresDisplayed();
    for (var i = 0; i < musicScoreLength; i++) {
        if (!firstGroupSepMes.includes(i)) {
            measurebck[(i)].classList.remove(activeClass);
        }
    }
    for(var j = index; (j < finalindex) && !measuresActive; j++){
        if(measurebck[j].classList.contains(activeClass)){
            measuresActive = true;
        }
    }
    if(!measuresActive){
        for(var j = index; (j < finalindex) && !measuresActive; j++){
            measurebck[j].classList.add("ActiveSeparated");
        }
    }
}

//FUNCTION WHERE WE FIND OUT WHAT IS THE CURRENT ACTIVE CLASS
function currentActiveClass(){
    let activeClassString = "ActiveContinuous";
    if(!consCarItem.classList.contains("active")){
        activeClassString = "ActiveSeparated";
    }
    return activeClassString;
    
}
//FUNCTION THAT CHANGES THE COLOR OF THE SELECTED MEASURE
function changeBckColor(measureNumber) {
    let activeClass = currentActiveClass();
    if (measurebck[measureNumber].classList.contains(activeClass)) {
        measurebck[measureNumber].classList.remove(activeClass);
    } else {
        measurebck[measureNumber].classList.add(activeClass);
    }
}

//SELECT NUMBER OF MEASURES - DROPDOWN BUTTONS
var measures8dropDown = document.getElementById("measures8-dropdown");
var measures16dropDown = document.getElementById("measures16-dropdown");
var measures32dropDown = document.getElementById("measures32-dropdown");

var nbActiveBars = 8;

//MEASURES WHERE IT AFFECTS
var measures16row = document.getElementsByClassName("measure16"); //this is only one row, the div that contains the 16 (8 to 15) measures -> Collection with only one row
var measures32row = document.getElementsByClassName("measure32"); //2 rows, the divs that contains the 32 (16 to 31) measures -> Collection with 2 rows of 8 bars

if (measures8dropDown) {
    measures8dropDown.addEventListener('click', display8bars);
}

if (measures16dropDown) {
    measures16dropDown.addEventListener('click', display16bars);
}

if (measures32dropDown) {
    measures32dropDown.addEventListener('click', display32bars);
}

function display8bars() {
    disappearMeasuresWhen8Selected();
    measures16row[0].classList.remove("active");
    for (var i = 0; i < measures32row.length; i++) { 
        measures32row[i].classList.remove("active");
    }
    nbActiveBars = 8;
}

function display16bars() {
    disappearMeasuresWhen16Selected();
    measures16row[0].classList.add("active");
    for (var i = 0; i < measures32row.length; i++) {
        measures32row[i].classList.remove("active");
    }
    nbActiveBars = 16;

}
function display32bars() {
    measures16row[0].classList.add("active");
    for (var i = 0; i < measures32row.length; i++) {
        measures32row[i].classList.add("active");
    }
    nbActiveBars = 32;
}
//ACTIVE MEASURE COUNTER
    //we have to do it with a proxy ///Indeed, it was not necessary doing it with a proxy
const counterObj = {
    value : 0
};

const handler1 = {
    
    set: (o, property, newValue) => {
        if(consCarItem.classList.contains("active")){ //Save button behaviour for Consecutive Measures
            if(newValue < 1) {
                saveConstraintsButton.classList.add("disabled-general");
            }
            else {
                saveConstraintsButton.classList.remove("disabled-general");
            }
        }
        else { //Save button behaviour for Separated Measures
                if(newValue == 0){
                switchSepMeasure.disabled = true;
                saveConstraintsButton.classList.add("disabled-general");
            } else {
                switchSepMeasure.disabled = false;
                if((switchSepMeasure.checked == true) && (newValue > firstGroupSepMes.length)){ //we make sure that we have selected the second group of measures
                    saveConstraintsButton.classList.remove("disabled-general");
                }
                else {
                    saveConstraintsButton.classList.add("disabled-general");
                }
            }

        }
        
        o[property] = newValue;
    }
};
const counterProxy = new Proxy(counterObj, handler1);


function activeMeasureCounter() {
    let activeClass = currentActiveClass();
    let j = 0;
    let musicScoreLength = numberMeasuresDisplayed();
    for (var i = 0; i < musicScoreLength; i++) {
        if (measurebck[(i)].classList.contains(activeClass)) {
            j++;
        }
    }
    counterProxy.value = j;
    return j;
}

//DELETE MARKED MEASURES WHEN THE MEASURE ROW DISSAPEARS
function disappearAllMeasures() {
    let activeClass = currentActiveClass();
    for (var i = 0; i < 8; i++) {
        measurebck[i].classList.remove(activeClass);
    }
    disappearMeasuresWhen8Selected();
}

function disappearMeasuresWhen8Selected() {
    let activeClass2 = currentActiveClass();
    for (var j = 8; j < 16; j++) {
        measurebck[j].classList.remove(activeClass2);
    }
    disappearMeasuresWhen16Selected();
}

function disappearMeasuresWhen16Selected() {
    let activeClass3 = currentActiveClass();
    for (var i = 16; i < 32; i++) {
        measurebck[i].classList.remove(activeClass3);
    }
    //we call to activeMeasureCounter()  to disable the Save Button when we have marked measures (ex: 30 and 31 measures selected)
    //but we "unmark" them via selecting a fever number of bars (from 32 bars to 8)
    activeMeasureCounter(); 
}


//DISABLE / ENABLE MUSIC SCORE

let pitchContSelector = document.getElementById("idConstraintPitchContGroup");
let durContSelector = document.getElementById("idConstraintDurationContGroup");
let pitchSelectorText = pitchContSelector.options[pitchContSelector.selectedIndex].text;
let durSelectorText = durContSelector.options[durContSelector.selectedIndex].text;
let pitchSepSelector = document.getElementById("idConstraintPitchSepGroup");
let durSepSelector = document.getElementById("idConstraintDurationSepGroup");
let musicScore = document.getElementById("musicscore");
let consCarItem = document.getElementById("consCarItem");
let arrowPrev = document.getElementById("carouselPrev");
let arrowPost = document.getElementById("carouselNext");
let saveConstraintsButton = document.getElementById("saveDurAndPitchRow");
let switchSepMeasure = document.getElementById("idInitialSepMeas");
let nextPageButton = document.getElementById("nextPageButton");

if (pitchContSelector) {
    pitchContSelector.addEventListener('click', enableDisableContent);
}

if (durContSelector) {
    durContSelector.addEventListener('click', enableDisableContent);
}

if (pitchSepSelector) {
    pitchSepSelector.addEventListener('click', enableDisableContent);
}

if(durSepSelector) {
    durSepSelector.addEventListener('click', enableDisableContent);
}

if(arrowPrev) {
    arrowPrev.addEventListener('click', enableDisableContentArrows);
}

if(arrowPost) {
    arrowPost.addEventListener('click', enableDisableContentArrows);
}

if(saveConstraintsButton){
    saveConstraintsButton.addEventListener('click', saveConstraint);
}

if(nextPageButton){
    nextPageButton.addEventListener('click',removeUnusedConstraints);
}


if(switchSepMeasure){
    switchSepMeasure.addEventListener('click', countFirstGroup);
}

function enableDisableContent() {
    if (consCarItem.classList.contains("active")) {
        if (pitchContSelector.selectedIndex == 0 && durContSelector.selectedIndex == 0) {
            musicScore.classList.add("disabled-general");
            //saveConstraintsButton.classList.add("disabled-general"); Not necessary, this will be disabled when we call the proxy
            disappearAllMeasures();
        }
        else {
            musicScore.classList.remove("disabled-general");    
        }
    } else {
        if(pitchSepSelector.selectedIndex == 0 && durSepSelector.selectedIndex == 0){
            musicScore.classList.add("disabled-general");
            //saveConstraintsButton.classList.add("disabled-general"); Not necessary, this will be disabled when we call the proxy
            switchSepMeasure.checked = false;
            switchSepMeasure.disabled = true;
            if(firstGroupSepMes.length > 0){
                for(let j = 0; j < firstGroupSepMes.length; j++){
                    measurebck[firstGroupSepMes[j]].classList.remove("Saved");
                }
                firstGroupSepMes = []; //we need to empty the dynamic array because we remove every measure
            }
            disappearAllMeasures();
        }
        else if(firstGroupSepMes.length > 0){ //this implies we are selecting the second measures group, we have a first measure group
            let activeClass = currentActiveClass();
            let musicScoreLength = numberMeasuresDisplayed();
            for (var i = 0; i < musicScoreLength; i++) {
                if (!firstGroupSepMes.includes(i)) {
                    measurebck[(i)].classList.remove(activeClass);
                }
            }
            counterProxy.value = firstGroupSepMes.length;
        } else {
            musicScore.classList.remove("disabled-general");
        }
    }
}

function enableDisableContentArrows() {
    if(consCarItem.classList.contains("active")) {
        pitchContSelector.selectedIndex = 0;
        durContSelector.selectedIndex = 0;   
    } else {
        pitchSepSelector.selectedIndex = 0; 
        durSepSelector.selectedIndex = 0;
        switchSepMeasure.checked = false;
        switchSepMeasure.disabled = true;
        if(firstGroupSepMes.length > 0){
            for(let j = 0; j < firstGroupSepMes.length; j++){
                measurebck[firstGroupSepMes[j]].classList.remove("Saved");
            }
            firstGroupSepMes = []; //we need to empty the dynamic array because we remove every measure, and its Saved class
        }
    }
    disappearAllMeasures(); 
    //saveConstraintsButton.classList.add("disabled-general"); not necessary, dissapearAllMeasures() calls ActiveMeasuresCounter() and desactivates the savebutton
    musicScore.classList.add("disabled-general");
}

function countFirstGroup() {
    switchSepMeasure.value = firstGroupSepCounter();
}

function firstGroupSepCounter() {
    let activeClass = currentActiveClass();
    let musicScoreLength = numberMeasuresDisplayed();
    if(switchSepMeasure.checked == true){
        firstGroupSepMes = [];
        let j = 0;
        for (var i = 0; i < musicScoreLength; i++) {
            if (measurebck[(i)].classList.contains(activeClass)) {
                firstGroupSepMes.push(i+1); //this only makes sense for the Separated sequence, that's why we sort of implement again the method 'Active measures counter'
                measurebck[(i)].classList.add("Saved");
                j++;
            }
        }
        counterProxy.value = j;
        return j;
    }
    else if(switchSepMeasure.checked == false) {
        for (var i = 0; i < musicScoreLength; i++) {
            if (!firstGroupSepMes.includes(i)) {
                measurebck[(i)].classList.remove(activeClass);
            } else {
                measurebck[(i)].classList.remove("Saved");
            }

        }
        counterProxy.value = firstGroupSepMes.length;
        return firstGroupSepMes.length; //not necessary when the check is false
    }    
}

//SAVE CONSTRAINTS IN A LIST

let pitchConstraints = [];
let durationConstraints = [];
let pitchConstraintForm = document.getElementById("pitchConstraintString");
let durConstraintForm = document.getElementById("durConstraintString");


function saveConstraint() {
    let stringPitchConst;
    let stringDurationConst;
    let musicScoreLength = numberMeasuresDisplayed();
    let activeClass = currentActiveClass();
    let firstMeasureFound = false;
    let firstMeasureNumber;
    let lastMeasureFound = false;
    let lastMeasureNumber;

    //we get the indexes of the continuous measures
    //Continuous -> Indexes of the continuous measures
    //Separated -> Indexes of the second group of continuous measures

    if(activeClass == "ActiveContinuous"){
        //we get the indexes of the continuous measures
        //Continuous -> Indexes of the continuous measures
        for(var i = 0; i < musicScoreLength && !lastMeasureFound; i++){
            if(!firstMeasureFound && measurebck[i].classList.contains(activeClass)){
                firstMeasureFound = true;
                firstMeasureNumber = i+1;
                if (i==musicScoreLength-1){
                    lastMeasureNumber = i+1;
                }
            }
            else if(firstMeasureFound && measurebck[i].classList.contains(activeClass)){
                lastMeasureNumber = i+1;
            }
            else if(firstMeasureFound){
                lastMeasureNumber = i;
                lastMeasureFound = true;
            }
        }
        
        if(pitchContSelector.selectedIndex != 0){
            if (pitchContSelector.value.includes("Fixed")) {
                var pitchFixValue = document.getElementById('pitchFix').value;
            }
            else {
                var pitchFixValue = "";
            }
            stringPitchConst = pitchContSelector.value + pitchFixValue + ":" + firstMeasureNumber + ":" + lastMeasureNumber + ";";

            // The user fixed several values:
            if (pitchContSelector.value.includes("Token")){
                stringPitchConst = pitchContSelector.value + ":" + document.getElementById('tokenIdx').value + ":" + document.getElementById('pitchChosen').value + ";";
            }

            pitchConstraints.push(stringPitchConst);
        }
        if(durContSelector.selectedIndex != 0){
            if (durContSelector.value.includes("Fixed")) {
                var durationFixValue = document.getElementById('durationFix').value;
            }
            else {
                var durationFixValue = "";
            }
            stringDurationConst = durContSelector.value + durationFixValue + ":" + firstMeasureNumber + ":" + lastMeasureNumber + ";";
            durationConstraints.push(stringDurationConst);
        }
    } else {
        //we get the indexes of the continuous measures
        //Separated -> Indexes of the second group of continuous measures
        //we create the distintion because we have to check if it does not contain Saved class
        for(var i = 0; i < musicScoreLength && !lastMeasureFound; i++){
            if(!firstMeasureFound && measurebck[i].classList.contains(activeClass) && !measurebck[i].classList.contains("Saved")){
                firstMeasureFound = true;
                firstMeasureNumber = i+1;
                if (i==musicScoreLength-1){
                    lastMeasureNumber = i+1;
                }
            }
            else if(firstMeasureFound && measurebck[i].classList.contains(activeClass) && !measurebck[i].classList.contains("Saved")){
                lastMeasureNumber = i+1;
            }
            else if(firstMeasureFound){
                lastMeasureFound = true;
            }
        }
        //unique case when the second group of consecutive measures == 1
        if(lastMeasureNumber == "undefined"){
            lastMeasureNumber = firstMeasureNumber;
        }
        if(pitchSepSelector.selectedIndex != 0){
            stringPitchConst = pitchSepSelector.value + ":" + firstGroupSepMes[0] + ":" + firstGroupSepMes[firstGroupSepMes.length - 1] + ":" + firstMeasureNumber + ":" + lastMeasureNumber + ";";
            pitchConstraints.push(stringPitchConst);
        }
        if(durSepSelector.selectedIndex != 0){
            stringDurationConst = durSepSelector.value + ":" + firstGroupSepMes[0] + ":" + firstGroupSepMes[firstGroupSepMes.length - 1] + ":" + firstMeasureNumber + ":" + lastMeasureNumber + ";";
            durationConstraints.push(stringDurationConst);
        }
    }

    enableDisableContentArrows();
    updatePitchConstraintsDisplay();
    updateDurConstraintsDisplay();
    updateConstraintFormContent();


}

function updateConstraintFormContent() {
    let durString = new String;
    let pitchString = new String;
    for (var i=0; i<durationConstraints.length; i++){
        durString += durationConstraints[i];
    }
    for (var i=0; i<pitchConstraints.length; i++){
        pitchString += pitchConstraints[i];
    }
    durConstraintForm.setAttribute("value", durString)
    pitchConstraintForm.setAttribute("value", pitchString)
}

// DISPLAY CONSTRAINTS
// Functions to update the pitch constraints display
function updatePitchConstraintsDisplay() {
  const constraintsList = document.getElementById("pitch-constraints");
  constraintsList.innerHTML = "";
  for (let i = 0; i < pitchConstraints.length; i++) {
    const constraint = pitchConstraints[i];
    const li = document.createElement("li");
    li.innerHTML = constraint + "              ";
    const removeButton = document.createElement("button");
    removeButton.innerHTML = "&times;";
    removeButton.style.cssText  = "background-color: #9b1c31;color: #fff;font-size: 15px;border: none;border-radius: 5px;padding: 2px 6px;cursor: pointer;text-align: center;text-decoration: none;display: inline-block;transition-duration: 0.4s;margin: 10px; ";
    removeButton.addEventListener("click", function() {
      removePitchConstraint(i);
    });
    li.appendChild(removeButton);
    constraintsList.appendChild(li);
  }
}

function removePitchConstraint(index) {
  pitchConstraints.splice(index, 1);
  updatePitchConstraintsDisplay();
}


// Functions to update the duration constraints display
function updateDurConstraintsDisplay() {
  const constraintsList = document.getElementById("dur-constraints");
  constraintsList.innerHTML = "";
  for (let i = 0; i < durationConstraints.length; i++) {
    const constraint = durationConstraints[i];
    const li = document.createElement("li");
    li.innerHTML = constraint + "              ";
    const removeButton = document.createElement("button");
    removeButton.innerHTML = "&times;";
    removeButton.style.cssText  = "background-color: #9b1c31;color: #fff;font-size: 15px;border: none;border-radius: 5px;padding: 2px 6px;cursor: pointer;text-align: center;text-decoration: none;display: inline-block;transition-duration: 0.4s;margin: 10px;";
    removeButton.addEventListener("click", function() {
      removeDurConstraint(i);
    });
    li.appendChild(removeButton);
    constraintsList.appendChild(li);
  }
}

function removeDurConstraint(index) {
  durationConstraints.splice(index, 1);
  updateDurConstraintsDisplay();
}


// Remove unused constraints when clicked 'continue' button

function removeUnusedConstraints() {
  // Pitch
  const toRemove = [];
  for (let i = 0; i < pitchConstraints.length; i++) {
    const constraint = pitchConstraints[i];
    const endInt = parseInt(constraint.split(":")[2]);
    const endIntSep = parseInt(constraint.split(":")[constraint.split(":").length - 1])
    if (endInt > nbActiveBars || endIntSep > nbActiveBars) {
      toRemove.push(constraint);
    }
  }

  for (let i = 0; i < toRemove.length; i++) {
    const constraint = toRemove[i];
    const index = pitchConstraints.indexOf(constraint);

    if (index !== -1) {
        removePitchConstraint(index)
        }
    }

  // Duration
  const toRemoveDur = [];
  for (let i = 0; i < durationConstraints.length; i++) {
    const constraint = durationConstraints[i];
    const endInt = parseInt(constraint.split(":")[2]);
    const endIntSep = parseInt(constraint.split(":")[constraint.split(":").length - 1])
    if (endInt > nbActiveBars || endIntSep > nbActiveBars) {
      toRemoveDur.push(constraint);
    }
  }

  for (let i = 0; i < toRemoveDur.length; i++) {
    const constraint = toRemoveDur[i];
    const index = durationConstraints.indexOf(constraint);

    if (index !== -1) {
        removeDurConstraint(index)
        }
    }

}


function pitchConstraintChange() {
    var tokenIdxInput = document.getElementById('tokenIdx');
    var pitchChosenInput = document.getElementById('pitchChosen');
    var pitchFixInput = document.getElementById('pitchFix');

    pitchSelectorText = pitchContSelector.options[pitchContSelector.selectedIndex].text;
  
    // Check if the selected option is 'Increasing'
    if (pitchSelectorText === 'Fix a pitch for a pointed token') {
      tokenIdxInput.style.display = 'block'; // Show the tokenIdx input
      pitchChosenInput.style.display = 'block'; // Show the pitchChosen input
    } 
    else {
      tokenIdxInput.style.display = 'none'; // Hide the tokenIdx input
      pitchChosenInput.style.display = 'none'; // Hide the pitchChosen input
    }
    
    if (pitchSelectorText.includes("Token")) {
        pitchFixInput.style.display = 'block'; // Show the pitchFIx input
      } 
    else {
        pitchFixInput.style.display = 'none'; // Hide the pitchFIx input
      }
  }