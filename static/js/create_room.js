let isRoomNameValid = false;
let isPasswordValid = false;

const room_exist = document.getElementById("exist_message");
const room_created = document.getElementById("room_created");
const error_message = document.getElementById("error_message");

function clear_messages(){
    room_exist.style.display = "none";
    room_created.style.display = "none";
    error_message.style.display = "none";
}

function roomNameValidates() {
    clear_messages();
    let roomName = document.getElementById("room_name").value;
    
    if (roomName.length < 6) {
        document.getElementById("roomname_length").style.display = "block";
        isRoomNameValid = false;
    } 
    else {
        document.getElementById("roomname_length").style.display = "none";
        isRoomNameValid = true;
    }
    toggleSubmitButton();
}

function passwordValidates() {
    clear_messages();
    let password = document.getElementById("password").value;
    let isValid = true;

    if (password.length < 6) {
        document.getElementById("password_length").style.display = "block";
        isValid = false;
    } 
    else {
        document.getElementById("password_length").style.display = "none";
    }

    const hasNumber = /\d/.test(password);
    if (!hasNumber) {
        document.getElementById("numbers").style.display = "block";
        isValid = false;
    } 
    else {
        document.getElementById("numbers").style.display = "none";
    }

    const hasAlphabet = /[a-zA-Z]/.test(password);
    if (!hasAlphabet) {
        document.getElementById("alphabets").style.display = "block";
        isValid = false;
    } 
    else {
        document.getElementById("alphabets").style.display = "none";
    }

    const hasSymbol = /[@_]/.test(password);
    if (!hasSymbol) {
        document.getElementById("symbols").style.display = "block";
        isValid = false;
    } 
    else {
        document.getElementById("symbols").style.display = "none";
    }

    const invalidSymbols = /[ |!~#$%^&*()-+=]/.test(password);
    if (invalidSymbols) {
        document.getElementById("no_symbols").style.display = "block";
        isValid = false;
    } 
    else {
        document.getElementById("no_symbols").style.display = "none";
    }
    isPasswordValid = isValid;
    toggleSubmitButton();
}

function toggleSubmitButton() {
    const submitButton = document.getElementById("submit_button");
    if (isRoomNameValid && isPasswordValid) {
        submitButton.disabled = false;
        submitButton.style.cursor = "pointer";
    } 
    else {
        submitButton.disabled = true;
    }
}
document.getElementById("room_name").addEventListener("input", roomNameValidates);
document.getElementById("password").addEventListener("input", passwordValidates);

document.getElementById("submit_button").addEventListener("click", (event)=> {
    event.preventDefault()
    const room_name = document.getElementById("room_name");
    const password = document.getElementById("password");
    const capacity = document.getElementById("capacity");

    const room_name_value =  room_name.value;
    const password_value = password.value;
    const capacity_value = capacity.value;

    room_name.value = "";
    password.value = "";
    capacity.value = "";
    clear_messages();

    fetch("/create_room", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            room_name: room_name_value,
            password: password_value,
            capacity: capacity_value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data['status'].includes("room_exist")) {
            room_exist.style.display = "block";
        } 
        else if (data['status'].includes("room_created")){
            room_created.style.display = "block";
        }
        else if (data['status'].includes("error")){
            error_message.style.display = "block";
            error_message.textContent = data['message'];
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
