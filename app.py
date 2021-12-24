import os
import uuid
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from flask_moment import Moment

from helpers import login_required

# https://flask.palletsprojects.com/en/2.0.x/patterns/fileuploads/
# Configure constants for file uploading
UPLOAD_FOLDER = './static/img/profiles'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
# Configure upload folder location
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///forum.db")

# Configure application to use datetime Moment
moment = Moment(app)

# Gives username when signed in
@app.context_processor
def inject_user():
    if "user_id" in session:
        user_info = (db.execute("SELECT username, pic FROM users WHERE id=?", session["user_id"]))[0]
        user_info["pic"] = "/static/img/profiles/" + user_info["pic"]
        return user_info
    return dict()

@app.route("/")
@app.route("/<sort>")
@login_required
def index(sort="new"):

    # Check if sort does not exist
    if sort not in ["new", "top"]:
        flash("Invalid path.", "danger")
        return redirect("/")

    if sort == "new":
        posts = db.execute("SELECT posts.post_id, content, votes, title, username, date, active, vote FROM posts JOIN users ON users.id = posts.user_id LEFT JOIN post_votes ON post_votes.post_id=posts.post_id AND post_votes.user_id=? ORDER BY posts.date DESC", session["user_id"])
    else:
        posts = db.execute("SELECT posts.post_id, content, votes, title, username, date, active, vote FROM posts JOIN users ON users.id = posts.user_id LEFT JOIN post_votes ON post_votes.post_id=posts.post_id AND post_votes.user_id=? ORDER BY posts.votes DESC", session["user_id"])

    # Convert datetime string back to datetime obj
    parseAllToDatetimeObj(posts)

    return render_template("index.html", posts=posts, sort=sort)

@app.route("/login", methods = ["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        
        # Check if username is blank
        username = request.form.get("login_username")
        if not username:
            flash("Username input is blank.", "danger")
            return render_template("login.html")

        # Check if password is blank
        password = request.form.get("login_password")
        if not password:
            flash("Password input is blank.", "danger")
            return render_template("login.html")
        
        # Check if there is a username associated to request
        # Where rows will return list of length 1 if an account is found
        rows = db.execute("SELECT * FROM users WHERE username=?", username)
        if len(rows) != 1:
            flash("The username or password is incorrect.", "danger")
            return render_template("login.html")

        # Check if password matches db
        if not check_password_hash(rows[0]["hash"], password):
            flash("The username or password is incorrect.", "danger")
            return render_template("login.html")
        
        # Check if account is deactivated
        if rows[0]["active"] == 0:
            flash("Account has been deactivated.", "danger")
            return render_template("login.html")
        
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash("Successfully logged in.", "success")
        return redirect("/")
    
    else:
        return render_template("login.html")

@app.route("/register", methods = ["GET", "POST"])
def register():

    if request.method == "POST":
        # Check if username is blank and already exists
        username = request.form.get("register_username")

        if not username:
            flash("Username input is blank.", "danger")
            return render_template("register.html")
        elif len(db.execute("SELECT * FROM users WHERE username=?", username)) != 0:
            flash("Username already exists.", "danger")
            return render_template("register.html")

        # https://owasp.org/www-community/password-special-characters
        special_chars = " !\"#$%&'()*+,./:;<=>?@[\]^`{|}~"
        # Check if username has special characters
        for c in username:
            if c in special_chars:
                flash("Username must not contain special characters or spaces.", "danger")
                return render_template("register.html")
            
        password = request.form.get("register_password")
        confirmation = request.form.get("register_confirmation")

        # Check if password/confirmation is blank and if !=
        if not password:
            flash("Password input is blank.", "danger")
            return render_template("register.html")
        elif not confirmation:
            flash("Confirmation password is blank.", "danger")
            return render_template("register.html")
        elif password != confirmation:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        # Register for user and insert into db
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password))

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username=?", username)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect to home page
        flash("Successfully registered.", "success")
        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear() 

    # Redirect user to login form
    return redirect("/")

