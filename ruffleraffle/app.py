import sqlite3
import random

from flask import Flask, render_template, flash, redirect, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

# Configure application
app = Flask(__name__)

# SHHHH IT'S A SECRET!
app.secret_key = '2d1e6a4f23b4a844ab72ea49509cb0a8'

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.after_request
def after_request(response):
    # Ensure responses aren't cached
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Set up the index route
@app.route("/")
@login_required
def home():
    with sqlite3.connect('database.db') as db:
        # Query database for username
        # Order all owned raffles by date
        rows = db.execute(
            "SELECT * FROM raffles WHERE host_id = ? ORDER BY end_date", (session["user_id"],)
        ).fetchall()

        username = db.execute(
            "SELECT username FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()

        return render_template("index.html", raffles=rows, username=username)


# Set up browse all raffles from the db route
@app.route("/browse")
@login_required
def browse():
    with sqlite3.connect('database.db') as db:
        # Query database for user_id
        logged_in_user = session["user_id"]

        # Order all raffles by Participation > Ownership > Number of Entries
        rows = db.execute("""
            SELECT raffle.*, user.username, entry.participant_id, entry.participant_id AS is_participating
            FROM raffles AS raffle
            JOIN users AS user ON raffle.host_id = user.id
            LEFT JOIN entries AS entry ON entry.raffle_id = raffle.raffle_id AND entry.participant_id = ?
            ORDER BY
                is_participating DESC,
                CASE WHEN raffle.host_id = ? THEN 0 ELSE 1 END,
                raffle.num_entries DESC
        """, (logged_in_user, logged_in_user)).fetchall()

        return render_template("browse_all.html", raffles=rows)


# Set up the login route
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    with sqlite3.connect('database.db') as db:
        cursor = db.cursor()

        # User reached route via POST (as by submitting a form via POST)
        if request.method == "POST":
            # Ensure username was submitted, Fail safe for if user deletes "required" field in HTML
            if not request.form.get("username"):
                return render_template("sorry.html")

            # Ensure password was submitted
            elif not request.form.get("password"):
                return render_template("sorry.html")

            # Query database for username
            rows = cursor.execute(
                "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)
            ).fetchall()

            # Ensure username exists and password is correct
            if len(rows) != 1 or not check_password_hash(
                rows[0][3], request.form.get("password")
            ):
                flash("Wrong username or password, try again!")
                return render_template("login.html")

            # Remember which user has logged in
            session["user_id"] = rows[0][0]

            flash("You have been logged in successfully!")
            return redirect("/")

        # User reached route via GET (as by clicking a link or via redirect)
        else:
            return render_template("login.html")


# Set up the logout route
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash(
        f"You have been logged out!"
    )
    return render_template("login.html")


# Set up the register route
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    with sqlite3.connect('database.db') as db:
        cursor = db.cursor()
        # Check all fields are filled (and check password)
        # If confirmation field is empty just return the mismatch apology to save memory
        if request.method == "POST":
            # Fail safe for if user deletes "required" field in HTML
            if not request.form.get("username") or not request.form.get("password") or not request.form.get("email"):
                return render_template("sorry.html")

            elif request.form.get("confirmation") != request.form.get("password"):
                flash("Passwords do not match, try again!")
                return render_template("register.html")
            
            if len(request.form.get("password")) < 8:
                flash("Minimum character length is 8, try again!")
                return render_template("register.html")

            # Insert the user information into the database
            username = request.form.get("username")
            email = request.form.get("email")
            hashed_password = generate_password_hash(
                request.form.get("password"), method="pbkdf2", salt_length=16
            )

            # Check if the username already exists
            user_name_exists = cursor.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()

            if user_name_exists:
                flash("Username already taken, try again!")
                return render_template("register.html")
            
            # Check if the email already exists
            email_exists = cursor.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()

            if email_exists:
                flash("Email address already taken, try again!")
                return render_template("register.html")

            cursor.execute("INSERT INTO users (username, email, hash) VALUES(?, ?, ?)", (username, email, hashed_password))

            db.commit()

            # Log the user in immediately after registering
            rows = cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchall()
            session["user_id"] = rows[0][0]

            # Take them to the home page
            flash("You have been logged in successfully!")
            return redirect("/")

        # User is just stopping by, display the form
        else:
            return render_template("register.html")


# Set up the create new raffle route
@app.route("/new", methods=["GET", "POST"])
@login_required
def create_raffle():
    """Add a new raffle to the database!"""

    with sqlite3.connect('database.db') as db:
        cursor = db.cursor()
        if request.method == "POST":
            # Get all raffle info as variables for easy use
            host_id = session["user_id"]
            title = request.form.get("title")
            description = request.form.get("description")
            end_date = request.form.get("end_date")

            # Fail safe for if user deletes "required" field in HTML
            if not title or not end_date:
                return render_template("sorry.html")

            # Check if the Description field is empty and add data accordingly
            has_description = request.form.get("description")
            if has_description is None or not has_description:
                # Insert the user information into the database without the description
                cursor.execute("INSERT INTO raffles (host_id, title, end_date) VALUES (?, ?, ?)", (host_id, title, end_date))

                db.commit()

                flash("Your raffle has been created successfully!")
                return redirect("/")

            else:
                # Insert the user information into the database with the description
                cursor.execute("INSERT INTO raffles (host_id, title, description, end_date) VALUES (?, ?, ?, ?)", (host_id, title, description, end_date))

                db.commit()

                flash("Your raffle has been created successfully!")
                return redirect("/")

        # User is just stopping by, display the form
        else:
            return render_template("create_raffle.html")


# Set up the edit route
@app.route("/edit/<int:raffle_id>", methods=["GET", "POST"])
@login_required
def edit(raffle_id):
    """Update or delete a specific raffle in the database!"""
    with sqlite3.connect('database.db') as db:
        cursor = db.cursor()

        if request.method == "POST":
            # Get all raffle info as variables for easy use
            logged_in_user = session["user_id"]
            edited_title = request.form.get("edited_title")
            edited_description = request.form.get("edited_description")
            edited_end_date = request.form.get("edited_end_date")

            # This is the old description
            description = cursor.execute("SELECT description FROM raffles WHERE host_id = ? AND raffle_id = ?", (logged_in_user, raffle_id,)).fetchone()[0]

            # Fail safe for if the user deletes "required" field in HTML
            if not edited_title or not edited_end_date:
                return render_template("sorry.html")

            """Series of checks to see if the Description should be changed, defaulted to, or nothing at all"""
            # Description Deleted
            if not edited_description:
                filler_description = "Description - N/A"
                cursor.execute("UPDATE raffles SET title = ?, description = ?, end_date = ? WHERE host_id = ? AND raffle_id = ?", (edited_title, filler_description, edited_end_date, logged_in_user, raffle_id))

                db.commit()

            # Description the same as before
            elif edited_description == description:
                cursor.execute("UPDATE raffles SET title = ?, end_date = ? WHERE host_id = ? AND raffle_id = ?", (edited_title, edited_end_date, logged_in_user, raffle_id))

                db.commit()

            # New description
            else:
                # Insert the user information into the database with the description
                cursor.execute("UPDATE raffles SET title = ?, description = ?, end_date = ? WHERE host_id = ? AND raffle_id = ?", (edited_title, edited_description, edited_end_date, logged_in_user, raffle_id))

                db.commit()

            flash("Your raffle has been updated successfully!")
            return redirect("/")

        else:
            # Handle GET request for displaying the form for editing
            # Retrieve the specific raffle using the title
            raffle = cursor.execute("SELECT * FROM raffles WHERE host_id = ? AND raffle_id = ?", (session["user_id"], raffle_id)).fetchone()

            return render_template("edit.html", raffle=raffle)




# Set up the delete route
@app.route("/delete")
@login_required
def delete():
    """Removed a raffle from the database and all relating info!"""
    with sqlite3.connect('database.db') as db:
        cursor = db.cursor()

        logged_in_user = session["user_id"]
        raffle_id = request.args.get('raffle_id')

        # Delete the raffle information from the database
        cursor.execute("DELETE FROM raffles WHERE host_id = ? AND raffle_id = ?", (logged_in_user, raffle_id))
        cursor.execute("DELETE FROM entries WHERE host_id = ? AND raffle_id = ?", (logged_in_user, raffle_id))

        db.commit()

        flash("Your raffle has been deleted successfully!")
        return redirect("/")


# Enter a raffle
@app.route("/enter")
@login_required
def enter():
    """Enter a user and display there username on the database!"""
    with sqlite3.connect('database.db') as db:
        cursor = db.cursor()

        # Imported information
        logged_in_user = session["user_id"]
        raffle_id = request.args.get('raffle_id')

        # Get all needed info for updating tables
        result = cursor.execute("""
            SELECT num_entries, host_id
            FROM raffles
            WHERE raffle_id = ?
        """, (raffle_id,)).fetchone()

        if result:
            current_num_entries = result[0]
            host_id = result[1]
        else:
            # Handle the case where the raffle_id doesn't exist
            flash("Raffle not found!")
            return redirect("/browse")

        # Check if the user has already entered this raffle
        existing_entry = cursor.execute("""
            SELECT 1
            FROM entries
            WHERE participant_id = ? AND raffle_id = ?
        """, (logged_in_user, raffle_id)).fetchone()

        if existing_entry:
            flash("You are already entered in this raffle!")
            return redirect("/browse")

        # Then increment "current_num_entries" by 1
        new_num_entries = current_num_entries + 1
        cursor.execute("UPDATE raffles SET num_entries = ? WHERE host_id = ? AND raffle_id = ?", (new_num_entries, host_id, raffle_id))

        db.commit()
    
        # Change the entries table
        cursor.execute("INSERT INTO entries (participant_id, host_id, raffle_id) VALUES (?, ?, ?)", (logged_in_user, host_id, raffle_id))

        db.commit()

        flash("You have entered!")
        return redirect("/browse")


# Set up the viewing all entries a specific raffle has
@app.route("/view_raffle/<int:raffle_id>", methods=["GET", "POST"])
@login_required
def view_raffle(raffle_id):
    """view all entries for a raffle in the database!"""
    with sqlite3.connect('database.db') as db:
        cursor = db.cursor()

        # Get all entries and relevant information too
        entries = cursor.execute("""
                SELECT entries.*, users.email, users.username
                FROM entries
                JOIN users ON entries.participant_id = users.id
                WHERE entries.raffle_id = ?
            """, (raffle_id,)).fetchall()

        if request.method == "POST":
            """
            "entries" is a tuple, thus I will add the usernames to a list via .append
            then I will randomly select a username.
            Lastly I will select all user information with that username and render the new winner.html template
            with that information
            """
            # Get all usernames that are entered in this raffle
            usernames = []
            for entry in entries:
                usernames.append(entry[4])

            # Pick a winner
            if not usernames or usernames == None:
                flash("Cannot choose a winner if there are no entries!")
                return redirect("/")
            else:
                winner = random.choice(usernames)

            # Get all info about the winner and pass it to the html page
            # winner_info[0] = username | winner_info[1] = email
            winner_info = cursor.execute("SELECT username, email FROM users WHERE username = ?", (winner,)).fetchone()

            flash(f"We have a winner!")
            return render_template("winner.html", winner_info=winner_info)

        else:
            # Handle GET request for displaying the form for editing
            # Retrieve the specific raffle using the title
            raffle = cursor.execute("SELECT * FROM raffles WHERE host_id = ? AND raffle_id = ?", (session["user_id"], raffle_id)).fetchone()

            return render_template("view.html", raffle=raffle, entries=entries)


# Set up the viewing of raffles the account has entered in
@app.route("/view_entries", methods=["GET", "POST"])
@login_required
def view_entries():
    """view all entries for a raffle in the database!"""
    with sqlite3.connect('database.db') as db:
        cursor = db.cursor()

        # Handle GET request for displaying the form for editing
        # Retrieve the raffle information for the logged-in user
        raffles = cursor.execute("""
            SELECT raffles.*, users.username AS participant_username, hosts.username AS host_username
            FROM raffles
            JOIN entries ON raffles.raffle_id = entries.raffle_id
            JOIN users ON entries.participant_id = users.id
            JOIN users AS hosts ON raffles.host_id = hosts.id
            WHERE entries.participant_id = ?
        """, (session["user_id"],)).fetchall()

        return render_template("view_entries.html", raffles=raffles)


# Set up the leave raffle route
@app.route("/leave_raffle")
@login_required
def leave_raffle():
    """Opt out of a raffle as the user chooses!"""
    with sqlite3.connect('database.db') as db:
        cursor = db.cursor()

        logged_in_user = session["user_id"]
        raffle_id = request.args.get('raffle_id')

        # Get current num of entries on this raffle
        result = cursor.execute("SELECT num_entries FROM raffles WHERE raffle_id = ?", (raffle_id,)).fetchone()

        if result:
            current_num_entries = result[0]
        else:
            # Handle the case where the raffle_id doesn't exist
            flash("Raffle not found!")
            return redirect("/view_entries")
        
        new_num_entries = current_num_entries - 1

        # Remove user from the entries table under raffle_id
        cursor.execute("DELETE FROM entries WHERE participant_id = ? AND raffle_id = ?", (logged_in_user, raffle_id))
        cursor.execute("UPDATE raffles SET num_entries = ? WHERE raffle_id = ?", (new_num_entries, raffle_id))

        db.commit()

        flash("You have left the raffle!")
        return redirect("/view_entries")


# Set up the account route
@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    with sqlite3.connect('database.db') as db:
        cursor = db.cursor()

        # Get all logged in user's information
        user_info = cursor.execute(
            "SELECT * FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()

        # Handle GET request
        return render_template("account.html", user_info=user_info)


# Add changed username
@app.route("/new_username", methods=["GET", "POST"])
@login_required
def new_username():
    """Change username"""
    with sqlite3.connect('database.db') as db:
        cursor = db.cursor()

        check_user_in_html = []
        check_user_in_html.append(session["user_id"])

        logged_in_user = session["user_id"]

        # Get all logged in user's information
        user_info = cursor.execute(
            "SELECT * FROM users WHERE id = ?", (logged_in_user,)
        ).fetchone()

        if request.method == "POST":
            """
            Make sure new username is not the same as the previous #########
            """
            new_username = request.form.get("new_username")
            current_password = request.form.get("current_password")

            if not current_password or not new_username:
                return render_template("sorry.html")

            # Ensure password is correct
            if not check_password_hash(
                user_info[3], current_password
            ):
                flash("Wrong password, try again!")
                return redirect("/new_username")

            if new_username == user_info[1]:
                flash("Username cannot be the same as before!")
                return redirect("/new_username")
            
            # Check if the username already exists
            user_name_exists = cursor.execute(
                "SELECT id FROM users WHERE username = ?", (new_username,)
            ).fetchone()

            if user_name_exists:
                flash("Username already taken, try again!")
                return redirect("/new_username")

            cursor.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, logged_in_user))
            db.commit()

            # Forget any user_id
            session.clear()

            # Redirect user to login form
            flash(
                f"Account information has changed, please log in again"
            )
            return render_template("login.html")


        else:
            return render_template("new_username.html", check_user_in_html=check_user_in_html)


