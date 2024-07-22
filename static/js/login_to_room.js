console.log("page loaded");

document.getElementById("submit_button").addEventListener("click", (event)=> {
    
    event.preventDefault();
    console.log("button clicked");

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
        console.log(data);
        if (data['status'].includes("error")) {
            const error_message = document.getElementById("error_message");
            error_message.style.display = "block";
            error_message.textContent = data['message'];
        } else if (data['status'] === 'success') {
            window.location.href = `/chat_room?room_name=${data["room_name"]}`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
