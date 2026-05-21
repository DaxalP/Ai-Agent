import sqlite3
import os

# Always write the DB next to this script, regardless of working directory
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "my_database.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Enable foreign key enforcement
cursor.execute("PRAGMA foreign_keys = ON")

# ── Drop existing tables (clean slate) ──────────────────────────────────────
cursor.executescript("""
    DROP TABLE IF EXISTS employee_projects;
    DROP TABLE IF EXISTS projects;
    DROP TABLE IF EXISTS employees;
    DROP TABLE IF EXISTS departments;
""")

# ── 1. departments ───────────────────────────────────────────────────────────
cursor.execute("""
    CREATE TABLE departments (
        id        INTEGER PRIMARY KEY,
        name      TEXT NOT NULL,
        location  TEXT NOT NULL,
        budget    INTEGER NOT NULL
    )
""")

cursor.executemany("INSERT INTO departments VALUES (?, ?, ?, ?)", [
    (1, "Engineering", "New York",    1_500_000),
    (2, "Marketing",   "Los Angeles",   800_000),
    (3, "HR",          "Chicago",       400_000),
    (4, "Finance",     "New York",      600_000),
    (5, "Design",      "San Francisco", 500_000),
])

# ── 2. employees ─────────────────────────────────────────────────────────────
cursor.execute("""
    CREATE TABLE employees (
        id            INTEGER PRIMARY KEY,
        name          TEXT NOT NULL,
        department_id INTEGER NOT NULL REFERENCES departments(id),
        salary        INTEGER NOT NULL,
        hire_date     TEXT NOT NULL
    )
""")

cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?)", [
    (1,  "Alice",    1, 95_000,  "2019-03-15"),
    (2,  "Bob",      2, 72_000,  "2020-07-01"),
    (3,  "Charlie",  1, 88_000,  "2018-11-20"),
    (4,  "Diana",    3, 65_000,  "2021-01-10"),
    (5,  "Eve",      1, 102_000, "2017-06-05"),
    (6,  "Frank",    2, 78_000,  "2022-04-18"),
    (7,  "Grace",    4, 91_000,  "2016-09-30"),
    (8,  "Hank",     5, 85_000,  "2020-02-14"),
    (9,  "Iris",     3, 60_000,  "2023-08-22"),
    (10, "Jack",     4, 97_000,  "2015-12-01"),
])

# ── 3. projects ───────────────────────────────────────────────────────────────
cursor.execute("""
    CREATE TABLE projects (
        id          INTEGER PRIMARY KEY,
        name        TEXT NOT NULL,
        department_id INTEGER NOT NULL REFERENCES departments(id),
        start_date  TEXT NOT NULL,
        end_date    TEXT,
        status      TEXT NOT NULL CHECK(status IN ('active', 'completed', 'on_hold'))
    )
""")

cursor.executemany("INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?)", [
    (1, "API Redesign",        1, "2024-01-01", None,          "active"),
    (2, "Q3 Campaign",         2, "2024-03-01", "2024-06-30",  "completed"),
    (3, "Talent Pipeline",     3, "2024-02-15", None,          "active"),
    (4, "Budget Forecast",     4, "2024-04-01", "2024-09-30",  "completed"),
    (5, "Mobile App",          1, "2023-11-01", None,          "active"),
    (6, "Brand Refresh",       5, "2024-05-01", None,          "active"),
    (7, "Compliance Audit",    4, "2024-06-01", "2024-08-31",  "completed"),
    (8, "Onboarding Revamp",   3, "2024-07-01", None,          "on_hold"),
])

# ── 4. employee_projects (many-to-many) ──────────────────────────────────────
cursor.execute("""
    CREATE TABLE employee_projects (
        employee_id INTEGER NOT NULL REFERENCES employees(id),
        project_id  INTEGER NOT NULL REFERENCES projects(id),
        role        TEXT NOT NULL,
        hours       INTEGER NOT NULL,
        PRIMARY KEY (employee_id, project_id)
    )
""")

cursor.executemany("INSERT INTO employee_projects VALUES (?, ?, ?, ?)", [
    (1,  1, "Lead Engineer",     320),
    (1,  5, "Contributor",       120),
    (3,  1, "Backend Dev",       280),
    (3,  5, "Lead Engineer",     400),
    (5,  1, "Architect",         180),
    (5,  5, "Architect",         200),
    (2,  2, "Campaign Manager",  150),
    (6,  2, "Analyst",            80),
    (6,  6, "Marketing Lead",    200),
    (4,  3, "HR Specialist",     100),
    (9,  3, "Recruiter",          90),
    (9,  8, "Program Manager",    60),
    (7,  4, "Finance Lead",      200),
    (10, 4, "Analyst",           120),
    (10, 7, "Audit Lead",        300),
    (7,  7, "Reviewer",          100),
    (8,  6, "UX Designer",       350),
])

conn.commit()
conn.close()

print("Database setup complete!")
print()
print("Tables created:")
print("  departments      — id, name, location, budget")
print("  employees        — id, name, department_id (FK), salary, hire_date")
print("  projects         — id, name, department_id (FK), start_date, end_date, status")
