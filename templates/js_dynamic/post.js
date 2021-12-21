var locked = false;
var toastShown = false;
var toast = new bootstrap.Toast(document.querySelector(".manual-flashbox"));

$(document).ready(function () {
    $(".manual-flashbox").click(function () {
        hideToast();
    })

    // Enables comment button if there is text inside of comment text area
    $("#commentarea").keyup(function () {
        if ($(this).val() != "" && $("#commentbtn").prop("disabled")) {
            $("#commentbtn").prop("disabled", false);
        } else if ($(this).val() == "" && !$("#commentbtn").prop("disabled")) {
            $("#commentbtn").prop("disabled", true);
        }
    })

    // Sends comment to server if textarea is not empty
    $("#commentbtn").click(function () {
        // Checks if comment area is not empty
        if ($("#commentarea").val() != "") {
            // https://stackoverflow.com/questions/15963687/prevent-spamming-of-button-to-call-function
            if (!locked) {
                locked = true;
                setTimeout(unlock, 5000);
                sendRequestAddComment();
            } else {
                if (!toastShown) {
                    toast.show();
                    toastShown = true;
                }
            }
        }
    })

    // TODO: REFACTOR - SAME SCRIPT AS INDEX
    $(".upvotepost").on("click", function (event) {
        var id = $(event.currentTarget).prop("id");
        upvote(id, "post");
    })

    // TODO: REFACTOR - SAME SCRIPT AS INDEX
    $(".downvotepost").on("click", function (event) {
        var id = $(event.currentTarget).prop("id");
        downvote(id, "post");
    })

    $(".a-post").on("click", ".upvotecomment", function (event) {
        var id = $(event.currentTarget).prop("id");
        upvote(id, "comment");
    })

    $(".a-post").on("click", ".downvotecomment", function (event) {
        var id = $(event.currentTarget).prop("id");
        downvote(id, "comment");
    })
})

// TODO: REFACTOR - SAME SCRIPT AS INDEX
function upvote(id, type) {
    $.ajax({
        type: "POST",
        url: "{{url_for('upvote')}}",
        contentType: "application/json; charset=UTF-8",
        dataType: "json",
        data: JSON.stringify({
            "type": type,
            "id": id
        }),
        success: function (data) {
            if (data["status"] == "success") {
                if (type == "post") {
                    if (data["unvote"] == "false") {
                        upvotePost(data["id"], data);
                    } else {
                        renderNovotesPost(data["id"], data);
                    }
                } else {
                    if (data["unvote"] == "false") {
                        upvoteComment(data["id"], data);
                    } else {
                        renderNovotesComment(data["id"], data);
                    }
                }
            } else {
                alert("Sorry, something went wrong. Please refresh the page.");
            }
        }
    })
}

// TODO: REFACTOR - SAME SCRIPT AS INDEX
function downvote(id, type) {
    $.ajax({
        type: "POST",
        url: "{{url_for('downvote')}}",
        contentType: "application/json; charset=UTF-8",
        dataType: "json",
        data: JSON.stringify({
            "type": type,
            "id": id
        }),
        success: function (data) {
            if (data["status"] == "success") {
                if (type == "post") {
                    if (data["unvote"] == "false") {
                        downvotePost(data["id"], data);
                    } else {
                        renderNovotesPost(data["id"], data);
                    }
                } else {
                    if (data["unvote"] == "false") {
                        downvoteComment(data["id"], data);
                    } else {
                        renderNovotesComment(data["id"], data);
                    }
                }
            } else {
                alert("Sorry, something went wrong. Please refresh the page.");
            }
        }
    })
}

// for posts
function upvotePost(id, data) {
    $("#postdownvote-".concat(id).concat(" ,", "#posticon-" + id)).removeClass("downvote-color");
    $("#postupvote-".concat(id).concat(" ,", "#posticon-" + id)).addClass("upvote-color");
    $("#posticon-" + id).text(data["votes"]);
}

function downvotePost(id, data) {
    $("#postupvote-".concat(id).concat(" ,", "#posticon-" + id)).removeClass("upvote-color");
    $("#postdownvote-".concat(id).concat(" ,", "#posticon-" + id)).addClass("downvote-color");
    $("#posticon-" + id).text(data["votes"]);
}

function renderNovotesPost(id, data) {
    $("#postdownvote-".concat(id).concat(" ,", "#posticon-" + id)).removeClass("downvote-color");
    $("#postupvote-".concat(id).concat(" ,", "#posticon-" + id)).removeClass("upvote-color");
    $("#posticon-" + id).text(data["votes"]);
}

