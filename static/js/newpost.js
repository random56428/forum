$(document).ready(function () {
    counter = $("#counter");

    $("#titleform").on("keyup keydown", function () {
        counter.text($(this).val().length);
    });

})