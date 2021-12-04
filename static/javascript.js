document.addEventListener('DOMContentLoaded', function () {
    document.querySelector("#textareabutton").addEventListener('click', function () {
        let textarea = document.querySelector("#floatingTextarea");
        let typed = textarea.value;
        if (typed != "") {
            textarea.value = "";

            var str = `<hr>
            <div class="post p-3">
                <div class="row p-2">
                    Name placeholder
                </div>
                <div class="row p-2">
                    ${typed}
                </div>
                <div class="row p-2">
                    <div class="col">
                        <button class="btn btn-default p-0">
                            <img src="./static/images/upvote_light.png">
                        </button>
                        <label class="p-2">1</label>
                        <button class="btn btn-default p-0">
                            <img src="./static/images/downvote_light.png">
                        </button>
                    </div>
                </div>
            </div>`
            
            document.querySelector(".post-holder").insertAdjacentHTML('afterbegin', str);
        }
    })
});