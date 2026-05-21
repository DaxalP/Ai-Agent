"""
database_tool.py — runs SQL queries against the SQLite database.
"""

import sqlite3
import config


# ── JSON schema (sent to the LLM) ────────────────────────────────────────────
SCHEMA = {
    "type": "function",
    "function": {
        "name": "query_database",
        "description": (
            "Runs a SQL query against the database. "
            "Use for any question about data stored in the DB."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "The SQL query to run (e.g. SELECT * FROM employees WHERE salary > 80000)"
                }
            },
            "required": ["sql"]
        }
    }
}


# ── Implementation ────────────────────────────────────────────────────────────
def query_database(sql: str) -> str:
    """Executes a SQL query and returns the results as a formatted string."""
    try:
        conn = sqlite3.connect(config.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql)

        if sql.strip().upper().startswith("SELECT"):
            rows    = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            conn.close()

            if not rows:
                return "No results found."

            col_widths = [max(len(c), max(len(str(r[i])) for r in rows))
                          for i, c in enumerate(columns)]
            sep  = "-+-".join("-" * w for w in col_widths)
            header = " | ".join(c.ljust(col_widths[i]) for i, c in enumerate(columns))
            lines  = [header, sep]
            for row in rows:
                lines.append(" | ".join(str(v).ljust(col_widths[i]) for i, v in enumerate(row)))
            return "\n".join(lines)
        else:
            conn.commit()
            conn.close()
            return f"Query executed successfully. Rows affected: {cursor.rowcount}"

    except Exception as e:
        return f"Database error: {str(e)}"


def get_db_schema() -> str:
    """Returns the full database schema so the LLM knows what tables and columns exist."""
    try:
        conn   = sqlite3.connect(config.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        schema = ""
        for (table,) in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            schema += f"\nTable: {table}  ({row_count} rows)\n"
            for col in columns:
                pk_marker = " [PK]" if col[5] else ""
                schema += f"  - {col[1]} ({col[2]}){pk_marker}\n"
        conn.close()
        return schema if schema else "No tables found."
    except Exception as e:
        return f"Schema error: {str(e)}"
