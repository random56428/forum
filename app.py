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

@app.route("/")
@login_required
def index():

    posts = db.execute("SELECT post_id, content, votes, title, username FROM posts JOIN users ON users.id = posts.user_id")

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
    data = request.get_json()
    print(data)
    return data