$(document).ready(function () {
    $("#registerForm").submit(function (event) {
        event.preventDefault();
        const inputUsername = ($("#inputUsername")).val();
        const inputPassword = ($("#inputPassword")).val();
        const inputEmail = ($("#inputEmail")).val();
        const data = {
            inputUsername: inputUsername,
            inputEmail: inputEmail,
            inputPassword: inputPassword
        };
        fetch('/register', {
            method: 'POST',
            cors: '*same-origin',
            headers: {
                'Content-Type': 'application/json',
            },
            body:JSON.stringify(data)
        })
            .then(response => {
                const result = response.json()
                console.log(result)
            })
            .catch(error => {
                console.log(error)
            })
        alert("button");
    })
})