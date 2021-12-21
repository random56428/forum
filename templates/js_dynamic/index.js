$(document).ready(function () {

    $(".upvote").on("click", function (event) {
        event.stopPropagation();
        var id = $(event.currentTarget).prop("id");
        upvote(id);
    })

    $(".downvote").on("click", function (event) {
        event.stopPropagation();
        var id = $(event.currentTarget).prop("id");
        downvote(id);
    })

    $(".profile-link").on("click", function (event) {
        event.stopPropagation();
    })

})

function upvote(id) {
    $.ajax({
        type: "POST",
        url: "{{url_for('upvote')}}",
        contentType: "application/json; charset=UTF-8",
        dataType: "json",
        data: JSON.stringify({
            "type": "post",
            "id": id
        }),
        success: function (data) {
            if (data["status"] == "success") {
                if (data["unvote"] == "false") {
                    upvotePost(data["id"], data);
                } else {
                    renderNovotes(data["id"], data);
                }
            } else {
                alert("Sorry, something went wrong. Please refresh the page.");
            }
        }
    })
}

function downvote(id) {
    $.ajax({
        type: "POST",
        url: "{{url_for('downvote')}}",
        contentType: "application/json; charset=UTF-8",
        dataType: "json",
        data: JSON.stringify({
            "type": "post",
            "id": id
        }),
        success: function (data) {
            if (data["status"] == "success") {
                if (data["unvote"] == "false") {
                    downvotePost(data["id"], data);
                } else {
                    renderNovotes(data["id"], data);
                }
            } else {
                alert("Sorry, something went wrong. Please refresh the page.");
            }
        }
    })
}

function upvotePost(id, data) {
    $("#downvote-".concat(id).concat(" ,", "#icon-" + id)).removeClass("downvote-color");
    $("#upvote-".concat(id).concat(" ,", "#icon-" + id)).addClass("upvote-color");
    $("#icon-" + id).text(data["votes"]);
}

function downvotePost(id, data) {
    $("#upvote-".concat(id).concat(" ,", "#icon-" + id)).removeClass("upvote-color");
    $("#downvote-".concat(id).concat(" ,", "#icon-" + id)).addClass("downvote-color");
    $("#icon-" + id).text(data["votes"]);
}

function renderNovotes(id, data) {
    $("#downvote-".concat(id).concat(" ,", "#icon-" + id)).removeClass("downvote-color");
    $("#upvote-".concat(id).concat(" ,", "#icon-" + id)).removeClass("upvote-color");
    $("#icon-" + id).text(data["votes"]);
}