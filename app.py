from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from temphelpers import login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

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

# Gives username when signed in
@app.context_processor
def inject_user():
    if "user_id" in session:
        user_info = (db.execute("SELECT username FROM users WHERE id=?", session["user_id"]))[0]
        return user_info
    return dict()

@app.route("/")
@login_required
def index():
    # TODO: Currently sorted by newest, add dropdown to sort any newest, oldest, top voted, less voted
    posts = db.execute("SELECT post_id, content, votes, title, username FROM posts JOIN users ON users.id = posts.user_id ORDER BY post_id DESC")

    return render_template("index.html", posts=posts)

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

        title = request.form.get("title")
        if not title:
            flash("Title input is blank", "danger")
            return render_template("newpost.html")
        
        text = request.form.get("text")
        
        db.execute("INSERT INTO posts (user_id, title, content, votes) VALUES (?, ?, ?, ?)", session["user_id"], title, text, 1)

        return redirect("/")
    else:
        return render_template("newpost.html")

@app.route("/post/<id>")
@login_required
def post(id):
    posts = db.execute("SELECT post_id, content, votes, title, username FROM posts JOIN users ON users.id = posts.user_id WHERE post_id = ?", id)
    comments = db.execute("SELECT comments.*, users.username FROM comments JOIN users ON users.id = comments.refuser_id WHERE refpost_id = ?", id)
    return render_template("post.html", posts=posts, comments=comments)

@app.route("/newcomment", methods=["POST"])
@login_required
def newcomment():
    textarea = request.get_json()

    # TODO: Check if textarea["text"] is empty, if empty, redirect to post id with flashed error message

    # Check if comments count is zero to remove no comments label
    count = (db.execute("SELECT COUNT(comment_id) FROM comments WHERE refpost_id=?", textarea["post_id"]))[0]["COUNT(comment_id)"]
    if count != 0:
        textarea["nocomments"] = "false"
    else:
        textarea["nocomments"] = "true"

    db.execute("INSERT INTO comments (refpost_id, refuser_id, comment, votes) VALUES (?, ?, ?, ?)", int(textarea["post_id"]), session["user_id"], textarea["text"], 1)
    username = db.execute("SELECT username FROM users WHERE id=?", session["user_id"])
    textarea["username"] = username[0]["username"]

    # Return constructed information to form a comment
    return textarea

@app.route("/profile/<user>")
@app.route("/profile/<user>/posts", endpoint="profile-posts")
@app.route("/profile/<user>/comments", endpoint="profile-comments")
@login_required
def profile(user):
    # TODO: index homepage will use this func -> search any user's profile
    
    # Check if user is valid
    user_id = db.execute("SELECT id FROM users WHERE username=?", user)
    if len(user_id) == 0:
        flash("Username does not exist", "danger")
        return redirect("/")
    user_id = user_id[0]["id"]

    if request.endpoint == "profile-posts":
        # TODO: Currently sorted by newest, add dropdown to sort any newest, oldest, top voted, less voted
        posts = db.execute("SELECT post_id, votes, title FROM posts WHERE user_id=? ORDER BY post_id DESC", user_id)
        return render_template("profileposts.html", posts=posts, user=user)
    elif request.endpoint == "profile-comments":
        # TODO: Currently sorted by newest, add dropdown to sort any newest, oldest, top voted, less voted
        # DEMO: SELECT comments.*, posts.title, users.username FROM comments JOIN posts ON posts.post_id=comments.refpost_id JOIN users ON posts.user_id=users.id WHERE comments.refuser_id = 1 ORDER BY comment_id DESC;
        comments = db.execute("SELECT comments.*, posts.title, users.username FROM comments JOIN posts ON posts.post_id=comments.refpost_id JOIN users ON posts.user_id=users.id WHERE comments.refuser_id = ? ORDER BY comment_id DESC", user_id)
        return render_template("profilecomments.html", comments=comments, user=user)

    # Endpoint is overview
    # Calculate total reputation for given user
    post_votes = db.execute("SELECT votes FROM posts WHERE user_id=?", user_id)
    comment_votes = db.execute("SELECT votes FROM comments WHERE refuser_id=?", user_id)
    post_count = db.execute("SELECT COUNT(votes) FROM posts WHERE user_id=?", user_id)
    comment_count = db.execute("SELECT COUNT(votes) FROM comments WHERE refuser_id=?", user_id)
    total_rep = 0
    for post in post_votes:
        total_rep += post["votes"]
    for comment in comment_votes:
        total_rep += comment["votes"]
    total_rep -= (post_count[0]["COUNT(votes)"] + comment_count[0]["COUNT(votes)"])

    # Calculate total post contributions
    post_contribution = (db.execute("SELECT COUNT(*) FROM posts WHERE user_id=?", user_id))[0]["COUNT(*)"]

    # Calculate total comment contributions
    comment_contribution = (db.execute("SELECT COUNT(*) FROM comments WHERE refuser_id=?", user_id))[0]["COUNT(*)"]

    return render_template("profile.html", total_rep=total_rep, post_contribution=post_contribution, comment_contribution=comment_contribution, user=user)