# Add changed email
@app.route("/new_email", methods=["GET", "POST"])
@login_required
def new_email():
    """Change email!"""
    with sqlite3.connect('database.db') as db:
        cursor = db.cursor()

        check_user_in_html = []
        check_user_in_html.append(session["user_id"])

        logged_in_user = session["user_id"]

        # Get all logged in user's information
        user_info = cursor.execute(
            "SELECT * FROM users WHERE id = ?", (logged_in_user,)
        ).fetchone()

        if request.method == "POST":
            """
            Make sure new email is not the same as the previous #########
            """
            new_email = request.form.get("new_email")
            current_password = request.form.get("current_password")

            if not current_password or not new_email:
                return render_template("sorry.html")

            # Ensure password is correct
            if not check_password_hash(
                user_info[3], current_password
            ):
                flash("Wrong password, try again!")
                return redirect("/new_email")

            if new_email == user_info[2]:
                flash("Email address cannot be the same as before!")
                return redirect("/new_email")
            
            # Check if the email already exists
            email_exists = cursor.execute(
                "SELECT id FROM users WHERE email = ?", (new_email,)
            ).fetchone()

            if email_exists:
                flash("Email address already taken, try again!")
                return redirect("/new_email")

            cursor.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, logged_in_user))
            db.commit()

            # Forget any user_id
            session.clear()

            # Redirect user to login form
            flash(
                f"Account information has changed, please log in again"
            )
            return render_template("login.html")

        else:
            return render_template("new_email.html", check_user_in_html=check_user_in_html)


