let isRoomNameValid = false;
let isPasswordValid = false;

function roomNameValidates() {
    let roomName = document.getElementById("room_name").value;
    
    if (roomName.length < 6) {
        document.getElementById("roomname_length").style.display = "block";
        isRoomNameValid = false;
    } else {
        document.getElementById("roomname_length").style.display = "none";
        isRoomNameValid = true;
    }
    toggleSubmitButton();
}

function passwordValidates() {
    let password = document.getElementById("password").value;
    let isValid = true;

    if (password.length < 6) {
        document.getElementById("password_length").style.display = "block";
        isValid = false;
    } else {
        document.getElementById("password_length").style.display = "none";
    }

    const hasNumber = /\d/.test(password);
    if (!hasNumber) {
        document.getElementById("numbers").style.display = "block";
        isValid = false;
    } else {
        document.getElementById("numbers").style.display = "none";
    }

    const hasAlphabet = /[a-zA-Z]/.test(password);
    if (!hasAlphabet) {
        document.getElementById("alphabets").style.display = "block";
        isValid = false;
    } else {
        document.getElementById("alphabets").style.display = "none";
    }

    const hasSymbol = /[@_]/.test(password);
    if (!hasSymbol) {
        document.getElementById("symbols").style.display = "block";
        isValid = false;
    } else {
        document.getElementById("symbols").style.display = "none";
    }

    const invalidSymbols = /[ |!~#$%^&*()-+=]/.test(password);
    if (invalidSymbols) {
        document.getElementById("no_symbols").style.display = "block";
        isValid = false;
    } else {
        document.getElementById("no_symbols").style.display = "none";
    }
    isPasswordValid = isValid;
    toggleSubmitButton();
}

function toggleSubmitButton() {
    const submitButton = document.getElementById("submit_button");
    if (isRoomNameValid && isPasswordValid) {
        submitButton.disabled = false;
    } else {
        submitButton.disabled = true;
    }
}

document.getElementById("room_name").addEventListener("input", roomNameValidates);
document.getElementById("password").addEventListener("input", passwordValidates);

document.getElementById("submit_button").addEventListener("click", function() {
    const room_name_value = document.getElementById("room_name").value;
    const password_value = document.getElementById("password").value;
    const capacity_value = document.getElementById("capacity").value;

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
        console.log(data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
});