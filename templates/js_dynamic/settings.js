$("body").css("background-color", "white");
$("#statusmsg-pass").hide();

var oldPassVisible = false;
var newPassVisible = false;
var confirmPassVisible = false;

$(document).ready(function () {
    // Change password form
    $("#passform").on("submit", function (e) {
        e.preventDefault();
        sendRequestChangePass();
    })

    // Upload profile picture
    $("#fileupload").on("change", function () {
        uploadPicture();
    })

    // Remove profile picture
    $("#removepic").on("click", function () {
        var path = $("#profilepic").prop("src").split("/");
        if (path[path.length - 1] != "default.jpg") {
            removePicture();
        }
    })

    // Enables terminate button in modal
    $("#confirmation").on("keyup", function () {
        if ($(this).val() == `{{username}}`) {
            $("#confirmationbtn").prop("disabled", false);
        } else {
            $("#confirmationbtn").prop("disabled", true);
        }
    })

    // Clears input and disables button to prevent misclicks
    $(".modal").on("hidden.bs.modal", function () {
        $("#confirmation").val("");
        $("#confirmationbtn").prop("disabled", true);
    })

    // Focus on input once modal is shown
    $(".modal").on("shown.bs.modal", function () {
        $("#confirmation").focus();
    })
})

function removePicture() {
    $.ajax({
        type: "POST",
        url: "{{url_for('removepic')}}",
        dataType: "text",
        beforeSend: function () {
            $("#removepic > .spinner-border").removeClass("visually-hidden");
            $("#removepic > .btn-text").addClass("visually-hidden");
        },
        success: function (data) {
            if (data != "") {
                $("#profilepic, #static-pic").prop("src", data);
            }
        },
        complete: function () {
            $("#removepic > .spinner-border").addClass("visually-hidden");
            $("#removepic > .btn-text").removeClass("visually-hidden");
        }
    })
}

function uploadPicture() {
    // https://stackoverflow.com/questions/21044798/how-to-use-formdata-for-ajax-file-upload
    var form = $("#picform")[0];
    var formData = new FormData(form);
    $.ajax({
        type: "POST",
        url: "{{url_for('uploadpic')}}",
        contentType: false,
        processData: false,
        dataType: "json",
        data: formData,
        beforeSend: function () {
            $("#pic-loading").removeClass("visually-hidden");
        },
        success: function (data) {
            if (data["status"] == "error") {
                $("#statusmsg-pic").text(data["msg"]);
                $("#statusmsg-pic").css("color", "red");
            } else {
                $("#statusmsg-pic").text(data["msg"]);
                $("#statusmsg-pic").css("color", "green");
                $("#profilepic, #static-pic").prop("src", data["newpic"]);
            }
        },
        complete: function () {
            $("#pic-loading").addClass("visually-hidden");
        }
    })
}

function sendRequestChangePass() {
    $.ajax({
        type: "POST",
        url: "{{url_for('changepass')}}",
        contentType: "application/x-www-form-urlencoded; charset=UTF-8",
        dataType: "json",
        data: $("#passform").serialize(),
        beforeSend: function () {
            // Disables button, hides button text and adds a spinning wheel from Bootstrap
            $("#chngpassbtn > .spinner-border").removeClass("visually-hidden");
            $("#chngpassbtn > .btn-text").addClass("visually-hidden");
        },
        success: function (data) {
            if (data["status"] == "error") {
                $("#statusmsg-pass").css("color", "red");
            } else {
                $("#statusmsg-pass").css("color", "green");
                resetPassForm();
            }
            $("#statusmsg-pass").text(data["msg"]);
            $("#statusmsg-pass").show();
        },
        complete: function () {
            $("#chngpassbtn > .spinner-border").addClass("visually-hidden");
            $("#chngpassbtn > .btn-text").removeClass("visually-hidden");
        }
    });
}

function resetPassForm() {
    document.querySelector("#passform").reset();
    oldPassVisible = true;
    newPassVisible = true;
    confirmPassVisible = true;
    showOldPass();
    showNewPass();
    showConfirmPass();
}

// TODO: Refactor these "show" functions - duplication - parameterize
function showOldPass() {
    var passwordInputs = document.querySelector("#oldpass");
    var element = document.querySelector("#oldpassicon");
    if (!oldPassVisible) {
        passwordInputs.type = "text";
        element.innerHTML = "&#xf070;";
        oldPassVisible = true;
    } else {
        passwordInputs.type = "password";
        element.innerHTML = "&#xf06e;";
        oldPassVisible = false;
    }
}

function showNewPass() {
    var passwordInputs = document.querySelector("#newpass");
    var element = document.querySelector("#newpassicon");
    if (!newPassVisible) {
        passwordInputs.type = "text";
        element.innerHTML = "&#xf070;";
        newPassVisible = true;
    } else {
        passwordInputs.type = "password";
        element.innerHTML = "&#xf06e;";
        newPassVisible = false;
    }
}

function showConfirmPass() {
    var passwordInputs = document.querySelector("#confirmpass");
    var element = document.querySelector("#confirmpassicon");
    if (!confirmPassVisible) {
        passwordInputs.type = "text";
        element.innerHTML = "&#xf070;";
        confirmPassVisible = true;
    } else {
        passwordInputs.type = "password";
        element.innerHTML = "&#xf06e;";
        confirmPassVisible = false;
    }
}