/**
* Once DOM creation is complete the contained functions are called if
* their triggering form is submitted.
*/
$(document).ready(function() {
    $("#registerForm").submit(function () {
        registerFormHandling()
    })
    $("#loginForm").submit(function() {
        loginFormHandling()
    })
    $("#createExerciseForm").submit(function() {
        event.preventDefault()
        createExerciseObject()
        fetch("/createexercise", fetchParameterInit(inputData))
            .then(
                displayModal("Exercise created", undefined, true)
            )
    })
    $("#editExerciseForm").submit(function() {
        event.preventDefault()
        createExerciseObject()
        fetch(window.location.href, fetchParameterInit(inputData))
            .then(
                displayModal("Exercise created", undefined, true)
            )
    }
    )
})
/**
* The fields from the registration form are added to an object, if the field's
* case is not required it is set to lowercase for standardisation.
* A fetch request is formed containing the submitted data for verification.
* If submitted credentials are valid: user is redirected to their exercise list.
* If credentials aren't valid: the invalid input is isolated and passed to a 
* modal that states the failed input to the user.
*/
function registerFormHandling() {
    event.preventDefault()
    const inputData = {
        inputUsername: ($("#inputUsername")).val().toLowerCase(),
        inputEmail: ($("#inputEmail")).val().toLowerCase(),
        inputPassword: ($("#inputPassword")).val()
    }
    fetch('/register', fetchParameterInit(inputData))
        .then(response => {
            response.json()
                .then(
                    responseJSON => {
                        if (responseJSON.hasOwnProperty("url")) {
                            window.location.replace(responseJSON.url)
                        }
                        const invalidInput = authBooleanCheck (responseJSON, 3)
                        let alertMessage = "";
                        Object.keys(invalidInput).forEach((key => {
                            alertMessage = alertMessage + `${invalidInput[key]} already exists.</br>`
                        }))
                            displayModal("Registration unsuccessful", alertMessage, false)
                        }
                )
                .catch(error => {
                    console.log(error)
                })
        })
}
/**
* Submitted form data is added to an object, if the field's case is 
* not required it is set to lowercase for standardisation.
* A fetch request is formed containing the submitted data for verification.
* If submitted credentials are valid: user is redirected to their exercise list.
* If credentials aren't valid: the invalid input is isolated and passed to a 
* modal that states the failed input to the user.
 */
function loginFormHandling() {
    event.preventDefault()
    const inputData = {
        inputUsername: ($("#inputUsername")).val().toLowerCase(),
        inputPassword: ($("#inputPassword")).val()
    }
    fetch('/login', fetchParameterInit(inputData))
        .then(response => {
            response.json()
                .then(
                    responseJSON => {
                        if (responseJSON.hasOwnProperty("url")) {
                            window.location.replace(responseJSON.url)
                        }
                        invalidInput = authBooleanCheck(responseJSON, 5)
                        if (invalidInput.length > 0){
                            displayModal("Login unsuccessful", `Invalid ${invalidInput}`, false)
                        }
                    })
        }
        )
        .catch(error => {
            console.log(error)
        })
}
/**
 * Submitted form data is placed into body of fetch parameters.
 * The fetch parameters provide detail of the request options.
 * These request options are constant for all requests made in this project.
 * @param {object} inputData - Object created from submitted form data.
 */
function fetchParameterInit (inputData) {
    const fetchParameters = {
        method: 'POST',
        cors: '*same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(inputData)
    }
    return fetchParameters
}
/**
 * 
 * @param {object} responseJSON -
 * @param {integer} isolationNumber -
 */
function authBooleanCheck (responseJSON, isolationNumber) {
    invalidKeys = []
    Object.keys(responseJSON).forEach((key) => {
        if (!responseJSON[key]) {
            invalidKeys.push((key.substr(isolationNumber)).toLowerCase())
        }
    })
    return invalidKeys
}
/**
 * 
 */
function createExerciseObject(){
    const inputData = {};
    ($("input").each(function () {
        inputData[this.id.toLowerCase()] = this.value.toLowerCase()
    }))
    return inputData
}
/**
 * 
 * @param {*} modalTitle 
 * @param {*} modalText 
 * @param {*} pageRedirect 
 */
function displayModal (modalTitle, modalText = "", pageRedirect = false) {
    Swal.fire({
        title: modalTitle,
        html: modalText,
        confirmButtonText: "Ok"
    })
        .then(function () {
            if (pageRedirect) {
                window.location.replace("/myexercises");
            }
        })
}