@app.route("/newpost", methods=["GET", "POST"])
@login_required
def newpost():
    if request.method == "POST":

        # Check if title is empty
        title = request.form.get("title")
        if not title or len(title) == 0:
            flash("Title input is blank.", "danger")
            return render_template("newpost.html")

        # Check if title > 300 letters
        if len(title) > 300:
            flash("Title input is greater than 300 characters.", "danger")
            return render_template("newpost.html")
        
        # Get text area value if it exists
        text = request.form.get("text")

        # Check for hard limit of 40000 characters for text field
        if len(text) >= 40000:
            flash("Text field must be less than 40000 characters.", "danger")
            return render_template("newpost.html")

        # Create datetime obj as string for when post is created
        created = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        db.execute("INSERT INTO posts (user_id, title, content, date) VALUES (?, ?, ?, ?)", session["user_id"], title, text, created)
        # Query for created post's id
        post_id = (db.execute("SELECT post_id FROM posts WHERE user_id=? AND date=?", session["user_id"], created))[0]["post_id"]
        # Upvote own post
        db.execute("INSERT INTO post_votes (user_id, post_id, vote) VALUES (?, ?, 1)", session["user_id"], post_id)

        return redirect("/")
    else:
        return render_template("newpost.html")

@app.route("/post/<id>")
@app.route("/post/<id>/<scroll>")
@app.route("/post/<id>/<sort>")
@login_required
def post(id, scroll = None, sort = "new"):

    # Exception is thrown with 2 routes of same length
    # sort is passed an int when we want scroll
    if sort.isdigit() and scroll == None:
        scroll = sort
        sort = "new"
    
    # Check if sort does not exist
    if sort not in ["new", "top"]:
        flash("Invalid path.", "danger")
        return redirect("/")

    # Check if scroll comment exists
    if scroll and len(db.execute("SELECT comment_id FROM comments WHERE comment_id=?", scroll)) == 0:
        flash("Comment does not exist.", "danger")
        return redirect("/")

    posts = db.execute("SELECT posts.post_id, content, votes, title, username, date, active, vote FROM posts JOIN users ON users.id = posts.user_id LEFT JOIN post_votes ON post_votes.post_id=posts.post_id AND post_votes.user_id=? WHERE posts.post_id = ?", session["user_id"], id)

    # Check if post exists
    if len(posts) == 0:
        flash("Post does not exist.", "danger")
        return redirect("/")

    # If scroll exists, check if comment matches post
    if scroll and len(db.execute("SELECT * FROM comments WHERE comment_id=? AND refpost_id=?", scroll, id)) == 0:
        flash("Comment does not exist.", "danger")
        return redirect("/")

    parseAllToDatetimeObj(posts)
    if sort == "new":
        comments = db.execute("SELECT comments.*, users.username, users.active, users.pic, vote FROM comments JOIN users ON users.id = comments.refuser_id LEFT JOIN comment_votes ON comment_votes.comment_id=comments.comment_id AND comment_votes.user_id=? WHERE refpost_id = ? ORDER BY comments.date DESC", session["user_id"], id)
    else:
        comments = db.execute("SELECT comments.*, users.username, users.active, users.pic, vote FROM comments JOIN users ON users.id = comments.refuser_id LEFT JOIN comment_votes ON comment_votes.comment_id=comments.comment_id AND comment_votes.user_id=? WHERE refpost_id = ? ORDER BY comments.votes DESC", session["user_id"], id)
    parseAllToDatetimeObj(comments)
    
    # https://stackoverflow.com/questions/31863582/automatically-scroll-to-a-div-when-flask-returns-rendered-template
    # If scroll endpoint is defined, scroll to comment
    if scroll:
        return render_template("post.html", posts=posts, comments=comments, scroll=("#comment-" + scroll), sort=sort, curr_post_id=id)

    return render_template("post.html", posts=posts, comments=comments, sort=sort, curr_post_id=id)

@app.route("/newcomment", methods=["POST"])
@login_required
def newcomment():
    textarea = request.get_json()

    # Check if textarea["text"] is empty
    if textarea["text"] == "":
        return jsonify(dict(status = "error"))

    # Check if comments count is zero to remove no comments label
    count = (db.execute("SELECT COUNT(comment_id) FROM comments WHERE refpost_id=?", textarea["post_id"]))[0]["COUNT(comment_id)"]
    if count != 0:
        textarea["nocomments"] = "false"
    else:
        textarea["nocomments"] = "true"
    
    # Create datetime object
    created_obj = datetime.utcnow()
    # Parse to string to insert into database
    created_str = created_obj.strftime("%Y-%m-%d %H:%M:%S")

    # Add comment to database
    db.execute("INSERT INTO comments (refpost_id, refuser_id, comment, date) VALUES (?, ?, ?, ?)", int(textarea["post_id"]), session["user_id"], textarea["text"], created_str)
    # Query for created comment's id
    comment_id = (db.execute("SELECT comment_id FROM comments WHERE refuser_id=? AND date=?", session["user_id"], created_str))[0]["comment_id"]
    textarea["comment_id"] = comment_id
    # Upvote own comment
    db.execute("INSERT INTO comment_votes (user_id, comment_id, vote) VALUES (?, ?, 1)", session["user_id"], comment_id)

    # Query for person who posted the post to be returned
    textarea["username_op"] = (db.execute("SELECT username FROM users JOIN posts ON posts.user_id=users.id WHERE posts.post_id=?", textarea["post_id"]))[0]["username"]

    # Return constructed information to form a comment
    return textarea

