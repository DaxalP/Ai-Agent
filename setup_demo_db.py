import sqlite3

conn = sqlite3.connect("my_database.db")
cursor = conn.cursor()

# Create a sample table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        name TEXT,
        department TEXT,
        salary INTEGER
    )
""")

# Insert sample data
cursor.executemany("INSERT OR IGNORE INTO employees VALUES (?, ?, ?, ?)", [
    (1, "Alice",   "Engineering", 95000),
    (2, "Bob",     "Marketing",   72000),
    (3, "Charlie", "Engineering", 88000),
    (4, "Diana",   "HR",          65000),
    (5, "Eve",     "Engineering", 102000),
])

conn.commit()
conn.close()
print("Database created!")