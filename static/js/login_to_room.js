document.getElementById("submit_button").addEventListener("submit", (event)=> {
    
    event.preventDefault();

    const room_name_value = document.getElementById("room_name").value;
    const password_value = document.getElementById("password").value;

    console.log("request sent");

    fetch("/login_to_room", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            room_name: room_name_value,
            password: password_value,
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("resaponse received");
        if (data['status'].includes("error")){
            const error_message = document.getElementById("error_message");
            error_message.style.display = "block";
            error_message.textContent = data['message'];
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