# Profile page
@app.route("/profile/<user>")
@app.route("/profile/<user>/posts", endpoint="profile-posts")
@app.route("/profile/<user>/comments", endpoint="profile-comments")
@login_required
def profile(user):
    
    # Check if user is valid
    user_info = db.execute("SELECT id, active, pic FROM users WHERE username=?", user)
    if len(user_info) == 0:
        flash("User profile does not exist.", "danger")
        return redirect("/")

    # Check if account is active
    if user_info[0]["active"] == 0:
        flash("User account is not active.", "danger")
        return redirect("/")
    
    user_id = user_info[0]["id"]

    if request.endpoint == "profile-posts":
        posts = db.execute("SELECT posts.post_id, votes, title, date, vote FROM posts JOIN post_votes ON post_votes.post_id=posts.post_id WHERE posts.user_id=? AND post_votes.user_id=? ORDER BY posts.date DESC", user_id, user_id)
        parseAllToDatetimeObj(posts)
        return render_template("profileposts.html", posts=posts, user=user)
    elif request.endpoint == "profile-comments":
        comments = db.execute("SELECT comments.*, posts.title, posts.post_id, users.username, users.active FROM comments JOIN posts ON posts.post_id=comments.refpost_id JOIN users ON posts.user_id=users.id WHERE comments.refuser_id = ? ORDER BY comments.date DESC", user_id)
        parseAllToDatetimeObj(comments)
        return render_template("profilecomments.html", comments=comments, user=user)

    # Endpoint is user - overview

    # Get profile picture
    pic = "/static/img/profiles/" + user_info[0]["pic"]

    # Calculate total reputation for given user
    post_votes = db.execute("SELECT votes FROM posts WHERE user_id=?", user_id)
    comment_votes = db.execute("SELECT votes FROM comments WHERE refuser_id=?", user_id)
    post_count = len(post_votes)
    comment_count = len(comment_votes)
    total_rep = 0
    for post in post_votes:
        total_rep += post["votes"]
    for comment in comment_votes:
        total_rep += comment["votes"]
    total_rep -= (post_count + comment_count)

    # Calculate total post contributions
    post_contribution = (db.execute("SELECT COUNT(*) FROM posts WHERE user_id=?", user_id))[0]["COUNT(*)"]

    # Calculate total comment contributions
    comment_contribution = (db.execute("SELECT COUNT(*) FROM comments WHERE refuser_id=?", user_id))[0]["COUNT(*)"]

    return render_template("profile.html", total_rep=total_rep, post_contribution=post_contribution, comment_contribution=comment_contribution, user=user, picture=pic)

# Settings for logged in user
@app.route("/settings")
@login_required
def settings():

    # Query for profile picture of logged in user
    pic = "/static/img/profiles/" + (db.execute("SELECT pic FROM users WHERE id=?", session["user_id"]))[0]["pic"]

    return render_template("settings.html", picture=pic)

# Change password
@app.route("/changepass", methods=["POST"])
@login_required
def changepass():

    oldpass = request.form.get("oldpass")
    newpass = request.form.get("newpass")
    confirmpass = request.form.get("confirmpass")

    # Check if any of the box fields are not filled in
    if not oldpass:
        return jsonify(dict(msg = "Old password input blank", status = "error"))
    elif not newpass:
        return jsonify(dict(msg = "New password input blank", status = "error"))
    elif not confirmpass:
        return jsonify(dict(msg = "Confirmation password input blank", status = "error"))

    # Verify if new password is the same as confirmpass
    if not newpass == confirmpass:
        return jsonify(dict(msg = "Old/new password must match", status = "error"))    
        
    # Verify if old password matches
    hashpass = db.execute("SELECT hash FROM users WHERE id=?", session["user_id"])
    if not check_password_hash(hashpass[0]["hash"], oldpass):
        return jsonify(dict(msg = "Invalid old password", status = "error"))

    db.execute("UPDATE users SET hash=? WHERE id=?", generate_password_hash(newpass), session["user_id"])

    return jsonify(dict(msg = "Successfully changed password", status = "success"))