// for comments
function upvoteComment(id, data) {
    $("#commentdownvote-".concat(id).concat(" ,", "#commenticon-" + id)).removeClass("downvote-color");
    $("#commentupvote-".concat(id).concat(" ,", "#commenticon-" + id)).addClass("upvote-color");
    $("#commenticon-" + id).text(data["votes"]);
}

function downvoteComment(id, data) {
    $("#commentupvote-".concat(id).concat(" ,", "#commenticon-" + id)).removeClass("upvote-color");
    $("#commentdownvote-".concat(id).concat(" ,", "#commenticon-" + id)).addClass("downvote-color");
    $("#commenticon-" + id).text(data["votes"]);
}

// TODO: REFACTOR - SAME SCRIPT AS INDEX
function renderNovotesComment(id, data) {
    $("#commentdownvote-".concat(id).concat(" ,", "#commenticon-" + id)).removeClass("downvote-color");
    $("#commentupvote-".concat(id).concat(" ,", "#commenticon-" + id)).removeClass("upvote-color");
    $("#commenticon-" + id).text(data["votes"]);
}

// Called to unlock button after setTimeout expires
function unlock() {
    locked = false;
    toastShown = false;
}

// Called when toast is clicked to hide
function hideToast() {
    toast.hide();
    toastShown = false;
}

function sendRequestAddComment() {
    // https://stackoverflow.com/questions/3730359/get-id-from-url-with-jquery
    var url = window.location.pathname;
    var id = url.substring(url.lastIndexOf('/') + 1);
    $.ajax({
        type: "POST",
        url: "{{url_for('newcomment')}}",
        contentType: "application/json; charset=UTF-8",
        data: JSON.stringify({
            "text": $('#commentarea').val(),
            "post_id": id,
        }),
        dataType: "json",
        beforeSend: function () {
            // Disables button, hides button text and adds a spinning wheel from Bootstrap
            $("#commentbtn").prop("disabled", true);
            $("#commentbtn > .spinner-border").removeClass("visually-hidden");
            $("#commentbtn > .btn-text").addClass("visually-hidden");
        },
        success: function (data) {
            if (data["status"] == "error") {
                alert("error: text field empty");
            } else {
                // Remove no comment label if it exists
                if (data["nocomments"] == "true") {
                    $(".nocomments").remove();
                }

                // Checks if commenter if OP
                function isOP() {
                    return (`{{ username }}` == data["username_op"] ? true : false);
                }
                console.log(data);
                console.log(data['pic']);

                // Insert comment into html
                var str = ` <div class="row" style="margin-left: -3px; margin-right: -3px;">
                                <div class="col-md-1" style="max-width: 55px;">
                                    <a class="pic-link" href="{{url_for('profile', user=username)}}">
                                    <img src="{{pic}}" class="img-fluid rounded-circle"
                                        style="margin-top: 9px; position: relative; z-index: 1; width: 31px;"></a>
                                </div>
                                <div class="col my-3 ps-0">
                                    <div style="font-size: 12px">
                                        <a class="profile-link black-text" href="{{url_for('profile', user=username)}}"
                                            style="font-size: 11px;">{{ username }}</a> 
                                        ${isOP() ? `<span class="text-primary fw-bold">OP</span>` : ''}
                                        &#183; <span class="text-muted">just now</span>
                                    </div>
                                    <div class="text-box text-break" style="font-size: 14px;">
                                        ${data["text"]}
                                    </div>
                                    <div id="votebox2" class="hstack">
                                        <div>
                                            <button id="commentupvote-${data['comment_id']}"
                                                class="upvote upvotecomment btn btn-sm mx-1 upvote-color">
                                                <i class="fas fa-caret-up fa-2x"></i>
                                            </button>
                                        </div>
                                        <div id="commenticon-${data['comment_id']}" class="fw-bold upvote-color" style="font-size: 11px;">
                                            1
                                        </div>
                                        <div>
                                            <button id="commentdownvote-${data['comment_id']}"
                                                class="downvote downvotecomment btn btn-sm mx-1">
                                                <i class="fas fa-caret-down fa-2x"></i>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>`
                document.querySelector(".top-hr").insertAdjacentHTML('afterend', str);
            }
        },
        complete: function () {
            // Clears text area, removes spinning wheel and restore button text
            $("#commentarea").val("");
            $("#commentbtn > .spinner-border").addClass("visually-hidden");
            $("#commentbtn > .btn-text").removeClass("visually-hidden");
        }
    });
}