# Ruffle Raffle - Harvard CS50 Final Project

## Video Showcase - [My Final Project](https://www.youtube.com/watch?v=bCH4q7l3HAI)

## Summary
I created this webapp for my final project to serve as a tool for people like myself (artists and others) when hosting giveaways/raffles.

The app allows you to Create raffles, edit/delete/view existing raffles you own, and also browse all raffles in the database.

## MISC:
My site does use Flash messages all throughout to tell the user when something isn't working or if their info is wrong.

If the users delete my required information such as in my forms, I render a "sorry.html" file.

I also have many safe checks built into my app, such as:

Password length must be greater than 8 characters and that the raffles have AT LEAST ONE entry when selecting a winner.

Which handled each of my tests (there may be errors I missed, but I believe it is 99% good-to-go)

Furthermore, after mentioning this, I will not go into detail where the safety checks are as that would take too long and not be very coherent.

## Description - app.py
Since the app was made in flask, I will start by listing the main routes in the app.py file and giving descriptions on them.

I will then move onto any important stuff in the templates/static folder (most is basic HTML and CSS so I won't go very deep into that.)

Lastly I will discuss any specific design choices I made, and what specific users can do/see (the different features for Hosts, Users and Participants)

All right, let's get into this!

### Home:
---
ROUTE NAME: "/"

This is the home page of the website, which simply queries the database for all raffles the current logged in user owns, and hands them over to "index.html" which displays them (if any exist).

### Browse Raffles in the DB:
---
ROUTE NAME: "/browse"

This route queries for all raffles in the DB and orders them:

First by Participation (If the logged in user has entered a raffle), Secondly by Ownership (Raffles the user owns) and Lastly by Number of Entries (How many people have entered the raffle).

It then sends then over to "browse_all.html" which displays them all (if any exist)

### Login/Logout/Register Pages:
---
ROUTE NAMES: "/login" -- "/logout" -- "/register"

#### Login:
Display a form.

Take in the user's information from the form they submit and check it against all usernames to see if they exist, and then check if the password hashes match to confirm the user is correct. Then set the session["user_id"] to the id that belongs to the username (query DB for id).

#### Logout:

Simply tell the session to forget the user (log them out), and redirect to the login screen.

#### Register:
Display a form.

Take in the user's input from the forms, after querying to see if the username exists in the DB already or not, check that the password is the right length and that the confirmation password matches.

Then hash the password and add all the new information into the "users" DB Table.

Finally, log the user in automatically if the DB command works.

### Create a New Raffle:
---
ROUTE NAME: "/new"

Display a form.

Take the user's information from the forms and run some checks, after we know the title and date are fine, check what state the description is in.

If the description is empty leave it as such, cause the database is set up to automatically fill in with "Description - N/A"

Then add all the new information to the "raffles" DB Table.

### Edit/Delete an Existing Raffle:
---
ROUTE NAMES: "/edit/\<int:raffle_id\>" -- "/delete"

After the edit button is clicked, it sends a request to this route with the raffle id of the specific raffle clicked attached.

#### Edit:

I use this raffle id and the id of the current logged in user (You can only edit something that belongs to you) to query the DB and get all information on this raffle in our local variables, and then hand all this info to the "edit.html" template which is identical to the "create_raffle.html" template except it now has the pre-populated data from my query in the form fields!

Then wait for the user to send a POST response which we then use to capture all their "new" data from the forms.

If all the data is the same, basically do nothing. Otherwise run a few checks for the state of the description and do 1 or 3 queries (just to auto fill in the description if it is blank).

#### Delete:

Use the raffle id and the id of the current logged in user (You can only delete something that belongs to you) to query for and delete a specific raffle in the DB.

### Enter a Raffle:
---
ROUTE NAME: "/enter"

Similar to /edit and /delete, when the user presses the button I use the attached raffle id and the user's id to query the DB and create an entry in the "entries" Table.

### View All Entries a Specific Raffle has: (The names made sense to me at the time xP)
---
ROUTE NAME: "/view_raffle/\<int:raffle_id\>"

Once again similar to /edit, /delete, and now /enter when the user presses the button I use the attached raffle id and the user's id, I query the DB to information regarding the owner (logged in user) and this specific raffle that they own.

I then render another webpage and display all related info, a button that lets you select a random winner (which when clicked runs a short python.choice() function and renders a "winner.html" webpage which displays them.) and a list of all the accounts entered in this raffle.

### View All Raffles the Account has Entered in: (The names made sense to me at the time xP)
---
ROUTE NAME: "/view_entries"

Select all raffles from my DB where the logged in user is a "participant" in the raffle, and give this to the "view_entries.html" page to display all raffles with a "Leave raffle" button if they choose to se it.

### Allow User to Leave a Raffle:
---
ROUTE NAME: "/leave_raffle"

Ok last time now, use the specific raffle id and logged in user id to query for and remove the user from the specific raffle, also role back the number of entries by one.

### Show All Account Options:
---
ROUTE NAME: "/account"

Display most of (besides the password) the user's information to them and give them a few buttons to press.

3x Change buttons which take you to new webpages (username, email, and password).
1x Delete Account button (does what it says).

### Render the Change Username/Email/Password Forms: ***
---
ROUTE NAMES: "/new_username" -- "/new_email" -- "/new_password"

These all do basically the same thing just with a few different checks for each; however, depending on which button was clicked in the account section, we will render a different html page with the required form.

I found this was the best way I could think of to implement this feature, even though there is definitely some lack of some efficiency here.

Use the forms to get the user's info and run checks on the data, then add them to the DB in place of the old (use an UPDATE query)


### Allow the User to Delete Their Account Permanently:
---
ROUTE NAME: "/delete_account"

Allow the user to delete their account, but first remove all trace of them.

Delete all owned raffles based on the logged in user id.

Role back the entries number counter by 1 for every raffle that this user was entered in when they deleted the account.

Delete one other trace in my "entries" DB Table which acts as a history of all entries (and we just removed their entries)

Finally delete the user, log them out, and send them to the login page!


## Description - static/templates folders and design choices

### Stylesheet.css

Utilized a SVG background and changed the colors of the "cards" from bootstrap to create a particular dark theme in my webapp.
I also used bootstrap for all my styling of the buttons and layout of components

### Confirmation buttons

Make sure the user actually wants to delete there account or leave a raffle by promoting them with an onclick function on the related buttons.

## Features available to each user

### Host
  - Create/Edit/Delete Raffles

### User
  - Browse Raffles

### Participant
  - View raffles they are in

## Installation

This is a very basic guide and will be updated in the future, for now it's just this.

You will have to clone the repo, then run the "create_table.py" file and then run the app as you would any other Flask app.

This all assumes that you have the required pip installs set up and know how to use Flask.
(If you know how to use a requirements.txt file. I do have that set up as well!)

I will make a detailed install later on, this is just so I can upload it now.

## Credits

This project was created by Joel Whyle in Flask with Python, HTML, CSS and a little JavaScript.

Thanks to [Codemy.com](https://www.youtube.com/c/Codemycom) for free flask lessons, and [FreeSVGImages](https://www.svgbackgrounds.com/set/free-svg-backgrounds-and-patterns/) for free to use SVG backgrounds which made my site look beautiful.