# Deactivate account
@app.route("/deactivateaccount", methods=["POST"])
@login_required
def deactivateaccount():

    user_id = session["user_id"]

    # Check if entered username matches session username
    if request.form.get("confirmation") != (db.execute("SELECT username FROM users WHERE id=?", user_id))[0]["username"]:
        flash("Confirmation username is invalid.", "danger")
        return redirect("/settings")

    db.execute("UPDATE users SET active=0 WHERE id=?", user_id)

    session.clear()
    flash("Deactivated! We're sorry to see you go.", "success")
    return render_template("login.html")

# Change/upload profile picture
@app.route("/uploadpic", methods=["POST"])
@login_required
def uploadpic():
    # https://flask.palletsprojects.com/en/2.0.x/patterns/fileuploads/
    # Check if file is in post request
    if "file" not in request.files:
        return jsonify(dict(msg = "No file part detected.", status = "error"))
    
    file = request.files.get("file")

    # Check if file name is empty or file doesn't exist
    if file.filename == "" or not file:
        return jsonify(dict(msg = "No file was selected.", status = "error"))

    # Check if file extension is allowed
    if not allowedFile(file.filename):
        return jsonify(dict(msg = "File extension not supported.", status = "error"))

    # Check if file size is smaller than 2mb
    if getSize(file) > 2097152:
        return jsonify(dict(msg = "File size limit of 2 MB exceeded.", status = "error"))

    # Replace file.filename with randomly generated uuid
    filename = str(uuid.uuid4()) + "." + file.filename.rsplit('.', 1)[1].lower()

    # Update profile picture link in database
    db.execute("UPDATE users SET pic=? WHERE id=?", filename, session["user_id"])

    # Store file in web server
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    # Get new profile picture link
    newpic = "/static/img/profiles/" + filename

    return jsonify(dict(msg = "", status="success", newpic=newpic))

# Remove profile picture
@app.route("/removepic", methods=["POST"])
@login_required
def removepic():
    # Check if user already has default picture
    if ((db.execute("SELECT pic FROM users WHERE id=?", session["user_id"]))[0]["pic"] == "default.jpg"):
        return ""
    db.execute("UPDATE users SET pic='default.jpg' WHERE id=?", session["user_id"])
    return "/static/img/profiles/default.jpg"

# Upvote post or comment
@app.route("/upvote", methods=["POST"])
@login_required
def upvote():
    info = request.json

    # Check if request is modified
    if len(info) != 2 or (info["type"] not in ["post", "comment"]) or not any(c.isdigit() for c in info["id"]):
        return jsonify(dict(status = "error"))
    # Continue checking
    if "-" not in info["id"] or len(info["id"].split("-")) != 2 or not any(c.isdigit() for c in info["id"].rsplit("-")[1]):
        return jsonify(dict(status = "error"))

    info["id"] = int(info["id"].rsplit("-")[1])

    # Check if post/comment exists
    if info["type"] == "post":
        if len(db.execute("SELECT * FROM posts WHERE post_id=?", info["id"])) == 0:
            return jsonify(dict(status = "error"))
    else:
        if len(db.execute("SELECT * FROM comments WHERE comment_id=?", info["id"])) == 0:
            return jsonify(dict(status = "error"))
    
    db.execute("BEGIN TRANSACTION")
    # Check for whether a post or comment is upvoted
    if info["type"] == "post":
        isUnvote = upvotePost(info)

        # Get final total votes
        votes = (db.execute("SELECT votes FROM posts WHERE post_id=?", info["id"]))[0]["votes"]
    else:
        isUnvote = upvoteComment(info)
        votes = (db.execute("SELECT votes FROM comments WHERE comment_id=?", info["id"]))[0]["votes"]
    db.execute("COMMIT")
    return jsonify(dict(status = "success", votes = votes, unvote = isUnvote, id=info["id"]))

