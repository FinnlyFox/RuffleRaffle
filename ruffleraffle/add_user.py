import sqlite3
from werkzeug.security import generate_password_hash

"""
    A file to add test usernames with VERY short passwords.
    Assumes the DB exists.
"""

# Connect to the database
with sqlite3.connect('database.db') as db:

    print("Connected successfully!")

    cursor = db.cursor()

    # User information (Change values to add new users as you wish)
    username = "finnly"
    email = 0
    temp_password = "f"

    hash_password = generate_password_hash(
        temp_password, method="pbkdf2", salt_length=16
    )

    # cursor.execute("INSERT INTO users (username, email, hash) VALUES(?, ?, ?)", (username, email, hash_password))
    cursor.execute("UPDATE users SET hash = ?", (hash_password,))

    db.commit()
    print("\nAdded the new user to the database!\n")    

db.close()


# User information to showcase the website
#
"""  username - password  """
# 
# ////  [fox] - [f]  ////
# 
# ////  [f] - [f]  ////
# 
# ////  [g] - [f]  ////
# 
# ////  [Luz Noceda] - [f]  ////
# 
# ////  [finnly] - [f]  ////
