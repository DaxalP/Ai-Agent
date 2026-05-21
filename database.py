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


def get_db_schema() -> str:
    """Returns the SQLite database schema so the LLM knows what tables and columns exist."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        schema = ""
        for (table,) in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            schema += f"\nTable: {table}\n"
            for col in columns:
                schema += f"  - {col[1]} ({col[2]})\n"
        conn.close()
        return schema if schema else "No tables found."
    except Exception as e:
        return f"Schema error: {str(e)}"
