// POST turing test answer
let sendAnswerButton = document.getElementById("answerButton");

sendAnswerButton.addEventListener("click", function sendTuringTestAnswer() {
        var choice = -1;
        var radioInputs = document.getElementsByName('radioTuring');
        for (var i = 0; i < radioInputs.length; i++) {
            if (radioInputs[i].checked) {
                choice = radioInputs[i].value;
                break;
            }
        }
        window.location.href= address + 'turing_test_result?choice=' + choice + '&name=' + midiFilePath;
      }
        );




