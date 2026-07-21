import sqlite3

conn = sqlite3.connect("alerts.db")
cursor = conn.cursor()