import sqlite3

conn = sqlite3.connect("votecount.db")
c = conn.cursor()