# Downvote post or comment
@app.route("/downvote", methods=["POST"])
@login_required
def downvote():
    info = request.json
    
    # Check if request is modified
    if len(info) != 2 or (info["type"] not in ["post", "comment"]) or not any(c.isdigit() for c in info["id"]):
        return jsonify(dict(status = "error"))
    # Continue checking
    if "-" not in info["id"] or len(info["id"].split("-")) != 2 or not any(c.isdigit() for c in info["id"].rsplit("-")[1]):
        return jsonify(dict(status = "error"))

    info["id"] = int(info["id"].rsplit("-")[1])

    # Check if post/comment exists
    if info["type"] == "post":
        if len(db.execute("SELECT * FROM posts WHERE post_id=?", info["id"])) == 0:
            return jsonify(dict(status = "error"))
    else:
        if len(db.execute("SELECT * FROM comments WHERE comment_id=?", info["id"])) == 0:
            return jsonify(dict(status = "error"))
    db.execute("BEGIN TRANSACTION")
    # Check for whether a post or comment is downvoted
    if info["type"] == "post":
        isUnvote = downvotePost(info)
        votes = (db.execute("SELECT votes FROM posts WHERE post_id=?", info["id"]))[0]["votes"]
    else:
        isUnvote = downvoteComment(info)
        votes = (db.execute("SELECT votes FROM comments WHERE comment_id=?", info["id"]))[0]["votes"]
    db.execute("COMMIT")
    return jsonify(dict(status = "success", votes = votes, unvote = isUnvote, id=info["id"]))

# Upvote post
def upvotePost(info):
    post_info = db.execute("SELECT * FROM post_votes WHERE user_id=? AND post_id=?", session["user_id"], info["id"])
    isUnvote = "false"

    # Check if there is no vote already made by user - post votes increase by 1
    if len(post_info) == 0:
        db.execute("INSERT INTO post_votes (user_id, post_id, vote) VALUES (?, ?, 1)", session["user_id"], info["id"])
        # Update post total votes
        db.execute("UPDATE posts SET votes = votes + 1 WHERE post_id=?", info["id"])
    # Check if there is a vote already made by user - post votes decrease by 1
    # Special condition
    elif post_info[0]["vote"] == 1:
        db.execute("UPDATE post_votes SET vote=0 WHERE user_id=? AND post_id=?", session["user_id"], info["id"])
        db.execute("UPDATE posts SET votes = votes - 1 WHERE post_id=?", info["id"])
        isUnvote = "true"
    # Check if there is a downvote made by user - post votes increase by 2
    elif post_info[0]["vote"] == -1:
        db.execute("UPDATE post_votes SET vote=1 WHERE user_id=? AND post_id=?", session["user_id"], info["id"])
        db.execute("UPDATE posts SET votes = votes + 2 WHERE post_id=?", info["id"])
    # Check if there is no vote - post votes increase by 1
    else:
        db.execute("UPDATE post_votes SET vote=1 WHERE user_id=? AND post_id=?", session["user_id"], info["id"])
        db.execute("UPDATE posts SET votes = votes + 1 WHERE post_id=?", info["id"])
    
    return isUnvote

# Upvote comment
def upvoteComment(info):
    comment_info = db.execute("SELECT * FROM comment_votes WHERE user_id=? AND comment_id=?", session["user_id"], info["id"])
    isUnvote = "false"

    # Check if there is no vote already made by user - comment votes increase by 1
    if len(comment_info) == 0:
        db.execute("INSERT INTO comment_votes (user_id, comment_id, vote) VALUES (?, ?, 1)", session["user_id"], info["id"])
        # Update comment total votes
        db.execute("UPDATE comments SET votes = votes + 1 WHERE comment_id=?", info["id"])
        # Get comment total votes
    # Check if there is a vote already made by user - comment votes decrease by 1 
    # Special condition
    elif comment_info[0]["vote"] == 1:
        db.execute("UPDATE comment_votes SET vote=0 WHERE user_id=? AND comment_id=?", session["user_id"], info["id"])
        db.execute("UPDATE comments SET votes = votes - 1 WHERE comment_id=?", info["id"])
        isUnvote = "true"
    # Check if there is a downvote made by user - comment votes increase by 2
    elif comment_info[0]["vote"] == -1:
        db.execute("UPDATE comment_votes SET vote=1 WHERE user_id=? AND comment_id=?", session["user_id"], info["id"])
        db.execute("UPDATE comments SET votes = votes + 2 WHERE comment_id=?", info["id"])
    # Check if there is no vote - comment votes increase by 1
    else:
        db.execute("UPDATE comment_votes SET vote=1 WHERE user_id=? AND comment_id=?", session["user_id"], info["id"])
        db.execute("UPDATE comments SET votes = votes + 1 WHERE comment_id=?", info["id"])

    return isUnvote

