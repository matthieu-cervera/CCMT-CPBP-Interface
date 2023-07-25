const deleteButtons = document.querySelectorAll('.delete-button');

deleteButtons.forEach(button => {
     button.addEventListener('click', function(event) {
        event.preventDefault(); // Prevent default form submission behavior

        // Get the form associated with the delete button
        const form = this.parentNode;

        xhr = new XMLHttpRequest();
        xhr.open("POST", address + "sampleDelete");
        const formData = new FormData(form);

        xhr.onload = function() {
                if (xhr.status === 200) {
                    alert("deleted");
                    button.classList.add("disabled-general");
                }
                else {
                    const response = JSON.parse(xhr.responseText);
                    if (xhr.status == 409) {
                        alert(response);
                    }
                    if (xhr.status == 400) {
                        alert(response);
                    }
                }
        };
        xhr.send(formData);
    }
    )
})
