import sqlite3

DB_PATH = "my_database.db"

def query_database(sql: str) -> str:
    """Executes a SQL query and returns the results as a string."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql)

        if sql.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            conn.close()

            if not rows:
                return "No results found."

            # Format as a readable table
            result = " | ".join(columns) + "\n"
            result += "-" * 40 + "\n"
            for row in rows:
                result += " | ".join(str(v) for v in row) + "\n"
            return result
        else:
            conn.commit()
            conn.close()
            return f"Query executed. Rows affected: {cursor.rowcount}"

    except Exception as e:
        return f"Database error: {str(e)}"