# Add changed password
@app.route("/new_password", methods=["GET", "POST"])
@login_required
def new_password():
    """Change password!"""
    with sqlite3.connect('database.db') as db:
        cursor = db.cursor()

        check_user_in_html = []
        check_user_in_html.append(session["user_id"])

        logged_in_user = session["user_id"]

        # Get all logged in user's information
        user_info = cursor.execute(
            "SELECT * FROM users WHERE id = ?", (logged_in_user,)
        ).fetchone()

        if request.method == "POST":
            current_password = request.form.get("current_password")
            new_password = request.form.get("new_password")
            new_confirmation = request.form.get("new_confirmation")

            if not current_password or not new_password or not new_confirmation:
                return render_template("sorry.html")
            
            if len(request.form.get("new_password")) < 8:
                flash("Minimum character length is 8, try again!")
                return redirect("/new_password")

            # Ensure password is correct
            if not check_password_hash(
                user_info[3], current_password
            ):
                flash("Wrong password, try again!")
                return redirect("/new_password")

            # Check if the password is the same as before
            if check_password_hash(
                user_info[3], new_password
            ):
                flash("Cannot use the same password as before, try again!")
                return redirect("/new_password")

            # Check that the password matches the confirmation
            elif new_password != new_confirmation:
                flash("Passwords do not match, try again!")
                return redirect("/new_password")
            
            new_hashed_password = generate_password_hash(
                new_password, method="pbkdf2", salt_length=16
            )

            cursor.execute("UPDATE users SET hash = ? WHERE id = ?", (new_hashed_password, logged_in_user))
            db.commit()

            # Forget any user_id
            session.clear()

            # Redirect user to login form
            flash(
                f"Account information has changed, please log in again"
            )
            return render_template("login.html")

        else:
            return render_template("new_password.html", check_user_in_html=check_user_in_html)


