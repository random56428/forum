$(document).ready(function () {
    $(".profile-link").on("click", function (event) {
        event.stopPropagation();
    })

    $(".post-link").on("click", function (event) {
        event.stopPropagation();
    })
})