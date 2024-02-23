import sqlite3

"""
    These are my database tables for ruffleraffle.com,
    if the database has not been created at any point,
    this will set everything up correctly!
"""

# Connect to the database
with sqlite3.connect('database.db') as db:

    print("Connected successfully!")

    # Create users table and unique index
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            hash TEXT NOT NULL
        );

        CREATE UNIQUE INDEX IF NOT EXISTS username ON users (username);
    ''')
    print("Created \"users\" table and added unique indices")


    # Create raffles table
    db.executescript('''
        CREATE TABLE IF NOT EXISTS raffles (
            raffle_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            host_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT 'Description - N/A',
            end_date TEXT NOT NULL,
            num_entries INTEGER DEFAULT 0,
            FOREIGN KEY(host_id) REFERENCES users(id)
        );
    ''')
    print("Created \"raffles\" table")


    # Create entires table
    db.executescript('''
        CREATE TABLE IF NOT EXISTS entries (
            participant_id INTEGER NOT NULL,
            host_id INTEGER NOT NULL,
            raffle_id INTEGER NOT NULL,
            FOREIGN KEY (participant_id) REFERENCES users(id)
        );
    ''')
    print("Created \"entries\" table")

db.close()