# Set the route to delete an account permanently
@app.route("/delete_account")
@login_required
def delete_account():
    """Remove your acount permanently!"""
    with sqlite3.connect('database.db') as db:
        cursor = db.cursor()

        logged_in_user = session["user_id"]


        """Retrieve and delete all owned raffles"""
        owned_raffles = cursor.execute("SELECT raffle_id FROM raffles WHERE host_id = ? ",(logged_in_user,)).fetchall()
        for id in owned_raffles:
            cursor.execute("DELETE FROM raffles WHERE raffle_id = ?", (id[0],))
        
            db.commit()


        """Remove 1 num from every raffle where the user is entered and Delete entries"""
        raffle_entered_ids = cursor.execute("SELECT raffle_id FROM entries WHERE participant_id = ?", (logged_in_user,)).fetchall()

        for id in raffle_entered_ids:
            # Get current num of entries on this raffle
            result = cursor.execute("SELECT num_entries FROM raffles WHERE raffle_id = ?", (id[0],)).fetchone()

            num_entries_per_raffle = result[0]
            new_num_entries = num_entries_per_raffle - 1

            cursor.execute("UPDATE raffles SET num_entries = ? WHERE raffle_id = ?", (new_num_entries, id[0]))

            db.commit()

            cursor.execute("DELETE FROM entries WHERE participant_id = ?", (logged_in_user,))

            db.commit()


        """Remove user from the entries table under raffle_id"""
        cursor.execute("DELETE FROM users WHERE id = ?", (logged_in_user,))
        
        db.commit()

        # Forget any user_id
        session.clear()

        # Redirect user to login form
        flash(f"Your account has been deleted, have a nice day!")
        return render_template("login.html")