# Downvote post
def downvotePost(info):
    post_info = db.execute("SELECT * FROM post_votes WHERE user_id=? AND post_id=?", session["user_id"], info["id"])
    isUnvote = "false"

    # Check if there is no vote already made by user - post votes decrease by 1
    if len(post_info) == 0:
        db.execute("INSERT INTO post_votes (user_id, post_id, vote) VALUES (?, ?, -1)", session["user_id"], info["id"])
        # Update post total votes
        db.execute("UPDATE posts SET votes = votes - 1 WHERE post_id=?", info["id"])
        # Get post total votes
    # Check if there is a vote already made by user - post votes decrease by 2
    elif post_info[0]["vote"] == 1:
        db.execute("UPDATE post_votes SET vote=-1 WHERE user_id=? AND post_id=?", session["user_id"], info["id"])
        db.execute("UPDATE posts SET votes = votes - 2 WHERE post_id=?", info["id"])
    # Check if there is a downvote made by user - post votes increase by 1
    # Special condition
    elif post_info[0]["vote"] == -1:
        db.execute("UPDATE post_votes SET vote=0 WHERE user_id=? AND post_id=?", session["user_id"], info["id"])
        db.execute("UPDATE posts SET votes = votes + 1 WHERE post_id=?", info["id"])
        isUnvote = "true"
    # Check if there is no vote - post votes decrease by 1
    else:
        db.execute("UPDATE post_votes SET vote=-1 WHERE user_id=? AND post_id=?", session["user_id"], info["id"])
        db.execute("UPDATE posts SET votes = votes - 1 WHERE post_id=?", info["id"])

    return isUnvote

# Downvote comment
def downvoteComment(info):
    comment_info = db.execute("SELECT * FROM comment_votes WHERE user_id=? AND comment_id=?", session["user_id"], info["id"])
    isUnvote = "false"

    # Check if there is no vote already made by user - comment votes decrease by 1
    if len(comment_info) == 0:
        db.execute("INSERT INTO comment_votes (user_id, comment_id, vote) VALUES (?, ?, -1)", session["user_id"], info["id"])
        # Update comment total votes
        db.execute("UPDATE comments SET votes = votes - 1 WHERE comment_id=?", info["id"])
        # Get comment total votes
    # Check if there is a vote already made by user - comment votes decrease by 2
    elif comment_info[0]["vote"] == 1:
        db.execute("UPDATE comment_votes SET vote=-1 WHERE user_id=? AND comment_id=?", session["user_id"], info["id"])
        db.execute("UPDATE comments SET votes = votes - 2 WHERE comment_id=?", info["id"])
    # Check if there is a downvote made by user - comment votes increase by 1
    # Special condition
    elif comment_info[0]["vote"] == -1:
        db.execute("UPDATE comment_votes SET vote=0 WHERE user_id=? AND comment_id=?", session["user_id"], info["id"])
        db.execute("UPDATE comments SET votes = votes + 1 WHERE comment_id=?", info["id"])
        isUnvote = "true"
    # Check if there is no vote - comment votes decrease by 1
    else:
        db.execute("UPDATE comment_votes SET vote=-1 WHERE user_id=? AND comment_id=?", session["user_id"], info["id"])
        db.execute("UPDATE comments SET votes = votes - 1 WHERE comment_id=?", info["id"])

    return isUnvote

def parseAllToDatetimeObj(blocks):
    # Convert datetime string back to datetime obj
    for block in blocks:
        block["date"] = datetime.strptime(block["date"], "%Y-%m-%d %H:%M:%S")

# https://flask.palletsprojects.com/en/2.0.x/patterns/fileuploads/
def allowedFile(filename):
    # Returns false if file does not have extension or if file extension is not allowed,
    # otherwise, return true
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# https://stackoverflow.com/questions/22105315/flask-getting-the-size-of-each-file-in-a-request?rq=1
# https://stackoverflow.com/questions/15772975/flask-get-the-size-of-request-files-object
# Get size of file
def getSize(file):
    # Check if file has content length header set, return it if so
    if file.content_length:
        return file.content_length

    try:
        # Start at end reference point, get file length, go back to beginning point
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0, 0)
        return file_size
    except (AttributeError, IOError):
        # Catch exception if file does not support seeking and continue
        pass

    # File doesn't support seeking
    return 0
